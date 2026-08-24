# AGENTS.md — novel-editor skill 開発リポジトリ

このリポジトリは日本語小説向け編集skill `novel-editor.skill`（claude.aiポータブル）を開発・検証する場。

## 構成

- `novel-editor/` — skill本体ツリー（SKILL.md + references/*.md 9ファイル構成）
- `novel-editor.skill` — 配布用zip。**tree変更後は必ず再構築し、SHA-256でtreeと一致を確認**
- `evals/evals.json` — eval定義 #1〜#13
- `evals/trigger-evals.json` — description発火判定用クエリ21件
- `evals/fixtures/fixtures.md` — テスト原稿（オリジナル創作・著作権クリア）
- `evals/raw_outputs/` — eval実行の出力原文
- `evals/results.md` — eval実行の詳細ログ
- `notes.md` — セッション横断の事実記録（**本文引用・原稿テキストは書かない。数値と手順の事実のみ**）

## 著作権ルール（厳守）

ユーザー供給の小説（Narō作品等）の分析はローカルでのみ行う。**GitHubには原稿テキスト・PDF・長文引用をコミットしない**。台帳やnotesには数値（字数・話数・密度・頻度）と手順の事実のみを記録する。

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

## 実績と学習済み事項（2026-08-24時点）

- **evals #1〜#12 正式実行済み**: 62/62アサーション PASS。trigger-evals 21/21整合。
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
