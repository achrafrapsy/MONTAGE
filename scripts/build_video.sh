#!/bin/bash
# Assemble the UGC reel: 6 segments chained with 0.4 s crossfades,
# Ken Burns on the two stills, vignette, fade-out, Kokoro am_adam voiceover.
# Output: work/base.mp4 (clean, no captions yet — captions are burned
# separately with OpenMontage video_compose burn_subtitles).
#
# Voiceover = 31.82 s. Segment durations (sum 33.82 s; 5 x 0.4 s
# crossfades -> 31.82 s final):
# S1 robot hook 3.68 | S2 code 4.00 | S3 cyborg 3.61 | S4 cover-scene 9.56
# S5 reading 7.29 | S6 front cover 5.68
# Ken Burns on stills uses a fast animated crop (NOT zoompan — zoompan is
# far too slow on a 2-vCPU runner). Window shrinks 1296x2304 -> 1200x2133 (1.08x).
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="$REPO_ROOT/assets"
STOCK="$REPO_ROOT/stock"
WORK="$REPO_ROOT/work"
S="$WORK/seg"
mkdir -p "$S" "$WORK"

VF="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p"
ENC="-c:v libx264 -preset veryfast -crf 20"

echo "== S1 robot (hook) =="
ffmpeg -y -v error -ss 0 -t 3.68 -i "$STOCK/robot1.mp4" -vf "$VF" $ENC -an "$S/s1.mp4"
echo "== S2 code =="
ffmpeg -y -v error -ss 0 -t 4.00 -i "$STOCK/code1.mp4" -vf "$VF" $ENC -an "$S/s2.mp4"
echo "== S3 cyborg =="
ffmpeg -y -v error -ss 0 -t 3.61 -i "$STOCK/cyborg.mp4" -vf "$VF" $ENC -an "$S/s3.mp4"
echo "== S4 cover scene (Ken Burns zoom-in, fast crop) =="
ffmpeg -y -v error -loop 1 -t 9.56 -i "$ASSETS/cover-scene-human-robot-v2.jpg" \
  -vf "scale=1296:2304:force_original_aspect_ratio=increase,crop=1296:2304,crop=w='1296*(1-0.074*n/287)':h='2304*(1-0.074*n/287)':x='(1296-ow)/2':y='(2304-oh)/2',scale=1080:1920,fps=30,format=yuv420p" \
  $ENC -an "$S/s4.mp4"
echo "== S5 reading =="
ffmpeg -y -v error -ss 2 -t 7.29 -i "$STOCK/read2.mp4" -vf "$VF" $ENC -an "$S/s5.mp4"
echo "== S6 front cover (Ken Burns zoom-in, fast crop) =="
ffmpeg -y -v error -loop 1 -t 5.68 -i "$ASSETS/cover_front.jpg" \
  -vf "scale=1296:2304:force_original_aspect_ratio=increase,crop=1296:2304,crop=w='1296*(1-0.057*n/170)':h='2304*(1-0.057*n/170)':x='(1296-ow)/2':y='(2304-oh)/2',scale=1080:1920,fps=30,format=yuv420p" \
  $ENC -an "$S/s6.mp4"

echo "== chain with 0.4s crossfades + vignette + fade-out =="
ffmpeg -y -v error \
  -i "$S/s1.mp4" -i "$S/s2.mp4" -i "$S/s3.mp4" -i "$S/s4.mp4" -i "$S/s5.mp4" -i "$S/s6.mp4" \
  -filter_complex "\
[0][1]xfade=transition=fade:duration=0.4:offset=3.28[x1];\
[x1][2]xfade=transition=fade:duration=0.4:offset=6.88[x2];\
[x2][3]xfade=transition=fade:duration=0.4:offset=10.09[x3];\
[x3][4]xfade=transition=fade:duration=0.4:offset=19.25[x4];\
[x4][5]xfade=transition=fade:duration=0.4:offset=26.14[x5];\
[x5]vignette=PI/5,fade=t=out:st=31.32:d=0.5,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -preset veryfast -crf 20 -an "$S/chained.mp4"

echo "== mux voiceover =="
ffmpeg -y -v error -i "$S/chained.mp4" -i "$ASSETS/voiceover-v3.wav" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest "$WORK/base.mp4"

ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_type,codec_name,width,height -of default=noprint_wrappers=1 "$WORK/base.mp4"
echo "DONE $WORK/base.mp4"
