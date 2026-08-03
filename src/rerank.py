"""Cross-encoder reranking of hybrid-search candidates, plus the citation-enforcement
confidence check.
"""

from sentence_transformers import CrossEncoder

RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Cross-encoder relevance score below this means "not actually relevant" --
# used to decide whether to answer or refuse.
RELEVANCE_SCORE_THRESHOLD = 0.0

_reranker = None


def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL_NAME)
    return _reranker


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Score each candidate against the query with a cross-encoder and return
    the top_k, sorted by relevance score (descending)."""
    if not candidates:
        return []

    reranker = get_reranker()
    pairs = [(query, c["text"]) for c in candidates]
    scores = reranker.predict(pairs)

    for c, score in zip(candidates, scores):
        c["rerank_score"] = float(score)

    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
    return candidates[:top_k]


def is_confident(chunks: list[dict], threshold: float = RELEVANCE_SCORE_THRESHOLD) -> bool:
    """Citation-enforcement check: refuse if even the best reranked match
    isn't relevant enough to trust."""
    if not chunks:
        return False
    return chunks[0]["rerank_score"] >= threshold


if __name__ == "__main__":
    import sys

    from src.retrieve import hybrid_search

    query = " ".join(sys.argv[1:]) or "what causes silent RAG degradation"
    candidates = hybrid_search(query)
    top = rerank(query, candidates)

    print(f"Query: {query}\nConfident: {is_confident(top)}\n")
    for c in top:
        print(f"[{c['rerank_score']:.3f}] {c['metadata']['source_company']} — {c['metadata']['incident_title']}")
