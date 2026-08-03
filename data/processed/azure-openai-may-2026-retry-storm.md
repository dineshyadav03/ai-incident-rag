---
source_company: Microsoft (Azure OpenAI Service)
incident_title: Upstream API change triggers retry-amplification storm, overwhelms shared inference load balancer
category: outage_fallback
date: 2026-05-29
source_url: https://azure.status.microsoft/en-us/status/history/
---

# Upstream API change triggers retry-amplification storm, overwhelms shared inference load balancer

## What happened

Between 09:39 UTC and 17:05 UTC on May 29, 2026, customers of Azure OpenAI Service experienced increased latency and intermittent request failures across multiple regions. The issue first appeared in Australia East before spreading, with particularly severe impact in Sweden Central, which handles significantly higher traffic volume than where the problem originated.

## Root cause

An upstream API layer change altered how capacity-related failures were communicated back to clients. This change triggered unexpected retry behavior in client/service code that had not been designed around the new failure-signaling format. The result was a cascading retry-amplification effect: internal traffic volume increased dramatically with no corresponding increase in actual customer demand, because the "extra" traffic was retries of requests that were themselves failing due to the signaling change. That amplified retry traffic overwhelmed a shared inference load-balancer component used across multiple regions, and because the component was shared, the overload in one region degraded service in others — which is why the impact was most severe in the highest-traffic region (Sweden Central) rather than the region where the change was first deployed.

## Fix / lessons

This is a textbook "retry storm" failure: a change to error/capacity signaling, without corresponding changes to client-side retry logic, turned a a localized capacity blip into a multi-region outage through amplification, not through any actual increase in real demand. It is a direct illustration of why naive fixed-interval or unconditional retry logic is dangerous in front of shared infrastructure — retries need to be capacity-aware and back off in response to the same signals that caused the failure, not blindly repeat the same request pattern that just failed. For teams building fallback/retry logic against any hosted LLM provider, this incident is a concrete argument for exponential backoff with jitter and circuit breakers over naive immediate retries, especially against shared backend components you don't control and can't see the load on directly.
