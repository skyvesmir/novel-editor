# Eval notes

## 2026-08-24 — evals added to archive

`evals.json`（11 cases）と `trigger-evals.json`（19 queries）が SKILL.md の参照先
（`evals/evals.json`, `evals/trigger-evals.json`）として初めてアーカイブに収められた。

追加前に参照ファイルとの整合性を機械的に確認した結果：

- JSON は両方とも妥当（11 evals / 19 trigger queries）。
- #1 単章採点 ↔ scoring-rubric.md「単章：牽引力は判定対象外・一行で明記」「総合点禁止」「改善案10件以下＋優先3件」— 一致。
- #2 連作一章（設計資料なし）↔ rubric の暫定判定指示、構成8点条件・感情設計クライマックス条件の作品スケール保留、牽引力の回収判定保留 — 一致。
- #7 未回収の引き ↔ score-anchors.md 上限規則「引きの空手形」＝牽引力6上限 — 一致。
- #8 引きの多様性と回収 ↔ 牽引力8点条件（性質の異なる手法3種以上＋後続章での回収）— 一致。
- #9 AI的紋切り型 ↔ prose-diagnostics.md の悪例（「手が震えた」「その瞬間，〜だと悟った」）と逐語一致。上限規則「AI的紋切り型の反復」＝文章6上限も一致。
- #10/#11 誤字チェックモード ↔ proofreading-mode.md の出力形式・「該当箇所なし」規則 — 一致。
- trigger-evals の should-not-trigger 群（新規小説の執筆依頼、ビジネス文書、校正なし翻訳等）は description の適用範囲と矛盾しない。

未解決事項：

- evals はまだ実行されていない。expected_output / assertions に対する実測は次回チェック時に記録すること。

## 運用メモ

- evals を更新したらこのファイルに日付と変更内容を記す。
- 実行して失敗した場合は、どの assertion が落ちたかを eval id 付きで記録する。
