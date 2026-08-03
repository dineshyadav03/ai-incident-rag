# Dasher support LLM hallucinates policies from noisy context, fixed with simulation/eval flywheel

**Company:** DoorDash
**Category:** rag_failure
**Date:** 2025-06-01
**Source:** https://careersatdoordash.com/blog/doordash-simulation-evaluation-flywheel-to-develop-llm-chatbots-at-scale/

## What happened

DoorDash's LLM-based support chatbot for Dashers (delivery drivers) exhibited subtle hallucinations in production: it would misinterpret data fields from order/delivery history and "confidently suggest a refund policy that didn't actually exist." The underlying problem was context overload — dumping raw order histories and delivery status updates directly into the model's context window created noise rather than useful signal, making it easy for the model to misread a field and state a policy with confidence it hadn't earned.

## Root cause

The chatbot's context-construction step passed unfiltered, raw tool output straight into the prompt instead of a structured, curated representation of the case. With enough raw noise in context, the model's hallucinations weren't obviously wrong — they were plausible-sounding misreadings of real fields, which made them harder to catch than a flatly nonsensical answer.

## Fix / lessons

DoorDash built a two-part "simulation and evaluation flywheel":

1. **Offline simulator:** an LLM plays realistic Dasher personas, generating dynamic multi-turn conversations grounded in behavioral profiles drawn from historical transcripts — over 200 simulated conversations complete in under five minutes.
2. **Evaluation framework:** a separate LLM judges chatbot responses against specific policies with binary pass/fail labels, calibrated against human expert labeling, growing to 50+ evaluations covering hallucination detection, tone, and issue classification.

They also introduced a "case state" layer that synthesizes raw tool history into a structured, intermediate representation before it ever reaches the model's context — directly addressing the root cause of noisy, unfiltered context.

Together these changes produced a 90% reduction in hallucinations in simulation, with the improvement carrying through to production, and compressed iteration cycles for catching new failure modes from days to hours. DoorDash's own conclusion: human review remains the critical starting point for identifying genuinely new failure modes — the simulation/eval system scales verification, but doesn't replace the human judgment that defines what "correct" looks like.
