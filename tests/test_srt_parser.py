from pathlib import Path

from core.srt_parser import parse_srt


def test_parse_demo_srt() -> None:
    path = Path("data/subtitles/Demo_Moon.srt")
    cues = parse_srt(path)
    assert len(cues) == 5
    assert cues[0].start == "00:00:02,000"
    assert "moon station" in cues[0].text.lower()
