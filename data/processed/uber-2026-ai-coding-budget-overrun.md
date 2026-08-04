---
source_company: Uber
incident_title: Uber exhausts its entire 2026 AI tooling budget in four months, forced into emergency spend caps
category: infra_failure
date: 2026-05-17
source_url: https://www.forbes.com/sites/janakirammsv/2026/05/17/uber-burns-its-2026-ai-budget-in-four-months-on-claude-code/
---

# Uber exhausts its entire 2026 AI tooling budget in four months, forced into emergency spend caps

## What happened

Uber budgeted AI tooling spend for the full 2026 calendar year, but had exhausted the entire budget by April — four months in — after rolling out Anthropic's Claude Code to roughly 5,000 engineers, 84% of whom adopted it. CTO Praveen Neppalli Naga confirmed the overrun publicly, stating the company was "back to the drawing board" on its cost assumptions. Individual sessions could run far higher than expected: one engineer's single two-hour agentic coding session cost $1,200. Total company R&D spend for 2025 had already reached $3.4 billion, up 9% year over year, making the 2026 tooling budget collapse a governance failure rather than a scale problem.

## Root cause

The overrun was not simply a matter of usage volume outstripping a fixed budget — it was a failure to model how per-developer token consumption scales under agentic (as opposed to single-shot autocomplete) usage. Uber's finance team had built its 2026 forecast on prior years' assumptions about AI tooling cost, but agentic coding sessions — where the model plans, executes multi-step tool calls, and iterates — produced five-to-twenty-fold increases in per-developer consumption compared to earlier tooling generations, with no public benchmark showing a matching multiplier in output value. Compounding this, Uber had run an internal leaderboard incentivizing teams by total AI tool usage, which pushed adoption and consumption up faster than finance models anticipated, with no per-engineer spend ceiling in place to catch the divergence early.

## Fix / lessons

By early June 2026, Uber introduced hard spend caps of $1,500 per employee per month for each AI coding tool, tracked on a dashboard visible to every engineer, with a manual request process for anyone needing to exceed the cap. This is a useful infra_failure example specifically because the failure wasn't in the model or the agent's behavior — it was an absence of infrastructure-level cost guardrails (metering, caps, alerting) around a genuinely new consumption pattern that traditional per-seat software licensing never had to account for. Adopting a tool that changes its own cost profile (agentic vs. single-shot) without updating the operational controls around it is itself an infra_failure class, distinct from the tool malfunctioning.
