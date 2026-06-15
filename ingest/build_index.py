"""
Build (or rebuild) the Chroma vector index from the Obsidian vault, and
run test retrieval queries against it.

Usage:
    python -m ingest.build_index                          # (re)build the index
    python -m ingest.build_index --no-reset                # add without clearing
    python -m ingest.build_index --query "NetSuite sync issue"
    python -m ingest.build_index --query "audit log" --doc-type competitive
"""

import argparse
from pathlib import Path

import chromadb
from dotenv import load_dotenv

from ingest.embeddings import get_embedding_function
from ingest.parse_vault import VAULT_DIR, parse_vault

load_dotenv()

INDEX_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION_NAME = "pmm_vault"


def get_client():
    return chromadb.PersistentClient(path=str(INDEX_DIR))


def get_collection(client=None):
    client = client or get_client()
    return client.get_or_create_collection(
        COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )


def build_index(vault_dir: Path = VAULT_DIR, reset: bool = True):
    client = get_client()

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = get_collection(client)

    chunks = parse_vault(vault_dir)
    if not chunks:
        raise RuntimeError(f"No chunks found in vault: {vault_dir}")

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source": c["source"],
                "doc_type": c["doc_type"],
                "title": c["title"],
                "heading": c["heading"],
                "tags": c["tags"],
                "related": c["related"],
            }
            for c in chunks
        ],
    )

    print(f"Indexed {len(chunks)} chunks into '{COLLECTION_NAME}' at {INDEX_DIR}")
    return collection


def query_index(query: str, n_results: int = 4, doc_type: str | None = None):
    collection = get_collection()

    where = {"doc_type": doc_type} if doc_type else None
    results = collection.query(query_texts=[query], n_results=n_results, where=where)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    if not docs:
        print("No results.")
        return

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
        preview = doc.replace("\n", " ")
        if len(preview) > 220:
            preview = preview[:220] + "..."
        print(f"\n--- Result {i + 1}  (distance={dist:.4f}) ---")
        print(f"Source: {meta['source']}  |  Heading: {meta['heading']}  |  doc_type: {meta['doc_type']}")
        print(preview)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build or query the PMM Second Brain vector index")
    parser.add_argument("--query", help="Run a test retrieval query against the index instead of building it")
    parser.add_argument("--n-results", type=int, default=4, help="Number of results to return for --query")
    parser.add_argument("--doc-type", help="Filter --query results by doc_type (product, competitive, customers, engineering, external)")
    parser.add_argument("--no-reset", action="store_true", help="Add to the existing collection instead of rebuilding it")
    args = parser.parse_args()

    if args.query:
        query_index(args.query, n_results=args.n_results, doc_type=args.doc_type)
    else:
        build_index(reset=not args.no_reset)
