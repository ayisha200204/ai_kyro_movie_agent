from pathlib import Path

from core.srt_parser import clean_text, parse_srt


def test_parse_demo_srt() -> None:
    path = Path("data/subtitles/Demo_Moon.srt")
    cues = parse_srt(path)

    assert len(cues) == 5
    assert cues[0].start == "00:00:02,000"
    assert cues[0].end == "00:00:05,000"
    assert "moon station" in cues[0].text.lower()


def test_clean_text_removes_html_and_normalizes_whitespace() -> None:
    text = "<i>Hello</i>   world\\Nfrom the station"

    cleaned = clean_text(text)

    assert cleaned == "Hello world from the station"


def test_parse_preserves_dialogue_order() -> None:
    path = Path("data/subtitles/Demo_Moon.srt")
    cues = parse_srt(path)

    assert cues[0].index < cues[1].index
    assert cues[0].start < cues[1].start