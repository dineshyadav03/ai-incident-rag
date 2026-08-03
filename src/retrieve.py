"""Vector retrieval over the ChromaDB collection.

Phase 1: vector-only search. Phase 2 will add BM25 hybrid search and
cross-encoder reranking on top of this.
"""

from src.embed import get_collection, get_embedding_model

# Cosine distance (1 - cosine similarity) above this is treated as "not
# relevant enough" — used by generate.py to decide whether to refuse.
RELEVANCE_DISTANCE_THRESHOLD = 0.6


def vector_search(query: str, top_k: int = 5) -> list[dict]:
    """Embed the query and return the top_k most similar chunks with their
    metadata and distance scores."""
    collection = get_collection()
    model = get_embedding_model()
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks


def is_confident(chunks: list[dict], threshold: float = RELEVANCE_DISTANCE_THRESHOLD) -> bool:
    """Basic Phase 1 confidence check: is the closest match relevant enough?
    Phase 2 replaces/augments this with reranker-based scoring."""
    if not chunks:
        return False
    return chunks[0]["distance"] <= threshold


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "what causes silent RAG degradation"
    results = vector_search(query)
    print(f"Query: {query}\nConfident: {is_confident(results)}\n")
    for r in results:
        print(f"[{r['distance']:.3f}] {r['metadata']['source_company']} — {r['metadata']['incident_title']}")
        print(f"  {r['text'][:150]}...\n")
