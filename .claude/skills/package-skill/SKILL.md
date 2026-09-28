---
name: package-skill
description: novel-editor.skill（配布用zip）を tree から再構築し、SHA-256一致・description長・参照切れを検証する。novel-editor/ を変更したら、コミット前に必ず使う。
---

# 配布zipの再構築と検証

```bash
python3 scripts/build_skill.py
```

- zip が tree とずれていれば、自動で再構築してから検証する。ずれていなければ何も書き換えない。
- `archive sync: OK` で、`!` の付いた行がなく、exit 0 なら完了。
- `!` の付いた行（参照切れ、description 超過など）があれば、原因を直してから再実行する。

検証だけを行う（書き換えない）場合：`python3 scripts/build_skill.py --check`

補足：コミット時には precommit フックが同じ検証を自動で行い、NG ならコミットを止める。
