from pathlib import Path

from core.chunker import make_chunks, movie_title_from_path
from core.srt_parser import parse_srt


def test_chunking_preserves_metadata() -> None:
    path = Path("data/subtitles/Demo_Moon.srt")
    cues = parse_srt(path)

    chunks = make_chunks(
        cues,
        movie_title_from_path(path),
        size=3,
        overlap=1,
    )

    assert chunks
    assert chunks[0].movie_title == "Demo Moon"
    assert chunks[0].start == cues[0].start
    assert chunks[0].end == cues[2].end
    assert chunks[0].cue_start == cues[0].index
    assert chunks[0].cue_end == cues[2].index


def test_chunk_overlap_preserves_context() -> None:
    path = Path("data/subtitles/Demo_Moon.srt")
    cues = parse_srt(path)

    chunks = make_chunks(
        cues,
        movie_title_from_path(path),
        size=3,
        overlap=1,
    )

    assert len(chunks) >= 2

    # With size=3 and overlap=1, the last cue of
    # the first chunk should appear in the second chunk.
    assert cues[2].text in chunks[0].dialogue
    assert cues[2].text in chunks[1].dialogue


def test_movie_title_from_path() -> None:
    assert movie_title_from_path(
        Path("The_Dark_Knight.srt")
    ) == "The Dark Knight"