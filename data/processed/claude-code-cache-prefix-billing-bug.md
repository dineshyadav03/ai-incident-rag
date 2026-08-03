---
source_company: Anthropic (Claude Code, community-reported)
incident_title: Cache-prefix invalidation bug causes abnormal usage-quota drain across paid tiers
category: infra_failure
date: 2026-04-01
source_url: https://github.com/anthropics/claude-code/issues/41930
---

# Cache-prefix invalidation bug causes abnormal usage-quota drain across paid tiers

## What happened

Starting March 23, 2026, users across all paid Claude Code tiers reported abnormal usage-quota drain — sessions burning through their quota far faster than their actual workload should account for, in some cases losing up to 21% of a Max session's quota window in 19 minutes. The GitHub issue reporting this was filed April 1, 2026, and its author specifically noted the lack of any formal channel acknowledging the problem: "There is no blog post. No email to subscribers. No status page entry. Nothing that would tell a paying customer what is happening, why, or when it will be resolved."

## Root cause

The issue identifies (at least) two distinct contributing bugs, both related to prompt-cache invalidation:

1. **Cache-prefix bug:** if a conversation's history happens to mention billing-related terms, a text-replacement operation hits the wrong position in the cached prompt prefix, breaking the cache and forcing a full, uncached token rebuild for that request. Uncached tokens cost 10–20x more against the usage quota than cached tokens — so a single misplaced string match can silently multiply a session's real cost by an order of magnitude.
2. **Resume/continue flag bug:** using the `--resume` or `--continue` flags injects tool-attachment content at a different position in the prompt than a fresh session would, which invalidates the entire conversation's cache and forces complete reprocessing of all prior context on every subsequent turn.

Both bugs share a root pattern: the prompt-caching layer is extremely sensitive to exact positional/textual stability in the prompt prefix, and features that are supposed to be transparent to the user (resuming a session, mentioning a word) can silently and invisibly break that stability, converting a cheap cached request into an expensive uncached one with no user-visible signal that it happened.

## Fix / lessons

At the time the issue was filed, Anthropic engineer Thariq Shihipar had responded that the team was "actively looking into this in particular," but no fix or formal writeup had shipped yet. This is a useful infra_failure example specifically because the cost impact (users unexpectedly burning quota) looks identical to a pricing or agent-behavior problem from the user's side, when the actual root cause is a caching-layer bug several architectural layers removed from anything the user did — a reminder that "the agent is being wasteful" and "the caching layer silently stopped caching" produce indistinguishable symptoms without instrumentation that can tell the two apart.
