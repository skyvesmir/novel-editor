# Handoff data format

Sessions end when a thread hits its length limit, not when the work is finished. The handoff block is what carries state across that seam, so it has to be short enough to paste and specific enough that the next session doesn't restart from zero or re-teach something already mastered.

## When to produce one

- At a natural break point: end of a session, after a drill sequence, or after a full chapter evaluation.
- When the author says the thread is getting long.
- Whenever asked.

## Template

Output it as a single fenced block so it can be copied in one action, and write the contents in Japanese.

```
【引き継ぎデータ】
■ 対象作品 / 現在地
- 作品：（タイトル・ジャンル・想定読者）
- 進行：（第N章まで執筆済 / プロット段階 など）

■ 直近の評価
- 評価対象：（章・改稿版・プロット・設定資料）
- 軸別スコア：構成 X / キャラクター X / 世界観 X / 感情設計 X / 牽引力 X / 独自性 X / 文章 X（判定不能・対象外の軸はその旨）
- 未解決の指摘：（次に直す前提で残っているもの。3件程度）

■ 表現力訓練
- 習得済み技術：（例：時制の統一、視点の固定、五感の配分）
- 未着手の技術：（次に扱う候補）
- 直近のお題と得点：（お題の要約 / X.X点）

■ 才能・技術スコア
- 才能：X/10（根拠を一行）
- 技術：X/10（根拠を一行）

■ 次セッションの開始点
-（次に何をするか。例：第4章の改稿版を評価 / 視点固定のお題から再開）
```

## Rules for filling it in

- Carry over the unresolved items verbatim in substance. If a weakness is dropped from the handoff, the next session cannot tell it was ever raised, and the same note gets delivered again as if new.
- Mark a technique "習得済み" only when it held up in a submission where it was *not* the stated constraint. Passing a drill that explicitly demanded the technique shows compliance, not mastery.
- Talent and technique are scored separately out of 10, each with a one-line basis. Talent is about the quality of the ideas and structural instincts; technique is about execution on the sentence level. They move at different speeds, and merging them hides which one is the bottleneck.
- Both numbers are **derived, never invented**. 技術 follows the 文章 axis score of the latest evaluation, and the basis line names which prose condition governs it. 才能 follows the highest score among the design axes (構成・キャラクター・世界観・感情設計・独自性), and the basis line names that axis and the condition that earned it. No condition named, no number — the same rule as everywhere else. When prose was not submitted, 技術 records 判定不能 instead of a guess.
- Never inflate the scores relative to the previous handoff without naming what specifically improved. A handoff that ratchets upward every session is the same drift the skill is built to prevent, just spread across threads.

## 作品台帳 (running work-ledger) — for serialized / long works

When the work is serialized or long (目安: 3章を超える、または1万字超の継続執筆), append this block to every handoff. It carries facts across sessions so later chapters can be scored with 併読資料 instead of provisional judgments. **Facts and quotations only — no judgments, no scores** (scores live in the history line as reference, never as evidence).

台帳の事実項目には「出所と位置／確認できた範囲／本文照合状態」を残す。本文照合状態は「本文確認済み」「未照合」「照合不一致」を区別し、推測は事実へ混ぜず確認事項へ分ける。同じ出所の項目をまとめる場合は見出しに共通情報を置いてよいが、異なる範囲・状態を一つにまとめない。以下の人物・引き・弧骨格・Step 0の4欄に共通する。

設定資料で規則の存在を確認したことと、その規則が本文で機能していることは別に記録する。本文未照合の設定資料が、規則の存在確認にも使えなくなるわけではない。軸ごとの適格性は `score-anchors.md` に従う。

引き台帳では、著者が申告した回収先と本文で確認した回収先を区別する。全体集計と引き継ぎにも同じ区別を残す。軸別点数から才能・技術を導く場合も、元の標本範囲・暫定・保留の留保を落とさない。

```
【作品台帳】
■ 人物レジスタ
-（名前：表記の揺れ候補／役割／現在状態。固有名詞は初出時の表記を固定する）

■ 引き台帳
-（開いた場所：章・節／内容と分類（情報の欠落・選択の分岐・脅威の切迫・関係性変化の予兆・正体部分開示・逆転の示唆）／回収状況：未回収・回収済み（場所）・空手形疑い）

■ 弧骨格
-（各章の場面手順の並び：例「移動→発見→対話→手がかり」——展開リズムの固定化判定用）

■ Step 0 恒久版
-（世界の基本規則・制約・費用・例外。規則の出所と、本文での開示・機能を照合した範囲を分けて記録する）

■ スコア履歴（参照専用・証拠ではない）
-（章：軸別点数の記録。次回採点はこの数値に依存しない）
```

Rules:

- Update the ledger at every scoring session on a serialized work; an audit (`audit-mode.md`) both consumes and rewrites it.
- 未回収の期間だけから「引きの空手形」を認定しない。回収と途中の言及を分け、提示章末と直後2章の本文で言及・無視を確認する。本文不足なら確認候補として残し、キャップの適用は保留する。
- 記憶だけに依存し、出所へ追跡できない事実の断定は取り下げ、その変更を記す。出所は追跡できるが本文と未照合の著者資料は、出所付きの未照合項目として残してよい。本文と食い違った場合は、該当する引用と照合不一致を残す。
