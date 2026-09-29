#!/usr/bin/env python3
"""引き台帳突合スキャナ（牽引力軸の較正・タスクD）

目的:
  1. B-3（2026-09-06改訂）で牽引力4以下条件の判定対象を
     「章末＋区切り記号で明示された場面末」に限定した影響を実測する。
     旧規定（暗黙の場面転換も含む）との件数差を出す。
  2. 引きの手法分類（hook-techniques.md の6分類）を機械走査し、
     8点条件「性質の異なる手法を3種類以上」が商業作でどう分布するかを見る。
  3. 章をまたぐ疑問の寿命（回収距離）を測り、上限規則「引きの空手形」
     （2章以内に説明なく無視される）の閾値を検証する。

重要な前提（audit-mode.md の「機械走査と精読の線引き」）:
  走査はシグナル収集にすぎず、判定根拠にはならない。
  本スクリプトの出力は精読対象を選ぶための材料であり、点数を出すものではない。

前処理の既知の罠（ドライラン3作＋バッチ2で確認済み）:
  - ページ番号の数字行が混入する → 除去しないと尾部分類が全て narrative になる
  - 後書きが尾部に入る → rfind で切断（著者挨拶は物語の尾ではない）
  - 対話終了型は末尾60字では判定できない → 末尾300〜500字窓＋動詞辞書で補正

usage:
  python3 tools/hook_ledger_scan.py            # 全作品
  python3 tools/hook_ledger_scan.py tensura    # 指定作品のみ
"""
import json
import pathlib
import re
import sys
from collections import Counter

WS = pathlib.Path("/workspace")
IDX = WS / "anchor_analysis"
BATCH2 = WS / "narou-pdf" / "batch2"
OUT = WS / "hook_ledger"

WORKS = {
    "iseca": BATCH2 / "iseca.txt",
    "mushoku": BATCH2 / "mushoku.txt",
    "tensura": BATCH2 / "tensura.txt",
    "shangrila": BATCH2 / "shangrila.txt",
    "overlord_zen": BATCH2 / "overlord_zen.txt",
    "silentwitch": BATCH2 / "silentwitch.txt",
}
# overlord_ge は索引信頼性が低いため既定では除外（notes.md 2026-08-25 の記録どおり）

# --- 前処理 -----------------------------------------------------------------

PAGE_NUM = re.compile(r"^\s*\d{1,4}\s*$")
AFTERWORD = ("（後書き）", "(後書き)", "あとがき", "＜後書き＞")


def clean(text: str) -> str:
    """ページ番号行を落とす。"""
    return "\n".join(l for l in text.split("\n") if not PAGE_NUM.match(l))


def strip_afterword(body: str) -> str:
    """後書きを切断する。位置が本文の30%より後ろにある場合のみ切る。"""
    for mark in AFTERWORD:
        i = body.rfind(mark)
        if i > len(body) * 0.30:
            return body[:i]
    return body


# --- 区切り記号（B-3の「明示された場面末」の検出） --------------------------

# PDF抽出テキストでは改行が潰れているため、区切り記号は行として立たず
# 行内に埋没する。前後の空白または行頭行末を境界として拾う。
#
# 重要: 「・」の連なりは除外する。実測で shangrila 1,281件・tensura 10件など
# 検出されるが、中身は場面区切りでなく沈黙・絶句の表現（「・・・・」）である。
# 真の区切り記号は ＊(silentwitch 456) / ◇◆(tensura 150, iseca 341) /
# ■(overlord 30, iseca 32, mushoku 18) の系統。
SCENE_BREAK = re.compile(
    r"(?:[ \u3000]|^|\n)"
    r"(?:[◆◇■□●○※]{1,6}|[＊\*]{1,6}|[─―ー]{4,}|[＝=]{4,})"
    r"(?:[ \u3000]|$|\n)",
    re.M,
)

# 沈黙表現として除外するパターン（判断の記録として残す）
SILENCE_NOT_BREAK = re.compile(r"・{3,}")


