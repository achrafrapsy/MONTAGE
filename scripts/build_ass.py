"""Build an animated TikTok-style ASS caption file for the reel.

Font 80 (bigger, per user feedback — v2 captions at 64 were too small).
Pop on phrase start is 64 -> 80 accordingly.

Timing source: OpenMontage transcriber word-level timestamps
(work/transcript.json). Display text source: the SCRIPT words from
phrases.txt — Whisper mis-heard "know" as "no" in "Can it know remorse?"
(probability 0.412), so the displayed words must come from the script,
not the transcript. Alignment is by word order (92 words both sides);
any mismatch is reported, not silently swallowed.

Animation: word-by-word highlight — each word event shows the whole phrase
with the currently spoken word in gold and the rest white, with a short
fade in/out on every word change (kinetic text). A subtle pop on the first
word of each phrase (font grows 64 -> 80 in 120 ms).

Adapted from the local v3 build (build_ass_v3.py); paths are relative to
the repo root so it runs unchanged in GitHub Actions.
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORK = REPO_ROOT / "work"
WORK.mkdir(parents=True, exist_ok=True)

TRANSCRIPT = WORK / "transcript.json"
PHRASES = REPO_ROOT / "phrases.txt"
TIMINGS = REPO_ROOT / "timings-v3.json"
OUT = WORK / "captions.ass"
FONT = 80
POP_FROM = 64

# ASS colours are &HAABBGGRR&. Gold #E08F1F -> B=1F G=8F R=E0 -> &H001F8FE0&
GOLD = r"{\c&H001F8FE0&}"
WHITE = r"{\c&HFFFFFF&}"

def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())

# --- script phrases ---
phrases = []
for line in PHRASES.read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    _num, text = line.split("|", 1)
    phrases.append(text.strip().split())

# --- whisper words, flattened in order ---
data = json.loads(TRANSCRIPT.read_text())
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
        span.append((ww["start"], ww["end"]))
        idx += 1
    phrase_spans.append((p, span))

lines = []
lines.append("[Script Info]")
lines.append("Title: The Digital Mind and the Human Heart - UGC Reel captions")
lines.append("ScriptType: v4.00+")
lines.append("PlayResX: 1080")
lines.append("PlayResY: 1920")
lines.append("WrapStyle: 0")
lines.append("ScaledBorderAndShadow: yes")
lines.append("")
lines.append("[V4+ Styles]")
lines.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")
# Bold white Noto Sans, thick black outline, slight shadow, bottom-centre, lower third
lines.append(f"Style: Default,Noto Sans,{FONT},&HFFFFFF,&HFFFFFF,&H000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,50,50,280,1")
lines.append("")
lines.append("[Events]")
lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")

def fmt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

n_events = 0
# Map each phrase to the generation chunk it belongs to: walk phrases and
# chunks in order, matching by real word count (the em-dash token in chunk 1
# is not a spoken word, so it is excluded from the count). The last phrase
# of a chunk stays visible until the chunk's audio end — Kokoro leaves a
# trailing pause after each chunk's final sentence, and the caption must
# not vanish ~1 s before the chunk actually ends. The first phrase of a
# chunk is anchored to the chunk's real start: Whisper sometimes mis-times
# a chunk's first word up to ~1 s early (it swallows the previous chunk's
# trailing pause), which would show the next phrase while the previous one
# is still up — two captions at once.
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
print("chunk-final phrases (phrase idx -> chunk end):", chunk_ends)
print("chunk-first phrases (phrase idx -> chunk start):", chunk_starts)

# Build raw events first, then correct them before rendering.
events = []  # (start, end, text)
for pi, (pwords, span) in enumerate(phrase_spans):
    # phrase end: last word end + 0.12 s into the inter-phrase gap, clamped
    # so it never overlaps the next phrase's first word; but a chunk-final
    # phrase stays up until the chunk's audio end (trailing pause included)
    last_end = span[-1][1]
    if pi in chunk_ends:
        phrase_end = chunk_ends[pi]
    elif pi + 1 < len(phrase_spans):
        next_start = phrase_spans[pi + 1][1][0][0]
        phrase_end = min(last_end + 0.12, next_start - 0.03)
    else:
        phrase_end = last_end + 0.15
    for i, (start, end) in enumerate(span):
        # anchor the first word of a chunk to the chunk's real start
        if i == 0 and pi in chunk_starts and start < chunk_starts[pi] - 0.15:
            print(f"ANCHOR phrase {pi+1} first word: {start:.2f} -> {chunk_starts[pi]:.2f} "
                  f"(Whisper was {chunk_starts[pi]-start:.2f}s early)")
            start = chunk_starts[pi]
            end = max(end, start + 0.25)
            # push the next word's start so the anchored word keeps its slot
            # (its Whisper start is stale — too early — and would otherwise
            # cut the anchored word to a 0.05 s flash)
            if len(span) > 1:
                ns, ne = span[1]
                if ns < end:
                    span[1] = (end, max(ne, end + 0.05))
        ev_end = span[i + 1][0] if i + 1 < len(span) else phrase_end
        parts = []
        for j, pw in enumerate(pwords):
            parts.append((GOLD if j == i else WHITE) + pw)
        text = " ".join(parts)
        if i == 0:
            text = r"{\fs%d\t(0,120,\fs%d)}" % (POP_FROM, FONT) + text
        text = r"{\fad(90,90)}" + text
        events.append([start, ev_end, text])

# Monotonicity pass: guarantee events never overlap and never invert.
# Each event starts no earlier than the previous event's end, and keeps a
# minimum 0.05 s duration. This is the final guard against double captions.
for i in range(1, len(events)):
    if events[i][0] < events[i - 1][1]:
        events[i][0] = events[i - 1][1]
    if events[i][1] <= events[i][0]:
        events[i][1] = events[i][0] + 0.05

for start, ev_end, text in events:
    lines.append(f"Dialogue: 0,{fmt(start)},{fmt(ev_end)},Default,,0,0,0,,{text}")
    n_events += 1

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {OUT} with {n_events} word events across {len(phrase_spans)} phrases, font={FONT}")
