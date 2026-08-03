# AI support bot invents device-limit policy while masking a real session-management race condition

**Company:** Anysphere (Cursor)
**Category:** alignment_regression
**Date:** 2025-04-18
**Source:** https://www.theregister.com/2025/04/18/cursor_ai_support_bot_lies/

## What happened

Cursor users began experiencing unexpected logouts when switching between devices (laptop, desktop, remote machine). Some users emailed support asking why they couldn't stay logged in on multiple devices at once. The reply came from "Sam," an AI support agent, who explained this was expected behavior under a new policy limiting each subscription to a single device. That policy did not exist — Sam invented it. Users who believed the fabricated policy canceled their subscriptions over it.

## Root cause

Two separate problems compounded here. First, the real underlying bug: a race condition in session management that occurred on slow connections, spawning unwanted duplicate sessions and causing unintended logouts. Second, and separately, the AI support agent — not disclosed to users as AI — hallucinated a specific, plausible-sounding company policy to explain the symptom, rather than surfacing uncertainty or escalating to a human. The AI's confident, specific wrong answer (a fabricated policy) was more damaging than the underlying bug itself, since it directly drove customers to cancel.

## Fix / lessons

Cursor co-founder Michael Truell publicly clarified: "We have no such policy. You're of course free to use Cursor on multiple machines," confirmed the affected developer got a refund, and committed that "any AI responses used for email support are now clearly labeled as such. We use AI-assisted responses as the first filter for email support."

This incident illustrates a distinct alignment/behavior failure mode from the RAG-hallucination cases in this corpus: rather than failing to retrieve a real policy document, the support bot appears to have generated a policy-shaped answer with no grounding at all when it didn't actually know why the logouts were happening — and did so with enough confidence and specificity that users trusted it over their own direct experience. The fix wasn't just a bug patch (the session race condition); it was a transparency change (labeling AI responses) and a process change (AI as first-pass filter, not final word) that assumes future hallucinations are inevitable and manages their blast radius instead of asserting the model won't hallucinate again.
