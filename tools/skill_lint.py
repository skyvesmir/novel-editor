#!/usr/bin/env python3
"""novel-editor skill の不変条件を機械検証する lint。

LLMを使わずに、編集事故（相互参照の切れ・条件表の欠損・アーカイブのずれ・
description長超過・eval定義の不整合）を検出する。回帰スモークは
「skillの判断が正しいか」を見るものだが、この lint は
「skillが構造として壊れていないか」を見る。役割が違うので両方必要。

usage:
    python3 tools/skill_lint.py            # 全チェック
    python3 tools/skill_lint.py --quiet    # 失敗だけ表示
exit code: 0=全通過 / 1=1件以上のエラー
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "novel-editor"
ARCHIVE = ROOT / "novel-editor.skill"
EVALS = ROOT / "evals"

DESCRIPTION_LIMIT = 1024

# skill本体を構成する9ファイル（この集合自体が不変条件）
EXPECTED_FILES = {
    "SKILL.md",
    "references/scoring-rubric.md",
    "references/score-anchors.md",
    "references/prose-diagnostics.md",
    "references/hook-techniques.md",
    "references/audit-mode.md",
    "references/handoff-format.md",
    "references/expression-training.md",
    "references/proofreading-mode.md",
}

# 7軸。score-anchors.md に条件表があり、rubric が言及していること
AXES = ["構成", "キャラクター", "世界観", "感情設計", "牽引力", "独自性", "文章"]

# 各軸の条件表が持つべき行ラベル（4以下〜9）
ROW_LABELS = ["4以下", "5", "6", "7", "8", "9"]

# 上限規則の名前と、それがかかる軸・上限値
# （score-anchors.md「Cap rules」節に、この名前と上限表記が存在すること）
CAP_RULES = {
    "ご都合主義": ("6を上限", ["構成", "感情設計"]),
    "説明の集中投下": ("6を上限", ["世界観"]),
    "差別化不在": ("4以下", ["独自性"]),
    "描写の空白": (None, ["文章"]),
    "AI的紋切り型の反復": ("6を上限", ["文章"]),
    "語彙の水準逸脱": ("6を上限", ["文章"]),
    "引きの空手形": ("6を上限", ["牽引力"]),
    "展開リズムの固定化": ("7を上限", ["構成"]),
    "同時代性": (None, []),
    "冒頭の掴み": (None, []),  # 別項報告（非採点）。Cap rules 節の下位に置いている
}

# 「このファイルはこのファイルを参照しているはず」という依存
# SKILL.md の Portable use 表と整合していること
DEPENDENCIES = [
    ("references/prose-diagnostics.md", "score-anchors.md"),
    ("references/audit-mode.md", "score-anchors.md"),
    ("references/scoring-rubric.md", "score-anchors.md"),
]

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> bool:
    results.append((ok, name, detail))
    return ok


def read(rel: str) -> str:
    """skillファイルを読む。欠落していても例外を投げず空文字を返す。

    ファイル欠落そのものは check_file_set() が検出する。ここで
    例外を投げると以降のチェックが全部走らず、1件の欠落が
    「他は無事なのか壊れているのか分からない」状態を作ってしまう。
    """
    p = SKILL_DIR / rel
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def _md_exists(name: str) -> bool:
    """skill本文が名指しした .md が実在するか。

    skillツリー内（SKILL.md / references/）に加え、リポジトリ直下の
    保守用ファイル（notes.md など）も実在とみなす。SKILL.md は
    「Test cases」節で notes.md を正当に名指ししている。
    """
    return (
        name in {pathlib.Path(f).name for f in EXPECTED_FILES}
        or (SKILL_DIR / name).exists()
        or (SKILL_DIR / "references" / name).exists()
        or (ROOT / name).exists()
    )


# ---------------------------------------------------------------- 1. ファイル集合
def check_file_set() -> None:
    actual = {
        str(p.relative_to(SKILL_DIR))
        for p in SKILL_DIR.rglob("*")
        if p.is_file()
    }
    missing = sorted(EXPECTED_FILES - actual)
    extra = sorted(actual - EXPECTED_FILES)
    check(
        not missing and not extra,
        "skillファイル集合が9ファイル構成と一致",
        f"欠落={missing} 余分={extra}" if (missing or extra) else f"{len(actual)}ファイル",
    )


# ---------------------------------------------------------------- 2. description
def check_description() -> None:
    text = read("SKILL.md")
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    if not check(bool(m), "SKILL.md に front matter がある"):
        return
    fm = m.group(1)
    dm = re.search(r"^description:\s*(.+?)(?=\n[a-z_]+:|\Z)", fm, re.S | re.M)
    if not check(bool(dm), "front matter に description がある"):
        return
    desc = " ".join(dm.group(1).split())
    check(
        len(desc) <= DESCRIPTION_LIMIT,
        f"description が {DESCRIPTION_LIMIT} 文字以内",
        f"{len(desc)}/{DESCRIPTION_LIMIT}",
    )
    nm = re.search(r"^name:\s*(\S+)", fm, re.M)
    check(
        bool(nm) and nm.group(1) == "novel-editor",
        "name が novel-editor",
        nm.group(1) if nm else "なし",
    )


# ---------------------------------------------------------------- 3. 条件表
def check_condition_tables() -> None:
    text = read("score-anchors.md" if False else "references/score-anchors.md")
    # 軸見出し（## 構成 (structure) など）で分割
    sections: dict[str, str] = {}
    parts = re.split(r"^## +", text, flags=re.M)
    for p in parts[1:]:
        head = p.split("\n", 1)[0]
        for ax in AXES:
            if head.startswith(ax):
                sections[ax] = p
    missing_ax = [a for a in AXES if a not in sections]
    if not check(
        not missing_ax, "7軸すべてに条件表の節がある", f"欠落={missing_ax}" if missing_ax else "7/7"
    ):
        return

    for ax in AXES:
        body = sections[ax]
        rows = re.findall(r"^\| *([0-9]以下|[0-9]) *\|", body, re.M)
        missing = [r for r in ROW_LABELS if r not in rows]
        dup = [r for r in set(rows) if rows.count(r) > 1]
        check(
            not missing and not dup,
            f"条件表 {ax}: 4以下〜9 の6段が過不足なし",
            f"欠落={missing} 重複={dup}" if (missing or dup) else "6段",
        )
        # 各行に空でない条件文があること
        empties = re.findall(r"^\| *([0-9]以下|[0-9]) *\| *\|", body, re.M)
        check(not empties, f"条件表 {ax}: 空の条件セルがない", f"空={empties}" if empties else "")


# ---------------------------------------------------------------- 4. 上限規則
def check_cap_rules() -> None:
    text = read("references/score-anchors.md")
    m = re.search(r"^## Cap rules.*?(?=^## )", text, re.S | re.M)
    if not check(bool(m), "score-anchors.md に Cap rules 節がある"):
        return
    caps = m.group(0)
    for name, (limit, _axes) in CAP_RULES.items():
        found = f"**{name}**" in caps
        check(found, f"上限規則「{name}」が Cap rules 節に定義されている")
        if found and limit:
            # その規則の行だけを取り出して上限表記を確認
            line = next(
                (l for l in caps.splitlines() if f"**{name}**" in l), ""
            )
            check(
                limit.replace("を上限", "") in line,
                f"上限規則「{name}」に上限値 {limit} の表記がある",
                line[:80],
            )
    # 数え漏れ検出: 定義されているのに CAP_RULES にない規則
    declared = set(re.findall(r"^- \*\*(.+?)\*\*", caps, re.M))
    unknown = sorted(declared - set(CAP_RULES))
    check(
        not unknown,
        "Cap rules 節に未登録の規則がない（lint側の追随漏れ検出）",
        f"未登録={unknown}" if unknown else f"{len(declared)}件",
    )


# ---------------------------------------------------------------- 5. 相互参照
def check_cross_references() -> None:
    for src, target in DEPENDENCIES:
        body = read(src)
        check(
            target in body,
            f"{src} が {target} を参照している",
        )
    # SKILL.md の Portable use 表に挙がるファイルが実在すること
    skill = read("SKILL.md")
    named = set(re.findall(r"`([a-z0-9-]+\.md)`", skill))
    ghost = sorted(n for n in named if not _md_exists(n))
    check(
        not ghost,
        "SKILL.md が実在しないファイルを名指ししていない",
        f"実在しない={ghost}" if ghost else f"{len(named)}件参照",
    )
    # 各referenceが名指しする .md も実在すること
    for rel in sorted(EXPECTED_FILES):
        if rel == "SKILL.md":
            continue
        named = set(re.findall(r"`(?:references/)?([a-z0-9-]+\.md)`", read(rel)))
        ghost = sorted(n for n in named if not _md_exists(n))
        check(not ghost, f"{rel} が実在しないファイルを名指ししていない",
              f"実在しない={ghost}" if ghost else "")


# ---------------------------------------------------------------- 6. 禁止表現
def check_forbidden_language() -> None:
    """skill本文が自ら禁じている表現を、規定の文脈以外で使っていないか。

    禁止語は「禁じる文」の中には当然出てくるので、
    禁止を宣言している行（否定・No・禁じ・使わない等を含む行）は除外する。

    「上位」は単独では日常語（「人物レジスタ上位」等）なので、
    skillが実際に禁じている相対順位表現の形（上位X%／上位N位）だけを拾う。
    """
    banned = {
        "すごい": re.compile(r"すごい"),
        "天才的": re.compile(r"天才的"),
        "傑作": re.compile(r"傑作"),
        "上位X%表現": re.compile(r"上位\s*[0-9Xx％%]"),
    }
    allow_markers = ["No ", "禁", "使わない", "避け", "しない", "ない。", "never", "not "]
    for rel in sorted(EXPECTED_FILES):
        body = read(rel)
        hits = []
        for i, line in enumerate(body.splitlines(), 1):
            if any(mk in line for mk in allow_markers):
                continue
            for label, pat in banned.items():
                if pat.search(line):
                    hits.append(f"L{i}:{label}")
        check(not hits, f"{rel} に禁止表現の素の使用がない", f"{hits}" if hits else "")


# ---------------------------------------------------- 6b. 証拠・保留・停止の条項
# 文言の存在・既知の旧条項の復活を検出する編集事故チェック。
# 意味上の一貫性やモデルの遵守を証明するものではない。
WORKFLOW_GUARDS = [
    ("P1-source", "score-anchors.md", ("出所不明の抜き書きに章・節を推定で補わない", "抜粋外を含む章全体の手順"), ()),
    ("P1-carry", "score-anchors.md", ("出所・確認範囲・未確認の留保を維持する", "要約や転記だけで確認済みに変えない"), ()),
    ("P5-conjunction", "score-anchors.md", ("連言の一部だけを確認して、その点数へ到達したとしない", "不足資料に一律6・7を割り当てる規則ではない"), ()),
    ("P5-insufficient", "score-anchors.md", ("数値を支える下位条件自体が確認できなければ", "その軸は「保留」または「採点不能」", "半点にも根拠が必要"), ()),
    # 掲載形態：統合版（2026-09-29）は「三択を示しつつ同じ応答で2として採点」。旧「質問して止まる」の復活を検出する
    ("P4-proceed", "scoring-rubric.md", ("質問だけで応答を終えない", "採点は **2 として進め**", "著者の回答を推測で書き込まない"), ("その応答は質問だけで終える",)),
    ("P4-confirmed", "scoring-rubric.md", ("すでに明示されていれば再質問せず",), ()),
    # Qwen 系統の較正値（docs/calibration-evidence.md）。旧値の復活を検出する
    ("Q-window", "score-anchors.md", ("冒頭400字以内", "沈黙の記号"), ("冒頭3文以内",)),
    ("Q-hook-opening", "score-anchors.md", ("冒頭**400字以内**に、疑問・異常・危機",), ("冒頭10行以内",)),
    ("Q-cliche", "score-anchors.md", ("同じ系統のまま3箇所以上、かつ1万字あたり3箇所以上", "「同じ系統」で数える"), ()),
    ("Q-cliche-diag", "prose-diagnostics.md", ("その件数に入れない",), ("3箇所以上がAI的紋切り型に該当する場合は",)),
    ("R-audit-perchapter", "audit-mode.md", ("章をまたいで足さない",), ("標本内5箇所＋台帳累積11箇所",)),
    ("R-planning", "scoring-rubric.md", ("The object being scored is the design itself",), ()),
    ("R-format-scope", "scoring-rubric.md", ("提出単位が「連作の一章」のときだけ行う",), ()),
    ("Q-lexdev", "score-anchors.md", ("同一話（章）内で3箇所以上、かつ1万字あたり2箇所以上", "ルビ・傍点・括弧書き"), ()),
    ("Q-dialogue", "score-anchors.md", ("台詞の識別性（6点条件の後半）は**この軸にのみ置く**", "**非対称がある**"), ()),
    ("Q-homogeneity", "prose-diagnostics.md", ("均質化の判定手順", "3次元すべてで差が認められないときにだけ"), ()),
    # v2 実走（#14）で確認された失敗への手当て
    ("R-convenience", "score-anchors.md", ("その障害がどう解消されたか",), ()),
    ("R-pull-targets", "score-anchors.md", ("**先に列挙し**",), ()),
    ("P2-status", "handoff-format.md", ("出所と位置／確認できた範囲／本文照合状態", "「本文確認済み」「未照合」「照合不一致」"), ()),
    ("P2-recovery", "handoff-format.md", ("著者が申告した回収先と本文で確認した回収先を区別する", "全体集計と引き継ぎにも同じ区別を残す"), ()),
    ("P2-setting", "handoff-format.md", ("本文での開示・機能を照合した範囲を分けて記録する",), ("設定資料が提出された時点で確定版として記録",)),
    ("P2-hook", "handoff-format.md", ("未回収の期間だけから「引きの空手形」を認定しない", "提示章末と直後2章の本文"), ("An unresolved hook older than two chapters without a 空手形疑い mark is a ledger error",)),
    ("P2-retain", "handoff-format.md", ("出所付きの未照合項目として残してよい",), ("If an entry can no longer be traced to a quotation, drop it",)),
    ("P3-report", "audit-mode.md", ("抜粋しかない章を章全体の確認済みとして要求から外さない", "追加の本文確認がなければ状態は上げない", "引用付きの限定所見は返す"), ()),
    ("P3-history", "audit-mode.md", ("採点歴がないことへ読み替えない", "最終章一つだけで確定できると約束しない"), ("Everything else was already judged per chapter.",)),
    ("P2-derived", "handoff-format.md", ("元の標本範囲・暫定・保留の留保を落とさない",), ()),
]


def check_evidence_workflow() -> None:
    for key, filename, required, forbidden in WORKFLOW_GUARDS:
        body = read(f"references/{filename}")
        missing = [term for term in required if term not in body]
        revived = [term for term in forbidden if term in body]
        check(not missing and not revived, f"証拠・手順条項 {key}",
              f"欠落={missing} 旧条項復活={revived}" if missing or revived else "")


# ---------------------------------------------------------------- 7. アーカイブ整合
def check_archive() -> None:
    if not check(ARCHIVE.exists(), "novel-editor.skill が存在する"):
        return
    tree = {
        str(p.relative_to(SKILL_DIR)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in SKILL_DIR.rglob("*")
        if p.is_file()
    }
    with zipfile.ZipFile(ARCHIVE) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        zh = {n: hashlib.sha256(z.read(n)).hexdigest() for n in names}
    check(
        sorted(names) == sorted(tree),
        "アーカイブとツリーのファイル集合が一致",
        f"zipのみ={sorted(set(zh) - set(tree))} treeのみ={sorted(set(tree) - set(zh))}",
    )
    mismatch = sorted(n for n in zh if tree.get(n) != zh[n])
    check(not mismatch, "アーカイブ全ファイルの SHA-256 がツリーと一致",
          f"不一致={mismatch}" if mismatch else f"{len(zh)}ファイル")


# ---------------------------------------------------------------- 8. eval定義
def check_evals() -> None:
    try:
        data = json.loads((EVALS / "evals.json").read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        check(False, "evals.json が妥当なJSON", str(e)[:100])
        return
    evs = data["evals"] if isinstance(data, dict) and "evals" in data else data
    check(True, "evals.json が妥当なJSON", f"{len(evs)}件")

    ids = [e.get("id") for e in evs]
    check(len(ids) == len(set(ids)), "eval id に重複がない", f"{ids}")
    check(ids == sorted(ids), "eval id が昇順", f"{ids}")

    for e in evs:
        eid = e.get("id")
        for key in ("id", "name", "prompt", "expected_output", "assertions"):
            check(key in e and e[key] not in (None, "", []),
                  f"eval #{eid} に {key} がある")
        # files に書かれたパスが実在すること
        for f in e.get("files", []):
            check((ROOT / f).exists(), f"eval #{eid} の files パスが実在: {f}")

    n_assert = sum(len(e.get("assertions", [])) for e in evs)
    check(True, "アサーション総数", str(n_assert))

    try:
        tdata = json.loads((EVALS / "trigger-evals.json").read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        check(False, "trigger-evals.json が妥当なJSON", str(e)[:100])
        return
    tevs = tdata["evals"] if isinstance(tdata, dict) and "evals" in tdata else tdata
    check(True, "trigger-evals.json が妥当なJSON", f"{len(tevs)}件")


# ---------------------------------------------------------------- 9. 入力ランナー整合
def check_runner() -> None:
    """scripts/eval_prep.py が生成側の入力を正しく作るか（Genspark 版 run_smoke.py の検査を移植）。"""
    runner = ROOT / "scripts" / "eval_prep.py"
    if not check(runner.exists(), "scripts/eval_prep.py が存在する"):
        return
    src = runner.read_text(encoding="utf-8")
    check("assertion" not in src.lower(), "eval_prep.py が生成側にアサーションを渡していない")
    check("strip_judge_only" in src and "JUDGE-ONLY:START" in src,
          "eval_prep.py が JUDGE-ONLY ブロックの除去機構を持っている")
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("_ep", runner)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        evs = mod.load_evals()
        fixtures = mod.parse_fixtures()
    except BaseException as e:  # noqa: BLE001
        check(False, "eval_prep.py を読み込める", str(e)[:120])
        return

    # 文字列の存在確認だけでは「定義はあるが呼んでいない」を見逃すので、実際に全件の入力を組む
    leak_words = [
        "JUDGE-ONLY", "発火すべき", "発火してはいけない", "意図的に埋め込",
        "意図的に不完全", "判定側のみ", "生成側には渡さない", "設計意図", "埋め込み誤り",
    ]
    built = {}
    for eid in sorted(evs):
        try:
            text, _ = mod.build_input(eid, evs, fixtures)
        except BaseException as e:  # noqa: BLE001  SystemExit（除去失敗時の安全装置）も捕まえる
            check(False, f"eval_prep build_input(#{eid}) が成功する", f"{type(e).__name__}: {str(e)[:110]}")
            continue
        built[eid] = text
        hits = sorted({w for w in leak_words if w in text})
        check(not hits, f"生成側入力 #{eid} に設計意図の漏洩がない", f"漏洩語={hits}" if hits else "")

    check_review_case_inputs(evs, built)


def check_review_case_inputs(evs: dict, built: dict) -> None:
    """#13〜#15の入力前提を検査する。文学的な判定の正しさは検査しない。"""
    for eid in (13, 14, 15):
        if not check(eid in evs and eid in built, f"eval #{eid}: 定義があり入力を組める"):
            continue
        files = evs[eid].get("files", [])
        check(len(files) == 1, f"eval #{eid}: 専用素材を1件参照している")
    if 14 in evs and 15 in evs:
        publication = "掲載形態は②連作の一章（単独では掲載されない）です。"
        p14, p15 = evs[14]["prompt"], evs[15]["prompt"]
        check(evs[14].get("files") == evs[15].get("files"), "eval #14/#15: 同じ素材を使う")
        check(publication in p14 and p14.replace(publication, "", 1) == p15,
              "eval #14/#15: 依頼文の差は掲載形態の指定だけ")
    if 14 in built:
        match = re.search(r"^## 【原稿】[^\n]*\n(.*)", built[14], re.S | re.M)
        if check(bool(match), "fixture-14: 原稿見出しが存在する"):
            body = match.group(1).strip()
            sentences = body.split("。")
            reaction = "喉の奥が焼けた"
            check(len(sentences) >= 3 and reaction in sentences[2]
                  and reaction not in "".join(sentences[:2]),
                  "fixture-14: 冒頭の身体反応は第3文にある")
            flat = re.sub(r"\s", "", body)
            check(0 <= flat.find(reaction) < 400, "fixture-14: 掴みの引用候補は冒頭400字以内")
            check(sum(line.strip() == "◆" for line in body.splitlines()) == 4,
                  "fixture-14: 明示区切りが4箇所ある")
    if 13 in built:
        chapters = re.findall(r"^### 標本[A-Z]: 第(\d+)章", built[13], re.M)
        check(chapters == ["1", "6", "10", "18"],
              "fixture-13: 本文標本は第1/6/10/18章の4区画", f"実際の章={chapters}")


