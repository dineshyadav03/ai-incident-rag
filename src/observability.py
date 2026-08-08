"""Query-level observability: every call to answer_question() appends one
JSON line to logs/query_log.jsonl -- question, outcome, generation backend,
per-stage latency, and which sources were retrieved.

Why this exists: this project's own corpus contains a case (Anthropic's
three-issues postmortem) where a RAG-adjacent system degraded silently for
weeks because every request still "succeeded" -- there was no error-rate
signal, only a quality signal nobody was measuring. A structured log plus
scripts/observability_report.py is the cheapest version of "how would I
know if this silently degraded," short of a real metrics backend.

Local file, no external service -- consistent with this project's
zero-budget constraint.
"""

import json
import time
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_PATH = LOG_DIR / "query_log.jsonl"


def log_event(event: dict) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    event = {"timestamp": time.time(), **event}
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
