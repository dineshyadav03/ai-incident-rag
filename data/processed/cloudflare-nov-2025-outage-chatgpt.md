---
source_company: Cloudflare (impacting OpenAI ChatGPT and others)
incident_title: Oversized auto-generated config file crashes Cloudflare traffic system, taking down ChatGPT and X
category: outage_fallback
date: 2025-11-18
source_url: https://www.forbes.com/sites/siladityaray/2025/11/18/cloudflare-outage-knocks-x-and-chatgpt-offline/
---

# Oversized auto-generated config file crashes Cloudflare traffic system, taking down ChatGPT and X

## What happened

On November 18, 2025, starting around 6:20 AM EST, an automatically generated configuration file used by Cloudflare to manage threat traffic grew beyond its expected size and crashed the software system handling traffic for several Cloudflare services. Because ChatGPT (and X, Spotify, Canva, and Archive of Our Own) sit behind Cloudflare's infrastructure, the crash took all of them offline simultaneously — despite none of those companies having changed anything on their own end.

## Root cause

Cloudflare CEO Matthew Prince described the trigger as a spike in unusual traffic to one internal service, which propagated into the oversized configuration file problem and then into a crash of the traffic-handling system. Prince stated there was "no evidence the outage was caused by an attack," framing it as an internal technical failure rather than a security incident. Cloudflare noted customers might continue to see "higher-than-normal error rates" even after the initial incident was declared resolved by mid-morning, as remediation continued.

## Fix / lessons

This incident is the clearest example in this corpus of the specific failure mode this project's "provider outage & fallback" category is meant to capture: an AI product's availability was fully determined by a piece of shared infrastructure (Cloudflare) that the AI company (OpenAI) does not control and that had nothing to do with any model or AI-specific code. For any team building on top of a hosted LLM provider, this is a reminder that the provider's own uptime is itself downstream of the provider's infrastructure vendors — a fallback strategy that only accounts for "the LLM API is down" and not "a CDN/edge provider three layers down is down" misses this entire failure class. The market also registered the risk directly: Cloudflare's stock fell 3.1% at the open following the outage.