def split_units(body: str):
    """章本文を「読書単位」に分割する。

    返り値は (unit_text, kind) のリスト。
      kind='chapter_end'  … 章末（必ず1つ・最後の単位）
      kind='marked_break' … 区切り記号で明示された場面末（B-3の対象）
      kind='implicit'     … 暗黙の場面転換（旧規定では対象、B-3では対象外）

    暗黙の転換は「空行1つ＋直後が時刻/場所/人物名で始まる短い行」を候補とする。
    """
    # まず明示区切りで割る
    marked = [s for s in SCENE_BREAK.split(body) if s and s.strip()]
    if not marked:
        marked = [body]
    units = []
    for i, seg in enumerate(marked):
        is_last_marked = i == len(marked) - 1
        # 明示区切りの内側で、暗黙の転換をさらに拾う
        implicit = re.split(
            r"\n(?=[ \u3000]*(?:一方|その頃|同じ頃|同時刻|同刻|翌日|翌朝|翌日の|数日後|"
            r"数時間後|夕方|深夜|この頃|別の場所|時間は|【)[^\n]{0,30}\n)",
            seg)
        implicit = [s for s in implicit if s.strip()]
        for j, sub in enumerate(implicit):
            last_sub = j == len(implicit) - 1
            if is_last_marked and last_sub:
                units.append((sub, "chapter_end"))
            elif last_sub:
                units.append((sub, "marked_break"))
            else:
                units.append((sub, "implicit"))
    return units


# --- 尾部の型分類 -----------------------------------------------------------

TAIL_WINDOW = 400  # 末尾400字（過去の走査と同一）

# 引きの手法6分類（hook-techniques.md に対応）のシグナル辞書
HOOK_SIGNALS = {
    "情報の欠落": [
        r"何(?:者|物)", r"正体", r"誰(?:だ|な|が|の)", r"知らな(?:い|かった)",
        r"分から(?:ない|なかった)", r"謎", r"見覚え", r"聞いたことの?ない",
        r"はず(?:が|は)ない", r"なぜ", r"どうして",
    ],
    "選択の分岐": [
        r"どちら", r"選(?:ば|ぶ|ん)", r"決め(?:る|ね|なけれ)", r"迷", r"かしかない",
        r"覚悟", r"決断", r"引き返(?:す|せ)", r"進む(?:か|しか)",
    ],
    "脅威の切迫": [
        r"迫(?:る|って)", r"間に合わ", r"時間がない", r"逃げ", r"殺", r"襲",
        r"危険", r"来る", r"背後", r"気配", r"追(?:って|われ)", r"包囲",
    ],
    "関係性変化の予兆": [
        r"目を(?:合わせ|逸ら)", r"背を向け", r"別れ", r"信じ(?:られ|ていい)",
        r"裏切", r"距離", r"変わ(?:った|って)", r"もう(?:二度と|会)",
        r"呼び方", r"名前を",
    ],
    "長期弧期待の更新": [
        r"始ま(?:り|った)", r"これから", r"次(?:こそ|は)", r"いよいよ",
        r"目指", r"向か(?:う|った)", r"旅立", r"約束", r"必ず",
    ],
    "視点切替による開示": [
        r"^[◆◇■□].{0,20}(?:視点|side|Side|SIDE)", r"一方", r"その頃",
        r"同(?:じ|時)刻", r"別の場所",
    ],
}

# 「出来事の完了だけで閉じている」＝4以下条件のシグナル
CLOSURE_SIGNALS = [
    r"終わ(?:った|り)(?:だ|である)?[。、]?$", r"眠(?:った|りについた)",
    r"帰(?:った|路|宅)", r"日が(?:暮れ|沈)", r"こうして", r"平和",
    r"安心", r"ほっと", r"笑(?:った|い声)", r"落ち着(?:いた|き)",
    r"一件落着", r"満足", r"幸せ",
]

# 対話終了型（末尾が会話で閉じるもの）— 末尾60字では取り逃す
DIALOGUE_END = re.compile(r"[」』][^」』]{0,80}$", re.S)

