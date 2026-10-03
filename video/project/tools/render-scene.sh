#!/usr/bin/env bash
# 1シーン（または連続する複数シーン）だけを書き出して検査する。
#   bash video/project/tools/render-scene.sh s01            # s01-hook だけ（draft 画質）
#   bash video/project/tools/render-scene.sh s01,s02        # s01〜s02（つなぎ目の確認）
#   bash video/project/tools/render-scene.sh s04 standard   # 画質指定（draft|standard|high）
# 出力:
#   video/out/scenes/<名>.mp4                   書き出し（上書き。本番の v<N>.mp4 とは別）
#   video/out/inspect/scene-<名>/sheet.png      縮小一覧（3フレーム=1/4拍ごと。ラベルは本番の絶対フレームと拍）
#   video/out/inspect/scene-<名>/overview.png ほか   av_inspect.py の結果（音ズレ・静止・黒画面）
set -euo pipefail
IDS="${1:?シーン id（例 s01 / s01-hook / s01,s02）}"
Q="${2:-draft}"
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO="$(dirname "$PROJ")"
cd "$PROJ"

NAME="$(echo "$IDS" | tr ',' '\n' | sed 's/-.*//' | paste -sd- -)"
node tools/build.mjs --solo "$IDS"
HTML="_solo-${NAME}.html"
# 書き出し後に消す（直下に入口の HTML が複数あると check が multiple_root_compositions で落ちる）
trap 'rm -f "$PROJ/$HTML"' EXIT
OUT_MP4="$VIDEO/out/scenes/${NAME}.mp4"
INS="$VIDEO/out/inspect/scene-${NAME}"
mkdir -p "$VIDEO/out/scenes" "$INS"

npx hyperframes render . -c "$HTML" -o "$OUT_MP4" -f 30 -q "$Q" 2>&1 | tail -n 4

OFF="$(python3 tools/scene_check.py cues "$IDS" "$INS/cues.json")"
python3 tools/scene_check.py sheet "$OUT_MP4" "$INS/sheet.png" --offset-frame "$OFF" --every 3
python3 "$VIDEO/tools/av_inspect.py" "$OUT_MP4" "$INS/cues.json" --out "$INS" || true
echo "mp4: $OUT_MP4"
echo "一覧: $INS/sheet.png"
