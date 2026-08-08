"""Build a cited prompt from retrieved chunks and generate an answer.

Two generation backends, both free (zero monetary cost, matching this
project's zero-budget constraint):

- Groq (default when GROQ_API_KEY is set): a free-tier hosted inference API.
  Chosen specifically to get generation off local CPU -- on a machine under
  real background load (other apps, other processes competing for cores),
  local CPU inference of even a small model can take 60-90+ seconds despite
  the model itself only needing ~1 second of compute once loaded. Groq's
  LPU hardware serves open models (Llama, etc.) fast regardless of what else
  is running locally.
- Ollama (fallback when no GROQ_API_KEY is set): fully local, no external
  calls at all -- what eval/evaluate.py and eval/check_retrieval.py assume,
  and useful for anyone running this project offline.
"""

import os
import re
import time

from dotenv import load_dotenv

from src.config.prompts import ACTIVE_SYSTEM_PROMPT, build_user_prompt
from src.guardrails import scan_chunks
from src.observability import log_event
from src.rerank import is_confident, rerank
from src.retrieve import hybrid_search

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
# Ollama defaults to the model's max supported context (131072 for llama3.2)
# when no num_ctx is given, which allocates a proportionally huge KV cache
# (17GB for this model) and slows every CPU-bound forward pass -- even
# though our actual prompts (top_k=5 chunks @ up to 700 tokens each, plus
# system prompt and question) never exceed ~4000 tokens. num_predict caps
# generation length, the other lever for wall-clock time on CPU since
# tokens are generated sequentially.
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "6144"))
OLLAMA_NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", "400"))

REFUSAL_MESSAGE = "I don't have enough grounded information in the corpus to answer this confidently."

# Small talk ("hi", "thanks") has no corpus match, so it fell through to the
# same REFUSAL_MESSAGE as a genuine out-of-scope question -- correct by the
# citation-enforcement logic (nothing to ground it in), but confusing UX: a
# greeting and a real refused question read identically to a first-time
# user. Handled before retrieval runs at all, so it's instant and doesn't
# cost a generation call. Logged as its own "chitchat" outcome (not
# "refused") so it doesn't distort the refusal-rate metric used in eval.
_CHITCHAT_PATTERN = re.compile(
    r"^\s*(hi|hello|hey|yo|howdy|good\s?(morning|afternoon|evening)|how'?s?\s+it\s+going|"
    r"how\s+are\s+you|what'?s\s+up|sup|thanks?|thank\s+you|thx|ty|bye|goodbye|see\s+ya)[\s!.,?]*$",
    re.IGNORECASE,
)
CHITCHAT_RESPONSE = (
    "Hi! I'm a research assistant over a curated corpus of real AI/LLM production incidents. "
    "Try asking something like \"Why did Uber run out of its 2026 AI budget so fast?\" or pick one "
    "of the example questions above."
)

# Published list pricing, $ per million tokens (source: Groq's pricing page,
# cross-checked 2026-08-08 -- verify at console.groq.com/pricing before
# relying on this for real budgeting, list prices change). We're on Groq's
# free tier so nothing is actually billed, but tracking what usage *would*
# cost at list price is the real production skill -- it's what lets you
# catch a cost blowup (see this project's own Uber source) before it
# happens, not just explain it after. Local Ollama generation has no
# per-token cost at all -- self-hosted compute on hardware you already
# have, not a billed API -- logged as exactly $0.0, not "unknown."
GROQ_PRICING_PER_MILLION_TOKENS = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
}

_groq_client = None
_ollama_client = None


GROQ_MAX_RETRIES = int(os.environ.get("GROQ_MAX_RETRIES", "3"))


def _generate_groq(user_prompt: str) -> tuple[str, dict]:
    global _groq_client
    from groq import RateLimitError

    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)

    # Free tier caps tokens-per-minute (6000 TPM at time of writing), not
    # just requests -- a burst of real questions with several KB of
    # retrieved context each can exceed that well before hitting a request
    # count limit. Discovered for real in CI (eval/check_generation_quality.py
    # firing 9 sequential questions), not theoretical. Exponential backoff
    # rather than failing outright -- the API's own error message reports
    # the wait is typically under 2 seconds.
    for attempt in range(GROQ_MAX_RETRIES):
        try:
            response = _groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": ACTIVE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_tokens=OLLAMA_NUM_PREDICT,
            )
            break
        except RateLimitError:
            if attempt == GROQ_MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)  # 1s, 2s, 4s, ...

    usage = {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens}
    return response.choices[0].message.content, usage


