from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .srt_parser import Cue, parse_srt


@dataclass
class DialogueChunk:
    chunk_id: str
    movie_title: str
    start: str
    end: str
    cue_start: int
    cue_end: int
    dialogue: str

    @property
    def citation(self) -> str:
        return f"{self.movie_title} — {self.start} → {self.end}"


def movie_title_from_path(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip()


def make_chunks(cues: list[Cue], movie_title: str, size: int = 6, overlap: int = 2) -> list[DialogueChunk]:
    if not cues:
        return []
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Chunk size must be > overlap >= 0")

    chunks: list[DialogueChunk] = []
    step = size - overlap
    for start_idx in range(0, len(cues), step):
        group = cues[start_idx : start_idx + size]
        if not group:
            break
        dialogue = " ".join(c.text for c in group)
        chunks.append(
            DialogueChunk(
                chunk_id=f"{movie_title.lower().replace(' ', '_')}_{group[0].index}_{group[-1].index}",
                movie_title=movie_title,
                start=group[0].start,
                end=group[-1].end,
                cue_start=group[0].index,
                cue_end=group[-1].index,
                dialogue=dialogue,
            )
        )
        if start_idx + size >= len(cues):
            break
    return chunks


def parse_and_chunk(path: Path, size: int, overlap: int) -> list[DialogueChunk]:
    cues = parse_srt(path)
    return make_chunks(cues, movie_title_from_path(path), size, overlap)
