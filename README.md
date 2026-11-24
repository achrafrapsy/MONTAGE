# MONTAGE — UGC book-trailer render pipeline

Renders the vertical UGC book trailer for **"The Digital Mind and the Human Heart"**
(Pixel & Paper Press) with [OpenMontage](https://github.com/openmontage/openmontage)
tools, on GitHub Actions. The video is produced as a workflow **artifact** — it is
never committed to this repo.

There are **two render workflows** producing the same reel:

- **`render-reel.yml` — FFmpeg assembly.** OpenMontage Python tools
  (transcriber, subtitle_gen, video_compose) + FFmpeg: 6 segments, crossfades,
  Ken Burns zooms, burned ASS captions. Artifact `book-reel-ugc`.
- **`render-reel-remotion.yml` — full OpenMontage + Remotion.** The same
  voiceover, script, clips and images, but composed and rendered with
  Remotion (React): `TransitionSeries` crossfades, eased Ken Burns zooms,
  and OpenMontage's `CaptionOverlay` (spring entrances, per-word gold
  highlight, word pop). Artifact `book-reel-ugc-remotion`. See
  `remotion/README.md`.

## What it produces

- **Video:** `book-reel-ugc.mp4` (FFmpeg) or `book-reel-ugc-remotion.mp4`
  (Remotion) — 1080×1920 vertical, 30 fps, H.264 + AAC, ~32 s. UGC
  first-person voiceover, bold kinetic captions (font 80, the spoken word
  highlighted gold), 6 segments with crossfades, Ken Burns zooms on the
  two stills, vignette, fade-out.
- **Voiceover:** Kokoro TTS, male voice `am_adam`, pre-generated and committed
  as `assets/voiceover-v3.wav.b64` (no TTS runs in the workflow).

## Pipeline (one GitHub Actions run)

### FFmpeg workflow (`render-reel.yml`)

1. **Decode assets** — binary assets are stored base64-encoded (`.b64`) because
   the upload tooling is text-only; the workflow decodes them to
   `assets/*.wav` / `assets/*.png`.
2. **Download stock** — the 6 Pexels clips (free licence) are downloaded at run
   time from Pexels' download endpoint into `stock/` (never committed, ~146 MB).
3. **Transcribe** — OpenMontage `transcriber` (faster-whisper `small`, CPU) gives
   word-level timestamps for the voiceover → `work/transcript.json`.
4. **Subtitles** — OpenMontage `subtitle_gen` → `work/captions.srt` + `work/captions.json`.
5. **Animated captions** — `scripts/build_ass.py` builds a kinetic ASS file
   (font 80, gold current word, 90 ms fades, phrase-start pop) → `work/captions.ass`.
6. **Assemble** — `scripts/build_video.sh` (FFmpeg): 6 segments, 0.4 s crossfades,
   Ken Burns zooms (fast animated-crop), vignette, fade-out, voiceover mux
   → `work/base.mp4`.
7. **Burn captions** — OpenMontage `video_compose` (`burn_subtitles`) burns the
   ASS into the video → `work/book-reel-ugc.mp4`.
8. **Upload artifact** — `book-reel-ugc` (retention 7 days).

### Remotion workflow (`render-reel-remotion.yml`)

Same source media and caption data, rendered with Remotion instead of FFmpeg
assembly:

1.–4. Same as above (decode assets, download stock, transcribe, subtitles).
5. **Build Remotion captions** — `scripts/build_captions_ts.py` emits the same
   word timings as a TypeScript `WordCaption[]` module → `remotion/src/captions.ts`.
6. **Prepare Remotion media** — decoded assets + stock clips copied into
   `remotion/public/`; the 4K stock clips are pre-scaled to 1080×1920 first
   (source preparation only — the composition is Remotion).
7. **Install + browser** — `npm ci`, `npx remotion browser ensure`.
8. **Render** — `npx remotion render src/index.tsx UgcReel` →
   `work/book-reel-ugc-remotion.mp4`.
9. **Upload artifact** — `book-reel-ugc-remotion` (retention 7 days).

## Run it

- **Automatic:** push to `main` triggers the workflow whose paths changed
  (FFmpeg: `assets/`, `scripts/`, `tools/`, …; Remotion: `remotion/**`,
  the caption/transcribe scripts, …).
- **Manual:** Actions → *Render UGC Reel* (FFmpeg) or *Render UGC Reel
  (Remotion)* → *Run workflow*.
- **Download the video:** Actions → the run → *Artifacts* → `book-reel-ugc`
  or `book-reel-ugc-remotion`. After downloading, delete the video file from
  the repo if it was ever committed (it should not be — the repo holds code +
  pipeline only).

## Layout

```
├── .github/workflows/
│   ├── render-reel.yml            # FFmpeg workflow
│   └── render-reel-remotion.yml   # Remotion workflow
├── assets/                        # voiceover + book images (base64 .b64)
├── phrases.txt                    # the 15 script phrases (caption text source)
├── timings-v3.json                # voiceover chunk timings (caption anchoring)
├── requirements.txt               # faster-whisper (+ av pin, see below)
├── scripts/                       # pipeline scripts (transcribe, subtitles,
│                                  # ASS captions, FFmpeg assembly, burn,
│                                  # Remotion captions.ts)
├── remotion/                      # Remotion project (see remotion/README.md)
│   ├── package.json               # @remotion/cli + remotion 4.0.484
│   └── src/
│       ├── UgcReel.tsx            # the composition
│       ├── captions.ts            # generated WordCaption[] (92 words)
│       └── components/CaptionOverlay.tsx  # vendored OpenMontage
└── tools/                         # vendored OpenMontage tools
    ├── base_tool.py               # minimal BaseTool shim
    ├── analysis/transcriber.py    # real OpenMontage transcriber
    ├── subtitle/subtitle_gen.py   # real OpenMontage subtitle_gen
    └── video/video_compose.py     # minimal copy: burn_subtitles only
```

## Notes

- **faster-whisper + `av`:** `av` is pinned to `12.3.0` — av 19 broke
  faster-whisper's `av.open` call. faster-whisper runs on CTranslate2,
  not torch; no GPU and no Kokoro install are needed in the workflow.
- **Fonts:** the workflow installs `fonts-noto-core` so the captions render
  in Noto Sans (bold), matching the local build.
- **Stock footage:** all 6 clips are Pexels, free licence, no attribution
  required. Download endpoint `https://www.pexels.com/download/video/<id>/`
  302-redirects to the original-quality file on `videos.pexels.com`.
- **Cost:** public repo + standard `ubuntu-latest` runner = $0 (GitHub Actions
  is free for public repositories on standard runners). No secrets are used
  or stored in this repo.
- **Licence:** the vendored OpenMontage tools are AGPL-3.0 (see `LICENSE`).
  The book images and voiceover are original work for Pixel & Paper Press.
