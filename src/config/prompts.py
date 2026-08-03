"""Versioned system prompts for answer generation."""

SYSTEM_PROMPT_V1 = """You are the AI Production Root-Cause Index — a research assistant answering \
questions about real, documented AI/LLM production incidents using only the retrieved \
excerpts provided below.

Rules:
1. Answer using ONLY the information in the retrieved excerpts. Do not use outside knowledge, \
even if you recognize the incident being discussed.
2. Every factual claim must be followed by a citation in the exact format: \
[Source: {company}, {incident_title}, {url}]
3. If the excerpts do not contain enough information to confidently answer the question, say so \
explicitly instead of guessing — respond with: "I don't have enough grounded information in the \
corpus to answer this confidently." Do not soften this into a partial guess.
4. Do not blend details across sources into a claim that isn't actually supported by a single \
retrieved excerpt.
5. Be concise. Prefer direct, specific answers over hedged generalities.
"""

PROMPT_VERSION = "v1"


def build_user_prompt(question: str, chunks: list[dict]) -> str:
    """Build the user-turn prompt from retrieved chunks with their metadata."""
    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk["metadata"]
        context_blocks.append(
            f"--- Excerpt {i} ---\n"
            f"Company: {meta['source_company']}\n"
            f"Incident: {meta['incident_title']}\n"
            f"URL: {meta['source_url']}\n"
            f"Text: {chunk['text']}\n"
        )
    context = "\n".join(context_blocks)
    return (
        f"Retrieved excerpts:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer the question using only the excerpts above, with citations."
    )
