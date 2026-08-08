"""Unit tests for src.generate's pure logic (cost estimation, chit-chat
detection). The actual _generate_groq/_generate_ollama functions make real
network/subprocess calls and are exercised end-to-end instead by
eval/check_generation_quality.py in CI.
"""

import pytest

from src.generate import _CHITCHAT_PATTERN, _estimate_cost_usd


def test_ollama_backend_always_costs_exactly_zero():
    cost = _estimate_cost_usd("ollama", "llama3.2:3b", {"input_tokens": 5000, "output_tokens": 500})
    assert cost == 0.0


def test_groq_known_model_computes_real_cost():
    cost = _estimate_cost_usd("groq", "llama-3.1-8b-instant", {"input_tokens": 1_000_000, "output_tokens": 1_000_000})
    assert cost == pytest.approx(0.05 + 0.08)


def test_groq_unpriced_model_returns_none_not_a_guess():
    cost = _estimate_cost_usd("groq", "some-future-model", {"input_tokens": 100, "output_tokens": 50})
    assert cost is None


@pytest.mark.parametrize("text", ["hi", "Hello!", "hey", "thanks", "Thank you!", "bye", "  hi  ", "Hi?"])
def test_chitchat_pattern_matches_greetings(text):
    assert _CHITCHAT_PATTERN.match(text)


@pytest.mark.parametrize("text", [
    "Why did Uber run out of its 2026 AI budget so fast?",
    "hi, what caused the Replit database deletion?",
    "hey there, can you tell me about Bing Sydney",
])
def test_chitchat_pattern_does_not_match_real_questions(text):
    assert _CHITCHAT_PATTERN.match(text) is None