def _generate_ollama(user_prompt: str) -> tuple[str, dict]:
    global _ollama_client
    if _ollama_client is None:
        import ollama
        _ollama_client = ollama.Client()

    response = _ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": ACTIVE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        options={"num_ctx": OLLAMA_NUM_CTX, "num_predict": OLLAMA_NUM_PREDICT},
    )
    usage = {"input_tokens": response["prompt_eval_count"], "output_tokens": response["eval_count"]}
    return response["message"]["content"], usage


def _generate(user_prompt: str) -> tuple[str, dict]:
    if GROQ_API_KEY:
        return _generate_groq(user_prompt)
    return _generate_ollama(user_prompt)


def _estimate_cost_usd(backend: str, model: str, usage: dict) -> float | None:
    if backend == "ollama":
        return 0.0  # self-hosted compute, genuinely not a billed API
    rates = GROQ_PRICING_PER_MILLION_TOKENS.get(model)
    if not rates:
        return None  # unpriced model -- don't guess
    return (usage["input_tokens"] * rates["input"] + usage["output_tokens"] * rates["output"]) / 1_000_000


def answer_question(question: str, top_k: int = 5) -> dict:
    """Hybrid-retrieve (vector + BM25) and cross-encoder rerank down to
    top_k, then generate a cited answer. Refuses when even the best
    reranked match isn't relevant enough to trust. Every call is logged
    (see src/observability.py) with per-stage latency and outcome."""
    t0 = time.perf_counter()

    if _CHITCHAT_PATTERN.match(question):
        log_event({
            "question": question,
            "outcome": "chitchat",
            "backend": None,
            "retrieval_ms": None,
            "rerank_ms": None,
            "generation_ms": None,
            "total_ms": round((time.perf_counter() - t0) * 1000, 1),
            "retrieved_source_ids": [],
            "injection_flags": {},
        })
        return {"answer": CHITCHAT_RESPONSE, "chunks": [], "refused": False}

    candidates = hybrid_search(question)
    t1 = time.perf_counter()
    chunks = rerank(question, candidates, top_k=top_k)
    t2 = time.perf_counter()

    retrieval_ms = round((t1 - t0) * 1000, 1)
    rerank_ms = round((t2 - t1) * 1000, 1)
    retrieved_source_ids = [c["id"] for c in chunks]
    injection_flags = scan_chunks(chunks)
    if injection_flags:
        # Flag, don't block -- see src/guardrails.py for why. Visible in the
        # observability log either way, refused or answered.
        print(f"[guardrails] possible prompt injection in retrieved content: {injection_flags}")

    if not is_confident(chunks):
        log_event({
            "question": question,
            "outcome": "refused",
            "backend": None,
            "retrieval_ms": retrieval_ms,
            "rerank_ms": rerank_ms,
            "generation_ms": None,
            "total_ms": round((time.perf_counter() - t0) * 1000, 1),
            "retrieved_source_ids": retrieved_source_ids,
            "injection_flags": injection_flags,
        })
        return {"answer": REFUSAL_MESSAGE, "chunks": chunks, "refused": True}

    user_prompt = build_user_prompt(question, chunks)
    backend = "groq" if GROQ_API_KEY else "ollama"
    model = GROQ_MODEL if backend == "groq" else OLLAMA_MODEL
    t3 = time.perf_counter()
    try:
        answer_text, usage = _generate(user_prompt)
    except Exception as e:
        log_event({
            "question": question,
            "outcome": "error",
            "backend": backend,
            "retrieval_ms": retrieval_ms,
            "rerank_ms": rerank_ms,
            "generation_ms": round((time.perf_counter() - t3) * 1000, 1),
            "total_ms": round((time.perf_counter() - t0) * 1000, 1),
            "retrieved_source_ids": retrieved_source_ids,
            "injection_flags": injection_flags,
            "error": str(e),
        })
        raise

    log_event({
        "question": question,
        "outcome": "answered",
        "backend": backend,
        "retrieval_ms": retrieval_ms,
        "rerank_ms": rerank_ms,
        "generation_ms": round((time.perf_counter() - t3) * 1000, 1),
        "total_ms": round((time.perf_counter() - t0) * 1000, 1),
        "retrieved_source_ids": retrieved_source_ids,
        "injection_flags": injection_flags,
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "estimated_cost_usd": _estimate_cost_usd(backend, model, usage),
    })

    return {"answer": answer_text, "chunks": chunks, "refused": False}


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Why was Anthropic's silent Claude quality degradation in 2025 hard to detect?"
    result = answer_question(question)
    print(f"Q: {question}\n\n{result['answer']}\n")
    if not result["refused"]:
        print("Sources:")
        for c in result["chunks"]:
            print(f"  - {c['metadata']['source_company']}: {c['metadata']['incident_title']} ({c['metadata']['source_url']})")
