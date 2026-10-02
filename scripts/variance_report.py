#!/usr/bin/env python3
"""同じ原稿を複数回採点した講評を並べ、ばらつきを数値で出す（判定はしない）。

使い方:
  python3 scripts/variance_report.py local/field/var/run-*.md --probe 語句 --probe 語句

- 軸ごとの点数（平均・標準偏差・範囲）
- Step 1 の件数、場面見出しの数、Step 2 の件数行
- --probe で渡した語句（既知の誤字など）が各講評に出たか
原稿の語句はコマンドラインで渡し、このスクリプトには書かない（著作権ルール）。
"""
import argparse, re, statistics, sys
from pathlib import Path

AXES = ["構成", "キャラクター", "世界観", "感情設計", "牽引力", "独自性", "文章"]


def axis_scores(text):
    out = {}
    parts = re.split(r"^### ", text, flags=re.M)
    for p in parts[1:]:
        name = p.splitlines()[0].strip()
        for ax in AXES:
            if name.startswith(ax):
                m = re.search(r"点数：\**\s*([0-9]+(?:\.[0-9])?)", p)
                if m and ax not in out:
                    out[ax] = float(m.group(1))
    return out


def section(text, head):
    m = re.search(rf"^## {head}.*?$(.*?)(?=^## )", text, flags=re.M | re.S)
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--probe", action="append", default=[])
    a = ap.parse_args()
    rows = []
    for f in a.files:
        t = Path(f).read_text(encoding="utf-8")
        s1 = section(t, "列挙")
        s2 = section(t, "精査")
        rows.append({
            "name": Path(f).stem,
            "scores": axis_scores(t),
            "items": len(re.findall(r"^\s*\d+[.．]", s1, flags=re.M)),
            "scenes": len(re.findall(r"^#{3,4} |^\*\*場面|^場面", s1, flags=re.M)),
            "count_line": (re.search(r"列挙\d+件[^\n]*", s2) or [""])[0] if s2 else "",
            "probes": {p: (p in t) for p in a.probe},
        })
    print("| run | " + " | ".join(AXES) + " | Step1件数 | 場面見出し | 件数行 |")
    print("|---|" + "---|" * (len(AXES) + 3))
    for r in rows:
        sc = " | ".join(str(r["scores"].get(ax, "-")) for ax in AXES)
        print(f"| {r['name']} | {sc} | {r['items']} | {r['scenes']} | {r['count_line'] or '（なし）'} |")
    print()
    for ax in AXES:
        v = [r["scores"][ax] for r in rows if ax in r["scores"]]
        if len(v) >= 2:
            print(f"{ax}: 平均 {statistics.mean(v):.2f} / 標準偏差 {statistics.pstdev(v):.2f} / 範囲 {min(v)}–{max(v)}")
    if a.probe:
        print()
        for p in a.probe:
            hit = sum(r["probes"][p] for r in rows)
            print(f"probe {p!r}: {hit}/{len(rows)} 回出現")


if __name__ == "__main__":
    sys.exit(main())
