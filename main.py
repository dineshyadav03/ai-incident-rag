"""CLI entry point for the AI Production Root-Cause Index."""

import argparse

from src.embed import build_index
from src.generate import answer_question


def cmd_ingest(args):
    n = build_index()
    print(f"Indexed {n} chunks from the curated corpus.")


def cmd_ask(args):
    question = " ".join(args.question)
    result = answer_question(question, top_k=args.top_k)

    print(f"\nQ: {question}\n")
    print(result["answer"])

    if not result["refused"]:
        print("\nSources:")
        for c in result["chunks"]:
            meta = c["metadata"]
            print(f"  - [{meta['category']}] {meta['source_company']}: {meta['incident_title']}")
            print(f"    {meta['source_url']}")


def main():
    parser = argparse.ArgumentParser(description="AI Production Root-Cause Index")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Build the ChromaDB index from the corpus")
    ingest_parser.set_defaults(func=cmd_ingest)

    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("question", nargs="+", help="The question to ask")
    ask_parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve")
    ask_parser.set_defaults(func=cmd_ask)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
