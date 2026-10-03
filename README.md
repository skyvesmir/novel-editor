# novel-editor — 日本語小説のための厳格編集skill

claude.aiにポータブルな形で動く、日本語小説専用の編集AI skillです。商業出版水準の編集者として、採点・訓練・校正・作品規模監査の4つのモードで原稿を扱います。

## 何ができるか

| モード | 用途 | 出力 |
|---|---|---|
| **採点モード** | 章・改稿版・プロット・設定資料の評価 | 7軸(構成/キャラクター/世界観/感情設計/牽引力/独自性/文章)の達成条件判定。総合点は出さない |
| **訓練モード** | 表現力ドリル | 200〜300字のお題+制約2〜3個→提出文を✕→分析→○形式で添削 |
| **誤字チェックモード** | 誤字・脱字・誤変換・表記ゆれの機械的指摘 | 指摘リストのみ(書き直し・採点なし) |
| **監査モード** | 100万字級・複数巻の作品全体評価 | 作品台帳+作品スケール条件の確定/保留/覆し判定 |

## 設計思想

このskillの核心は**点数インフレの防止**です。長い会話では「お世話になっているので点数が上がる」ドリフトが必ず起きます。だから:

- すべての点数は`score-anchors.md`の達成条件表から**引用付きで**再導出される(前回の点数は証拠にならない)
- 条件を満たさないなら、著者がどれだけ頑張っても点数は上がらない
- 「上位X%」のような相対ランキングは禁止(測定された分布がないため)
- 感情的賛辞(すごい・傑作)も禁止——改善に使えない情報だから

逆に言えば、**条件を満たす引用を本文中に作れば確実に点数は上がります**。何を直せば数字が動くのかが常に見えるのがこのskillの売りです。

## 使い方(claude.ai)

無料プラン・有料プランのどちらでも使えます(無料プランでは Sonnet で動きます)。**事前に「設定 → Capabilities」でコード実行をオンにしてください**(skill 機能の前提条件です)。

1. claude.aiの「カスタマイズ」を押す
2. スキルを選択
3. 追加を押し、アップロードを選ぶ
4. skill機能がある環境なら `novel-editor.skill` をzipのままアップロード
5. 原稿と依頼(例:「第3章を厳しく採点して」)を送る。連載の一章なら「単独でも掲載するか」も書いておくと、確認の質問が省けます(書いていない場合は、連作の一章として採点しつつ確認の質問が添えられます)

### 注意事項

- **引用の照合で使用量が増えます。** 講評に出す「」(原稿の引用)と字数は、同梱の `scripts/check_quotes.py` で原稿と機械照合してから出します。講評をいったん下書きとして書き出すため、1回あたりの出力が最大2倍近くになり、無料プランの利用上限に早く届くことがあります。
- **照合は確実ではありません。** モデルが照合の手順を飛ばすことがあります。照合しなかった講評(コード実行が使えない環境を含む)には、末尾に「引用・字数は機械照合していない」と書かれます。この1行がある講評の「」は、原稿と見比べてから使ってください。
- **誤字チェックは全数を保証しません。** 同じ読みの別の語でも文が通ってしまう取り違え（変換で別の熟語になったもの）は、見落とすことがあります。誤字チェックの出力の最後にもその旨が一行添えられます。大事な原稿は人の目でも確かめてください。
- **採点は編集判断の補助です。** 条件表に基づく判定でも読み違いは起こりえます。気になる判定は、根拠の引用を原稿で確かめてください。
- **Claude 以外のサービスで使う場合**: 下の「ポータブル利用」のファイルを貼れば動きます。コードを実行できない環境では照合が行われないため、上の1行が付きます。

### ポータブル利用(必要最小限のファイルセット)

| 目的 | 貼るファイル |
|---|---|
| 採点 | SKILL.md + scoring-rubric.md + score-anchors.md + prose-diagnostics.md + hook-techniques.md |
| 訓練 | SKILL.md + expression-training.md |
| 誤字チェック | SKILL.md + proofreading-mode.md |
| 監査 | SKILL.md + audit-mode.md + score-anchors.md + handoff-format.md + prose-diagnostics.md |

すべて `novel-editor/references/` 配下にあります。参照先ファイルが足りない場合は、記憶で補完せず「このファイルが足りない」と伝える仕様になっています。

## 長編連載での使い方(台帳システム)

連載が3章を超えると、セッションごとに「作品台帳」が更新されます:

```
【作品台帳】
■ 人物レジスタ(名前/役割/現在状態)
■ 引き台帳(開いた場所/分類/回収状況)
■ 弧骨格(場面手順の並び)
■ Step 0恒久版(世界規則)
■ スコア履歴(参照専用)
```

