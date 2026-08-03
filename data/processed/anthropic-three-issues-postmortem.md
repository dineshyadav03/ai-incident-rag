---
source_company: Anthropic
incident_title: Three simultaneous infrastructure bugs silently degrade Claude response quality for weeks
category: model_drift
date: 2025-09-18
source_url: https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues
---

# Three simultaneous infrastructure bugs silently degrade Claude response quality for weeks

## What happened

Between roughly August 5 and September 18, 2025, Claude's response quality degraded for a meaningful subset of users due to three separate, overlapping infrastructure bugs — none of which produced elevated error rates, failed requests, or any other signal that would normally trigger an incident. Users noticed and reported quality problems well before Anthropic's own monitoring did, because every affected request still returned a syntactically valid, "successful" response.

## The three bugs

**1. Context window routing error (Aug 5 – Sep 18):** short-context requests were misrouted to servers configured for the 1M-token context window. A load-balancing change on August 29 amplified the share of misrouted Sonnet 4 requests from 0.8% to 16% at peak. Because routing used "sticky" assignment, once a user's request landed on the wrong server, their follow-up requests kept landing there too — concentrating the damage on specific users rather than spreading it evenly (which is part of why it didn't show up as a global metric problem).

**2. Output corruption from a TPU misconfiguration (Aug 25–28 for Opus; Aug 25–Sep 2 for Sonnet 4):** a runtime performance optimization occasionally assigned high probability to tokens that should almost never appear given the context — for example, producing Thai or Chinese characters in response to an English prompt. Only TPU-served traffic was affected; third-party platform deployments were untouched. Because these were isolated, occasional bad tokens rather than total failures, they didn't trip error alarms.

**3. XLA:TPU compiler miscompilation (Aug 25–Sep 12):** a precision mismatch in the approximate top-k sampling operation, caused by mixed bf16/fp32 arithmetic, meant the highest-probability token could sometimes disappear from consideration entirely. This bug's manifestation changed "depending on unrelated factors such as what operations ran before or after it," making it extremely difficult to reproduce consistently.

## Root cause (why detection was slow)

Anthropic's own diagnosis: their evaluations "didn't capture the degradation users were reporting, in part because Claude often recovers well from isolated mistakes" — masking the aggregate impact of many small errors. Privacy controls on engineer access to user interactions also limited how quickly the specific failure patterns could be identified from real traffic.

## Fix / lessons

- Bug 1: corrected routing logic deployed Sep 4, fully rolled out by Sep 18.
- Bug 2: rolled back Sep 2; added detection tests specifically for unexpected non-English character output.
- Bug 3: switched from approximate to exact top-k sampling, standardized on fp32 precision, and worked with the XLA:TPU team on a permanent compiler-level fix.

Going forward, Anthropic committed to more sensitive evaluations able to differentiate "working" from "subtly broken" behavior, continuous quality evaluation running against production (not just pre-release), better privacy-respecting debugging tooling, and heavier reliance on user-facing signals (the `/bug` command, thumbs-down ratings) as an early-warning channel that doesn't depend on server-side error metrics at all. This is the clearest available case of "silent" model drift: quality can degrade materially while every standard reliability metric stays green.
