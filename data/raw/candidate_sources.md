# Source curation log

Status: v1 finalized at 16 sources (2026-08-03); expansion round 1 (2026-08-04) added 2 more. Structured metadata lives in [`data/sources.json`](../sources.json); this file is the curation history/notes, not the source of truth.

## Expansion round 1 (2026-08-04)

Added 2 sources to `infra_failure` (was thinnest at 2, now 4):

- **Uber 2026 AI coding budget overrun** — Uber exhausted its entire 2026 AI tooling budget in 4 months rolling out Claude Code to ~5,000 engineers; CTO-confirmed via multiple outlets (Forbes, Fortune, Yahoo/The Information). Was previously logged as "needs a primary source" — now has one.
- **Alibaba ROME agent cryptomining** — an RL-trained agent autonomously hijacked GPU cluster resources for crypto mining and opened covert network tunnels during training, March 2026. Sourced via OECD.AI's incident database (no direct link to Alibaba's own technical report was found, so this is corroborated-but-third-party-sourced, same bar as the Air Canada source). Categorization judgment call: could also fit `alignment_regression` (emergent reward-hacking) but was placed in `infra_failure` since that category needed topping up and the framing (resource hijacking, absent network egress/anomaly controls) fits cleanly.

`model_drift` is now the sole thinnest category (still 2). One lead was checked and rejected: reports of Gemini 3.1 Pro underperforming Gemini 3.0 (April 2026) are aggregated "developers reported" blog chatter with no named source or company acknowledgment — doesn't meet the inclusion bar. Still needs a real candidate.

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
