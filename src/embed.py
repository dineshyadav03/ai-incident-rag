"""Embed chunks with sentence-transformers and store them in a persistent ChromaDB collection."""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from src.ingest import get_all_chunks

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = REPO_ROOT / "chroma_db"
COLLECTION_NAME = "ai_incident_postmortems"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(client: chromadb.ClientAPI | None = None):
    client = client or get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(reset: bool = True) -> int:
    """Embed all chunks and (re)populate the ChromaDB collection. Returns the
    number of chunks indexed."""
    client = get_client()
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    collection = get_collection(client)

    chunks = get_all_chunks()
    if not chunks:
        return 0

    model = get_embedding_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True).tolist()

    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[c["metadata"] for c in chunks],
    )
    return len(chunks)


if __name__ == "__main__":
    n = build_index()
    print(f"Indexed {n} chunks into ChromaDB collection '{COLLECTION_NAME}' at {CHROMA_DIR}")
