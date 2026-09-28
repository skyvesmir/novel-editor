#!/usr/bin/env python3
"""eval 実行の下ごしらえと集計（LLM不要・トークン消費ゼロ）。

生成役（eval-generator）に渡す入力から「正解の手がかり」を機械的に取り除くのが目的。
フィクスチャ見出しの括弧書き（例:「誤字ゼロを意図」）や本文中の（…）注記行
（例:「埋め込み誤り: …」）は生成役に見せない。

使い方:
  python3 scripts/eval_prep.py prep 1 3 10     # evals/.work/evalNN-input.md を作る（all で #1〜#12）
  python3 scripts/eval_prep.py trigger         # evals/.work/trigger-queries.md（正解ラベル抜き）を作る
  python3 scripts/eval_prep.py trigger-score   # evals/.work/trigger-answers.txt を正解と照合
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals" / "evals.json"
TRIGGERS = ROOT / "evals" / "trigger-evals.json"
FIXTURES = ROOT / "evals" / "fixtures" / "fixtures.md"
WORK = ROOT / "evals" / ".work"

# fixture を持たない／前ターンの文脈が要る eval。自動では組めないので案内だけ出す
MANUAL = {
    4: "前ターン（採点結果）が必要。既存の採点出力（例: evals/raw_outputs/eval03-revision.md）を"
       "「前回のアシスタントの返答」として input に追記すること。",
    6: "2ターン構成。第1ターン（出題）の出力を得た後、fixture-writer に提出文を書かせ、"
       "第1ターン出力＋提出文を追記した input で第2ターンを生成すること。",
    13: "監査モード。長編原稿（local/ 配下）が必要なため /run-evals の対象外。audit-scanner で別途実施。",
}
HEADING = re.compile(r"^## fixture-(\w+):\s*(.*)$")


def parse_fixtures():
    """{eval番号: [(ラベル, タイトル, 本文, 除去した行のリスト), ...]}"""
    sections, cur = [], None
    for line in FIXTURES.read_text(encoding="utf-8").splitlines():
        m = HEADING.match(line)
        if m:
            cur = {"heading": m.group(2), "lines": []}
            sections.append(cur)
        elif cur is not None:
            cur["lines"].append(line)
    out = {}
    for s in sections:
        ids = [int(n) for n in re.findall(r"eval #(\d+)", s["heading"])]
        label = re.split(r"[（(]", s["heading"], 1)[0].strip()
        title = (re.findall(r"「[^」]+」", s["heading"]) or [""])[-1]
        kept, stripped = [], []
        for line in s["lines"]:
            # 行全体が（…）の注記は作者メモ＝正解の手がかりになり得るので除去
            if re.match(r"^\s*[（(].*[）)]\s*$", line):
                stripped.append(line.strip())
            else:
                kept.append(line)
        body = "\n".join(kept).strip("\n")  # 全角スペースの字下げは残す
        for i in ids:
            out.setdefault(i, []).append((label, title, body, stripped))
    return out


def load_evals():
    return {e["id"]: e for e in json.loads(EVALS.read_text(encoding="utf-8"))["evals"]}


def prep(ids):
    evals, fixtures = load_evals(), parse_fixtures()
    if ids == ["all"]:
        ids = [i for i in sorted(evals) if i <= 12]
    WORK.mkdir(parents=True, exist_ok=True)
    for raw in ids:
        i = int(raw)
        e = evals[i]
        parts = ["## ユーザーの発言", "", e["prompt"].strip(), ""]
        fx = fixtures.get(i, [])
        for label, title, body, _ in fx:
            head = "## 貼り付けられた原稿" + (f"（{label}）" if len(fx) > 1 else "")
            parts += [head, "", title, "", body, ""] if title else [head, "", body, ""]
        path = WORK / f"eval{i:02d}-input.md"
        path.write_text("\n".join(parts), encoding="utf-8")
        chars = sum(len(b) for _, _, b, _ in fx)
        print(f"#{i:>2} {e['name']}: {path.relative_to(ROOT)}（原稿 {chars} 字 / fixture {len(fx)} 件）")
        for _, _, _, stripped in fx:
            for s in stripped:
                print(f"     除去した注記: {s[:40]}…")
        if i in MANUAL:
            print(f"     要手作業: {MANUAL[i]}")


def trigger():
    items = json.loads(TRIGGERS.read_text(encoding="utf-8"))
    WORK.mkdir(parents=True, exist_ok=True)
    lines = [f"{n:02d}. {x['query']}" for n, x in enumerate(items, 1)]
    (WORK / "trigger-queries.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(items)} 件を evals/.work/trigger-queries.md に書き出し（正解ラベルなし）")


def trigger_score():
    items = json.loads(TRIGGERS.read_text(encoding="utf-8"))
    answers = {}
    for line in (WORK / "trigger-answers.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(\d+)\D+?([YN])\b", line.strip(), re.I)
        if m:
            answers[int(m.group(1))] = m.group(2).upper() == "Y"
    hits = 0
    for n, x in enumerate(items, 1):
        got = answers.get(n)
        ok = got is not None and got == x["should_trigger"]
        hits += ok
        if not ok:
            want = "発火すべき" if x["should_trigger"] else "発火すべきでない"
            print(f"  NG {n:02d} ({want} / 判定={'なし' if got is None else ('Y' if got else 'N')}): {x['query'][:50]}")
    print(f"trigger-evals: {hits}/{len(items)} 一致")
    sys.exit(0 if hits == len(items) else 1)


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
    if cmd == "prep" and args:
        prep(args)
    elif cmd == "trigger":
        trigger()
    elif cmd == "trigger-score":
        trigger_score()
    else:
        print(__doc__)
        sys.exit(2)
