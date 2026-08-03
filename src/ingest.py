"""Load curated postmortem sources, clean/structure them, and chunk for embedding."""

import json
import re
from pathlib import Path

import tiktoken

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SOURCES_CATALOG = DATA_DIR / "sources.json"

CHUNK_SIZE_TOKENS = 700
CHUNK_OVERLAP_TOKENS = 100

_encoding = tiktoken.get_encoding("cl100k_base")


def load_source_catalog() -> list[dict]:
    with open(SOURCES_CATALOG, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_and_structure(source: dict) -> str:
    """Read a source's raw markdown and write a cleaned copy with a metadata
    header into data/processed/. Returns the cleaned body text (without the
    header) for chunking."""
    raw_path = RAW_DIR / f"{source['id']}.md"
    raw_text = raw_path.read_text(encoding="utf-8")

    # Strip the raw file's own title/metadata lines (first few lines before
    # the first "## " section) — the processed header replaces them.
    body_start = raw_text.find("## What happened")
    body = raw_text[body_start:] if body_start != -1 else raw_text

    header = (
        f"---\n"
        f"source_company: {source['source_company']}\n"
        f"incident_title: {source['incident_title']}\n"
        f"category: {source['category']}\n"
        f"date: {source['date']}\n"
        f"source_url: {source['source_url']}\n"
        f"---\n\n"
        f"# {source['incident_title']}\n\n"
    )

    processed_text = header + body
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / f"{source['id']}.md").write_text(processed_text, encoding="utf-8")
    return body


def _token_len(text: str) -> int:
    return len(_encoding.encode(text))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_TOKENS, overlap: int = CHUNK_OVERLAP_TOKENS) -> list[str]:
    """Chunk text into ~chunk_size-token pieces with ~overlap-token overlap,
    preferring to split on markdown section boundaries ("## ") before
    falling back to a sliding window over tokens."""
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    chunks = []
    current = ""
    current_tokens = 0

    for section in sections:
        section_tokens = _token_len(section)

        if section_tokens > chunk_size:
            # Section itself is too big — slide a token window over it.
            if current:
                chunks.append(current)
                current, current_tokens = "", 0
            tokens = _encoding.encode(section)
            start = 0
            while start < len(tokens):
                end = min(start + chunk_size, len(tokens))
                chunks.append(_encoding.decode(tokens[start:end]))
                if end == len(tokens):
                    break
                start = end - overlap
            continue

        if current_tokens + section_tokens <= chunk_size:
            current = f"{current}\n\n{section}".strip()
            current_tokens += section_tokens
        else:
            chunks.append(current)
            current, current_tokens = section, section_tokens

    if current:
        chunks.append(current)

    return chunks


def get_all_chunks() -> list[dict]:
    """Clean + chunk every source in the catalog, returning chunk records
    ready for embedding: {id, chunk_index, text, metadata}."""
    records = []
    for source in load_source_catalog():
        body = clean_and_structure(source)
        chunks = chunk_text(body)
        for i, chunk in enumerate(chunks):
            records.append({
                "id": f"{source['id']}::chunk{i}",
                "chunk_index": i,
                "text": chunk,
                "metadata": {
                    "source_company": source["source_company"],
                    "incident_title": source["incident_title"],
                    "category": source["category"],
                    "date": source["date"],
                    "source_url": source["source_url"],
                    "chunk_index": i,
                },
            })
    return records


if __name__ == "__main__":
    all_chunks = get_all_chunks()
    print(f"Loaded {len(load_source_catalog())} sources -> {len(all_chunks)} chunks")
    for c in all_chunks[:3]:
        print(f"\n[{c['id']}] ({_token_len(c['text'])} tokens)\n{c['text'][:200]}...")
