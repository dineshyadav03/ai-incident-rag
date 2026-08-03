# RAG Q&A assistant retrieval accuracy stuck at 49%, fixed via chunking and embedding changes

**Company:** Amazon Finance Automation
**Category:** rag_failure
**Date:** 2024-12-02
**Source:** https://aws.amazon.com/blogs/machine-learning/how-amazon-finance-automation-built-a-generative-ai-qa-chat-assistant-using-amazon-bedrock/

## What happened

Amazon Finance Automation built a RAG-based Q&A assistant on Amazon Bedrock to let analysts quickly answer customer queries. The first version of the system landed at only 49% accuracy — far below what was usable in production. The team broke down the inaccuracies: fixed-size chunking (512 tokens / 384 words) that ignored document section boundaries caused incomplete context to reach the LLM in 14% of cases; retrieval relevance scores were low (55–65%); the model hallucinated when no relevant context was retrieved in another 14% of cases; and 13% of failures were overly brief answers missing necessary context.

## Root cause

The failure was distributed across the whole RAG pipeline rather than one single bug: naive fixed-size chunking split documents in the middle of logical sections, degrading retrieval relevance, which in turn increased hallucination since the generator had to fill gaps with unsupported content.

## Fix / lessons

The team improved accuracy in three iterative stages, each independently measured:

1. **Semantic chunking (49% → 64%):** converted unstructured text to structured HTML, inserted section dividers based on HTML tags and section-keyword tags, and used embedding vectors to detect semantic boundaries instead of chunking by fixed token count.
2. **Prompt engineering (64% → 76%):** instructed the model to explicitly decline answering when it lacked relevant context (an early form of the refusal behavior this project's own citation-enforcement step is designed around), added chain-of-thought reasoning for completeness, and added inline citation generation with hyperlinks.
3. **Embedding model upgrade (76% → 86%):** switched from the original embedding model to Amazon Titan Text Embeddings G1, which raised context-retrieval relevance from 55–65% up to 75–80%.

The net result was a 49%-to-86% accuracy improvement, achieved entirely through iterative, measured changes to chunking strategy, prompting, and embedding choice — not a bigger or different generator model. This is a strong illustration of why retrieval quality (chunking + embeddings), not just the LLM, is usually the dominant lever in RAG system accuracy.
