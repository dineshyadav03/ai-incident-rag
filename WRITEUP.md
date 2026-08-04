# Portfolio writeup / LinkedIn post

## Short version (LinkedIn post)

I built a RAG system over real AI production postmortems — because I couldn't find one that existed.

**The gap:** when an AI/LLM system fails in production, the writeup explaining what went wrong usually gets published once, on one company's engineering blog, and then disappears into the noise. I checked the AI Incident Database first — it catalogs ~1,000 harm and ethics incidents, but not engineering root-cause. I found roundup posts, but they're static summaries, not queryable, and not grounded per-claim. Nothing let you ask "what causes silent RAG degradation in production?" and get an answer traceable to the exact incident it came from.

**What I built:** a hand-curated corpus of 18 real, verified incidents — Replit's agent deleting a production database mid-code-freeze, OpenAI's GPT-4o sycophancy rollback, Anthropic's own postmortem on three silent quality-degradation bugs, the Azure OpenAI retry storm, Uber burning its entire 2026 AI budget in four months, Alibaba's ROME agent hijacking GPU resources for crypto mining, and more — spanning agent failures, RAG failures, model drift, provider outages, alignment regressions, and infra failures. The system does hybrid retrieval (vector + BM25), cross-encoder reranking, and refuses to answer when the corpus doesn't support a confident response, rather than guessing. Every claim comes with a citation back to the source.

**Why it's not just a chatbot wrapper:** a general LLM will recall famous incidents from training data but confidently blur details on less-famous ones, can't point to the source paragraph a claim came from, and knows nothing published after its cutoff. This is the textbook case for RAG — fragmented primary sources, no compiled reference, correctness that depends on exact grounding rather than paraphrase.

Built with phased discipline: core pipeline → hybrid retrieval + reranking → formal evaluation (RAGAS: faithfulness, context precision/recall, answer relevancy) against a 28-question golden set. Retrieval hit rate: 100%. Runs entirely on free resources — local Ollama for generation, and a free Google Colab GPU instance for the full evaluation run once local hardware couldn't keep up. Zero paid API calls anywhere in the stack.

Repo: [github.com/dineshyadav03/ai-incident-rag](https://github.com/dineshyadav03/ai-incident-rag)

---

## Longer version (for a README/portfolio page or interview talking points)

**The problem.** AI production failures are a genuinely fragmented information space. A startup's agent racks up a surprise API bill, a mid-size company's RAG system silently degrades, a major provider has an outage traced to a Kubernetes DNS dependency nobody thought to check — each gets written up once, by one team, on one blog, and then it's gone. There's no compiled, queryable reference for "what patterns of production AI failure exist and how were they root-caused."

**What already exists, and why it falls short.** The AI Incident Database is the obvious prior art — it's well-maintained and has ~1,000 entries — but it's scoped to harm and ethics incidents (bias, safety, misuse), not engineering root-cause analysis. Roundup blog posts exist too, but they're static: no per-claim grounding, no way to query them, and they go stale the moment they're published.

**Why a general chatbot can't fill this gap.** It'll recall the famous incidents — the OpenAI or Anthropic ones — from training data, but confidently invent or blur details on the long-tail ones, which are exactly the specific, low-frequency information LLMs are worst at recalling accurately. It can't cite the source paragraph a claim came from. And anything published after its training cutoff doesn't exist to it at all.

**The build.** Sources were fetched, read, and manually excerpted — not bulk-scraped — because the curation itself is part of the value: each source was checked against inclusion criteria (real, publicly published, named specifics, engineering root cause) before being written up. The pipeline itself follows the same phased discipline production RAG teams use: a working vector-only baseline first, then hybrid BM25 + vector retrieval with cross-encoder reranking and citation enforcement, then formal evaluation against a golden set rather than eyeballing outputs.

**The results.** Retrieval hit rate — whether the correct source was actually retrieved, measured independently of any LLM judge — was 100% across all 28 golden questions, with a 0% refusal rate on in-corpus questions. RAGAS scores (local `llama3.2:3b` as judge): `context_precision` 0.989 (27/28 parsed successfully), `context_recall` 0.650 (26/28), `answer_relevancy` 0.762 (23/28), `faithfulness` 0.850 (only 10/28 parsed — the small judge model struggles most with faithfulness's longer statement-extraction step). I report the parse-failure rates alongside the scores rather than hiding them, because a mean computed over a fraction of the sample needs that context to be read honestly. These numbers held essentially flat after a later corpus expansion from 16 to 18 sources — a useful signal that quality didn't quietly regress as the corpus grew.

**What I'd tell an interviewer about the honest parts.** A few things went sideways during the eval and each taught me something. First, a local 3B-parameter judge model produces unreliable structured JSON for some RAGAS metrics — that's a real, measured limitation of the judge, not the underlying RAG system, and the parse-failure rate itself varies a lot by metric (27/28 for context_precision vs. 10/28 for faithfulness). Second, a full run on my own machine degraded from ~60 seconds per question to over 800 seconds under real system memory pressure (other apps eating RAM), projecting 9+ hours to finish — so I diagnosed the actual bottleneck (memory, not model capability), moved the same code to a free Google Colab GPU instance instead. Third, even that fix wasn't perfectly stable: the same code and a similar question count took 35 minutes on one Colab run and 81 minutes on another, a reminder that free-tier GPU allocation and network conditions vary and "it worked once" isn't the same as "it's reliably fast."

**What's next.** The corpus is designed to grow — 18 sources as of this expansion, target range was 15-25 — and the eval's clearest lever for improvement is a stronger local judge model to close the faithfulness parse-failure gap.
