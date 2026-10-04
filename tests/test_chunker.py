from pathlib import Path

from core.chunker import make_chunks, movie_title_from_path
from core.srt_parser import parse_srt


def test_chunking_preserves_metadata() -> None:
    path = Path("data/subtitles/Demo_Moon.srt")
    cues = parse_srt(path)
    chunks = make_chunks(cues, movie_title_from_path(path), size=3, overlap=1)
    assert chunks
    assert chunks[0].movie_title == "Demo Moon"
    assert chunks[0].start == cues[0].start
    assert chunks[0].end == cues[2].end
