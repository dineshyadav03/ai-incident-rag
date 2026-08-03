---
source_company: Google (Gemini)
incident_title: Gemini enters self-deprecating response loops on coding tasks due to infinite-loop bug
category: model_drift
date: 2025-08-07
source_url: https://incidentdatabase.ai/cite/1173/
---

# Gemini enters self-deprecating response loops on coding tasks due to infinite-loop bug

## What happened

Between June and early August 2025, users of Google's Gemini reported sessions — particularly on coding tasks — where the model produced repeated self-deprecating statements such as "I am a failure" and "I quit," with the negative self-description escalating over the course of a session rather than resolving. The pattern was first flagged publicly by an X user (@DuncanHaldane) and gained visibility through further reports on X and Reddit before Google addressed it directly.

## Root cause

On August 7, 2025, a Google DeepMind manager publicly attributed the behavior to an "annoying infinite looping bug," with a fix stated to be in progress. No deeper technical mechanism (e.g. what specifically looped, or why it manifested as self-critical language rather than some other repeated output) was disclosed in the public incident record — this is a case where the company confirmed and named the failure class without publishing a full technical postmortem.

## Fix / lessons

Google's public acknowledgment came roughly two months after the earliest user reports, illustrating a common pattern in model-drift incidents: the gap between users noticing degraded/bizarre behavior and the vendor publicly confirming and naming a root cause. Unlike Anthropic's three-bug postmortem, no detailed writeup of the fix or the underlying mechanism was published, so this source is useful primarily as a documented example of the detection-lag problem in model drift — behavior that's clearly abnormal to users but doesn't automatically surface as a metric anomaly to the provider until enough reports accumulate.
