---
name: review-skill
description: novel-editor/ の未コミット変更（なければ直近コミット）を skill-reviewer に査読させ、指摘と再実行すべき eval 番号を得る。
context: fork
agent: skill-reviewer
background: false
argument-hint: "[範囲の指定（任意）例: HEAD~3..HEAD]"
---

novel-editor/ の変更を査読してください。

- 範囲：$ARGUMENTS（空なら、未コミットの差分。それもなければ直近のコミット）
- あなたのエージェント定義にある検査項目 A〜G と、返答の形式に従うこと。
