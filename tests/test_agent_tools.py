"""
Tests for the agent tools.

Run with:
    EMBEDDING_PROVIDER=hash LLM_PROVIDER=mock pytest tests/test_agent_tools.py

These force the dependency-free hash embeddings and mock LLM responses,
so the full retrieval -> prompt -> generation -> render pipeline runs
end-to-end with no API keys, no network calls, and no model downloads.
They check pipeline wiring and citation correctness, not generation quality
(the mock provider returns fixed, hand-written content).
"""

import os

os.environ["EMBEDDING_PROVIDER"] = "hash"
os.environ["LLM_PROVIDER"] = "mock"

import pytest

from agent import render, tools
from ingest import build_index as bi


@pytest.fixture(autouse=True)
def fresh_index(tmp_path, monkeypatch):
    """Build a throwaway index per test so we never touch the real chroma_db/."""
    monkeypatch.setattr(bi, "INDEX_DIR", tmp_path / "chroma_db")
    bi.build_index(reset=True)


def test_battle_card_opschain_cites_competitive_and_winloss():
    data = tools.generate_battle_card("OpsChain")

    assert data["competitor"] == "OpsChain"
    assert len(data["objections"]) >= 2
    assert "competitive/opschain.md" in data["sources"]
    assert "customers/win-loss-notes.md" in data["sources"]

    rendered = render.render_battle_card(data)
    assert "Battle Card: OpsChain" in rendered
    assert "competitive/opschain.md" in rendered


def test_battle_card_unknown_competitor_raises():
    with pytest.raises(ValueError):
        tools.generate_battle_card("NotARealCompetitor")


def test_release_note_includes_known_limitation_from_jira():
    data = tools.draft_release_note("AutoSync")

    assert data["feature_name"] == "AutoSync"
    assert any("NetSuite" in item for item in data["known_limitations"])
    assert "engineering/jira-export-autosync.md" in data["sources"]


def test_comparison_table_has_all_three_columns():
    data = tools.generate_comparison_table()

    assert len(data["rows"]) >= 4
    for row in data["rows"]:
        assert {"dimension", "flowpilot", "opschain", "routely"} <= row.keys()

    rendered = render.render_comparison_table(data)
    assert "| Dimension | FlowPilot | OpsChain | Routely |" in rendered


def test_customer_story_uses_correct_transcript():
    data = tools.generate_customer_story("Brightline Logistics")

    assert data["customer_name"] == "Brightline Logistics"
    assert "customers/call-transcripts/brightline-logistics.md" in data["sources"]


def test_drift_check_flags_outdated_csv_claim():
    data = tools.check_messaging_drift()

    assert data["flags"], "Expected at least one drift flag"
    flagged_sources = {f["source"] for f in data["flags"]}
    assert "product/autosync-spec.md" in flagged_sources

    rendered = render.render_drift_report(data)
    assert "Messaging Drift Check" in rendered
    assert "🔴" in rendered  # at least one high-severity flag rendered
