from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    subtitle_dir: Path = ROOT / "data" / "subtitles"
    chroma_dir: Path = ROOT / "storage" / "chroma"
    collection_name: str = "movie_dialogue"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    embedding_model: str = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
    top_k: int = int(os.getenv("TOP_K", "5"))
    chunk_size_cues: int = int(os.getenv("CHUNK_SIZE_CUES", "6"))
    chunk_overlap_cues: int = int(os.getenv("CHUNK_OVERLAP_CUES", "2"))
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "")


settings = Settings()
