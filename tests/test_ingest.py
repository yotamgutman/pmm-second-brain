"""
Smoke tests for the ingestion pipeline.

Run with:
    EMBEDDING_PROVIDER=hash pytest

These tests force the dependency-free "hash" embedding function so they
run without downloading any models — suitable for CI. They check the
*pipeline mechanics* (parsing, chunking, metadata, indexing, retrieval
filtering), not retrieval quality.
"""

import os

os.environ["EMBEDDING_PROVIDER"] = "hash"

from ingest import build_index as bi
from ingest.parse_vault import parse_vault


def test_parse_vault_returns_expected_sources():
    chunks = parse_vault()
    sources = {c["source"] for c in chunks}

    assert len(chunks) > 30
    assert "product/autosync-spec.md" in sources
    assert "competitive/opschain.md" in sources
    assert "external/current-landing-page.md" in sources


def test_known_issues_chunk_mentions_netsuite():
    chunks = parse_vault()
    known_issues = [
        c for c in chunks
        if c["source"] == "product/autosync-spec.md" and c["heading"] == "Known Issues"
    ]

    assert known_issues
    assert "NetSuite" in known_issues[0]["text"]


def test_wikilinks_are_flattened_and_tracked():
    chunks = parse_vault()
    problem_chunk = next(
        c for c in chunks
        if c["source"] == "product/autosync-spec.md" and c["heading"] == "Problem"
    )

    # [[wikilink]] syntax should not leak into embedded text...
    assert "[[" not in problem_chunk["text"]
    # ...but the link target should be tracked in metadata
    assert "brightline-logistics" in problem_chunk["related"]


def test_build_and_query_index(tmp_path, monkeypatch):
    monkeypatch.setattr(bi, "INDEX_DIR", tmp_path / "chroma_db")

    bi.build_index(reset=True)
    collection = bi.get_collection()

    results = collection.query(query_texts=["NetSuite duplicate sync issue"], n_results=3)
    sources = [m["source"] for m in results["metadatas"][0]]

    assert "engineering/jira-export-autosync.md" in sources


def test_query_index_respects_doc_type_filter(tmp_path, monkeypatch):
    monkeypatch.setattr(bi, "INDEX_DIR", tmp_path / "chroma_db")

    bi.build_index(reset=True)
    collection = bi.get_collection()

    results = collection.query(
        query_texts=["audit log compliance"],
        n_results=5,
        where={"doc_type": "competitive"},
    )

    doc_types = {m["doc_type"] for m in results["metadatas"][0]}
    assert doc_types == {"competitive"}
