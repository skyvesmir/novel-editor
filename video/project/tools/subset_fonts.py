#!/usr/bin/env python3
"""video/assets/fonts の TTF を、動画で使う字だけに絞って video/project/assets/fonts/ に写す。

字の出どころ: video/brief/*.md と cues.json の全文字 + ASCII + scenes/extra-chars.txt（足りない字を足す場所）。
使い方: python3 video/project/tools/subset_fonts.py
"""
import glob, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
VIDEO = os.path.dirname(PROJ)
SRC = os.path.join(VIDEO, "assets", "fonts")
DST = os.path.join(PROJ, "assets", "fonts")

FONTS = {  # 出力名: 元ファイル
    "DelaGothicOne-400.ttf": "DelaGothicOne/DelaGothicOne-400.ttf",
    "ShipporiMinchoB1-400.ttf": "ShipporiMinchoB1/ShipporiMinchoB1-400.ttf",
    "ShipporiMinchoB1-700.ttf": "ShipporiMinchoB1/ShipporiMinchoB1-700.ttf",
    "KleeOne-600.ttf": "KleeOne/KleeOne-600.ttf",
    "ZenKakuGothicNew-500.ttf": "ZenKakuGothicNew/ZenKakuGothicNew-500.ttf",
    "ZenKakuGothicNew-900.ttf": "ZenKakuGothicNew/ZenKakuGothicNew-900.ttf",
}

chars = set(chr(c) for c in range(0x20, 0x7F))
files = glob.glob(os.path.join(VIDEO, "brief", "*.md")) + [os.path.join(VIDEO, "brief", "cues.json"),
                                                           os.path.join(PROJ, "scenes", "extra-chars.txt")]
for f in files:
    if os.path.exists(f):
        chars |= set(open(f, encoding="utf-8").read())
chars -= {"\n", "\r", "\t"}
os.makedirs(DST, exist_ok=True)
txt = os.path.join(DST, ".chars.txt")
open(txt, "w", encoding="utf-8").write("".join(sorted(chars)))
for out, src in FONTS.items():
    r = subprocess.run(["pyftsubset", os.path.join(SRC, src), f"--text-file={txt}", "--layout-features=*",
                        "--no-hinting", f"--output-file={os.path.join(DST, out)}"], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr); sys.exit(1)
    print(f"{out}: {os.path.getsize(os.path.join(DST, out)) // 1024} KB")
print(f"{len(chars)} 字")
