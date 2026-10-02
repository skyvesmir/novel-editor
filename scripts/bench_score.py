#!/usr/bin/env python3
"""ベンチ原稿（fixture-16〜18）の出力を正解キーと照合する（LLM不要）。

使い方:
  python3 scripts/bench_score.py fixture-16 out1.md out2.md ...

判定（1行単位・機械的）:
  検出   = 出力のある行に、誤った文字列（wrong）と正しい形（right）が両方ある
  言及のみ = wrong はあるが right がない行しかない（根拠の引用などで、指摘とは限らない）
  偽陽性 = negatives の文字列を含む行があり、その行が指摘の行（表の行・番号付きの行）である
誤字の節（「誤字」を含む見出し以降）があればそこだけを見る。fixture-18 は全体を見る。
人の確認が要る境界例（言及のみ・偽陽性の候補）は一覧で出すので、最後は目で確かめる。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = ROOT / "evals" / "fixtures" / "bench-keys.json"
ITEM = re.compile(r"^\s*(\||\d+[.．、)]|[-*・])")


def section(text, fixture):
    if fixture == "fixture-18":
        return text
    m = re.search(r"^#+[^\n]*誤字[^\n]*$", text, re.M)
    return text[m.start():] if m else text


def score(fixture, path, key):
    lines = section(Path(path).read_text(encoding="utf-8"), fixture).splitlines()
    hits, mentions = [], []
    for p in key["positives"]:
        rows = [l for l in lines if p["wrong"] in l]
        if any(p["right"] in l for l in rows):
            hits.append(p)
        elif rows:
            mentions.append(p)
    fps = [n for n in key.get("negatives", [])
           if any(n in l and ITEM.match(l) for l in lines)]
    return hits, mentions, fps


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    fixture, outs = sys.argv[1], sys.argv[2:]
    key = json.loads(KEYS.read_text(encoding="utf-8"))[fixture]
    pos = key["positives"]
    found = {p["wrong"]: 0 for p in pos}
    print(f"{fixture}: 仕込み {len(pos)} / 対照 {len(key.get('negatives', []))}")
    for o in outs:
        hits, mentions, fps = score(fixture, o, key)
        for p in hits:
            found[p["wrong"]] += 1
        by = {}
        for p in hits:
            by[p.get("class", "-")] = by.get(p.get("class", "-"), 0) + 1
        print(f"- {Path(o).name}: 検出 {len(hits)}/{len(pos)} {by}"
              f" 言及のみ {[p['wrong'] for p in mentions]} 偽陽性候補 {fps}")
    print("仕込みごとの検出回数:")
    for p in pos:
        print(f"  {found[p['wrong']]}/{len(outs)}  [{p.get('class','-')}"
              f"{'・' + str(p['third']) + '/3' if 'third' in p else ''}] {p['wrong']} → {p['right']}")


if __name__ == "__main__":
    main()
