"""
Retrieval helpers used by the agent tools.

Thin wrapper around the Chroma collection built by ingest/build_index.py.
Every helper returns a list of chunk dicts (chunk text + metadata), which
the agent tools turn into prompt context and a "Sources" citation list.
"""

from ingest.build_index import get_collection


def query(text: str, n_results: int = 5, doc_type: str | None = None, source: str | None = None):
    """Semantic search over the vault, optionally filtered by metadata."""
    collection = get_collection()

    where = None
    if doc_type and source:
        where = {"$and": [{"doc_type": doc_type}, {"source": source}]}
    elif doc_type:
        where = {"doc_type": doc_type}
    elif source:
        where = {"source": source}

    results = collection.query(query_texts=[text], n_results=n_results, where=where)

    return [
        {"text": doc, **meta}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]


def get_all_for_source(source: str):
    """Retrieve every chunk for a given vault file (exact match, no embedding needed)."""
    collection = get_collection()
    results = collection.get(where={"source": source})

    return [
        {"text": doc, **meta}
        for doc, meta in zip(results["documents"], results["metadatas"])
    ]


def format_context(chunks) -> str:
    """Render chunks into a context string with inline source/heading tags."""
    blocks = [f"[Source: {c['source']} — {c['heading']}]\n{c['text']}" for c in chunks]
    return "\n\n---\n\n".join(blocks)


def sources_from_chunks(chunks) -> list[str]:
    """Deduplicated, order-preserving list of source file paths."""
    seen: list[str] = []
    for c in chunks:
        if c["source"] not in seen:
            seen.append(c["source"])
    return seen
