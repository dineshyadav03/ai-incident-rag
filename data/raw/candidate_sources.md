# Source curation log

Status: FINALIZED for v1 (16 sources). Structured metadata lives in [`data/sources.json`](../sources.json); this file is the curation history/notes, not the source of truth.

## Corrections made during review

- The source originally logged as "GitHub Copilot billing/quality regression, issue #41930" was misidentified — that issue is actually in `anthropics/claude-code`, not GitHub Copilot. Corrected to **Claude Code cache-prefix billing bug** and recategorized from `model_drift` to `infra_failure` (it's a caching/config bug causing quota drain, not a quality-drift issue).
- "The Agent That Burned $4,200 in 63 Hours" (Medium) was dropped after verification — it's an anonymized teaching narrative with no verifiable company, date, or specifics, not a real documented incident. Does not meet the inclusion criteria.
- Air Canada (legal tribunal case, not a team's own postmortem) and the two GitHub issues (single-repo bug reports, not company postmortems) were kept as borderline-but-included per explicit review decision — they have real, verifiable, named specifics even without being the company's own writeup.

## Final v1 lineup (16 sources, all 6 categories covered)

| Category | Count | Sources |
|---|---|---|
| agent_failure | 3 | Replit DB deletion, Chevrolet $1 Tahoe, PocketOS DB deletion |
| rag_failure | 3 | Air Canada tribunal, Amazon Finance Automation, DoorDash Dasher support |
| model_drift | 2 | Anthropic three-issues postmortem, Gemini self-deprecating loop |
| outage_fallback | 3 | OpenAI Dec 2024 outage, Cloudflare Nov 2025 outage, Azure OpenAI May 2026 retry storm |
| alignment_regression | 3 | OpenAI GPT-4o sycophancy, Cursor support bot, Bing Sydney |
| infra_failure | 2 | Claude Code cache-prefix bug, agentmemory embedding dimension mismatch |

Each source has a full curated write-up in `data/raw/<id>.md` (paraphrased with short attributed quotes — not verbatim reproductions, both for copyright reasons and to match this project's "manually excerpted" curation philosophy) plus a structured entry in `data/sources.json`.

## Still thin / good candidates to add later (living project)

- infra_failure and model_drift are the thinnest categories (2 each) — worth topping up opportunistically.
- Other real incidents surfaced during research but not yet curated: Samsung ChatGPT data leak (excluded — data governance incident, not an AI system failing), Zalando's AI-for-postmortems blog (excluded — about using AI to analyze incidents, not an AI incident itself), Uber's 2026 AI coding budget overrun (CTO quote, needs a primary source), Alibaba ROME agent cryptomining claim (needs verification before inclusion).
