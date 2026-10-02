#!/usr/bin/env python3
"""ベンチ原稿（fixture-16〜18）の出力を正解キーと照合する（LLM不要）。

使い方:
  python3 scripts/bench_score.py fixture-16 out1.md out2.md ...

判定（1行単位・機械的）:
  指摘のまとまり = 番号・表の行・箇条で始まり、次の項目の直前までの行
  検出   = 誤った文字列（wrong）を含むまとまりがある
  偽陽性候補 = negatives の文字列を含むまとまりがある（引用の巻き込みもありうるので目で確かめる）
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


def blocks(lines):
    """指摘1件ずつのまとまり（番号・表の行・箇条から次の項目の直前まで）に分ける。"""
    out = []
    for l in lines:
        if ITEM.match(l) or not out:
            out.append(l)
        else:
            out[-1] += "\n" + l
    return [b for b in out if ITEM.match(b)]


def score(fixture, path, key):
    bs = blocks(section(Path(path).read_text(encoding="utf-8"), fixture).splitlines())
    hits = [p for p in key["positives"] if any(p["wrong"] in b for b in bs)]
    fps = [n for n in key.get("negatives", []) if any(n in b for b in bs)]
    return hits, [], fps


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
              f" 偽陽性候補 {fps}")
    print("仕込みごとの検出回数:")
    for p in pos:
        print(f"  {found[p['wrong']]}/{len(outs)}  [{p.get('class','-')}"
              f"{'・' + str(p['third']) + '/3' if 'third' in p else ''}] {p['wrong']} → {p['right']}")


if __name__ == "__main__":
    main()
