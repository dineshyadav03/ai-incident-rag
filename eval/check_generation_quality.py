"""Fast, deterministic-ish generation-quality gate for CI -- checks that the
full pipeline (retrieval + rerank + real LLM generation) still produces
correctly-cited, non-refused answers on a small known-good subset of the
golden set. Requires GROQ_API_KEY (skips gracefully if absent, so CI
doesn't fail for forks/PRs without the secret configured).

This is deliberately NOT the full RAGAS eval (see eval/evaluate.py) --
RAGAS needs a local Ollama judge and takes 35-80+ minutes, which doesn't
belong in a per-push gate, and its faithfulness/relevancy scoring is
LLM-judged (soft, sometimes flaky JSON parsing). This check instead
exercises the full pipeline once per sample question, using Groq for fast
generation, and asks purely mechanical questions of the output: did it
refuse when it shouldn't have, does it contain a properly-formatted
citation, and does that citation actually point at the expected source.
Cheap enough to run on every PR; the full RAGAS run stays a periodic/
manual step on Colab, unchanged.
"""

import json
import os
import re
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"
SOURCES_PATH = EVAL_DIR.parent / "data" / "sources.json"

# Same representative subset (one/two per category, spanning all 6) used by
# eval/evaluate.py's local RAGAS sample, reused here for consistency rather
# than duplicated logic -- but redefined as a plain constant, not imported,
# so this script doesn't pull in ragas/langchain's heavy import chain.
SAMPLE_IDS = {"q01", "q05", "q07", "q11", "q14", "q17", "q19", "q23", "q24"}

CITATION_PATTERN = re.compile(r"\[Source:", re.IGNORECASE)


def main() -> int:
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set -- skipping generation-quality check (this is fine; it's opt-in).")
        return 0

    # Import lazily: pulls in sentence-transformers/ollama/groq, which we
    # want to avoid loading at all when the check is about to skip anyway.
    from src.generate import answer_question

    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        golden_set = [q for q in json.load(f) if q["id"] in SAMPLE_IDS]
    with open(SOURCES_PATH, "r", encoding="utf-8") as f:
        sources_by_id = {s["id"]: s for s in json.load(f)}

    failures = []
    for item in golden_set:
        result = answer_question(item["question"])
        source = sources_by_id[item["expected_source_id"]]
        answer = result["answer"]

        problems = []
        if result["refused"]:
            problems.append("refused a question expected to be answerable")
        else:
            if not CITATION_PATTERN.search(answer):
                problems.append("no '[Source:' citation found in the answer")
            if source["source_company"].lower() not in answer.lower() and source["source_url"] not in answer:
                problems.append(f"answer doesn't cite the expected source ({source['source_company']!r} / {source['source_url']})")

        status = "OK" if not problems else "FAIL"
        print(f"  [{item['id']}] {status} -- {item['question'][:60]}")
        for p in problems:
            print(f"      - {p}")
        if problems:
            failures.append(item["id"])

    n = len(golden_set)
    print(f"\nGeneration quality: {n - len(failures)}/{n} passed")

    if failures:
        print(f"FAILED -- issues on: {', '.join(failures)}")
        return 1

    print("PASSED -- generation stayed correctly cited and non-refusing on the sample set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
