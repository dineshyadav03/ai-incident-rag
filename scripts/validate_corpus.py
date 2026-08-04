"""Structural consistency checks for the corpus and golden set -- catches the
kind of mistake that's easy to make by hand when adding a source (typo in an
id, forgetting the raw/processed file, a golden question pointing at a source
that no longer exists) without needing to run the full pipeline. Pure file/
JSON checks, no models loaded, runs in well under a second.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SOURCES_CATALOG = DATA_DIR / "sources.json"
GOLDEN_SET_PATH = REPO_ROOT / "eval" / "golden_set.json"

REQUIRED_SOURCE_FIELDS = {"id", "source_company", "incident_title", "category", "date", "source_url"}
REQUIRED_QUESTION_FIELDS = {"id", "question", "reference_answer", "expected_source_id", "category"}


def main() -> int:
    errors = []

    with open(SOURCES_CATALOG, "r", encoding="utf-8") as f:
        sources = json.load(f)
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    source_ids = set()
    for s in sources:
        missing = REQUIRED_SOURCE_FIELDS - s.keys()
        if missing:
            errors.append(f"sources.json entry {s.get('id', '<no id>')} missing fields: {missing}")
            continue

        if s["id"] in source_ids:
            errors.append(f"sources.json has a duplicate id: {s['id']}")
        source_ids.add(s["id"])

        raw_path = RAW_DIR / f"{s['id']}.md"
        if not raw_path.exists():
            errors.append(f"sources.json entry {s['id']} has no matching data/raw/{s['id']}.md")

    question_ids = set()
    for q in golden_set:
        missing = REQUIRED_QUESTION_FIELDS - q.keys()
        if missing:
            errors.append(f"golden_set.json entry {q.get('id', '<no id>')} missing fields: {missing}")
            continue

        if q["id"] in question_ids:
            errors.append(f"golden_set.json has a duplicate id: {q['id']}")
        question_ids.add(q["id"])

        if q["expected_source_id"] not in source_ids:
            errors.append(
                f"golden_set.json question {q['id']} references unknown expected_source_id: "
                f"{q['expected_source_id']}"
            )

    print(f"Checked {len(sources)} sources and {len(golden_set)} golden questions.")

    if errors:
        print(f"\nFAILED -- {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASSED -- corpus and golden set are structurally consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