これを次のセッションに貼れば、前章までの事実を踏まえた採点ができます。スレッドが長くなってきたら「引き継ぎデータちょうだい」でOK。

## 開発者向け

### リポジトリ構成

```
novel-editor/          skill本体(Skill.json相当のSKILL.md + references/)
novel-editor.skill     配布用zip(treeとSHA-256一致を保つこと)
evals/
  evals.json           eval定義15件・87項目(#1〜#12挙動/#13監査/#14歯止め/#15掲載形態)
  trigger-evals.json   description発火テスト21件
  fixtures/            テスト原稿(オリジナル創作)
  raw_outputs/         eval実行の出力原文
  results.md           eval実行ログ
scripts/               zip再構築・eval入力づくり
tools/                 構造検査(skill_lint.py)・引きの走査
docs/                  較正値の根拠(calibration-evidence.md)と過去系統の記録(history/)
notes.md               セッション横断の事実記録
HANDOFF.md             セッション引き継ぎデータ
AGENTS.md              AIエージェント向けリポジトリ情報
CLAUDE.md              Claude Code での運用ルール
```

### 検証コマンド

```bash
# アーカイブ整合確認(zipの中身==tree)
python3 - <<'EOF'
import zipfile, hashlib
with zipfile.ZipFile('novel-editor.skill') as z:
    print(all(hashlib.sha256(z.read(n)).hexdigest()==hashlib.sha256(open(f'novel-editor/{n}','rb').read()).hexdigest() for n in z.namelist()))
EOF

# zip整合性
python3 -c "import zipfile; print(zipfile.ZipFile('novel-editor.skill').testzip() is None)"
```

SKILL.mdのdescriptionは1024文字以内という制約があります(現在972文字)。変更時は長さ確認を。

### eval再実行の方法

1. `evals/fixtures/fixtures.md` の該当フィクスチャを取り出す
2. skill本体(novel-editor/)を読めるエージェント環境で、「skill読んだ前提でこのプロンプトに答えて」とサブエージェントに投げる(**アサーションは生成側に渡さない**)
3. 出力原文を `evals/raw_outputs/evalNN-*.md` に保存
4. `evals/evals.json` の assertions と照合して pass/fail 判定
5. 結果を `evals/results.md` と `notes.md` に追記してコミット

詳細なノウハウ(出力復旧方法等)は AGENTS.md 参照。

### Claude Code での開発(自動化済み)

Claude Code では上記の手順がコマンド化されています(設定は `.claude/`、運用ルールは `CLAUDE.md`)。

| コマンド | 内容 |
|---|---|
| `/review-skill` | skill本体の変更を査読し、再実行すべきeval番号を出す |
| `/package-skill` | zip再構築＋検証(`python3 scripts/build_skill.py` と同じ) |
| `/run-evals 3 7` | 指定evalを生成役・判定役の分離方式で実行(入力の注記除去は自動) |
| `/check-triggers` | description発火テスト21件 |

`git commit` 時には、原稿ファイルの混入・zipのずれ・description超過をフックが自動で止めます。

### 変更時のチェックリスト

- [ ] reference file変更 → novel-editor.skill 再構築+SHA-256照合
- [ ] SKILL.md description変更 → 1024文字以内確認
- [ ] 採点ルール変更 → `python3 tools/skill_lint.py --quiet` → 影響する eval を Sonnet で再実行(`/run-evals`)
- [ ] notes.md に事実を追記(GitHubには数値のみ・本文引用禁止)

## 著作権ポリシー

ユーザー供給の小説(公開中のNarō作品を含む)の分析はローカル環境でのみ行う。**GitHubには原稿テキスト・PDF・長文引用をコミットしない**。台帳やnotesには数値(字数・話数・密度・頻度)と手順の事実のみを記録する。テスト用のフィクスチャはオリジナル創作に限る。

## 現在の状態と次の課題

- 段階：仕上げ。Genspark 系統と Qwen 系統を要素ごとに統合した版（2026-09-29）
- evals #1〜#15（87項目）：統合版の通し実行で 81/87 PASS・FAIL 0（Sonnet、2026-09-29）。残った要確認6件を規則側で手当てし、再実行後の最新値は 85/87・FAIL 0（2026-09-30）
- 監査モード：完結3作（765/371/274話）でドライラン検証済み。パイプラインは動くが、正式監査の水準には未達
- 次の課題：実原稿での試用（点数が原稿の良し悪しに合うかの確認）、eval のばらつきの測定、claude.ai 本番での動作確認
- 暫定のままの較正値：`docs/calibration-evidence.md` の「暫定のまま」を参照

詳細は HANDOFF.md を参照。
