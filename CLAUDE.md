@AGENTS.md

<!-- 保守メモ（HTMLコメントは読み込み時に除去されトークンを消費しない）:
     共通ルールは AGENTS.md（他ツールと共有）に書き、このファイルには Claude Code 固有の運用だけを書く。
     CLAUDE.md を置くと AGENTS.md は自動では読まれなくなるため、先頭の @AGENTS.md は消さないこと。
     合計200行以内を維持する（公式推奨）。 -->

## Claude Code での進め方

### 役割分担（`.claude/agents/`・`.claude/skills/`）

| やること | 呼び出し | 担当（モデル／effort） |
|---|---|---|
| skill本体の変更を査読 | `/review-skill` | skill-reviewer（opus／high） |
| 回帰確認（evals #1〜#15） | `/run-evals 3 7` | eval-generator（sonnet／medium）→ eval-grader（opus／high） |
| description の発火確認 | `/check-triggers` | trigger-judge（opus／low） |
| 配布zipの再構築・検証 | `/package-skill` | スクリプトのみ（LLM不要） |
| 長編原稿の機械走査 | audit-scanner に依頼 | sonnet／medium |
| テスト原稿の作成 | fixture-writer に依頼 | opus／medium |

この skill は claude.ai の無料枠・有料枠のどちらでも動くことを目標にする。eval-generator は無料枠で使われる Sonnet（`sonnet` = 最新の Sonnet）を基準にし、有料枠の確認が要るときだけ opus でも回す。skill の読み込み量（採点1回あたりのトークン）も無料枠の負担になるので、配布ファイルに開発の経緯を書かない（経緯は `docs/calibration-evidence.md`）。

### 標準フロー（skill本体を変えたとき）

1. 変更 → 2. `/review-skill` → 🔴 を直す → 3. `/package-skill` → 4. 推奨された eval だけ `/run-evals` → 5. description を変えたなら `/check-triggers` → 6. commit・push

### トークン節約の約束

- 決定的な作業（zip、検証、eval 入力づくり、発火の答え合わせ）は `scripts/` のスクリプトで行い、LLM に読ませない。
- eval 出力の本文はメイン会話に持ち込まない。生成役がファイルに保存し、判定役は表だけを返す。
- 大量の出力が出る作業（原稿の走査、長いログ）はサブエージェントに任せ、メインは結論だけを受け取る。
- モデルは作業の途中で切り替えない（キャッシュが全部作り直しになる）。effort は Opus 5.5 ならキャッシュを保ったまま変えられる。
- メインは Opus 5.5・medium が基本。詰まったら high、同じ所で2回詰まったら上位モデルに切り替え、解決したら戻す。
- 環境変数 `CLAUDE_CODE_EFFORT_LEVEL` は設定しない。各エージェントの effort 指定より優先されてしまう。
- 無関係な作業に移るときは `/clear`。区切りでは `/compact`（下記の方針で要約される）。

### 安全装置（`.claude/settings.json` のフック）

- `git commit` の直前に `.claude/hooks/precommit_guard.py` が走り、次の場合はコミットを止める：原稿系ファイル（`local/`、.pdf、.epub、.docx、.txt、300KB超のファイル）が含まれる／zip と tree がずれている／description が1024字を超えている。
- eval の生成役は、フック（`path_guard.py`）でアサーションや過去の出力を読めないようにしてある。

# Compact instructions

要約するときは、次を必ず残す：進行中のタスクとフェーズ、実行した eval の番号と PASS/FAIL 数、変更したファイルと zip 再構築の有無、ユーザーの判断待ちの論点、著作権上の制約。次は捨ててよい：eval 出力の本文、原稿テキスト、ツールのログ。
