"""Build a cited prompt from retrieved chunks and generate an answer via a local Ollama model."""

import os

from dotenv import load_dotenv

from src.config.prompts import ACTIVE_SYSTEM_PROMPT, build_user_prompt
from src.rerank import is_confident, rerank
from src.retrieve import hybrid_search

load_dotenv()

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
REFUSAL_MESSAGE = "I don't have enough grounded information in the corpus to answer this confidently."

_ollama_client = None


def _generate_ollama(user_prompt: str) -> str:
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
    )
    return response["message"]["content"]


def answer_question(question: str, top_k: int = 5) -> dict:
    """Hybrid-retrieve (vector + BM25) and cross-encoder rerank down to
    top_k, then generate a cited answer. Refuses when even the best
    reranked match isn't relevant enough to trust."""
    candidates = hybrid_search(question)
    chunks = rerank(question, candidates, top_k=top_k)

    if not is_confident(chunks):
        return {"answer": REFUSAL_MESSAGE, "chunks": chunks, "refused": True}

    user_prompt = build_user_prompt(question, chunks)
    answer_text = _generate_ollama(user_prompt)

    return {"answer": answer_text, "chunks": chunks, "refused": False}


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "What causes silent RAG degradation in production?"
    result = answer_question(question)
    print(f"Q: {question}\n\n{result['answer']}\n")
    if not result["refused"]:
        print("Sources:")
        for c in result["chunks"]:
            print(f"  - {c['metadata']['source_company']}: {c['metadata']['incident_title']} ({c['metadata']['source_url']})")
