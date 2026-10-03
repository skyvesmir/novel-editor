#!/usr/bin/env python3
"""cues.json → video/out/audio/{bgm,sfx,mix}.wav（48kHz・ステレオ・24bit、尺は duration_seconds ちょうど）。
使い方: python3 video/audio/build.py [cues.json] [outdir]
同じ入力からは同じ wav が出る（乱数の種は固定、イベントごとに種を派生）。"""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
from synth import SR, write_wav24, limiter, place, oversample_peak
import sfx as P
import bgm as B

ROOT = Path(__file__).resolve().parents[1]
CUES = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "brief" / "cues.json"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "out" / "audio"
SEED = 20261003

TARGET_LUFS = -14.0
CEIL_DB = -1.5  # 真ピークのリミッタ天井（AAC 化での上振れに余裕を持たせる）

# 効果音の種類ごとの音量（dB）と BGM のダッキング量（dB, 保持秒）
# 効果音の種類ごとのピーク（dBFS、ミックス前）。打撃系は tanh で頭を丸めて波高率を下げる（drive）
SFX_PEAK = {"slash": -4, "stamp": -1, "slam": -1.5, "impact": 0, "whoosh": -10, "type": -17, "pen": -14, "drop": -5,
            "tick": -9, "fall": -9, "riser": -4, "title": -6, "end": 0}
SFX_DRIVE = {"slash": 2.5, "stamp": 2.0, "slam": 2.0, "impact": 2.0, "end": 2.0, "drop": 1.5, "whoosh": 1.5,
             "type": 1.5, "pen": 1.5}
DUCK = {"slash": (3, 0.15), "stamp": (6, 0.35), "slam": (5, 0.3), "impact": (8, 0.8), "whoosh": (3, 0.25),
        "type": (1.5, 0.05), "pen": (3, 0.5), "drop": (3, 0.3), "tick": (2.5, 0.15), "fall": (3, 1.0),
        "riser": (0, 0), "title": (4, 0.8), "end": (6, 1.5)}


def event_time(e, fps):
    return e["frame"] / fps  # 整数フレームをそのまま使う


def slam_pitches(events):
    """同じ場面で続く slam は音程を1段ずつ上げる（D ナチュラルマイナーの音階）。"""
    scale = [50, 52, 53, 55, 57, 58, 60, 62]
    special = {8: 46, 9: 48, 10: 50}  # 掴みの3連発は BGM のスタブ Bb→C→D と同じ根音
    out, last_scene, k = {}, None, 0
    for i, e in enumerate(events):
        if e["kind"] != "slam":
            continue
        k = k + 1 if e["scene"] == last_scene else 0
        last_scene = e["scene"]
        out[i] = special.get(e["beat"], scale[min(k, len(scale) - 1)])
    return out


def render_event(e, i, pitches):
    rng = np.random.default_rng([SEED, i])
    k = e["kind"]
    if k == "slash":
        return P.slash(rng)
    if k == "stamp":
        return P.stamp(rng, 1.15 if e.get("accent") else 1.0)
    if k == "slam":
        return P.slam(rng, pitches[i])
    if k == "impact":
        return P.impact(rng, 1.3 if e.get("accent") == "peak" else 1.0)
    if k == "whoosh":
        return P.whoosh(rng)
    if k == "type":
        return P.type_(rng)
    if k == "pen":
        return P.pen(rng)
    if k == "drop":
        return P.drop(rng)
    if k == "tick":
        return P.tick(rng, int(e["pitch_step"]))
    if k == "fall":
        return P.fall(rng)
    if k == "riser":
        return P.riser(rng, e["length_beats"] * 60 / cue["bpm"])
    if k == "title":
        return P.title(rng)
    if k == "end":
        return P.end(rng)
    if k == "silence":
        return None
    raise ValueError(f"未知のイベント種類: {k}")


def loudness(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1))
    TP = float(re.search(r"Peak:\s+(-?[\d.inf]+) dBFS", s).group(1))
    LRA = float(re.search(r"LRA:\s+(-?[\d.]+) LU", s).group(1))
    return I, TP, LRA


