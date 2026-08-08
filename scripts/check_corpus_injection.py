"""Scan every chunk in the curated corpus for prompt-injection-like patterns
(see src/guardrails.py). Pure regex over local files -- no models, no API
key, runs in well under a second, safe for every CI run.

This is a sanity check on the *detector*, not primarily a security gate:
several sources in this corpus (Chevrolet, Air Canada, Bing Sydney, Cursor)
are themselves about injection/manipulation attacks and narrate them in
past tense -- this script proves that narration doesn't false-positive
against the same patterns used to flag live retrieved content in
src/generate.py. A flag here on a *newly added* source is worth a manual
look (is a new source accidentally phrased as a direct command?), but
isn't automatically a hard failure -- see main() for why it warns rather
than fails CI by default.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.guardrails import scan_for_injection  # noqa: E402
from src.ingest import get_all_chunks  # noqa: E402


def main() -> int:
    chunks = get_all_chunks()
    flagged = []
    for c in chunks:
        hits = scan_for_injection(c["text"])
        if hits:
            flagged.append((c["id"], hits))

    print(f"Scanned {len(chunks)} chunks for prompt-injection patterns.")

    if not flagged:
        print("PASSED -- no chunks flagged.")
        return 0

    print(f"\n{len(flagged)} chunk(s) flagged (review manually -- this may be a false positive on legitimate incident narration, or a real issue in a newly added source):")
    for chunk_id, hits in flagged:
        print(f"  - {chunk_id}: {hits}")

    # Flag, don't fail: matches the flag-not-block design in src/guardrails.py.
    # A hit here means "a human should look at this source," not "the build
    # is broken" -- hard-failing CI on a heuristic regex match against
    # manually-curated, already-reviewed source text would be noisy for a
    # corpus literally about injection attacks. Escalate to a hard failure
    # once sources are no longer 100% manually reviewed before merge.
    return 0


if __name__ == "__main__":
    sys.exit(main())