# ------------------------------------------------- 9b. フィクスチャの分離方式
def check_fixture_separation() -> None:
    """フィクスチャの設計意図が生成側へ漏れない構造になっているか。

    フィクスチャに「どの上限規則が発火すべきか」を書くこと自体は
    判定側の資料として有用だが、生成側に見せるとアサーションを
    先に渡したのと同じになり、スモークの分離方式が実質破られる。
    JUDGE-ONLY ブロックに入っているかを機械で確認する。
    """
    fx_dir = EVALS / "fixtures"
    if not check(fx_dir.is_dir(), "evals/fixtures/ が存在する"):
        return

    judge_block = re.compile(r"<!--\s*JUDGE-ONLY:START.*?JUDGE-ONLY:END\s*-->", re.S)
    # 生成側に見せてはいけない語（設計意図の記述に特有のもの）
    leak_words = [
        "発火すべき", "発火してはいけない", "意図的に埋め込", "意図的に不完全",
        "判定側のみ", "生成側には渡さない", "設計意図", "アサーション",
        "この規則は発火", "誤発火",
    ]
    for p in sorted(fx_dir.glob("*.md")):
        body = p.read_text(encoding="utf-8")
        # START/END の対応が取れていること
        n_start = body.count("JUDGE-ONLY:START")
        n_end = body.count("JUDGE-ONLY:END")
        check(n_start == n_end, f"{p.name}: JUDGE-ONLY の START/END が対応している",
              f"START={n_start} END={n_end}" if n_start != n_end else "")
        # 除去後に設計意図の語が残っていないこと
        visible = judge_block.sub("", body)
        hits = sorted({w for w in leak_words if w in visible})
        check(not hits, f"{p.name}: 除去後に設計意図の記述が残っていない",
              f"漏洩語={hits}" if hits else "")


