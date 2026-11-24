# Remotion composition — UGC book trailer (v3, Remotion render)

Renders the same UGC reel as the FFmpeg workflow (`render-reel.yml`) — same
script, same v3 male voiceover (Kokoro `am_adam`), same stock clips, same
book images, same caption words and timings — but composed and rendered with
[Remotion](https://www.remotion.dev/) (React) instead of FFmpeg assembly, so
the motion graphics are the full Remotion treatment.

## What is Remotion here (and what is not)

- **Composition:** `src/UgcReel.tsx` — `UgcReel`, 1080×1920, 30 fps,
  955 frames (31.83 s).
- **Crossfades:** `<TransitionSeries>` + `fade()` from
  `@remotion/transitions` (0.4 s fades, same cut points as the v3 FFmpeg
  build).
- **Ken Burns:** `interpolate()` with eased scaling — 1.0→1.08 on the two
  stills (same as v3), 1.0→1.03 gentle push-in on the video clips.
- **Captions:** OpenMontage's `CaptionOverlay`
  (`src/components/CaptionOverlay.tsx`, vendored from OpenMontage,
  AGPL-3.0) — spring entrances, per-word gold highlight, word pop. One
  caption page per script phrase. Font 80, bold Noto Sans, thick black
  outline, gold `#E08F1F` active word — the v3 look.
- **Vignette + fade-out:** Remotion overlays (radial-gradient vignette,
  fade to black over the last 0.5 s).
- **Audio:** the v3 voiceover WAV, via Remotion `<Audio>`.

The word timings come from OpenMontage's transcriber (faster-whisper) via
`scripts/build_captions_ts.py` — same alignment and chunk fixes as
`scripts/build_ass.py`, emitted as a TypeScript `WordCaption[]` module
(`src/captions.ts`).

## Source preparation (not composition)

The workflow pre-scales the 4K Pexels clips to the 1080×1920 composition
resolution with FFmpeg before the Remotion render, so headless Chrome
decodes 1080p instead of 4K. This is source preparation only — the
composition, transitions, captions and all motion graphics are Remotion.

## Local test

```bash
# 1. Put media in place (never committed — see .gitignore):
#    - voiceover + cover images -> remotion/public/assets/
#      (decode from the repo's assets/*.b64, or copy from the local reel dir)
#    - stock clips (scaled to 1080x1920) -> remotion/public/stock/
# 2. Generate captions from the local v3 transcript:
#      python3 scripts/build_captions_ts.py \
#        --transcript <path>/reel/transcript-v3.json \
#        --out remotion/src/captions.ts
# 3. Install + validate:
#      cd remotion && npm install
#      npx remotion compositions src/index.tsx
# 4. Short test render (first 30 frames):
#      npx remotion render src/index.tsx UgcReel /tmp/test.mp4 --frames=0-29
# 5. Full render:
#      npm run render
```

## Render on GitHub Actions

Workflow `.github/workflows/render-reel-remotion.yml` (manual trigger or push
to `main` touching `remotion/**`, the caption/transcribe scripts, or the
workflow itself). It runs the full pipeline — decode assets, download
Pexels clips, transcribe, build captions, prepare media, `npm ci`,
`npx remotion browser ensure`, render — and uploads the artifact
`book-reel-ugc-remotion` (7-day retention). The video is never committed.

## Files

```
remotion/
├── package.json            # @remotion/cli + remotion + @remotion/transitions 4.0.484
├── package-lock.json       # pinned for reproducible `npm ci` on Actions
├── tsconfig.json
├── src/
│   ├── index.tsx           # registerRoot
│   ├── Root.tsx            # Composition "UgcReel"
│   ├── UgcReel.tsx         # the composition (segments, transitions, overlays)
│   ├── captions.ts         # generated WordCaption[] (92 words, 15 phrases)
│   ├── components/
│   │   └── CaptionOverlay.tsx   # vendored from OpenMontage (AGPL-3.0)
│   └── lib/
│       └── resolveAsset.ts     # vendored from OpenMontage (AGPL-3.0)
└── public/                 # populated at render time only (.gitkeep committed)
```

## Licence

The vendored OpenMontage components are AGPL-3.0 (see the repo `LICENSE`).
The book images and voiceover are original work for Pixel & Paper Press.
