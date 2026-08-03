"""Build a cited prompt from retrieved chunks and generate an answer via the Claude API."""

import os

import anthropic
from dotenv import load_dotenv

from src.config.prompts import SYSTEM_PROMPT_V1, build_user_prompt
from src.retrieve import is_confident, vector_search

load_dotenv()

MODEL = "claude-sonnet-5"
REFUSAL_MESSAGE = "I don't have enough grounded information in the corpus to answer this confidently."

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def answer_question(question: str, top_k: int = 5) -> dict:
    """Retrieve chunks for the question and generate a cited answer. Refuses
    when the top match isn't relevant enough (Phase 1 confidence check)."""
    chunks = vector_search(question, top_k=top_k)

    if not is_confident(chunks):
        return {"answer": REFUSAL_MESSAGE, "chunks": chunks, "refused": True}

    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT_V1,
        messages=[{"role": "user", "content": build_user_prompt(question, chunks)}],
    )
    answer_text = next((b.text for b in response.content if b.type == "text"), "")

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
