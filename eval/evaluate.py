"""Run the golden eval set through the RAG pipeline and score it with RAGAS.

Uses a local Ollama model as the RAGAS judge (LangchainLLMWrapper + ChatOllama)
and local sentence-transformers embeddings -- no paid API calls, matching the
project's zero-budget generation setup. See README "Known limitations" for
how judge-model size affects these scores.
"""

import json
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

# A single local Ollama instance on CPU serves one generation at a time.
# RAGAS's default (max_workers=16, timeout=180s) fires far more concurrent
# judge calls than that can keep up with, so almost everything times out
# queued behind the model rather than actually failing to answer. Run
# serially with a generous per-call timeout instead.
LOCAL_JUDGE_RUN_CONFIG = RunConfig(timeout=600, max_workers=1, max_retries=2)

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"
RESULTS_PATH = EVAL_DIR / "results.json"

JUDGE_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


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
    """Score the non-refused records with RAGAS. Refused records are scored
    as-is by the pipeline's own refusal behavior, not by RAGAS (there's no
    generated answer to judge)."""
    scorable = [r for r in records if not r["refused"]]
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
