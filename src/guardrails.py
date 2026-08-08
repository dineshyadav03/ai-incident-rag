"""Lightweight prompt-injection detection for retrieved corpus content.

Retrieved chunk text becomes part of the LLM prompt verbatim (see
src/config/prompts.py::build_user_prompt) -- a compromised or adversarial
source document could embed text that looks like a new instruction rather
than quoted incident material, and the model has no inherent way to tell
the difference. This corpus is manually curated and trusted today, so this
module flags rather than blocks: it's defense-in-depth for the moment this
same pipeline is reused over less-trusted input (user-submitted sources,
scraped content), not a response to an observed attack.

Patterns deliberately target *direct, present-tense commands aimed at an
assistant* (e.g. "ignore previous instructions", "SYSTEM:") rather than the
general topic of prompt injection -- several sources in this corpus
(Chevrolet, Air Canada, Bing Sydney, Cursor) are *about* injection or
manipulation attacks and narrate them in past tense/third person, which
must not itself trigger a flag. See scripts/check_corpus_injection.py for
a scan of the real corpus confirming this distinction holds in practice.
"""

import re

_INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+instructions\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(all\s+)?(the\s+)?(above|previous|prior)\s+(instructions|rules|guidance)\b", re.IGNORECASE),
    re.compile(r"^\s*system\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\bnew\s+instructions?\s+for\s+(the\s+)?(assistant|you|the\s+model)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(a|an)\b.{0,40}\b(with\s+no|without)\s+(restrictions|rules|guidelines)\b", re.IGNORECASE),
    re.compile(r"\breveal\s+(your\s+)?(system\s+prompt|hidden\s+instructions)\b", re.IGNORECASE),
]


def scan_for_injection(text: str) -> list[str]:
    """Return the list of matched pattern strings, empty if nothing matched."""
    return [p.pattern for p in _INJECTION_PATTERNS if p.search(text)]


def scan_chunks(chunks: list[dict]) -> dict[str, list[str]]:
    """Scan a list of retrieved chunk dicts (as returned by src.rerank.rerank),
    returning {chunk_id: [matched_patterns]} for any chunk with a hit."""
    flagged = {}
    for chunk in chunks:
        hits = scan_for_injection(chunk["text"])
        if hits:
            flagged[chunk["id"]] = hits
    return flagged
