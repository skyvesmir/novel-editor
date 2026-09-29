# AGENTS.md — novel-editor skill 開発リポジトリ

このリポジトリは日本語小説向け編集skill `novel-editor.skill`（claude.aiポータブル）を開発・検証する場。

## 構成

- `novel-editor/` — skill本体ツリー（SKILL.md + references/*.md 8ファイル + scripts/check_quotes.py）
- `novel-editor.skill` — 配布用zip。**tree変更後は必ず再構築し、SHA-256でtreeと一致を確認**
- `evals/evals.json` — eval定義 #1〜#15（アサーション計87件）
- `evals/trigger-evals.json` — description発火判定用クエリ21件
- `evals/fixtures/` — テスト原稿（オリジナル創作・著作権クリア）。判定側だけが読む設計意図は `<!-- JUDGE-ONLY:START … END -->` に入れる（生成側への入力から機械除去される）
- `evals/raw_outputs/` — eval実行の出力原文
- `evals/results.md` — eval実行の詳細ログ
- `notes.md` — セッション横断の事実記録（**本文引用・原稿テキストは書かない。数値と手順の事実のみ**）
- `scripts/build_skill.py` — zip再構築＋検証（SHA-256・description長・参照切れ）。`--check` で検証のみ
- `scripts/eval_prep.py` — eval入力の生成（フィクスチャの注記・JUDGE-ONLY＝正解の手がかりを除去）と発火判定の答え合わせ
- `tools/skill_lint.py` — 構造検査（条件表・上限規則・条項の保持・eval定義・入力の漏洩・キー混入、216項目）。**skillを編集したら走らせる**。検査を足したら、壊したコピーで検出できることを確かめる
- `tools/hook_ledger_scan.py` — 章末の引きの走査（シグナルのみ・判定しない）
- `docs/calibration-evidence.md` — 較正値の根拠と、統合時に各要素をどちらの系統から採ったか。`docs/history/` — 過去系統の作業記録
- `local/` — ユーザー供給原稿・台帳・監査作業の置き場（.gitignore済み）
- `.claude/` — Claude Code用のエージェント・手順・フック（運用は CLAUDE.md）

## 著作権ルール（厳守）

ユーザー供給の小説（Narō作品等）の分析はローカルでのみ行う。**GitHubには原稿テキスト・PDF・長文引用をコミットしない**。台帳やnotesには数値（字数・話数・密度・頻度）と手順の事実のみを記録する。原稿ファイルは必ず `local/` に置く。

## 検証コマンド

```bash
# アーカイブ整合確認
python3 - <<'EOF'
import zipfile, hashlib
with zipfile.ZipFile('novel-editor.skill') as z:
    print(all(hashlib.sha256(z.read(n)).hexdigest()==hashlib.sha256(open(f'novel-editor/{n}','rb').read()).hexdigest() for n in z.namelist()))
EOF
```

SKILL.mdのdescriptionは1024文字以内制限（現在972文字）。変更時は長さ確認。

```bash
python3 scripts/build_skill.py        # zip再構築＋検証
python3 tools/skill_lint.py --quiet   # 構造検査（exit 0 = 全通過）
```

## 設計目標（2026-09-29〜）

- **claude.ai の無料枠・有料枠のどちらでも動く**こと。無料枠は Sonnet（2026-09時点で Sonnet 5.5）で動くので、eval の基準モデルは Sonnet。skill の読み込み量も無料枠の負担になるため、配布ファイルに開発の経緯を書かない。
- Skill は Free〜Enterprise の全プランで使えるが、設定でコード実行をオンにする必要がある（公式ヘルプで確認済み）。

## 系統の統合（2026-09-29）

8/26 以降、作業は2系統に分かれていた：Genspark 系統（証拠の出所・保留・停止の規則 P1〜P5、eval #14・#15、構造lint）と、Qwen 系統（商業作品13作・5,950話の全数走査による閾値の較正）。**新しさではなく要素ごとの優劣で統合した**。採用元の一覧は `docs/calibration-evidence.md`。Qwen 系統の生の記録はAPIキーと作品本文の断片を含むため、リポジトリに入れていない（数値のみ要約）。

## 実績と学習済み事項（2026-08-24時点・統合前の旧版の記録）

- **evals #1〜#12 正式実行済み**: 当時の記録は 62/62 アサーション PASS。ただし当時の evals.json の #1〜#12 の定義数は59で（2026-09-29 に再計算）、記録の分母と一致しない。失敗の報告はない。trigger-evals 21/21整合。
- **監査モード(eval #13)ドライラン3作完了**: 出涸らし皇子(277万字765話)・状態異常スキル(234万字371話)・モンスターあふれる世界(120万字274話)。いずれもローカル完結。
- **区切り表記は作品ごとに異なる**: 第N話型／無番号タイトル行型／全角番号型／前書き後書き混在型。索引化前に様式確認→番号整合検証が必須(audit-mode.mdに明文化済み)。
- **機械走査↔精読の線引き**: 走査はシグナル収収のみ、判定は必ず精読+精読量宣言+反証探索(audit-mode.md「機械走査と精読の線引き」)。ファイルアクセス環境向けの手順付録もある。
- **尾フック率は作品内経時比較のみ有効**(作品間差0〜16%)。横断絶対アンカー禁止。

## eval実行ノウハウ

- サブエージェント生成+メイン判定の分離方式。アサーションは生成側に非開示。
- サブエージェントはskillファイルを実パスから読ませる（プロンプトへの全文貼付より確実）。
- 「要約だけ返す」問題は最終返答に出力本文そのものを要求するよう明示して回避。
- 割り込みで失われた出力は `/workspace/conversations/<id>/subagents/<hash>/events/event-*.json` から復旧可能(role:assistantのtext部分を抽出)。

## Phase状況

- A1(evals正式実行): **完了**
- A2(機械抽出手順の文書化): **完了**(audit-mode.md付録)
- C(正式監査・相対/絶対評価方針): 未着手——動機ができてから。尾フック率の方針決定(相対か絶対か)はPhase 3論点としてnotes.md記録済み。
- 改善案キャップの数え方明文化: **完了**(scoring-rubric.md)
