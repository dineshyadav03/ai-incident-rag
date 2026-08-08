"""Unit tests for src.ingest's pure chunking logic -- no I/O, no models."""

from src.ingest import _token_len, chunk_text


def test_empty_text_produces_no_chunks():
    assert chunk_text("") == []


def test_short_text_produces_a_single_chunk():
    text = "## What happened\n\nSomething went wrong."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert "Something went wrong." in chunks[0]


def test_packs_multiple_small_sections_into_one_chunk():
    text = "## What happened\n\nShort.\n\n## Root cause\n\nAlso short."
    chunks = chunk_text(text, chunk_size=700)
    assert len(chunks) == 1
    assert "What happened" in chunks[0]
    assert "Root cause" in chunks[0]


def test_splits_into_multiple_chunks_when_sections_dont_fit_together():
    section_a = "## A\n\n" + ("word " * 50)
    section_b = "## B\n\n" + ("word " * 50)
    text = section_a + "\n\n" + section_b
    chunks = chunk_text(text, chunk_size=40, overlap=5)
    assert len(chunks) >= 2


def test_oversized_single_section_falls_back_to_token_sliding_window():
    # One section far bigger than chunk_size, no internal boundary to split on
    text = "## Huge\n\n" + ("word " * 2000)
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    for c in chunks:
        assert _token_len(c) <= 105  # small slack for decode/re-encode rounding


def test_sliding_window_chunks_overlap():
    text = "## Huge\n\n" + " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    # consecutive chunks should share some trailing/leading words given overlap
    first_words = set(chunks[0].split())
    second_words = set(chunks[1].split())
    assert first_words & second_words
