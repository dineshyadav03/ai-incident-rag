"""Run the golden eval set through the RAG pipeline and score it with RAGAS.

Uses a local Ollama model as the RAGAS judge (LangchainLLMWrapper + ChatOllama)
and local sentence-transformers embeddings -- no paid API calls, matching the
project's zero-budget generation setup. See README "Known limitations" for
how judge-model size affects these scores.
"""

import json
import os
import statistics
from pathlib import Path

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings as LangchainHuggingFaceEmbeddings
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
from ragas.run_config import RunConfig

from src.generate import answer_question

# A single Ollama instance serving one CPU-bound request at a time can't keep
# up with RAGAS's default (max_workers=16, timeout=180s) -- almost everything
# times out queued behind the model instead of actually failing to answer.
# Default to serial with a generous timeout; override on a less-constrained
# machine (more RAM, a GPU) via env vars.
LOCAL_JUDGE_RUN_CONFIG = RunConfig(
    timeout=int(os.environ.get("RAGAS_TIMEOUT", "600")),
    max_workers=int(os.environ.get("RAGAS_MAX_WORKERS", "1")),
    max_retries=2,
)

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"
RESULTS_PATH = EVAL_DIR / "results.json"

JUDGE_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# RAGAS scoring (faithfulness/answer_relevancy/context_precision/context_recall)
# needs ~10 sequential LLM calls per question. On a local CPU model under real
# system memory pressure, a full 24-question run degraded from ~60s/job to
# 800+s/job and projected 9+ hours -- not tractable on constrained local
# hardware. Retrieval quality is checked on the FULL golden set regardless
# (retrieval_hit_rate below, no LLM judge needed, cheap and fast). RAGAS
# scoring defaults to a representative subset -- one or two questions per
# category, spanning all 6 -- but set RAGAS_FULL_EVAL=1 (e.g. on a
# less-constrained machine or free cloud notebook) to score the full set.
_SAMPLE_IDS = {"q01", "q05", "q07", "q11", "q14", "q17", "q19", "q23", "q24"}
RAGAS_SAMPLE_IDS = None if os.environ.get("RAGAS_FULL_EVAL") == "1" else _SAMPLE_IDS


def load_golden_set() -> list[dict]:
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_pipeline_over_golden_set(golden_set: list[dict]) -> list[dict]:
    """Run each golden question through the actual RAG pipeline, recording
    the generated answer, retrieved source ids (for a simple retrieval-hit
    check independent of RAGAS), and the chunk texts as RAGAS contexts."""
    records = []
    for item in golden_set:
        result = answer_question(item["question"])
        retrieved_ids = [c["metadata"]["source_url"] for c in result["chunks"]]
        expected_url = next(
            (c["metadata"]["source_url"] for c in result["chunks"]
             if c["id"].startswith(item["expected_source_id"])),
            None,
        )
        records.append({
            "id": item["id"],
            "question": item["question"],
            "reference_answer": item["reference_answer"],
            "expected_source_id": item["expected_source_id"],
            "category": item["category"],
            "generated_answer": result["answer"],
            "refused": result["refused"],
            "retrieved_source_hit": any(
                c["id"].startswith(item["expected_source_id"]) for c in result["chunks"]
            ),
            "contexts": [c["text"] for c in result["chunks"]],
        })
        print(f"  [{item['id']}] retrieval_hit={records[-1]['retrieved_source_hit']} refused={result['refused']}")
    return records


def score_with_ragas(records: list[dict]) -> list[dict]:
    """Score a representative subset of the non-refused records with RAGAS
    (see RAGAS_SAMPLE_IDS). Refused records are scored as-is by the
    pipeline's own refusal behavior, not by RAGAS (there's no generated
    answer to judge)."""
    scorable = [
        r for r in records
        if not r["refused"] and (RAGAS_SAMPLE_IDS is None or r["id"] in RAGAS_SAMPLE_IDS)
    ]
    if not scorable:
        return records

    chat = ChatOllama(model=JUDGE_MODEL, temperature=0)
    llm = LangchainLLMWrapper(chat)
    embeddings = LangchainEmbeddingsWrapper(LangchainHuggingFaceEmbeddings(model_name=EMBEDDING_MODEL))

    samples = [
        SingleTurnSample(
            user_input=r["question"],
            response=r["generated_answer"],
            retrieved_contexts=r["contexts"],
            reference=r["reference_answer"],
        )
        for r in scorable
    ]
    dataset = EvaluationDataset(samples=samples)

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False,
        run_config=LOCAL_JUDGE_RUN_CONFIG,
    )
    scores_df = result.to_pandas()

    for r, (_, row) in zip(scorable, scores_df.iterrows()):
        r["ragas"] = {
            "faithfulness": _clean(row.get("faithfulness")),
            "answer_relevancy": _clean(row.get("answer_relevancy")),
            "context_precision": _clean(row.get("context_precision")),
            "context_recall": _clean(row.get("context_recall")),
        }
    return records


def _clean(value):
    if value is None:
        return None
    try:
        if value != value:  # NaN check without importing numpy/math
            return None
    except TypeError:
        pass
    return float(value)


def summarize(records: list[dict]) -> dict:
    retrieval_hit_rate = sum(r["retrieved_source_hit"] for r in records) / len(records)
    refusal_rate = sum(r["refused"] for r in records) / len(records)

    metric_names = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    summary = {
        "n_questions": len(records),
        "retrieval_hit_rate": retrieval_hit_rate,
        "refusal_rate_on_in_corpus_questions": refusal_rate,
        "n_ragas_sampled": len(records) if RAGAS_SAMPLE_IDS is None else len(RAGAS_SAMPLE_IDS),
        "ragas_sample_note": (
            "RAGAS-scored on the FULL golden set (RAGAS_FULL_EVAL=1)."
            if RAGAS_SAMPLE_IDS is None else
            "RAGAS-scored on a representative subset (one/two per category), not the full set -- "
            "set RAGAS_FULL_EVAL=1 to score everything. retrieval_hit_rate and refusal_rate above "
            "ARE measured on the full set regardless."
        ),
    }
    for metric in metric_names:
        values = [r["ragas"][metric] for r in records if r.get("ragas") and r["ragas"][metric] is not None]
        failed = sum(1 for r in records if r.get("ragas") and r["ragas"][metric] is None)
        summary[metric] = {
            "mean": statistics.mean(values) if values else None,
            "n_scored": len(values),
            "n_parse_failed": failed,
        }
    return summary


def main():
    golden_set = load_golden_set()
    print(f"Running {len(golden_set)} golden questions through the RAG pipeline...")
    records = run_pipeline_over_golden_set(golden_set)

    print("\nScoring with RAGAS (local Ollama judge -- this takes a while)...")
    records = score_with_ragas(records)

    summary = summarize(records)
    output = {"summary": summary, "records": records}

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults written to {RESULTS_PATH}\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
