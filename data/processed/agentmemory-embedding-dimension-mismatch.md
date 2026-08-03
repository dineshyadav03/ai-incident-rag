---
source_company: agentmemory (open-source project)
incident_title: Embedding provider switch leaves stale higher-dimension vectors in index, worker refuses to start
category: infra_failure
date: 2026-01-01
source_url: https://github.com/rohitg00/agentmemory/issues/455
---

# Embedding provider switch leaves stale higher-dimension vectors in index, worker refuses to start

## What happened

A user of the open-source `agentmemory` project switched their configured embedding provider from a 2048-dimension model to a local `all-MiniLM-L6-v2` model, which produces 384-dimension vectors. On restart, the worker refused to start, throwing: "Refusing to start: persisted vector index has 19 of 19 vectors with the wrong dimension. Active provider (local) declares 384; dimensions seen on disk: 2048."

## Root cause

The embedding provider was changed without any migration step for the existing vector index. All 19 previously stored vectors were still 2048-dimensional, but the newly active provider only produces 384-dimensional vectors — a hard incompatibility for similarity search, since vector distance comparisons require consistent dimensionality. The worker's refusal to start was intentional, not a crash: the maintainers had built in a check specifically to prevent the alternative failure mode, which is worse — silently running similarity search across a mixed-dimension index, which would either error unpredictably or (depending on the vector store implementation) silently return meaningless results without any error at all.

## Fix / lessons

Resolution was manual and destructive: the user had to set `AGENTMEMORY_DROP_STALE_INDEX=true`, restart the worker, and accept complete loss of the existing memory index while it rebuilt from scratch under the new provider. At the time of reporting, no non-destructive path existed — the issue's author specifically requested CLI flags for a guided migration, a background re-embedding process that could migrate old vectors to the new dimensionality without downtime, a non-destructive fallback mode (e.g., BM25-only search while re-embedding proceeds), and dashboard visibility into index health — none of which had been implemented at the time.

This is a small-scale but sharp illustration of a data/infra-layer failure mode directly relevant to this project's own architecture: any system that lets its embedding model be swapped independently of its vector store needs either a migration path or a hard compatibility check — silent corruption from a dimension mismatch is strictly worse than a loud refusal to start, but a loud refusal with no automated recovery path just converts an invisible failure into an operational fire drill instead.
