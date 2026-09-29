---
name: run-evals
description: novel-editor の behavior evals を「生成役と判定役の分離方式」で実行し、結果を記録する。skill 本体を変更したあとの回帰確認に使う。
argument-hint: "[eval番号… | all]  例: 3 7 10"
---

# eval 実行手順

対象：$ARGUMENTS（指定がなければ、skill-reviewer が推奨した番号。それもなければユーザーに確認せず all ＝ 全件）

all はサブエージェントを約30体動かす重い処理になる。変更の影響範囲が分かっているときは、番号を絞る。

**モデル**：生成役の既定は `sonnet`（無料枠で使われる Sonnet。無料・有料どちらでも動く設計の最低ラインとして基準にする）。有料枠の挙動も確かめたいときだけ、同じ eval を Agent 呼び出しの `model: opus` で追加生成し、保存名に `-opus` を付ける。

## 1. 下ごしらえ（スクリプト。トークンはかからない）

```bash
python3 scripts/eval_prep.py prep <番号…>
```

- `evals/.work/evalNN-input.md` ができる。フィクスチャの注記（正解の手がかり）は自動で除かれる。
- 表示される「除去した注記」を目で確認する。ユーザーの発言として必要な文脈まで消えていたら、input に手で戻す。
- 「要手作業」と出た eval（#4、#6）は、表示された指示どおりに input へ前ターンを追記する。#6 は第1ターンを生成したあと、**fixture-writer** に提出文を `evals/.work/eval06-submission.md` として書かせ、第2ターン用の input を作る。

## 2. 生成（eval-generator）

eval ごとに **eval-generator** を1体ずつ呼ぶ。互いに独立しているので、3〜4体ずつ並列で動かしてよい。依頼文には次の3つだけを書く。

- 入力ファイル：`evals/.work/evalNN-input.md`
- 保存先：`evals/raw_outputs/evalNN-<name>.md`（既存のファイル名があれば上書きする）
- 日付：今日の日付

アサーション、期待される出力、eval の名前の意味を依頼文に書かない（ブラインドが崩れるため）。

## 3. 判定（eval-grader）

生成が終わった eval から、**eval-grader** に「eval 番号と出力ファイルのパス」を渡す。返ってきた表だけをメイン会話で受け取り、出力の本文は読まない（トークン節約）。

FAIL と要確認は、メインが出力の該当箇所だけを読んで再確認する。判定役の見立てをそのまま鵜呑みにしない。

## 3.5 引用の機械照合（スクリプト。トークンはかからない）

```bash
python3 novel-editor/scripts/check_quotes.py quotes evals/raw_outputs/evalNN-<name>.md evals/.work/evalNN-input.md
```

- 出力の「」がすべて入力（依頼文＋原稿）か skill の references にあるかを調べる。判定役の目視より確実なので、未照合の件数はこの結果を記録する。
- skill の規則名や、出力が自分で付けた見出し語も未照合に出ることがある。件数を記録するときは、原稿の引用として示しているもの（偽の引用）と、それ以外を分けて数える。

## 4. 記録

- `evals/results.md` に、実行日、対象、PASS 数、FAIL・要確認の内訳を追記する。
- `notes.md` には数値と手順の事実だけを書く（AGENTS.md のルール）。
- FAIL があれば、原因が skill 側か eval 側かを切り分けて、ユーザーに報告する。skill 側の修正は、この手順の中では行わない。

## 中断したとき

- 生成役の出力ファイルが途中で切れていたら、その eval だけ生成し直す。
- 3回続けて同じ eval が失敗したら、止めて状況を報告する。
