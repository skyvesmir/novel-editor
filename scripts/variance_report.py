#!/usr/bin/env python3
"""同じ原稿を複数回採点した講評を並べ、ばらつきを数値で出す（判定はしない）。

使い方:
  python3 scripts/variance_report.py local/field/var/run-*.md --probe 語句 --probe 語句

- 軸ごとの点数（平均・標準偏差・範囲）
- Step 1 の件数、場面見出しの数、Step 2 の件数行
- --probe で渡した語句（既知の誤字など）が、誤字の節（「## 誤字」で始まる節）に出たか。
  誤字の節がない講評（誤字チェックモードの出力）は全文を見る。本文の引用として載っただけの語を
  検出と数えないため（2026-10-02、全文検索で根拠の引用を検出と誤計数した）
- Step 1 と誤字表の重なり：各項目の最初の「」の頭8字を目印にして、何回の講評に出たかと、2回間の Jaccard
原稿の語句はコマンドラインで渡し、このスクリプトには書かない（著作権ルール）。
"""
import argparse, itertools, re, statistics, sys
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
    m = re.search(rf"^## {head}.*?$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    return m.group(1) if m else ""


def anchors(sec, table=False):
    out = set()
    for line in sec.splitlines():
        if re.match(r"^\s*\d+[.．]", line) or (table and line.startswith("| 「")):
            m = re.search(r"「([^」]*)", line)
            if m:
                out.add(m.group(1)[:8])
    return out


def overlap(label, sets):
    if len(sets) < 2:
        return
    allk = set().union(*sets)
    dist = [sum(1 for k in allk if sum(k in s for s in sets) == i) for i in range(1, len(sets) + 1)]
    jac = [len(a & b) / len(a | b) for a, b in itertools.combinations(sets, 2) if a | b]
    print(f"{label}: 延べ{len(allk)}件／出た回数 " + "・".join(f"{i}回{n}" for i, n in enumerate(dist, 1))
          + (f"／2回間の Jaccard {min(jac):.2f}–{max(jac):.2f}" if jac else ""))


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
        typo = section(t, "誤字")
        rows.append({
            "name": Path(f).stem,
            "scores": axis_scores(t),
            "items": len(re.findall(r"^\s*\d+[.．]", s1, flags=re.M)),
            "scenes": len(re.findall(r"^#{3,4} |^\*\*場面|^場面", s1, flags=re.M)),
            "count_line": (re.search(r"列挙\d+件[^\n]*", s2) or [""])[0] if s2 else "",
            "probes": {p: (p in (typo or t)) for p in a.probe},
            "a1": anchors(s1),
            "at": anchors(typo, table=True),
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
    print()
    overlap("Step 1 の重なり", [r["a1"] for r in rows if r["a1"]])
    overlap("誤字表の重なり", [r["at"] for r in rows if r["at"]])
    if a.probe:
        print()
        for p in a.probe:
            hit = sum(r["probes"][p] for r in rows)
            print(f"probe {p!r}: {hit}/{len(rows)} 回出現")


if __name__ == "__main__":
    sys.exit(main())
