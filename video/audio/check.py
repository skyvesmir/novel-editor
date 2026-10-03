#!/usr/bin/env python3
"""書き出した wav の検査（耳の代わり）。
- ラウドネス：ffmpeg ebur128（統合・True Peak・LRA）
- 立ち上がり：av_inspect.py と同じ定義（窓 -0.1〜+0.25s、窓内ピークの15%を最初に超えた時刻）を
  (a) sfx.wav（全体）と (b) イベント単体の書き出し の両方で測る。riser は山（末尾）の位置を測る。
- 画像：スペクトログラム（ffmpeg showspectrumpic）、イベント線つき波形、区間ごとの短期ラウドネス
使い方: python3 video/audio/check.py"""
import os, sys, json, wave, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

import build as BLD
from synth import SR

OUT = BLD.OUT
CHK = OUT / "check"


def read(path):
    with wave.open(str(path)) as w:
        n, ch, sw = w.getnframes(), w.getnchannels(), w.getsampwidth()
        b = np.frombuffer(w.readframes(n), np.uint8).reshape(-1, 3)
    q = np.zeros((len(b), 4), np.uint8); q[:, 1:] = b
    x = q.view("<i4").reshape(-1) / 2 ** 31
    return x.reshape(-1, ch), w.getframerate()


def mono_maxabs(x):
    return x[np.arange(len(x)), np.abs(x).argmax(axis=1)]


def onset(x, t0, t1):
    a, b = max(0, int(t0 * SR)), min(len(x), int(t1 * SR))
    seg = np.abs(x[a:b])
    if len(seg) == 0 or seg.max() < 0.01:
        return None
    return (a + int(np.argmax(seg >= seg.max() * 0.15))) / SR


def main():
    CHK.mkdir(parents=True, exist_ok=True)
    cue = BLD.cue
    fps = cue["fps"]
    res = {}
    for name in ("bgm", "sfx", "mix"):
        I, TP, LRA = BLD.loudness(OUT / f"{name}.wav")
        x, sr = read(OUT / f"{name}.wav")
        res[name] = {"I": I, "TP": TP, "LRA": LRA, "seconds": len(x) / sr, "sr": sr, "ch": x.shape[1]}
    print(json.dumps(res, indent=1))

    sfx, _ = read(OUT / "sfx.wav")
    m = mono_maxabs(sfx)
    pitches = BLD.slam_pitches(cue["events"])
    rows = []
    for i, e in enumerate(cue["events"]):
        t = e["frame"] / fps
        if e["kind"] == "silence":
            seg = np.abs(m[int(t * SR) + 10: int((t + 0.4) * SR) - 10])
            rows.append((i, e["beat"], "silence", None, None, float(seg.max())))
            continue
        if e["kind"] == "riser":
            pk = t + e["length_beats"] * 60 / cue["bpm"]
            sig = BLD.render_event(e, i, pitches)
            env = np.abs(sig).max(axis=1)
            iso = (len(sig) - 1 - int(np.argmax(env[::-1] >= env.max() * 0.999))) / SR - len(sig) / SR  # 山の位置（末尾基準）
            w = np.abs(m[int((pk - 0.3) * SR): int(pk * SR) + 1])
            full = (int((pk - 0.3) * SR) + int(np.argmax(w)) ) / SR - pk
            rows.append((i, e["beat"], "riser(peak)", iso * 1000, full * 1000, None))
            continue
        sig = BLD.render_event(e, i, pitches)
        iso_x = np.concatenate([np.zeros((int(0.5 * SR), 2)), sig])
        iso = onset(mono_maxabs(iso_x), 0.5 - 0.1, 0.5 + 0.25) - 0.5
        full = onset(m, t - 0.1, t + 0.25)
        rows.append((i, e["beat"], e["kind"], iso * 1000, None if full is None else (full - t) * 1000, None))
    print(f"{'#':>3} {'beat':>9} {'kind':<12} {'iso_ms':>8} {'full_ms':>8}")
    for r in rows:
        print(f"{r[0]:>3} {r[1]:>9.3f} {r[2]:<12} {'' if r[3] is None else f'{r[3]:8.2f}':>8} {'' if r[4] is None else f'{r[4]:8.2f}':>8}"
              + ("" if r[5] is None else f"  sfx_max_in_silence={r[5]:.5f}"))
    iso_max = max(abs(r[3]) for r in rows if r[3] is not None)
    full_max = max(abs(r[4]) for r in rows if r[4] is not None)
    print(f"max |offset| isolated={iso_max:.2f}ms  in-mix(sfx stem)={full_max:.2f}ms")

    # 溜めの拍：mix の最大振幅
    mix, _ = read(OUT / "mix.wav")
    for e in cue["events"]:
        if e["kind"] == "silence":
            a = e["frame"] / fps
            seg = mix[int(a * SR) + 1: int((a + 0.4) * SR) - 1]
            print(f"silence beat {e['beat']}: mix peak {20*np.log10(np.abs(seg).max()+1e-9):.1f} dBFS")

    bgm_all, _ = read(OUT / "bgm.wav")
    # 拍ごとの RMS（dBFS）を区間ごとに
    spb = int(0.4 * SR)
    for sc in cue["scenes"]:
        a, b = sc["startBeat"] * spb, (sc["startBeat"] + sc["lengthBeats"]) * spb
        r = 20 * np.log10(np.sqrt(np.mean(mix[a:b] ** 2)) + 1e-9)
        rb = 20 * np.log10(np.sqrt(np.mean(bgm_all[a:b] ** 2)) + 1e-9)
        print(f"{sc['id']:<18} mix RMS {r:6.1f} dBFS   bgm RMS {rb:6.1f} dBFS")

    # 画像
    for name in ("mix", "bgm", "sfx"):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(OUT / f"{name}.wav"), "-lavfi",
                        "showspectrumpic=s=1920x512:legend=1:scale=log:fscale=log:color=intensity",
                        str(CHK / f"spectrum_{name}.png")], check=True)
    W, H = 3200, 600
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    bg, _ = read(OUT / "bgm.wav")
    tot = len(mix)
    for arr, col, y0 in ((bg, (60, 90, 200), 0), (sfx, (200, 50, 30), 200), (mix, (20, 20, 20), 400)):
        a = np.abs(arr).max(axis=1)
        cols = a[: tot // W * W].reshape(W, -1).max(axis=1)
        for x in range(W):
            h = int(cols[x] * 95)
            d.line([(x, y0 + 100 - h), (x, y0 + 100 + h)], fill=col)
    for sc in cue["scenes"]:
        x = int(sc["startBeat"] * 0.4 * SR / tot * W)
        d.line([(x, 0), (x, H)], fill=(0, 160, 0)); d.text((x + 2, 2), sc["id"], fill=(0, 120, 0))
    for e in cue["events"]:
        x = int(e["frame"] / fps * SR / tot * W)
        d.line([(x, 190), (x, 210)], fill=(255, 0, 255) if e["kind"] == "silence" else (240, 140, 0))
    img.save(CHK / "waveform.png")
    print("images:", sorted(str(p) for p in CHK.glob("*.png")))


if __name__ == "__main__":
    main()
