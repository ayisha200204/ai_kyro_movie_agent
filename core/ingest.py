from __future__ import annotations

import argparse
from pathlib import Path

from .chunker import parse_and_chunk
from .config import settings
from .vector_store import MovieVectorStore


def ingest(reset: bool = False) -> None:
    paths = sorted(settings.subtitle_dir.glob("*.srt"))
    if len(paths) > 100:
        raise ValueError(f"Found {len(paths)} subtitle files. The task specifies up to 100 movies.")
    if not paths:
        raise FileNotFoundError(f"No .srt files found in {settings.subtitle_dir}")

    store = MovieVectorStore()
    if reset:
        store.reset()

    all_chunks = []
    for path in paths:
        chunks = parse_and_chunk(path, settings.chunk_size_cues, settings.chunk_overlap_cues)
        print(f"{path.name}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    added = store.add_chunks(all_chunks)
    print(f"Indexed {added} chunks across {len(paths)} movies.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    ingest(args.reset)
