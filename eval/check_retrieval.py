"""Retrieval-only regression check over the golden set -- no LLM generation,
no Ollama dependency. Runs hybrid search + reranking (both local, CPU-only
models) for every golden question and asserts every one retrieves its
expected source. Exits non-zero on any miss so it can gate CI.

Deliberately separate from eval/evaluate.py's full RAGAS run: that needs a
local Ollama judge and can take an hour+ (see README known limitations),
which doesn't belong in a push/PR gate. This check covers the piece of the
pipeline that doesn't depend on an LLM at all, so it can run on any
GitHub-hosted runner in well under a minute.
"""

import json
import sys
from pathlib import Path

from src.rerank import is_confident, rerank
from src.retrieve import hybrid_search

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"


def main() -> int:
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    misses = []
    for item in golden_set:
        candidates = hybrid_search(item["question"])
        chunks = rerank(item["question"], candidates)
        confident = is_confident(chunks)
        hit = confident and any(c["id"].startswith(item["expected_source_id"]) for c in chunks)

        status = "OK" if hit else "MISS"
        print(f"  [{item['id']}] {status} (confident={confident}) -- {item['question'][:70]}")
        if not hit:
            misses.append(item["id"])

    n = len(golden_set)
    hit_rate = (n - len(misses)) / n
    print(f"\nRetrieval hit rate: {hit_rate:.2%} ({n - len(misses)}/{n})")

    if misses:
        print(f"FAILED -- missed retrieval on: {', '.join(misses)}")
        return 1

    print("PASSED -- every golden question retrieved its expected source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
