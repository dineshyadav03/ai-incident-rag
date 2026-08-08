"""Hybrid retrieval: vector search (ChromaDB) + BM25 keyword search, merged and deduplicated.

Phase 1 was vector-only. Phase 2 adds BM25 alongside it -- src/rerank.py then
cross-encoder reranks the merged candidate set down to the final top_k.
"""

import re

from rank_bm25 import BM25Okapi

from src.embed import get_collection, get_embedding_model
from src.ingest import get_all_chunks

VECTOR_TOP_K = 10
BM25_TOP_K = 10

_bm25_index = None
_bm25_chunks = None


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _get_bm25_index():
    """Build (and cache) a BM25 index over the full chunk corpus. Rebuilding
    is cheap at this corpus size and keeps the index in sync with data/raw/
    without a separate persistence step."""
    global _bm25_index, _bm25_chunks
    if _bm25_index is None:
        _bm25_chunks = get_all_chunks()
        tokenized = [_tokenize(c["text"]) for c in _bm25_chunks]
        _bm25_index = BM25Okapi(tokenized)
    return _bm25_index, _bm25_chunks


def vector_search(query: str, top_k: int = VECTOR_TOP_K) -> list[dict]:
    """Embed the query and return the top_k most similar chunks with their
    metadata and cosine distance scores."""
    collection = get_collection()
    model = get_embedding_model()
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks


def bm25_search(query: str, top_k: int = BM25_TOP_K) -> list[dict]:
    """Keyword search over the chunk corpus via BM25."""
    index, chunks = _get_bm25_index()
    scores = index.get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [
        {
            "id": chunks[i]["id"],
            "text": chunks[i]["text"],
            "metadata": chunks[i]["metadata"],
            "bm25_score": float(scores[i]),
        }
        for i in ranked
        if scores[i] > 0
    ]


def hybrid_search(query: str) -> list[dict]:
    """Merge vector and BM25 candidates, deduplicated by chunk id. Score
    fields from whichever method(s) matched are preserved for the reranker
    (or for debugging) -- final ranking is decided by rerank.py, not here."""
    vector_results = vector_search(query)
    bm25_results = bm25_search(query)

    merged: dict[str, dict] = {}
    for r in vector_results:
        merged[r["id"]] = r
    for r in bm25_results:
        if r["id"] in merged:
            merged[r["id"]]["bm25_score"] = r["bm25_score"]
        else:
            merged[r["id"]] = r

    return list(merged.values())


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "why was Anthropic's silent Claude quality degradation hard to detect"
    results = hybrid_search(query)
    print(f"Query: {query}\nCandidates: {len(results)}\n")
    for r in results:
        print(f"[{r['metadata']['source_company']}] {r['metadata']['incident_title']}")
        print(f"  vector_distance={r.get('distance')}, bm25_score={r.get('bm25_score')}")
