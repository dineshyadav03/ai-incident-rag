"""Summarize logs/query_log.jsonl -- outcome breakdown, backend usage, and
latency percentiles per stage. The report a production RAG system needs to
answer "did this silently degrade?" without reading every request by hand.
No external service, no configuration -- reads whatever's been logged
locally. See src/observability.py for what gets logged and why.
"""

import json
import sys
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "query_log.jsonl"


def _percentile(values: list[float], p: float) -> float:
    values = sorted(values)
    k = (len(values) - 1) * (p / 100)
    f, c = int(k), min(int(k) + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


def _latency_line(label: str, values: list[float]) -> str:
    if not values:
        return f"{label}: no data"
    return (
        f"{label}: p50={_percentile(values, 50):.0f}ms  "
        f"p95={_percentile(values, 95):.0f}ms  max={max(values):.0f}ms  (n={len(values)})"
    )


def main() -> int:
    if not LOG_PATH.exists():
        print(f"No log file at {LOG_PATH} yet -- ask some questions first (CLI or web UI).")
        return 0

    lines = [line for line in LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        print("Log file is empty.")
        return 0

    events = [json.loads(line) for line in lines]
    n = len(events)

    outcomes: dict[str, int] = {}
    backends: dict[str, int] = {}
    for e in events:
        outcomes[e["outcome"]] = outcomes.get(e["outcome"], 0) + 1
        if e.get("backend"):
            backends[e["backend"]] = backends.get(e["backend"], 0) + 1

    total_ms = [e["total_ms"] for e in events if e.get("total_ms") is not None]
    retrieval_ms = [e["retrieval_ms"] for e in events if e.get("retrieval_ms") is not None]
    rerank_ms = [e["rerank_ms"] for e in events if e.get("rerank_ms") is not None]
    generation_ms = [e["generation_ms"] for e in events if e.get("generation_ms") is not None]

    print(f"Query log: {n} event(s) in {LOG_PATH}\n")

    print("Outcomes:")
    for outcome, count in sorted(outcomes.items()):
        print(f"  {outcome}: {count} ({count / n:.1%})")

    if backends:
        print("\nGeneration backend usage:")
        for backend, count in sorted(backends.items()):
            print(f"  {backend}: {count}")

    print("\nLatency:")
    print(f"  {_latency_line('total', total_ms)}")
    print(f"  {_latency_line('retrieval', retrieval_ms)}")
    print(f"  {_latency_line('rerank', rerank_ms)}")
    print(f"  {_latency_line('generation', generation_ms)}")

    errors = [e for e in events if e["outcome"] == "error"]
    if errors:
        print(f"\n{len(errors)} error(s), most recent first:")
        for e in reversed(errors[-5:]):
            print(f"  - {e['question'][:70]!r}: {e.get('error', 'unknown error')}")

    flagged = [e for e in events if e.get("injection_flags")]
    if flagged:
        print(f"\n{len(flagged)} quer(y/ies) with possible prompt injection in retrieved content (see src/guardrails.py):")
        for e in flagged[-5:]:
            print(f"  - {e['question'][:70]!r}: {e['injection_flags']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