# ---------------------------------------------------------------- 10. 著作権ルール
def _committable_files():
    """コミットされうるファイル（追跡中＋.gitignore 対象外の未追跡）。local/ などの除外領域は見ない。"""
    import subprocess

    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    for rel in out.splitlines():
        p = ROOT / rel
        if p.is_file():
            yield p


def check_no_manuscript_leak() -> None:
    """リポジトリに原稿テキスト・APIキーが混入していないか。"""
    patterns = {
        "OpenRouterキー": re.compile(r"sk-or-v1-[A-Za-z0-9]"),
        "OpenAIキー": re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{40,}"),
    }
    hits: list[str] = []
    for p in _committable_files():
        try:
            body = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        for label, pat in patterns.items():
            if pat.search(body):
                hits.append(f"{p.relative_to(ROOT)}:{label}")
    check(not hits, "リポジトリにAPIキーの混入がない", f"{hits}" if hits else "")

    # 監査対象作品の実名ファイルが紛れていないか
    banned_names = ["shusunouji", "hazure", "monster.txt", "iseca", "tensura",
                    "shangrila", "overlord", "mushoku", "silentwitch"]
    leaked = [
        str(p.relative_to(ROOT))
        for p in _committable_files()
        if any(b in p.name.lower() for b in banned_names)
    ]
    check(not leaked, "監査対象作品の本文ファイルがコミット領域にない",
          f"{leaked}" if leaked else "")


# ---------------------------------------------------------------- main
def main() -> int:
    quiet = "--quiet" in sys.argv
    check_file_set()
    check_description()
    check_condition_tables()
    check_cap_rules()
    check_cross_references()
    check_forbidden_language()
    check_evidence_workflow()
    check_archive()
    check_evals()
    check_runner()
    check_fixture_separation()
    check_no_manuscript_leak()

    failed = [r for r in results if not r[0]]
    for ok, name, detail in results:
        if quiet and ok:
            continue
        mark = "PASS" if ok else "FAIL"
        line = f"[{mark}] {name}"
        if detail:
            line += f"  — {detail}"
        print(line)
    print(f"\n{len(results) - len(failed)}/{len(results)} 通過"
          + (f" / 失敗 {len(failed)}件" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
