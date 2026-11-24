"""Build a Remotion WordCaption[] TypeScript module for the reel.

Same timing model as scripts/build_ass.py (the ASS caption builder):
- Timing source: OpenMontage transcriber word-level timestamps
  (work/transcript.json). Display text source: the SCRIPT words from
  phrases.txt — Whisper mis-heard "know" as "no" in "Can it know remorse?"
  (probability 0.412), so the displayed words must come from the script,
  not the transcript. Alignment is by word order (92 words both sides).
- Chunk-final phrase stays visible until the chunk's audio end (Kokoro
  leaves a trailing pause after each chunk's final sentence).
- First word of a chunk is anchored to the chunk's real start (Whisper
  sometimes mis-times it up to ~1 s early).
- Monotonicity pass: events never overlap and never invert.

Output: remotion/src/captions.ts — a WORDS array of
{ word, startMs, endMs, pageBreakAfter }, where each word's end is the
next word's start inside its phrase (so the gold highlight advances
exactly when the next word is spoken), and pageBreakAfter marks the last
word of each of the 15 script phrases so OpenMontage's CaptionOverlay
renders one phrase per caption page, exactly like the v3 ASS captions.

Usage:
  python3 scripts/build_captions_ts.py [--transcript PATH] [--out PATH]
Defaults read work/transcript.json and write remotion/src/captions.ts,
both relative to the repo root, so it runs unchanged in GitHub Actions.
"""
import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORK = REPO_ROOT / "work"
PHRASES = REPO_ROOT / "phrases.txt"
TIMINGS = REPO_ROOT / "timings-v3.json"


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default=str(WORK / "transcript.json"))
    ap.add_argument("--out", default=str(REPO_ROOT / "remotion" / "src" / "captions.ts"))
    args = ap.parse_args()

    transcript_path = Path(args.transcript)
    out_path = Path(args.out)

    # --- script phrases ---
    phrases = []
    for line in PHRASES.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        _num, text = line.split("|", 1)
        phrases.append(text.strip().split())

    # --- whisper words, flattened in order ---
    data = json.loads(transcript_path.read_text())
    w_words = [w for seg in data["segments"] for w in seg.get("words", []) if w["word"].strip()]
    assert len(w_words) == sum(len(p) for p in phrases), (
        f"word count mismatch: whisper={len(w_words)} script={sum(len(p) for p in phrases)}")

    # align by order; report any normalized mismatch (display uses script words)
    idx = 0
    phrase_spans = []  # list of (phrase_words, [(start,end), ...])
    for p in phrases:
        span = []
        for sw in p:
            ww = w_words[idx]
            if norm(sw) != norm(ww["word"]):
                print(f"NOTE word mismatch at #{idx}: script={sw!r} whisper={ww['word'].strip()!r} "
                      f"(t={ww['start']:.2f}, prob={ww.get('probability', 0):.2f}) — displaying script word")
            span.append([ww["start"], ww["end"]])
            idx += 1
        phrase_spans.append((p, span))

    # --- chunk anchoring (same as build_ass.py) ---
    chunk_ends = {}    # phrase idx -> chunk end
    chunk_starts = {}  # phrase idx (first phrase of a chunk) -> chunk start
    _chunks = json.loads(TIMINGS.read_text())["chunks"]
    _acc = 0
    _ci = 0
    _start_pi = 0
    for _pi, _p in enumerate(phrases):
        _acc += len(_p)
        _real = len([w for w in _chunks[_ci]["text"].split() if w != "\u2014"])
        if _acc >= _real:
            chunk_ends[_pi] = _chunks[_ci]["end"]
            chunk_starts[_start_pi] = _chunks[_ci]["start"]
            _ci += 1
            _acc = 0
            _start_pi = _pi + 1

    # --- per-word (start, end) with the same fixes as build_ass.py ---
    words = []  # (script_word, start_s, end_s, page_break_after)
    for pi, (pwords, span) in enumerate(phrase_spans):
        last_end = span[-1][1]
        if pi in chunk_ends:
            phrase_end = chunk_ends[pi]
        elif pi + 1 < len(phrase_spans):
            next_start = phrase_spans[pi + 1][1][0][0]
            phrase_end = min(last_end + 0.12, next_start - 0.03)
        else:
            phrase_end = last_end + 0.15
        for i, (start, end) in enumerate(span):
            if i == 0 and pi in chunk_starts and start < chunk_starts[pi] - 0.15:
                print(f"ANCHOR phrase {pi+1} first word: {start:.2f} -> {chunk_starts[pi]:.2f}")
                start = chunk_starts[pi]
                end = max(end, start + 0.25)
                if len(span) > 1:
                    ns, ne = span[1]
                    if ns < end:
                        span[1] = [end, max(ne, end + 0.05)]
            ev_end = span[i + 1][0] if i + 1 < len(span) else phrase_end
            words.append([pwords[i], start, ev_end, i == len(span) - 1])

    # Monotonicity pass: never overlap, never invert, min 0.05 s duration.
    for i in range(1, len(words)):
        if words[i][1] < words[i - 1][2]:
            words[i][1] = words[i - 1][2]
        if words[i][2] <= words[i][1]:
            words[i][2] = words[i][1] + 0.05

    # --- emit TypeScript ---
    lines = [
        "// Generated by scripts/build_captions_ts.py — do not edit by hand.",
        "// Word-level caption timings for the UGC reel (v3 voiceover, Kokoro am_adam).",
        "// Timing: OpenMontage transcriber (faster-whisper, word timestamps).",
        "// Display words: the script (phrases.txt) — Whisper mis-hears one word.",
        "// One caption page per script phrase (pageBreakAfter on each phrase's",
        "// last word), exactly like the v3 ASS captions.",
        "",
        'import type { WordCaption } from "./components/CaptionOverlay";',
        "",
        "export const WORDS: WordCaption[] = [",
    ]
    for w, s, e, brk in words:
        esc = w.replace("\\", "\\\\").replace('"', '\\"')
        brk_s = ", pageBreakAfter: true" if brk else ""
        lines.append(f'  {{ word: "{esc}", startMs: {round(s * 1000)}, endMs: {round(e * 1000)}{brk_s} }},')
    lines.append("];")
    lines.append("")
    lines.append(f"export const WORD_COUNT = {len(words)};")
    lines.append(f"export const PHRASE_COUNT = {len(phrase_spans)};")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_path} with {len(words)} words across {len(phrase_spans)} phrases")


if __name__ == "__main__":
    main()
