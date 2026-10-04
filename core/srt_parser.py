from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path


TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2},\d{3})"
)
TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Cue:
    index: int
    start: str
    end: str
    text: str


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = TAG_RE.sub("", text)
    text = text.replace("\\N", " ").replace("\\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_srt(path: str | Path) -> list[Cue]:
    raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", raw.strip())
    cues: list[Cue] = []

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue
        match = next((TIMESTAMP_RE.search(line) for line in lines[:2] if TIMESTAMP_RE.search(line)), None)
        if not match:
            continue
        index = int(lines[0]) if lines[0].isdigit() else len(cues) + 1
        text_start = 2 if lines[0].isdigit() else 1
        text = clean_text(" ".join(lines[text_start:]))
        if text:
            cues.append(Cue(index, match.group("start"), match.group("end"), text))
    return cues


def cue_to_seconds(timestamp: str) -> float:
    h, m, rest = timestamp.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def format_timestamp(timestamp: str) -> str:
    return timestamp.replace(",", ".")
