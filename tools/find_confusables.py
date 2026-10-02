#!/usr/bin/env python3
"""取り違えやすい表記の候補を原稿から機械的に拾う（試作・判定はしない）。

使い方:
  python3 tools/find_confusables.py 一覧.tsv 原稿 [原稿 ...]

一覧は TSV（tier, 誤り側, 正しい側, 見分け方）。原稿の各行で「誤り側」の文字列を探し、
行番号・tier・該当文字列・もう一方・前後の文脈を出す。
tier A は形そのものがほぼ誤り、tier B はどちらも実在語で文脈で決まる組。
候補は誤りの根拠ではない。正誤は文脈で判定する。
"""
import sys
from pathlib import Path

CTX = 15


def load(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        cols = line.split("\t")
        if len(cols) >= 3 and cols[0] in ("A", "B") and cols[1]:
            rows.append((cols[0], cols[1], cols[2], cols[3] if len(cols) > 3 else ""))
    return rows


def scan(rows, text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for tier, wrong, right, note in rows:
            i = line.find(wrong)
            while i >= 0:
                ctx = line[max(0, i - CTX):i + len(wrong) + CTX].strip()
                out.append((n, tier, wrong, right, note, ctx))
                i = line.find(wrong, i + 1)
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    rows = load(sys.argv[1])
    for f in sys.argv[2:]:
        for n, tier, wrong, right, note, ctx in scan(rows, Path(f).read_text(encoding="utf-8")):
            print(f"{Path(f).name}:{n}\t{tier}\t{wrong}→{right}\t{note}\t…{ctx}…")


if __name__ == "__main__":
    main()