cue = json.load(open(CUES))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fps = cue["fps"]
    total = int(round(cue["duration_seconds"] * SR))
    events = cue["events"]
    silences = [e["beat"] for e in events if e["kind"] == "silence"]
    spb = 60 / cue["bpm"]

    # ---- 効果音
    sfx = np.zeros((total, 2))
    riser_bus = np.zeros((total, 2))
    pitches = slam_pitches(events)
    duck_db = np.zeros(total)
    placed = []
    for i, e in enumerate(events):
        sig = render_event(e, i, pitches)
        if sig is None:
            continue
        sig = sig / np.abs(sig).max()
        dr = SFX_DRIVE.get(e["kind"])
        if dr:
            sig = np.tanh(sig * dr) / np.tanh(dr)
        sig = sig * 10 ** (SFX_PEAK[e["kind"]] / 20)
        s = int(round(event_time(e, fps) * SR))
        if e["kind"] == "riser":
            # 末尾（山）を length_beats 後の拍頭に合わせる
            peak = s + int(round(e["length_beats"] * spb * SR))
            place(riser_bus, sig, peak - len(sig))
            placed.append((i, e, peak, "peak"))
        else:
            place(sfx, sig, s)
            placed.append((i, e, s, "head"))
        d, hold = DUCK[e["kind"]]
        if d:
            a0 = max(0, s - int(0.005 * SR))
            n = int((0.005 + hold + 0.3) * SR)
            t = np.arange(n) / SR
            curve = np.where(t < 0.005, -d * t / 0.005, np.where(t < 0.005 + hold, -d, -d * np.exp(-(t - 0.005 - hold) / 0.1)))
            m = min(n, total - a0)
            duck_db[a0:a0 + m] = np.minimum(duck_db[a0:a0 + m], curve[:m])

    # ---- 溜め（silence）：その1拍は BGM と効果音の尾を消す（ライザーは山へ向けて残す）
    gate = np.ones(total)
    fo, fi = int(0.006 * SR), int(0.003 * SR)
    for b in silences:
        e = next(x for x in events if x["kind"] == "silence" and x["beat"] == b)
        a = int(round(event_time(e, fps) * SR))
        z = a + int(round(spb * SR))
        gate[a - fo:a] = np.minimum(gate[a - fo:a], np.linspace(1, 0, fo))
        gate[a:z] = 0
        gate[z:z + fi] = np.minimum(gate[z:z + fi], np.linspace(0, 1, fi))

    # ---- BGM
    cache = os.environ.get("BGM_CACHE")
    if cache and os.path.exists(cache):
        bgm = np.load(cache)
    else:
        bgm, S = B.render(total, silences, seed=SEED)
        if cache:
            np.save(cache, bgm)
    bgm *= 10 ** (duck_db / 20)[:, None]
    bgm *= gate[:, None]
    sfx *= gate[:, None]
    sfx += riser_bus
    # 最後の 0.8 秒で余韻を閉じる
    fade = int(0.8 * SR)
    w = np.linspace(1, 0, fade) ** 2
    bgm[-fade:] *= w[:, None]; sfx[-fade:] *= w[:, None]

    # ---- ミックスとラウドネス合わせ
    bgm_gain, sfx_gain = 10 ** (-1.0 / 20), 10 ** (0.0 / 20)
    g = 0.5
    tmp = OUT / ".tmp_mix.wav"
    for it in range(6):
        mix, gr = limiter((bgm * bgm_gain + sfx * sfx_gain) * g, CEIL_DB)
        write_wav24(tmp, mix)
        I, TP, LRA = loudness(tmp)
        print(f"iter{it}: gain={20*np.log10(g):+.2f}dB  I={I:.2f} LUFS  TP={TP:.2f} dBTP  maxGR={20*np.log10(gr.min()):.2f}dB", flush=True)
        if abs(I - TARGET_LUFS) < 0.05 and TP <= -1.0:
            break
        g *= 10 ** ((TARGET_LUFS - I) / 20)
    tmp.unlink()
    grb = gr[: total // int(spb * SR) * int(spb * SR)].reshape(-1, int(spb * SR)).min(axis=1)
    print("limiter GR < -2dB at beats:", [(b, round(20 * np.log10(v), 1)) for b, v in enumerate(grb) if v < 10 ** (-2 / 20)])
    # stem は mix と同じゲインと同じリミッタのゲイン曲線をかける（bgm+sfx ≒ mix）
    bgm_out = bgm * bgm_gain * g * gr[:, None]
    sfx_out = sfx * sfx_gain * g * gr[:, None]
    # stem 単体でも真ピーク -1 dBTP 以下にする（必要な所だけ薄くリミット。mix は上で確定済み）
    bgm_out, _ = limiter(bgm_out, CEIL_DB)
    sfx_out, _ = limiter(sfx_out, CEIL_DB)
    write_wav24(OUT / "bgm.wav", bgm_out)
    write_wav24(OUT / "sfx.wav", sfx_out)
    write_wav24(OUT / "mix.wav", mix)
    json.dump({"placed": [(i, e["beat"], e["kind"], s, how) for i, e, s, how in placed],
               "silences": silences, "seed": SEED},
              open(OUT / "placement.json", "w"), ensure_ascii=False, indent=1)
    for name in ("bgm", "sfx", "mix"):
        print(name, loudness(OUT / f"{name}.wav"))


if __name__ == "__main__":
    main()
