# Portfolio writeup / LinkedIn post

## Short version (LinkedIn post)

I built a RAG system over real AI production postmortems — because I couldn't find one that existed.

**The gap:** when an AI/LLM system fails in production, the writeup explaining what went wrong usually gets published once, on one company's engineering blog, and then disappears into the noise. I checked the AI Incident Database first — it catalogs ~1,000 harm and ethics incidents, but not engineering root-cause. I found roundup posts, but they're static summaries, not queryable, and not grounded per-claim. Nothing let you ask "what causes silent RAG degradation in production?" and get an answer traceable to the exact incident it came from.

**What I built:** a hand-curated corpus of 16 real, verified incidents — Replit's agent deleting a production database mid-code-freeze, OpenAI's GPT-4o sycophancy rollback, Anthropic's own postmortem on three silent quality-degradation bugs, the Azure OpenAI retry storm, and more — spanning agent failures, RAG failures, model drift, provider outages, alignment regressions, and infra failures. The system does hybrid retrieval (vector + BM25), cross-encoder reranking, and refuses to answer when the corpus doesn't support a confident response, rather than guessing. Every claim comes with a citation back to the source.

**Why it's not just a chatbot wrapper:** a general LLM will recall famous incidents from training data but confidently blur details on less-famous ones, can't point to the source paragraph a claim came from, and knows nothing published after its cutoff. This is the textbook case for RAG — fragmented primary sources, no compiled reference, correctness that depends on exact grounding rather than paraphrase.

Built with phased discipline: core pipeline → hybrid retrieval + reranking → formal evaluation (RAGAS: faithfulness, context precision/recall, answer relevancy) against a 24-question golden set. Retrieval hit rate: 100%. Runs entirely on free resources — local Ollama for generation, and a free Google Colab GPU instance for the full evaluation run once local hardware couldn't keep up. Zero paid API calls anywhere in the stack.

Repo: [github.com/dineshyadav03/ai-incident-rag](https://github.com/dineshyadav03/ai-incident-rag)

---

## Longer version (for a README/portfolio page or interview talking points)

**The problem.** AI production failures are a genuinely fragmented information space. A startup's agent racks up a surprise API bill, a mid-size company's RAG system silently degrades, a major provider has an outage traced to a Kubernetes DNS dependency nobody thought to check — each gets written up once, by one team, on one blog, and then it's gone. There's no compiled, queryable reference for "what patterns of production AI failure exist and how were they root-caused."

**What already exists, and why it falls short.** The AI Incident Database is the obvious prior art — it's well-maintained and has ~1,000 entries — but it's scoped to harm and ethics incidents (bias, safety, misuse), not engineering root-cause analysis. Roundup blog posts exist too, but they're static: no per-claim grounding, no way to query them, and they go stale the moment they're published.

**Why a general chatbot can't fill this gap.** It'll recall the famous incidents — the OpenAI or Anthropic ones — from training data, but confidently invent or blur details on the long-tail ones, which are exactly the specific, low-frequency information LLMs are worst at recalling accurately. It can't cite the source paragraph a claim came from. And anything published after its training cutoff doesn't exist to it at all.

**The build.** Sources were fetched, read, and manually excerpted — not bulk-scraped — because the curation itself is part of the value: each of the 16 sources was checked against inclusion criteria (real, publicly published, named specifics, engineering root cause) before being written up. The pipeline itself follows the same phased discipline production RAG teams use: a working vector-only baseline first, then hybrid BM25 + vector retrieval with cross-encoder reranking and citation enforcement, then formal evaluation against a golden set rather than eyeballing outputs.

**The results.** Retrieval hit rate — whether the correct source was actually retrieved, measured independently of any LLM judge — was 100% across all 24 golden questions, with a 0% refusal rate on in-corpus questions. RAGAS scores (local `llama3.2:3b` as judge): `context_precision` 0.989 (23/24 parsed successfully), `context_recall` 0.661 (22/24), `answer_relevancy` 0.787 (15/24), `faithfulness` 0.877 (only 6/24 parsed — the small judge model struggles most with faithfulness's longer statement-extraction step). I report the parse-failure rates alongside the scores rather than hiding them, because a mean computed over 6 out of 24 samples needs that context to be read honestly.

**What I'd tell an interviewer about the honest parts.** Two things went sideways during the eval and both taught me something. First, a local 3B-parameter judge model produces unreliable structured JSON for some RAGAS metrics — that's a real, measured limitation of the judge, not the underlying RAG system, and the parse-failure rate itself varies a lot by metric (23/24 for context_precision vs. 6/24 for faithfulness). Second, a full run on my own machine degraded from ~60 seconds per question to over 800 seconds under real system memory pressure (other apps eating RAM), projecting 9+ hours to finish — so I diagnosed the actual bottleneck (memory, not model capability), moved the same code to a free Google Colab GPU instance, and it finished in 35 minutes. Same code, same free-tier budget, just the right compute for the job.

**What's next.** The corpus is designed to grow — 16 sources at v1, target range was 15-25 — and the eval's clearest lever for improvement is a stronger local judge model to close the faithfulness parse-failure gap.
