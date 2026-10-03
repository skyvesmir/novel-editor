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

    # av_inspect と同じ立ち上がりの定義（直後 8ms −直前 20ms の段差が最大の点、6dB 未満は検出不能）で sfx.wav を測る
    sys.path.insert(0, str(OUT.parents[1] / "tools"))
    from av_inspect import audio_onset
    m32 = m.astype(np.float32)
    worst, undet = 0.0, []
    for i, e in enumerate(cue["events"]):
        if e["kind"] in ("silence", "riser"):
            continue
        t = e["frame"] / fps
        a_t, st = audio_onset(m32, t - 0.1, t + 0.1)
        if a_t is None:
            undet.append((i, e["beat"], e["kind"], st))
            continue
        d = (a_t - t) * 1000
        if abs(d) > abs(worst):
            worst = d
        if 88 <= e["beat"] <= 90:
            print(f"  av_inspect onset #{i} beat {e['beat']} {e['kind']}: {d:+.1f}ms")
    print(f"av_inspect-style onset on sfx.wav: max |offset| = {abs(worst):.1f}ms ({worst:+.1f}); undetectable: {undet}")

    # 低域のモノラル度（BGM）：150Hz 未満の side/mid のエネルギー比
    bg2, _ = read(OUT / "bgm.wav")
    mid_, side_ = bg2.mean(axis=1), (bg2[:, 0] - bg2[:, 1]) / 2
    f = np.fft.rfftfreq(len(mid_), 1 / SR)
    Mm, Ss = np.abs(np.fft.rfft(mid_)) ** 2, np.abs(np.fft.rfft(side_)) ** 2
    for lo, hi in ((20, 150), (150, 1000), (1000, 4000), (4000, 16000)):
        k = (f >= lo) & (f < hi)
        print(f"bgm side/mid {lo}-{hi}Hz: {10*np.log10(Ss[k].sum()/(Mm[k].sum()+1e-20)+1e-20):6.1f} dB")

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
    # 旧版（audio-v4）との比較：同じ設定のスペクトログラムを上下に並べる（BGM と mix）
    OLD = OUT.parent / "audio-v4"
    if OLD.exists():
        tiles = []
        for tag, d_ in (("v4 bgm", OLD / "bgm.wav"), ("v5 bgm", OUT / "bgm.wav"), ("v4 mix", OLD / "mix.wav"), ("v5 mix", OUT / "mix.wav")):
            p = CHK / f".tmp_{tag.replace(' ', '_')}.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(d_), "-lavfi",
                            "showspectrumpic=s=1600x360:legend=1:scale=log:fscale=log:color=intensity",
                            str(p)], check=True)
            im = Image.open(p).convert("RGB"); p.unlink()
            ImageDraw.Draw(im).text((10, 6), tag, fill=(255, 255, 255))
            tiles.append(im)
        out = Image.new("RGB", (max(t.width for t in tiles), sum(t.height for t in tiles)))
        y = 0
        for t in tiles:
            out.paste(t, (0, y)); y += t.height
        out.save(CHK / "compare_v4_v5.png")
        # 帯域ごとの平均レベル（dB）の差：区間ごと
        o, _ = read(OLD / "bgm.wav")
        print("band level (bgm, LUFS 差を除いた相対 dB: 各帯域 − 全帯域)  [<120, 120-1k, 1-4k, >4k]")
        for nm, a, b in (("hook", 0, 12), ("drop", 12, 24), ("demo", 24, 88), ("section", 88, 116), ("peak/outro", 132, 152)):
            for tag, arr in (("v4", o), ("v5", bg2)):
                seg = arr[a * spb:b * spb].mean(axis=1)
                X = np.abs(np.fft.rfft(seg)) ** 2; ff = np.fft.rfftfreq(len(seg), 1 / SR); tot = X.sum()
                vals = [10 * np.log10(X[(ff >= lo) & (ff < hi)].sum() / tot + 1e-20) for lo, hi in ((20, 120), (120, 1000), (1000, 4000), (4000, 20000))]
                print(f"  {nm:<11} {tag}: " + " ".join(f"{v:6.1f}" for v in vals))
    # ポンプの確認：拍12〜20 の BGM の拡大スペクトログラムと、60〜400Hz の包絡
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "4.8", "-t", "3.2", "-i", str(OUT / "bgm.wav"), "-lavfi",
                    "showspectrumpic=s=1600x512:legend=1:scale=log:fscale=log:color=intensity",
                    str(CHK / "zoom_bgm_beats12-20.png")], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "9.6", "-t", "6.4", "-i", str(OUT / "bgm.wav"), "-lavfi",
                    "showspectrumpic=s=1600x512:legend=1:scale=log:fscale=log:color=intensity",
                    str(CHK / "zoom_bgm_beats24-40.png")], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "49.6", "-t", "4.0", "-i", str(OUT / "bgm.wav"), "-lavfi",
                    "showspectrumpic=s=1600x512:legend=1:scale=log:fscale=log:color=intensity",
                    str(CHK / "zoom_bgm_beats124-134_tapestop.png")], check=True)

    # ポンプの確認：BGM の 150〜1000Hz（和音の帯域）の 5ms 包絡を、拍 12〜20（ドロップ）と 24〜32（デモ）で描く。
    # 縦の線はキック／ゴーストのトリガーの位置（譜面から）
    import bgm as BG
    Sc = BG.score([e["beat"] for e in cue["events"] if e["kind"] == "silence"])
    trig = [nt["beat"] for nt in Sc["trig"]]
    from synth import fft_filter as _ff
    band = _ff(bg2.mean(axis=1), 150, 1000, 2)
    hop = 960  # 20ms
    env = 20 * np.log10(np.sqrt(np.mean(band[: len(band) // hop * hop].reshape(-1, hop) ** 2, axis=1)) + 1e-9)
    PW, PH = 1600, 300
    pimg = Image.new("RGB", (PW, PH * 2), "white")
    pd_ = ImageDraw.Draw(pimg)
    for row, (b0, b1) in enumerate(((12, 20), (24, 32))):
        y0 = row * PH
        a, b = int(b0 * 0.4 * SR / hop), int(b1 * 0.4 * SR / hop)
        seg = env[a:b]
        lo_, hi_ = seg.max() - 24, seg.max()
        for tb in trig:
            if b0 <= tb < b1:
                x = int((tb - b0) / (b1 - b0) * PW)
                pd_.line([(x, y0), (x, y0 + PH)], fill=(255, 140, 0))
        for k in range(b0, b1 + 1):
            x = int((k - b0) / (b1 - b0) * PW)
            pd_.line([(x, y0 + PH - 12), (x, y0 + PH)], fill=(0, 0, 0))
        pts = [(int(i / len(seg) * PW), y0 + int((1 - (np.clip(v, lo_, hi_) - lo_) / 24) * (PH - 20)) + 10) for i, v in enumerate(seg)]
        pd_.line(pts, fill=(30, 60, 200), width=2)
        pd_.text((6, y0 + 4), f"bgm 150-1000Hz envelope, beats {b0}-{b1} (orange = sidechain trigger, 24dB span)", fill=(0, 0, 0))
    pimg.save(CHK / "pump_envelope.png")

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
