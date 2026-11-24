"""Run OpenMontage's subtitle_gen on the transcript (word-level
timestamps from the transcriber) to produce SRT + caption JSON.

Reads work/transcript.json, writes work/captions.srt + work/captions.json.
Adapted from the local v3 build (run_subtitle_gen_v3.py); paths are
relative to the repo root so it runs unchanged in GitHub Actions.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.subtitle.subtitle_gen import SubtitleGen

WORK = REPO_ROOT / "work"
WORK.mkdir(parents=True, exist_ok=True)

data = json.loads((WORK / "transcript.json").read_text())
segments = data["segments"]

for fmt, out in [("srt", WORK / "captions.srt"), ("json", WORK / "captions.json")]:
    res = SubtitleGen().execute({
        "segments": segments,
        "format": fmt,
        "output_path": str(out),
        "max_words_per_cue": 8,
        "max_chars_per_line": 42,
        "highlight_style": "word_by_word",
    })
    print(fmt, "success:", res.success, res.error if not res.success else "")
    if res.success:
        print("  ->", out)

cues = json.loads((WORK / "captions.json").read_text())["cues"]
print(f"cues: {len(cues)}")
for c in cues:
    print(f"  {c['start']:6.2f}-{c['end']:6.2f}  {c['text']}")
