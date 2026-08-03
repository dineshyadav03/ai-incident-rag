# AI Production Root-Cause Index

A citation-grounded RAG system over real, public AI/LLM engineering postmortems.

Ask a question about how AI systems fail in production — silent RAG degradation, agent cost overruns, provider outages, model drift — and get an answer grounded in actual incidents, with citations back to the exact source and section it came from. The system refuses to answer when the corpus doesn't support a confident response.

## Status

Build in progress. See phases below.

## Why this exists

The [AI Incident Database](https://incidentdatabase.ai/) catalogs harm/ethics incidents, not engineering root-cause analysis. Individual postmortem roundups exist but are static, not queryable, and not citation-grounded per claim. This project builds the missing piece: a queryable, source-grounded reference over real AI engineering failures.

## Architecture

```
Ingestion: raw postmortem -> clean/structure -> chunk -> tag metadata -> embed -> ChromaDB
Query:     question -> embed -> vector search + BM25 -> merge -> cross-encoder rerank -> top-5
           -> refuse if below relevance threshold -> else build cited prompt -> Claude -> answer + citations
```

## Repository structure

```
data/
  raw/                 original source text/notes per incident
  processed/           cleaned markdown with metadata headers
src/
  ingest.py            load, clean, chunk
  embed.py             create + populate ChromaDB collection
  retrieve.py          vector + BM25 hybrid search
  rerank.py            cross-encoder reranking
  generate.py          prompt construction + Claude API call
  config/prompts.py    versioned system prompts
eval/
  golden_set.json      manually verified Q&A pairs
  evaluate.py           RAGAS evaluation script
main.py                CLI entry point
```

## Build phases

1. **Core pipeline** — ingest, chunk, embed, vector-only retrieval, cited generation
2. **Production-quality retrieval** — hybrid BM25 + vector search, cross-encoder reranking, citation enforcement, versioned prompts
3. **Evaluation and rigor** — 20-30 question golden set, RAGAS scoring (faithfulness, context precision/recall, answer relevancy), documented known limitations

## Known limitations

_Documented honestly here as the project develops._

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
```
