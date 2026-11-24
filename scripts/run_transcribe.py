"""Run OpenMontage's transcriber (faster-whisper) on the voiceover
to get word-level timestamps for captions.

Reads assets/voiceover-v3.wav, writes work/transcript.json.
Adapted from the local v3 build (run_transcribe_v3.py); paths are
relative to the repo root so it runs unchanged in GitHub Actions.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.analysis.transcriber import Transcriber

ASSETS = REPO_ROOT / "assets"
WORK = REPO_ROOT / "work"
WORK.mkdir(parents=True, exist_ok=True)

audio = str(ASSETS / "voiceover-v3.wav")
out = WORK / "transcript.json"

res = Transcriber().execute({
    "input_path": audio,
    "model_size": "small",
    "language": "en",
    "word_timestamps": True,
    # The transcriber also writes {stem}_transcript.json into output_dir;
    # point it at work/ so it never pollutes assets/.
    "output_dir": str(WORK),
})
print("success:", res.success)
if not res.success:
    print("error:", res.error)
    raise SystemExit(1)
data = res.data
print("language:", data.get("language"), "| model:", data.get("model_size"))
segs = data.get("segments", [])
full = " ".join(s.get("text", "").strip() for s in segs)
print("TRANSCRIPT:", full)
print("segments:", len(segs))
nwords = sum(len(s.get("words", [])) for s in segs)
print("words with timestamps:", nwords)
out.write_text(json.dumps(data, indent=2))
print("wrote", out)
