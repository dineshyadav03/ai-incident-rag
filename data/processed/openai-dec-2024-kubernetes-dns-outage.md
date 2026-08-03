---
source_company: OpenAI
incident_title: Telemetry service misconfiguration triggers Kubernetes control-plane/DNS outage across ChatGPT, API, Sora
category: outage_fallback
date: 2024-12-11
source_url: https://status.openai.com/incidents/01JMYB483C404VMPCW726E8MET
---

# Telemetry service misconfiguration triggers Kubernetes control-plane/DNS outage across ChatGPT, API, Sora

## What happened

On December 11, 2024, OpenAI deployed a new telemetry service at 3:12 PM PST intended to collect metrics from the Kubernetes control plane. Its configuration was unexpectedly broad: it triggered resource-intensive Kubernetes API operations simultaneously across every node in each large cluster. Alerts fired within a minute (3:13 PM); customer-visible impact began at 3:16 PM and reached maximum severity by 3:40 PM. Full recovery across all services wasn't achieved until 7:38 PM — a 4-hour-22-minute outage affecting ChatGPT, the API, and Sora.

## Root cause

Three compounding factors turned a bad config push into a multi-hour outage:

1. **Scale-dependent failure:** the telemetry service's problematic behavior only appeared in clusters above a certain size, so it passed testing in smaller staging environments and only broke in large production clusters.
2. **DNS caching masked the problem:** DNS-based service discovery depends on the Kubernetes control plane, but stale cached DNS records kept services able to find each other for about 20 minutes after the control plane started failing — delaying visibility into how serious the problem already was.
3. **Control-plane lockout:** once engineers identified the issue, they couldn't easily fix it, because the fix required accessing the Kubernetes API servers — the very systems being overwhelmed by the runaway telemetry load. The tool needed to stop the fire was on fire.

## Fix / lessons

Recovery required three parallel interventions: reducing cluster size to cut aggregate API load, blocking network access to expensive Kubernetes admin operations to relieve pressure, and scaling up API server resources directly.

OpenAI's stated prevention measures: staged rollouts with cluster-health monitoring at each stage, fault-injection testing specifically targeting control-plane failure modes, an emergency access path that doesn't depend on the same control plane it needs to fix, decoupling the data plane from the control plane architecturally so data-plane traffic can survive a control-plane failure, and improved caching/rate-limiting on the recovery path itself. This incident is a clean example of a single configuration change cascading into full-service unavailability via a dependency (DNS-via-control-plane) most engineers wouldn't think to check first.
