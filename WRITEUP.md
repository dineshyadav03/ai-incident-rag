# Portfolio writeup / LinkedIn post

## Short version (LinkedIn post)

I built a RAG system over real AI production postmortems — because I couldn't find one that existed.

**The gap:** when an AI/LLM system fails in production, the writeup explaining what went wrong usually gets published once, on one company's engineering blog, and then disappears into the noise. I checked the AI Incident Database first — it catalogs ~1,000 harm and ethics incidents, but not engineering root-cause. I found roundup posts, but they're static summaries, not queryable, and not grounded per-claim. Nothing let you ask "what causes silent RAG degradation in production?" and get an answer traceable to the exact incident it came from.

**What I built:** a hand-curated corpus of 16 real, verified incidents — Replit's agent deleting a production database mid-code-freeze, OpenAI's GPT-4o sycophancy rollback, Anthropic's own postmortem on three silent quality-degradation bugs, the Azure OpenAI retry storm, and more — spanning agent failures, RAG failures, model drift, provider outages, alignment regressions, and infra failures. The system does hybrid retrieval (vector + BM25), cross-encoder reranking, and refuses to answer when the corpus doesn't support a confident response, rather than guessing. Every claim comes with a citation back to the source.

**Why it's not just a chatbot wrapper:** a general LLM will recall famous incidents from training data but confidently blur details on less-famous ones, can't point to the source paragraph a claim came from, and knows nothing published after its cutoff. This is the textbook case for RAG — fragmented primary sources, no compiled reference, correctness that depends on exact grounding rather than paraphrase.

Built with phased discipline: core pipeline → hybrid retrieval + reranking → formal evaluation (RAGAS: faithfulness, context precision/recall, answer relevancy) against a 24-question golden set. Runs entirely on free, local resources — a local Ollama model for both generation and evaluation, zero paid API calls anywhere in the stack.

Repo: [github.com/dineshyadav03/ai-incident-rag](https://github.com/dineshyadav03/ai-incident-rag)

---

## Longer version (for a README/portfolio page or interview talking points)

**The problem.** AI production failures are a genuinely fragmented information space. A startup's agent racks up a surprise API bill, a mid-size company's RAG system silently degrades, a major provider has an outage traced to a Kubernetes DNS dependency nobody thought to check — each gets written up once, by one team, on one blog, and then it's gone. There's no compiled, queryable reference for "what patterns of production AI failure exist and how were they root-caused."

**What already exists, and why it falls short.** The AI Incident Database is the obvious prior art — it's well-maintained and has ~1,000 entries — but it's scoped to harm and ethics incidents (bias, safety, misuse), not engineering root-cause analysis. Roundup blog posts exist too, but they're static: no per-claim grounding, no way to query them, and they go stale the moment they're published.

**Why a general chatbot can't fill this gap.** It'll recall the famous incidents — the OpenAI or Anthropic ones — from training data, but confidently invent or blur details on the long-tail ones, which are exactly the specific, low-frequency information LLMs are worst at recalling accurately. It can't cite the source paragraph a claim came from. And anything published after its training cutoff doesn't exist to it at all.

**The build.** Sources were fetched, read, and manually excerpted — not bulk-scraped — because the curation itself is part of the value: each of the 16 sources was checked against inclusion criteria (real, publicly published, named specifics, engineering root cause) before being written up. The pipeline itself follows the same phased discipline production RAG teams use: a working vector-only baseline first, then hybrid BM25 + vector retrieval with cross-encoder reranking and citation enforcement, then formal evaluation against a golden set rather than eyeballing outputs.

**What I'd tell an interviewer about the honest parts.** The RAGAS evaluation currently runs on a local 3B-parameter judge model, because there was zero API budget for this build — and that shows up directly in the numbers: `faithfulness` and `context_recall` score reliably, while `answer_relevancy` and `context_precision` frequently fail to parse because the small model can't reliably produce the strict JSON those metrics require internally. That's a documented, known limitation, not a hidden one — and it's a genuinely useful thing to be able to explain: I know exactly which of my four eval metrics I can trust today and why, and what upgrading the judge model would fix.

**What's next.** The corpus is designed to grow — 16 sources at v1, target range was 15-25 — and the eval is the clearest lever for improvement: a stronger local judge model would resolve the JSON-parsing failures on two of the four RAGAS metrics.
