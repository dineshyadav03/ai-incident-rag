"""Optional Streamlit web UI over the existing RAG pipeline. The CLI
(main.py) remains the primary interface -- this is a demo layer added as a
stretch goal so the project is explorable without a terminal.
"""

import streamlit as st

from src.generate import GROQ_API_KEY, GROQ_MODEL, OLLAMA_MODEL, answer_question
from src.ingest import load_source_catalog

st.set_page_config(page_title="AI Production Root-Cause Index", page_icon="🔍", layout="centered")


@st.cache_resource(show_spinner="Building the search index (one-time setup, ~10-20s)...")
def _ensure_index_built() -> None:
    # A fresh deployment (e.g. Streamlit Community Cloud) gets a clean clone
    # of this repo -- chroma_db/ is gitignored (derived data, not source), so
    # the index doesn't exist until something builds it. st.cache_resource
    # makes this run exactly once per server process, not once per visitor.
    from src.embed import build_index, get_collection

    if get_collection().count() == 0:
        build_index()


_ensure_index_built()

if "question" not in st.session_state:
    st.session_state.question = ""

st.title("AI Production Root-Cause Index")
st.caption(
    "Ask how AI/LLM systems fail in production. Every answer is grounded in a real, "
    "curated incident with a citation back to the source -- the system refuses to answer "
    "when the corpus doesn't support a confident response."
)

with st.sidebar:
    st.header("Corpus")
    sources = load_source_catalog()
    st.metric("Curated incidents", len(sources))
    counts = {}
    for s in sources:
        counts[s["category"]] = counts.get(s["category"], 0) + 1
    for category, count in sorted(counts.items()):
        st.write(f"**{category}**: {count}")
    st.divider()
    if GROQ_API_KEY:
        st.caption(f"Generation via Groq's free-tier hosted API (`{GROQ_MODEL}`). Fast regardless of local machine load.")
    else:
        st.caption(f"Generation via a local Ollama model (`{OLLAMA_MODEL}`). No API key, no data leaves this machine.")

EXAMPLE_QUESTIONS = [
    "Why was Anthropic's silent Claude quality degradation in 2025 hard to detect?",
    "Why did Uber run out of its 2026 AI budget so fast?",
    "What did the Replit AI agent do after deleting a production database?",
]

st.write("Try an example, or ask your own question below:")
cols = st.columns(len(EXAMPLE_QUESTIONS))
for col, example in zip(cols, EXAMPLE_QUESTIONS):
    if col.button(example, use_container_width=True):
        st.session_state.question = example

question = st.text_input("Your question", key="question")

if st.button("Ask", type="primary") and question.strip():
    spinner_text = "Retrieving and generating..." if GROQ_API_KEY else "Retrieving and generating (local model, can take 10-30s)..."
    with st.spinner(spinner_text):
        result = answer_question(question)

    if result["refused"]:
        st.warning(result["answer"])
    else:
        st.markdown(result["answer"])
        if result["chunks"]:
            st.subheader("Sources")
        for c in result["chunks"]:
            meta = c["metadata"]
            st.markdown(
                f"- **[{meta['category']}] {meta['source_company']}** — {meta['incident_title']}  \n"
                f"  {meta['source_url']}"
            )
