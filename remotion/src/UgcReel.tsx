import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { CaptionOverlay } from "./components/CaptionOverlay";
import { WORDS } from "./captions";

// ---------------------------------------------------------------------------
// UGC reel — "The Digital Mind and the Human Heart" (v3)
// 1080x1920 vertical, 30 fps, 955 frames (31.83 s — the v3 voiceover is
// 31.825 s). Same script, same v3 male voiceover (Kokoro am_adam), same
// 6 segments and the same caption words/timings as the FFmpeg v3, but the
// composition and all motion graphics are Remotion:
//   - crossfades via TransitionSeries + fade() (Remotion-native)
//   - Ken Burns zooms via interpolate() with ease-out easing
//   - captions via OpenMontage's CaptionOverlay (spring entrances,
//     per-word gold highlight, word pop) — vendored, see components/
//   - vignette + final fade-out as Remotion overlays
// ---------------------------------------------------------------------------

export const REEL_FPS = 30;
export const REEL_WIDTH = 1080;
export const REEL_HEIGHT = 1920;
export const REEL_FRAMES = 955;

// Segment lengths in frames (30 fps). Sum 1015 minus 5 x 12-frame (0.4 s)
// crossfades = 955 frames. Same cut points as the v3 FFmpeg build:
//   S1 robot hook 3.68 s | S2 code 4.00 s | S3 cyborg 3.61 s |
//   S4 cover scene 9.56 s | S5 reading 7.29 s | S6 front cover 5.70 s
const SEG_FRAMES = [110, 120, 108, 287, 219, 171];
const XFADE_FRAMES = 12; // 0.4 s

const GOLD = "#E08F1F"; // Pixel & Paper Press brand gold (v3 caption highlight)

// --- clip primitives -------------------------------------------------------

const VideoClip: React.FC<{
  src: string;
  startFromSec?: number;
  kenBurnsTo?: number;
  durationInFrames: number;
}> = ({ src, startFromSec = 0, kenBurnsTo = 1.03, durationInFrames }) => {
  const frame = useCurrentFrame();
  // Gentle push-in over the clip's life (eased, so it settles smoothly).
  const scale = interpolate(frame, [0, durationInFrames], [1, kenBurnsTo], {
    easing: Easing.out(Easing.quad),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <OffthreadVideo
        src={src}
        startFrom={Math.round(startFromSec * REEL_FPS)}
        muted
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
        }}
      />
    </AbsoluteFill>
  );
};

const StillClip: React.FC<{
  src: string;
  kenBurnsTo?: number;
  durationInFrames: number;
}> = ({ src, kenBurnsTo = 1.08, durationInFrames }) => {
  const frame = useCurrentFrame();
  // Ken Burns zoom-in, same 1.08x as the v3 FFmpeg build, eased.
  const scale = interpolate(frame, [0, durationInFrames], [1, kenBurnsTo], {
    easing: Easing.out(Easing.quad),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
        }}
      />
    </AbsoluteFill>
  );
};

// --- overlays ---------------------------------------------------------------

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.35) 100%)",
      pointerEvents: "none",
    }}
  />
);

const FadeOut: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  // Fade to black over the last 0.5 s (15 frames), like the v3 fade-out.
  const opacity = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return <AbsoluteFill style={{ backgroundColor: "black", opacity }} />;
};

// --- composition ------------------------------------------------------------

export const UgcReel: React.FC = () => {
  const xfade = (key: string) => (
    <TransitionSeries.Transition
      key={key}
      presentation={fade()}
      timing={linearTiming({ durationInFrames: XFADE_FRAMES })}
    />
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Audio src={staticFile("assets/voiceover-v3.wav")} />

      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={SEG_FRAMES[0]}>
          <VideoClip
            src={staticFile("stock/robot1.mp4")}
            durationInFrames={SEG_FRAMES[0]}
          />
        </TransitionSeries.Sequence>
        {xfade("x1")}
        <TransitionSeries.Sequence durationInFrames={SEG_FRAMES[1]}>
          <VideoClip
            src={staticFile("stock/code1.mp4")}
            durationInFrames={SEG_FRAMES[1]}
          />
        </TransitionSeries.Sequence>
        {xfade("x2")}
        <TransitionSeries.Sequence durationInFrames={SEG_FRAMES[2]}>
          <VideoClip
            src={staticFile("stock/cyborg.mp4")}
            durationInFrames={SEG_FRAMES[2]}
          />
        </TransitionSeries.Sequence>
        {xfade("x3")}
        <TransitionSeries.Sequence durationInFrames={SEG_FRAMES[3]}>
          <StillClip
            src={staticFile("assets/cover-scene-human-robot-v2.jpg")}
            durationInFrames={SEG_FRAMES[3]}
          />
        </TransitionSeries.Sequence>
        {xfade("x4")}
        <TransitionSeries.Sequence durationInFrames={SEG_FRAMES[4]}>
          <VideoClip
            src={staticFile("stock/read2.mp4")}
            startFromSec={2}
            durationInFrames={SEG_FRAMES[4]}
          />
        </TransitionSeries.Sequence>
        {xfade("x5")}
        <TransitionSeries.Sequence durationInFrames={SEG_FRAMES[5]}>
          <StillClip
            src={staticFile("assets/cover_front.jpg")}
            durationInFrames={SEG_FRAMES[5]}
          />
        </TransitionSeries.Sequence>
      </TransitionSeries>

      <Vignette />

      {/* OpenMontage word-level captions: spring entrance, gold active word,
          word pop. One page per script phrase (see captions.ts). Font 80,
          bold Noto Sans, thick black outline — same look as the v3 ASS. */}
      <CaptionOverlay
        words={WORDS}
        wordsPerPage={12}
        fontSize={80}
        color="#FFFFFF"
        highlightColor={GOLD}
        backgroundColor="transparent"
        fontFamily="Noto Sans, Arial, sans-serif"
        bottomOffset={280}
        wordPop={{ scale: 1.25, damping: 12, stiffness: 220 }}
        wordStyle={{
          textShadow:
            "-3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 3px 3px 0 #000, 0 0 14px rgba(0,0,0,0.9), 0 4px 6px rgba(0,0,0,0.6)",
        }}
        boxStyle={{ backgroundColor: "transparent", padding: 0 }}
      />

      <FadeOut />
    </AbsoluteFill>
  );
};
