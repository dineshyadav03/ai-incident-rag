"""Unit tests for src.rerank's pure confidence-check logic. rerank() itself
loads a real cross-encoder model and is exercised end-to-end instead by
eval/check_retrieval.py in CI -- these cover the threshold logic around it,
which doesn't need a model loaded to test.
"""

from src.rerank import RELEVANCE_SCORE_THRESHOLD, is_confident


def test_empty_chunks_is_never_confident():
    assert is_confident([]) is False


def test_confident_when_top_score_meets_threshold():
    chunks = [{"rerank_score": 0.5}, {"rerank_score": -3.0}]
    assert is_confident(chunks) is True


def test_not_confident_when_top_score_below_threshold():
    chunks = [{"rerank_score": -0.01}, {"rerank_score": -5.0}]
    assert is_confident(chunks) is False


def test_boundary_score_exactly_at_threshold_counts_as_confident():
    chunks = [{"rerank_score": RELEVANCE_SCORE_THRESHOLD}]
    assert is_confident(chunks) is True


def test_only_the_top_scored_chunk_matters():
    # A low first-place score shouldn't be rescued by a high one later in the list
    chunks = [{"rerank_score": -1.0}, {"rerank_score": 10.0}]
    assert is_confident(chunks) is False
