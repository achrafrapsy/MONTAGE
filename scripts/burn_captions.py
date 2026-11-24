"""Burn the animated ASS captions into the base video using OpenMontage's
video_compose tool (operation='burn_subtitles'). The ASS carries the
word-by-word gold highlight + fade + pop animation; the force_style passed
here matches the ASS style (font 80) so the look is unchanged.

Reads work/base.mp4 + work/captions.ass, writes work/book-reel-ugc.mp4.
Adapted from the local v3 build (burn_captions_v3.py); paths are relative
to the repo root so it runs unchanged in GitHub Actions.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.video.video_compose import VideoCompose

WORK = REPO_ROOT / "work"

res = VideoCompose().execute({
    "operation": "burn_subtitles",
    "input_path": str(WORK / "base.mp4"),
    "subtitle_path": str(WORK / "captions.ass"),
    "output_path": str(WORK / "book-reel-ugc.mp4"),
    "subtitle_style": {
        "font": "Noto Sans",
        "font_size": 80,
        "bold": True,
        "primary_color": "&HFFFFFF",
        "outline_color": "&H000000",
        "outline_width": 4,
        "shadow": 1,
        "margin_v": 280,
        "alignment": 2,
    },
    "crf": 20,
})
print("success:", res.success)
if not res.success:
    print("error:", res.error)
    raise SystemExit(1)
print("output:", res.data.get("output"))
print("artifacts:", res.artifacts)
