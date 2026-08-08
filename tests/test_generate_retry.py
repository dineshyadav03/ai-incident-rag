"""Unit test for _generate_groq's rate-limit retry logic -- discovered for
real in CI (see src/generate.py's comment), not theoretical. Mocks the Groq
client entirely: no real network calls, no real sleeping.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from groq import RateLimitError

import src.generate as generate_module


@pytest.fixture(autouse=True)
def _reset_groq_client():
    # Tests here mutate the module-level client singleton; don't leak that
    # mock into other test modules.
    yield
    generate_module._groq_client = None


def _rate_limit_error():
    resp = httpx.Response(status_code=429, request=httpx.Request("POST", "https://api.groq.com/x"))
    return RateLimitError("rate limited", response=resp, body=None)


def _fake_response(text="An answer.", input_tokens=10, output_tokens=5):
    response = MagicMock()
    response.choices[0].message.content = text
    response.usage.prompt_tokens = input_tokens
    response.usage.completion_tokens = output_tokens
    return response


def test_retries_after_rate_limit_then_succeeds(monkeypatch):
    monkeypatch.setattr(generate_module.time, "sleep", lambda _: None)  # don't actually wait in tests
    generate_module._groq_client = MagicMock()
    generate_module._groq_client.chat.completions.create.side_effect = [
        _rate_limit_error(),
        _fake_response("It worked on the second try."),
    ]

    text, usage = generate_module._generate_groq("some prompt")

    assert text == "It worked on the second try."
    assert usage == {"input_tokens": 10, "output_tokens": 5}
    assert generate_module._groq_client.chat.completions.create.call_count == 2


def test_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr(generate_module.time, "sleep", lambda _: None)
    monkeypatch.setattr(generate_module, "GROQ_MAX_RETRIES", 2)
    generate_module._groq_client = MagicMock()
    generate_module._groq_client.chat.completions.create.side_effect = _rate_limit_error()

    with pytest.raises(RateLimitError):
        generate_module._generate_groq("some prompt")

    assert generate_module._groq_client.chat.completions.create.call_count == 2
