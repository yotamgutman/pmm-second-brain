"""
The PMM agent's tools. Each function follows the same pattern:

    1. Retrieve relevant chunks from the vault (agent.retrieval)
    2. Fill a prompt template (agent/prompts/*.md) with that context
    3. Request structured JSON from the LLM (agent.llm)
    4. Attach the list of source files used, for citation

Every tool returns a plain dict matching the schema documented in its
prompt template, plus a "sources" key.
"""

from pathlib import Path
import os

from agent import llm, retrieval

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tool 1: Battle Card Generator
# ---------------------------------------------------------------------------

COMPETITOR_SLUGS = {"opschain": "OpsChain", "routely": "Routely"}


def generate_battle_card(competitor: str) -> dict:
    """competitor: 'OpsChain' or 'Routely'."""
    slug = competitor.strip().lower()
    if slug not in COMPETITOR_SLUGS:
        raise ValueError(f"Unknown competitor '{competitor}'. Expected one of {list(COMPETITOR_SLUGS.values())}")
    canonical = COMPETITOR_SLUGS[slug]

    profile_chunks = retrieval.get_all_for_source(f"competitive/{slug}.md")
    winloss_chunks = retrieval.query(f"{canonical} win loss reasons", n_results=3, doc_type="customers")

    chunks = profile_chunks + winloss_chunks
    context = retrieval.format_context(chunks)
    sources = retrieval.sources_from_chunks(chunks)

    prompt = _load_prompt("battle_card").replace("{{COMPETITOR}}", canonical).replace("{{CONTEXT}}", context)

    data = llm.complete_json(
        system_prompt=prompt,
        user_prompt=f"Generate the battle card for {canonical}.",
        mock_key=f"battle_card_{slug}",
    )
    data["sources"] = sources
    return data


# ---------------------------------------------------------------------------
# Tool 2: Release Note Drafter
# ---------------------------------------------------------------------------

def draft_release_note(feature: str = "AutoSync") -> dict:
    spec_chunks = retrieval.get_all_for_source("product/autosync-spec.md")
    jira_chunks = retrieval.get_all_for_source("engineering/jira-export-autosync.md")

    chunks = spec_chunks + jira_chunks
    context = retrieval.format_context(chunks)
    sources = retrieval.sources_from_chunks(chunks)

    prompt = _load_prompt("release_note").replace("{{FEATURE}}", feature).replace("{{CONTEXT}}", context)

    data = llm.complete_json(
        system_prompt=prompt,
        user_prompt=f"Draft the release note for {feature}.",
        mock_key=f"release_note_{feature.lower()}",
    )
    data["sources"] = sources
    return data


# ---------------------------------------------------------------------------
# Tool 3: Comparison Table Builder
# ---------------------------------------------------------------------------

def generate_comparison_table() -> dict:
    opschain_chunks = retrieval.get_all_for_source("competitive/opschain.md")
    routely_chunks = retrieval.get_all_for_source("competitive/routely.md")
    product_chunks = retrieval.get_all_for_source("product/autosync-spec.md")
    roadmap_chunks = retrieval.get_all_for_source("product/roadmap.md")

    chunks = opschain_chunks + routely_chunks + product_chunks + roadmap_chunks
    context = retrieval.format_context(chunks)
    sources = retrieval.sources_from_chunks(chunks)

    prompt = _load_prompt("comparison_table").replace("{{CONTEXT}}", context)

    data = llm.complete_json(
        system_prompt=prompt,
        user_prompt="Build the FlowPilot vs. OpsChain vs. Routely comparison table.",
        mock_key="comparison_table",
    )
    data["sources"] = sources
    return data


# ---------------------------------------------------------------------------
# Tool 4: Customer Story Drafter (stretch)
# ---------------------------------------------------------------------------

CUSTOMER_SLUGS = {
    "brightline logistics": "brightline-logistics",
    "hearth & co.": "hearth-and-co",
    "hearth & co": "hearth-and-co",
}


def generate_customer_story(customer: str) -> dict:
    """customer: 'Brightline Logistics' or 'Hearth & Co.'"""
    key = customer.strip().lower()
    if key not in CUSTOMER_SLUGS:
        raise ValueError(f"Unknown customer '{customer}'. Expected one of {list(CUSTOMER_SLUGS.values())}")
    slug = CUSTOMER_SLUGS[key]

    transcript_chunks = retrieval.get_all_for_source(f"customers/call-transcripts/{slug}.md")
    product_chunks = retrieval.query("AutoSync", n_results=2, doc_type="product")

    chunks = transcript_chunks + product_chunks
    context = retrieval.format_context(chunks)
    sources = retrieval.sources_from_chunks(chunks)

    prompt = _load_prompt("customer_story").replace("{{CUSTOMER}}", customer).replace("{{CONTEXT}}", context)

    data = llm.complete_json(
        system_prompt=prompt,
        user_prompt=f"Draft a customer story for {customer}.",
        mock_key=f"customer_story_{slug}",
    )
    data["sources"] = sources
    return data


# ---------------------------------------------------------------------------
# Tool 5: Messaging Drift Checker — the differentiator
# ---------------------------------------------------------------------------

def check_messaging_drift() -> dict:
    external_chunks = retrieval.get_all_for_source("external/current-landing-page.md")
    product_chunks = retrieval.get_all_for_source("product/autosync-spec.md")
    jira_chunks = retrieval.get_all_for_source("engineering/jira-export-autosync.md")

    internal_chunks = product_chunks + jira_chunks
    external_context = retrieval.format_context(external_chunks)
    internal_context = retrieval.format_context(internal_chunks)

    sources = retrieval.sources_from_chunks(external_chunks + internal_chunks)

    prompt = (
        _load_prompt("drift_check")
        .replace("{{EXTERNAL_CONTEXT}}", external_context)
        .replace("{{CONTEXT}}", internal_context)
    )

    data = llm.complete_json(
        system_prompt=prompt,
        user_prompt="Check the current landing page copy for messaging drift against internal reality.",
        mock_key="drift_check",
    )
    data["sources"] = sources
    return data


# ---------------------------------------------------------------------------
# Tool 6: Ask the Brain (free-text Q&A)
# ---------------------------------------------------------------------------

def answer_question(question: str, n_results: int = 4) -> dict:
    """
    Answer an arbitrary question grounded in the vault.

    In mock mode, an arbitrary question can't be matched to a canned
    answer, so this returns the raw retrieved chunks instead of a
    synthesized answer — still demonstrating that retrieval works,
    without pretending to generate a real response.
    """
    chunks = retrieval.query(question, n_results=n_results)
    sources = retrieval.sources_from_chunks(chunks)

    if os.environ.get("LLM_PROVIDER", "anthropic").lower() == "mock":
        return {"answer": None, "context_chunks": chunks, "sources": sources}

    context = retrieval.format_context(chunks)
    prompt = _load_prompt("qa").replace("{{CONTEXT}}", context)

    data = llm.complete_json(system_prompt=prompt, user_prompt=question)
    data["sources"] = sources
    return data
