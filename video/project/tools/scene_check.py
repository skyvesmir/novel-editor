#!/usr/bin/env python3
"""1シーン書き出しの検査用。

  python3 tools/scene_check.py cues  <scene-ids(,区切り)> <out.json>
      cues.json からそのシーンのイベントだけを取り、拍をシーン頭=0 にずらした cues を書く（av_inspect.py 用）
  python3 tools/scene_check.py sheet <video.mp4> <out.png> --offset-frame N [--every 3]
      縮小一覧（既定 3フレームごと＝1/4拍）。ラベルは本番の絶対フレーム番号と拍
"""
import os, sys
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
import argparse, json, subprocess
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CUES = os.path.join(os.path.dirname(os.path.dirname(HERE)), "brief", "cues.json")


def cmd_cues(ids, out):
    c = json.load(open(CUES))
    want = ids.split(",")
    sc = [s for s in c["scenes"] if any(s["id"] == w or s["id"].split("-")[0] == w for w in want)]
    lo = min(s["startBeat"] for s in sc)
    hi = max(s["startBeat"] + s["lengthBeats"] for s in sc)
    names = {s["id"] for s in sc}
    fpb = c["fps"] * 60 / c["bpm"]
    ev = []
    for e in c["events"]:
        if e["scene"] in names:
            e = dict(e)
            e["beat"] = round(e["beat"] - lo, 6)
            e["frame"] = e["frame"] - round(lo * fpb)
            ev.append(e)
    scenes = [dict(s, startBeat=s["startBeat"] - lo) for s in sc]
    d = {k: v for k, v in c.items() if k not in ("events", "scenes")}
    d.update(duration_beats=hi - lo, duration_seconds=(hi - lo) * 60 / c["bpm"], scenes=scenes, events=ev)
    json.dump(d, open(out, "w"), ensure_ascii=False, indent=1)
    print(round(lo * fpb))


def cmd_sheet(video, out, offset, every, cols=8, tw=320, th=180):
    c = json.load(open(CUES))
    fpb = c["fps"] * 60 / c["bpm"]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={tw}:{th}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    tiles, i = [], 0
    while True:
        buf = p.stdout.read(tw * th * 3)
        if len(buf) < tw * th * 3:
            break
        if i % every == 0:
            img = Image.fromarray(np.frombuffer(buf, np.uint8).reshape(th, tw, 3)).copy()
            f = i + offset
            d = ImageDraw.Draw(img)
            lab = f"f{f} b{f / fpb:.2f}"
            d.rectangle([0, 0, 8 * len(lab) + 6, 14], fill=(0, 0, 0))
            d.text((3, 1), lab, fill=(255, 255, 0))
            tiles.append(img)
        i += 1
    p.wait()
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (40, 40, 40))
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % cols) * tw, (k // cols) * th))
    sheet.save(out)
    print(f"{out} ({len(tiles)} コマ / {i} フレーム)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("cues"); a1.add_argument("ids"); a1.add_argument("out")
    a2 = sub.add_parser("sheet"); a2.add_argument("video"); a2.add_argument("out")
    a2.add_argument("--offset-frame", type=int, default=0); a2.add_argument("--every", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "cues":
        cmd_cues(a.ids, a.out)
    else:
        cmd_sheet(a.video, a.out, a.offset_frame, a.every)