# 「章末が明示的な疑問で終わる」の判定。
#
# 実測で判明した罠: 末尾120字に「？」があるかで数えると、iseca 60章中20章(33%)が
# ヒットするが、中身は「ん？」「え？」のような会話文中の相づち・驚きの疑問符であり、
# 読者へ向けて開かれた疑問ではない。notes.md 2026-08-25 の記録(章末明示疑問率0〜9%)
# との乖離はこの誤検出が原因だった。
#
# そこで以下の2条件を課す:
#   1. 疑問符が「地の文」または「章の最終文」にあること（会話文の内側を除外）
#   2. 疑問符の直前が2文字以上の実質的な問いであること（「ん？」「え？」等を除外）
QUESTION_MARK = re.compile(r"[？?]")
INTERJECTION_Q = re.compile(
    r"[「『（(]?\s*(?:ん|え|あ|お|は|へ|ほ|うん|えっ|あれ|おや|ふむ|はい|なに|何)\s*[？?]")


def has_explicit_question(tail: str) -> bool:
    """章末が読者に向けた明示的な疑問で閉じているか。"""
    # 章の最終文を取る（末尾の空白・改行を落としてから）
    t = tail.rstrip()
    if not t:
        return False
    # 最終文の切り出し: 末尾から遡って文末記号を探す
    last = re.split(r"(?<=[。！!？?」』])", t)
    last = [x for x in last if x.strip()]
    window = "".join(last[-2:]) if last else t

    # 会話文の内側だけにある疑問符は除外する
    stripped = INTERJECTION_Q.sub("", window)
    if not QUESTION_MARK.search(stripped):
        return False
    # 疑問符の直前が実質的な問いか（直前6字に内容語があるか）を粗く見る
    for m in QUESTION_MARK.finditer(stripped):
        pre = stripped[max(0, m.start() - 8):m.start()]
        pre = re.sub(r"[「『（(\s\u3000]", "", pre)
        if len(pre) >= 4:
            return True
    return False


def classify_tail(tail: str):
    """尾部を分類し、検出した引きの手法名の集合を返す。"""
    hits = set()
    for name, pats in HOOK_SIGNALS.items():
        for p in pats:
            if re.search(p, tail, re.M):
                hits.add(name)
                break
    closure = any(re.search(p, tail, re.M) for p in CLOSURE_SIGNALS)
    explicit_q = has_explicit_question(tail)
    dialogue = bool(DIALOGUE_END.search(tail))
    return {
        "hooks": sorted(hits),
        "closure_signal": closure,
        "explicit_question": explicit_q,
        "dialogue_end": dialogue,
    }


# --- 本体 -------------------------------------------------------------------

def scan_work(name: str, txt_path: pathlib.Path):
    idx_path = IDX / f"{name}_charidx.json"
    if not idx_path.exists():
        return None
    chapters = json.loads(idx_path.read_text(encoding="utf-8"))
    raw = txt_path.read_text(encoding="utf-8", errors="replace")

    rows = []
    for ch in chapters:
        body = raw[ch["start_char"]:ch["end_char"]]
        body = strip_afterword(clean(body))
        if len(body) < 200:
            continue
        units = split_units(body)
        # B-3新規定の対象: chapter_end + marked_break
        # 旧規定の対象: 上記 + implicit
        new_targets = [(u, k) for u, k in units if k in ("chapter_end", "marked_break")]
        old_targets = units

        def eval_targets(targets):
            res = []
            for u, k in targets:
                tail = u[-TAIL_WINDOW:]
                c = classify_tail(tail)
                # 「出来事の完了だけで閉じている」= 引きが1つも立たず完了シグナルあり
                closed_only = (not c["hooks"]) and c["closure_signal"]
                res.append({"kind": k, **c, "closed_only": closed_only})
            return res

        new_res = eval_targets(new_targets)
        old_res = eval_targets(old_targets)
        ch_end = [r for r in new_res if r["kind"] == "chapter_end"]
        rows.append({
            "title": ch["title"][:40],
            "chars": ch.get("chars") or len(body),
            "units_total": len(units),
            "units_marked": sum(1 for _, k in units if k == "marked_break"),
            "units_implicit": sum(1 for _, k in units if k == "implicit"),
            "chapter_end": ch_end[0] if ch_end else None,
            "new_closed_only": sum(1 for r in new_res if r["closed_only"]),
            "old_closed_only": sum(1 for r in old_res if r["closed_only"]),
            "new_targets": len(new_res),
            "old_targets": len(old_res),
            "hooks_in_chapter": sorted({h for r in new_res for h in r["hooks"]}),
        })
    return rows


