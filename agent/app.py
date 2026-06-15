"""
PMM Second Brain — Streamlit demo app.

Run with:
    streamlit run agent/app.py

If chroma_db/ doesn't exist yet, build it first:
    python -m ingest.build_index
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent import render, tools  # noqa: E402  (import after load_dotenv)

INDEX_DIR = Path(__file__).resolve().parent.parent / "chroma_db"

st.set_page_config(page_title="PMM Second Brain", page_icon="🧠", layout="wide")

st.title("🧠 PMM Second Brain")
st.caption(
    "An AI agent for FlowPilot that generates product marketing assets "
    "from the company's internal knowledge base — and checks whether "
    "external messaging still matches internal reality."
)

# ---------------------------------------------------------------------------
# Sidebar — mode / setup info
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Setup")

    llm_provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    embedding_provider = os.environ.get("EMBEDDING_PROVIDER", "local").lower()

    st.markdown(f"**LLM provider:** `{llm_provider}`")
    st.markdown(f"**Embedding provider:** `{embedding_provider}`")

    if llm_provider == "mock":
        st.info(
            "**Demo mode** — generation uses hand-written, vault-grounded "
            "mock responses (no API key needed). Retrieval and source "
            "citations are real. Set `LLM_PROVIDER=anthropic` and "
            "`ANTHROPIC_API_KEY` in `.env` for live generation."
        )

    st.markdown("---")
    st.markdown(
        "**The vault:** `vault/` is an Obsidian-compatible markdown "
        "knowledge base for a fictional company, FlowPilot. Every "
        "generated asset below cites the vault files it drew from."
    )

if not INDEX_DIR.exists():
    st.error(
        "No vector index found. Build it first by running:\n\n"
        "```\npython -m ingest.build_index\n```"
    )
    st.stop()


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_battle, tab_release, tab_compare, tab_story, tab_drift, tab_ask = st.tabs(
    ["Battle Cards", "Release Notes", "Comparison Table", "Customer Stories", "Drift Check", "Ask the Brain"]
)

with tab_battle:
    st.subheader("Battle Card Generator")
    st.write("Generates a competitive battle card from the competitor profile and relevant win/loss notes.")

    competitor = st.selectbox("Competitor", ["OpsChain", "Routely"])
    if st.button("Generate Battle Card", key="battle_card_btn"):
        with st.spinner("Retrieving context and generating..."):
            data = tools.generate_battle_card(competitor)
        st.markdown(render.render_battle_card(data))

with tab_release:
    st.subheader("Release Note Drafter")
    st.write("Drafts a release note from the product spec and engineering ticket — including any known limitations.")

    feature = st.selectbox("Feature", ["AutoSync"])
    if st.button("Draft Release Note", key="release_note_btn"):
        with st.spinner("Retrieving context and generating..."):
            data = tools.draft_release_note(feature)
        st.markdown(render.render_release_note(data))

with tab_compare:
    st.subheader("Comparison Table Builder")
    st.write("Builds a FlowPilot vs. OpsChain vs. Routely comparison table from competitive and product context.")

    if st.button("Build Comparison Table", key="comparison_btn"):
        with st.spinner("Retrieving context and generating..."):
            data = tools.generate_comparison_table()
        st.markdown(render.render_comparison_table(data))

with tab_story:
    st.subheader("Customer Story Drafter")
    st.write("Drafts a customer story from a call transcript — flagged as a draft for human review.")

    customer = st.selectbox("Customer", ["Brightline Logistics", "Hearth & Co."])
    if st.button("Draft Customer Story", key="customer_story_btn"):
        with st.spinner("Retrieving context and generating..."):
            data = tools.generate_customer_story(customer)
        st.markdown(render.render_customer_story(data))

with tab_drift:
    st.subheader("Messaging Drift Check")
    st.write(
        "Compares the **current external landing page copy** against "
        "**internal product and engineering reality**, and flags claims "
        "that no longer hold up."
    )

    if st.button("Run Drift Check", key="drift_btn"):
        with st.spinner("Comparing external messaging to internal reality..."):
            data = tools.check_messaging_drift()
        st.markdown(render.render_drift_report(data))

with tab_ask:
    st.subheader("Ask the Brain")
    st.write("Free-text Q&A over the vault — ask anything about FlowPilot's product, competitors, or customers.")

    question = st.text_input("Your question", placeholder="e.g. Why did we lose the Meridian Health Group deal?")
    if question:
        with st.spinner("Searching the vault..."):
            data = tools.answer_question(question)
        st.markdown(render.render_qa_result(data))
