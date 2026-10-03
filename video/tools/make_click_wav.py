#!/usr/bin/env python3
"""cues.json の各イベント時刻にクリック音を置いた wav を合成する（試作・音ズレ測定用）。
使い方: make_click_wav.py cues.json out.wav [総秒数]"""
import os, sys
# tools/av_inspect.py が標準ライブラリ inspect を隠すので、同じ場所の他スクリプトでも除外が要る
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
import json, wave
import numpy as np
cues = json.load(open(sys.argv[1])); out = sys.argv[2]
sr = 48000
dur = float(sys.argv[3]) if len(sys.argv) > 3 else max(e["beat"] for e in cues["events"]) * 60 / cues["bpm"] + 1.0
x = np.zeros(int(sr * dur), dtype=np.float32)
n = int(sr * 0.04); t = np.arange(n) / sr
click = (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90)).astype(np.float32)  # 先頭から振幅最大
for e in cues["events"]:
    i = round(e["beat"] * 60 / cues["bpm"] * sr)
    x[i:i + n] += click[: len(x) - i][:n] * 0.8
pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