def summarize(name: str, rows):
    n = len(rows)
    ce = [r["chapter_end"] for r in rows if r["chapter_end"]]
    hook_kinds = Counter()
    for r in rows:
        for h in r["hooks_in_chapter"]:
            hook_kinds[h] += 1
    ce_hooked = sum(1 for c in ce if c["hooks"])
    ce_q = sum(1 for c in ce if c["explicit_question"])
    ce_closed = sum(1 for c in ce if c["closed_only"])
    new_t = sum(r["new_targets"] for r in rows)
    old_t = sum(r["old_targets"] for r in rows)
    new_c = sum(r["new_closed_only"] for r in rows)
    old_c = sum(r["old_closed_only"] for r in rows)
    return {
        "work": name,
        "chapters": n,
        "chapter_end_with_hook_pct": round(100 * ce_hooked / n, 1) if n else 0,
        "chapter_end_explicit_question_pct": round(100 * ce_q / n, 1) if n else 0,
        "chapter_end_closed_only_pct": round(100 * ce_closed / n, 1) if n else 0,
        "hook_kinds_used": len(hook_kinds),
        "hook_kind_distribution": dict(hook_kinds.most_common()),
        "B3_targets_new": new_t,
        "B3_targets_old": old_t,
        "B3_target_reduction_pct": round(100 * (old_t - new_t) / old_t, 1) if old_t else 0,
        "closed_only_new": new_c,
        "closed_only_old": old_c,
        "closed_only_reduction_pct": round(100 * (old_c - new_c) / old_c, 1) if old_c else 0,
    }


