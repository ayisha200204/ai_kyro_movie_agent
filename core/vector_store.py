from __future__ import annotations

from pathlib import Path
from typing import Any
import sys
import pysqlite3

sys.modules["sqlite3"] = pysqlite3
import chromadb

from .config import settings
from .chunker import DialogueChunk
from .llm import GeminiService


class MovieVectorStore:
    def __init__(self) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"description": "Movie subtitle dialogue chunks"},
        )
        self.llm = GeminiService()

    def reset(self) -> None:
        try:
            self.client.delete_collection(settings.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"description": "Movie subtitle dialogue chunks"},
        )

    def add_chunks(self, chunks: list[DialogueChunk], batch_size: int = 64) -> int:
        added = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.dialogue for c in batch]
            embeddings = self.llm.embed(texts, task_type="RETRIEVAL_DOCUMENT")
            self.collection.upsert(
                ids=[c.chunk_id for c in batch],
                documents=texts,
                embeddings=embeddings,
                metadatas=[
                    {
                        "movie_title": c.movie_title,
                        "start": c.start,
                        "end": c.end,
                        "cue_start": c.cue_start,
                        "cue_end": c.cue_end,
                    }
                    for c in batch
                ],
            )
            added += len(batch)
        return added

    def query(self, text: str, top_k: int | None = None, movie_title: str | None = None) -> list[dict[str, Any]]:
        n = top_k or settings.top_k
        query_embedding = self.llm.embed([text], task_type="RETRIEVAL_QUERY")[0]
        where = {"movie_title": movie_title} if movie_title else None
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {
                "dialogue": doc,
                "movie_title": meta.get("movie_title", "Unknown"),
                "start": meta.get("start", ""),
                "end": meta.get("end", ""),
                "cue_start": meta.get("cue_start", ""),
                "cue_end": meta.get("cue_end", ""),
                "distance": distance,
            }
            for doc, meta, distance in zip(docs, metas, distances)
        ]

    def movie_titles(self) -> list[str]:
        data = self.collection.get(include=["metadatas"])
        titles = {m.get("movie_title") for m in data.get("metadatas", []) if m}
        return sorted(t for t in titles if t)

    def count(self) -> int:
        return self.collection.count()
