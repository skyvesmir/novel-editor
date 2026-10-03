#!/usr/bin/env bash
# 本番の書き出しと、配布用の音の載せ替えを決まった手順で行う。
#   bash video/tools/finalize.sh v4
# 1. HyperFrames で通し書き出し → video/out/render/<版>-render.mp4
#    （この書き出しは音を約 2.6dB 下げる。v4 で -14.0 → -16.6 LUFS を実測）
# 2. 映像はそのまま（再エンコードしない）、音を mix.wav から載せ替える → video/out/render/<版>.mp4
#    AAC は鋭い立ち上がりで山が 2dB ほど跳ねるので、先にリミッターで山だけ抑える。
#    リミッターの先読み 1ms は atrim で戻す（v4：mix.wav とのずれ -0.02ms）。
#    limit は 0.60（v4 で実測：-14.7 LUFS・True Peak -2.2 dBTP・クリップ 0）。
#    AAC の跳ね方は 1ms のずれでも変わるので、limit を変えたら必ず測り直す。
# 3. av_inspect で検査する。
set -euo pipefail
V="${1:?版の名前（例 v4）}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/video/out/render"
mkdir -p "$OUT"
cd "$ROOT/video/project"
node tools/build.mjs
npx hyperframes render . -o "$OUT/$V-render.mp4" -f 30 -q standard
DUR=$(python3 -c "import json;print(json.load(open('$ROOT/video/brief/cues.json'))['duration_seconds'])")
ffmpeg -v error -y -i "$OUT/$V-render.mp4" -i "$ROOT/video/out/audio/mix.wav" -map 0:v -map 1:a -c:v copy \
  -af "alimiter=limit=0.60:attack=1:release=50:level=false,atrim=start=0.001,asetpts=PTS-STARTPTS,apad=whole_dur=$DUR" \
  -c:a aac -b:a 256k -ar 48000 -t "$DUR" -movflags +faststart "$OUT/$V.mp4"
cd "$ROOT"
python3 video/tools/av_inspect.py "$OUT/$V.mp4" video/brief/cues.json || true
