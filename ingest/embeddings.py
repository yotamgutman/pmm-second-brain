"""
Embedding function selection for the PMM Second Brain index.

Set EMBEDDING_PROVIDER in your .env to choose:

  "local"  (default) — sentence-transformers/all-MiniLM-L6-v2.
            Runs fully offline after the model is downloaded on first use.
            No API key required. Recommended for the demo.

  "openai" — OpenAI text-embedding-3-small.
            Requires OPENAI_API_KEY. Slightly higher retrieval quality,
            costs a fraction of a cent for a vault this size.

  "hash"   — deterministic, dependency-free bag-of-words embedding.
            NOT semantically rich — intended only for testing the
            pipeline (chunking, indexing, metadata filtering) in
            environments without internet access to download models,
            e.g. CI. Do not use this for the actual demo.
"""

import hashlib
import os
import struct

from chromadb import Documents, EmbeddingFunction, Embeddings

EMBEDDING_DIM = 384  # matches all-MiniLM-L6-v2


class HashEmbeddingFunction(EmbeddingFunction[Documents]):
    """Deterministic bag-of-words embedding — no ML dependencies."""

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002 - Chroma's signature
        return [self._embed(text) for text in input]

    @staticmethod
    def name() -> str:
        return "hash-bow"

    def get_config(self):
        return {"dim": self.dim}

    @staticmethod
    def build_from_config(config):
        return HashEmbeddingFunction(dim=config.get("dim", EMBEDDING_DIM))

    def _embed(self, text: str):
        vec = [0.0] * self.dim
        for word in text.lower().split():
            digest = hashlib.md5(word.encode("utf-8")).digest()
            for i in range(0, len(digest), 4):
                idx = struct.unpack("I", digest[i:i + 4])[0] % self.dim
                vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


def get_embedding_function():
    provider = os.environ.get("EMBEDDING_PROVIDER", "local").lower()

    if provider == "hash":
        return HashEmbeddingFunction()

    if provider == "openai":
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        return OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-3-small")

    if provider == "local":
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

        return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    raise ValueError(f"Unknown EMBEDDING_PROVIDER: '{provider}' (expected local | openai | hash)")
