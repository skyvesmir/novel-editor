#!/usr/bin/env python3
"""紹介動画のフォントを取得し、ライセンスと字形の収録を確かめて video/brief/fonts.md に書く。

フォント本体は git に入れない（.gitignore 済み）ので、新しい環境ではこれを1回走らせる。
  python3 video/tools/fetch_fonts.py
取得元：Google Fonts の css2 API（古い UA を名乗ると分割されない TTF 1本が返る）と、
google/fonts リポジトリの OFL.txt（raw.githubusercontent.com）。
字形の確認には、絵コンテ・デモ原稿・skill の出力・cues.json に出てくる全ての非 ASCII 文字を使う。
"""
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
FONTS = ROOT / "video/assets/fonts"
BRIEF = ROOT / "video/brief"
UA = "Mozilla/4.0"  # css2 API が unicode-range の分割をしない TTF を返す

# (表示名, google/fonts の ofl ディレクトリ, ウェイト, 役割)
FAMILIES = [
    ("Dela Gothic One", "delagothicone", [400], "叩きつけ見出し・数字"),
    ("Shippori Mincho B1", "shipporiminchob1", [400, 700], "原稿の本文・出力カード"),
    ("Klee One", "kleeone", [600], "赤ペンの書き込み"),
    ("Zen Kaku Gothic New", "zenkakugothicnew", [500, 900], "UI・小さな補足"),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def coverage_text():
    chars = set()
    # 画面に出る文字の正本は cues.json の text。md だけを見て「①②③」の欠けを見逃した前例がある
    for p in list(BRIEF.glob("*.md")) + [BRIEF / "cues.json"]:
        if p.name in ("fonts.md",):
            continue
        chars |= {c for c in p.read_text(encoding="utf-8") if ord(c) > 0x7F and not c.isspace()}
    return chars


def main():
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "fonttools"])
        from fontTools.ttLib import TTFont

    need = coverage_text()
    rows = []
    for name, ofl, weights, role in FAMILIES:
        d = FONTS / name.replace(" ", "")
        d.mkdir(parents=True, exist_ok=True)
        lic = get(f"https://raw.githubusercontent.com/google/fonts/main/ofl/{ofl}/OFL.txt")
        (d / "OFL.txt").write_bytes(lic)
        is_ofl = b"SIL Open Font License" in lic
        for w in weights:
            css = get("https://fonts.googleapis.com/css2?family="
                      + urllib.parse.quote_plus(name) + f":wght@{w}").decode()
            urls = re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)
            if len(urls) != 1:
                sys.exit(f"{name} {w}: TTF の URL が1本に定まらない（{len(urls)}本）")
            f = d / f"{name.replace(' ', '')}-{w}.ttf"
            f.write_bytes(get(urls[0]))
            cmap = TTFont(f).getBestCmap()
            missing = "".join(sorted(c for c in need if ord(c) not in cmap))
            rows.append((name, f.relative_to(ROOT), w, "OFL" if is_ofl else "要確認", role, missing))
            print(f"{name} {w}: {f.stat().st_size // 1024}KB 欠け{len(missing)}字")

    out = ["# 採用フォント（`video/tools/fetch_fonts.py` が生成）", "",
           f"確認に使った文字：`video/brief/*.md` と `cues.json` に出てくる非 ASCII 文字 {len(need)} 種。", "",
           "| 書体 | ファイル | ウェイト | ライセンス | 役割 | 欠けた字 |", "|---|---|---|---|---|---|"]
    out += [f"| {n} | `{p}` | {w} | {l} | {r} | {m or 'なし'} |" for n, p, w, l, r, m in rows]
    out += ["", "Noto Sans JP（`video/assets/fonts/NotoSansJP.ttf`、可変・OFL）は試作で使用済み。",
            "欠けた字がある書体でその字を出す場面は、同じ役割の別書体に落とさず、文言か書体を変える。"]
    (BRIEF / "fonts.md").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
