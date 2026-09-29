#!/usr/bin/env python3
"""講評の下書きにある「」の中身が、提出物に原文どおりあるかを照合する。字数も数える。

使い方:
  python3 check_quotes.py quotes 下書き.md 提出物1 [提出物2 ...]
  python3 check_quotes.py count 提出物 [提出物 ...]

quotes: 下書きの最上位の「」を1つずつ取り出し、提出物（と、この skill の references/）に
  同じ文字列があるかを調べる。空白・改行の違いは無視する。「…」「……」「...」「（中略）」で
  区切られた抜粋は、区切りごとに照合する。見つからないものだけを一覧にする（終了コード 1）。
count: 空白・改行を除いた字数と、段落数を出す。
"""
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

ELLIPSIS = re.compile(r"……|…|\.\.\.|（中略）|〜")
SPACE = re.compile(r"[\s　]+")


def norm(s):
    return SPACE.sub("", s)


def top_level_quotes(text):
    out, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch == "「":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == "」" and depth:
            depth -= 1
            if depth == 0:
                out.append(text[start:i])
    return out


def nearest(frag, hay):
    m = SequenceMatcher(None, hay, frag, autojunk=False).find_longest_match(0, len(hay), 0, len(frag))
    lo = max(0, m.a - m.b)
    return hay[lo:lo + len(frag) + 4]


def quotes(draft, sources):
    hay = "".join(norm(Path(p).read_text(encoding="utf-8")) for p in sources)
    refs = Path(__file__).resolve().parent.parent
    hay_ref = "".join(norm(p.read_text(encoding="utf-8")) for p in refs.rglob("*.md"))
    bad = []
    for q in top_level_quotes(Path(draft).read_text(encoding="utf-8")):
        frags = [norm(f) for f in ELLIPSIS.split(q) if norm(f)]
        miss = [f for f in frags if f not in hay and f not in hay_ref]
        if miss:
            bad.append((q, miss[0]))
    for q, f in bad:
        print(f"未照合「{q}」\n  近い原文: {nearest(f, hay)}")
    print(f"未照合 {len(bad)} 件")
    return 1 if bad else 0


def count(sources):
    for p in sources:
        t = Path(p).read_text(encoding="utf-8")
        paras = [x for x in re.split(r"\n\s*\n|\n(?=　)", t) if x.strip()]
        print(f"{p}: {len(norm(t))} 字（空白・改行を除く）／段落 {len(paras)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "quotes":
        sys.exit(quotes(sys.argv[2], sys.argv[3:]))
    if len(sys.argv) >= 3 and sys.argv[1] == "count":
        sys.exit(count(sys.argv[2:]))
    print(__doc__)
    sys.exit(2)