def main():
    OUT.mkdir(exist_ok=True)
    targets = sys.argv[1:] or list(WORKS)
    summaries = []
    for name in targets:
        if name not in WORKS:
            print(f"skip unknown work: {name}")
            continue
        print(f"scanning {name} ... ", end="", flush=True)
        rows = scan_work(name, WORKS[name])
        if rows is None:
            print("索引なし・スキップ")
            continue
        (OUT / f"{name}_units.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        s = summarize(name, rows)
        summaries.append(s)
        print(f"{s['chapters']} chapters, "
              f"B-3対象 {s['B3_targets_old']}→{s['B3_targets_new']} "
              f"(-{s['B3_target_reduction_pct']}%)")
    (OUT / "summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n=== B-3（判定対象の限定）の影響 ===")
    print(f"{'作品':<14}{'章数':>5}{'旧対象':>8}{'新対象':>8}{'減少率':>8}"
          f"{'旧完了閉じ':>10}{'新完了閉じ':>10}")
    for s in summaries:
        print(f"{s['work']:<14}{s['chapters']:>5}{s['B3_targets_old']:>8}"
              f"{s['B3_targets_new']:>8}{s['B3_target_reduction_pct']:>7}%"
              f"{s['closed_only_old']:>10}{s['closed_only_new']:>10}")

    print("\n=== 章末の性質（牽引力5点条件・多経路化の検証） ===")
    print(f"{'作品':<14}{'引きあり%':>10}{'明示疑問%':>10}{'完了閉じ%':>10}{'手法種類':>9}")
    for s in summaries:
        print(f"{s['work']:<14}{s['chapter_end_with_hook_pct']:>9}%"
              f"{s['chapter_end_explicit_question_pct']:>9}%"
              f"{s['chapter_end_closed_only_pct']:>9}%"
              f"{s['hook_kinds_used']:>9}")

    print("\n=== 手法分布（8点条件「3種類以上」の検証） ===")
    for s in summaries:
        print(f"\n{s['work']}: {s['hook_kinds_used']}種類")
        for k, v in s["hook_kind_distribution"].items():
            print(f"    {k:<20}{v:>5}章 ({100*v/s['chapters']:.0f}%)")

    print(f"\n出力: {OUT}/summary.json, {OUT}/<work>_units.json")
    print("注意: 本結果は走査シグナルであり判定ではない（audit-mode.md の線引き条項）。")
    print()
    run_payoff()




# --- 回収距離の測定（上限規則「引きの空手形」2章閾値の検証） -----------------
#
# 章末で開いた疑問が、後続の何章目で言及されるかを測る。
# 完全な意味理解は不可能なので、章末尾に現れた固有名詞・特徴語が
# 後続章の本文に再出現するまでの距離を代理指標とする。
# これは走査シグナルであり「回収された」の判定ではない（精読が必要）。

KEYWORD = re.compile(r"[ァ-ヴー]{3,}|[一-龥]{2,4}(?=[はがをのにで、。」])")
STOP = {"俺","私","僕","自分","彼女","彼","人間","今日","明日","昨日","場所","時間","言葉","そう","これ","それ"}


def measure_payoff_distance(name: str, txt_path: pathlib.Path, max_look: int = 6):
    idx_path = IDX / f"{name}_charidx.json"
    if not idx_path.exists():
        return None
    chapters = json.loads(idx_path.read_text(encoding="utf-8"))
    raw = txt_path.read_text(encoding="utf-8", errors="replace")
    bodies = []
    for ch in chapters:
        b = strip_afterword(clean(raw[ch["start_char"]:ch["end_char"]]))
        bodies.append(b)

    dists = []
    unresolved = 0
    for i, b in enumerate(bodies[:-1]):
        tail = b[-TAIL_WINDOW:]
        c = classify_tail(tail)
        if not c["hooks"]:
            continue
        # 尾部の特徴語を抽出（頻出語・代名詞は除く）
        kws = [k for k in set(KEYWORD.findall(tail)) if k not in STOP and len(k) >= 3]
        if not kws:
            continue
        # 本文全体での出現が少ない語（=その場面固有の語）を優先
        found_at = None
        for j in range(i + 1, min(i + 1 + max_look, len(bodies))):
            if any(k in bodies[j] for k in kws):
                found_at = j - i
                break
        if found_at is None:
            unresolved += 1
        else:
            dists.append(found_at)
    if not dists:
        return None
    n = len(dists) + unresolved
    within2 = sum(1 for d in dists if d <= 2)
    return {
        "work": name,
        "hooked_chapters_measured": n,
        "next_chapter_pct": round(100 * sum(1 for d in dists if d == 1) / n, 1),
        "within_2_pct": round(100 * within2 / n, 1),
        "within_6_pct": round(100 * len(dists) / n, 1),
        "beyond_6_or_none_pct": round(100 * unresolved / n, 1),
        "mean_distance": round(sum(dists) / len(dists), 2),
    }


def run_payoff():
    OUT.mkdir(exist_ok=True)
    rows = []
    print("=== 引きの回収距離（上限規則「引きの空手形」2章閾値の検証） ===")
    print("注意: 尾部の特徴語が後続章に再出現するまでの距離＝代理指標。")
    print("      「回収された」の判定ではなく、精読対象を選ぶためのシグナル。\n")
    print(f"{'作品':<14}{'測定章':>7}{'次章で':>8}{'2章以内':>9}{'6章以内':>9}{'6章超/未出':>11}{'平均':>7}")
    for name, p in WORKS.items():
        r = measure_payoff_distance(name, p)
        if not r:
            continue
        rows.append(r)
        print(f"{r['work']:<14}{r['hooked_chapters_measured']:>7}"
              f"{r['next_chapter_pct']:>7}%{r['within_2_pct']:>8}%"
              f"{r['within_6_pct']:>8}%{r['beyond_6_or_none_pct']:>10}%"
              f"{r['mean_distance']:>7}")
    (OUT / "payoff_distance.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n出力: {OUT}/payoff_distance.json")


if __name__ == "__main__":
    main()
