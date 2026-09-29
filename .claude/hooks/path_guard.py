#!/usr/bin/env python3
"""サブエージェント用 PreToolUse フック: 読み書きできるパスを許可リストで縛る。

eval の生成役がアサーション（evals/evals.json）や過去の判定・出力を覗けないようにする
「ブラインド」の機械的な担保。プロンプトでの指示が一次防衛、これは安全網。

使い方（エージェント frontmatter の hooks から呼ぶ）:
  path_guard.py --read novel-editor/ evals/.work/ --write evals/raw_outputs/
  （--write を省略すると書き込み系ツールはすべて拒否）

対象ツール: Read / Grep / Glob（読み取り）, Write / Edit（書き込み）,
Bash（skill 同梱の novel-editor/scripts/check_quotes.py の実行だけを許可。引数のパスも読み取り許可範囲内に限る）。
Grep/Glob で path 省略（＝リポジトリ全体の検索）は拒否する。
"""
import json
import os
import re
import shlex
import sys

READ_TOOLS = {"Read": "file_path", "Grep": "path", "Glob": "path"}
WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "NotebookEdit": "notebook_path"}


def parse_args(argv):
    allow, mode = {"read": [], "write": []}, None
    for a in argv:
        if a in ("--read", "--write"):
            mode = a[2:]
        elif mode:
            allow[mode].append(a)
    return allow


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))
    sys.exit(0)


def main():
    allow = parse_args(sys.argv[1:])
    data = json.load(sys.stdin)
    tool, args = data.get("tool_name", ""), data.get("tool_input", {}) or {}
    root = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")

    if tool == "Bash":
        cmd = args.get("command", "")
        if re.search(r"[;&|<>`$()\\\n]", cmd):
            deny("Bash ではシェルの記号を使えません。許可: python3 novel-editor/scripts/check_quotes.py quotes|count <ファイル>")
        parts = shlex.split(cmd)
        if parts[:2] != ["python3", "novel-editor/scripts/check_quotes.py"] or len(parts) < 4 or parts[2] not in ("quotes", "count"):
            deny("Bash で実行できるのは python3 novel-editor/scripts/check_quotes.py quotes|count <ファイル> だけです")
        for f in parts[3:]:
            fp = os.path.realpath(os.path.join(root, f))
            if not any(fp.startswith(os.path.realpath(os.path.join(root, b)).rstrip("/") + "/") for b in allow["read"] + allow["write"]):
                deny(f"check_quotes.py に渡せるのは許可範囲内のファイルだけです: {f}")
        sys.exit(0)

    if tool in READ_TOOLS:
        kind, key = "read", READ_TOOLS[tool]
    elif tool in WRITE_TOOLS:
        kind, key = "write", WRITE_TOOLS[tool]
    else:
        sys.exit(0)  # 対象外のツールは素通し

    target = args.get(key)
    if not target:
        deny(f"{tool} はパス指定が必須です（リポジトリ全体の検索は禁止）。許可: {', '.join(allow[kind]) or 'なし'}")
    path = os.path.realpath(target if os.path.isabs(target) else os.path.join(root, target))
    # Glob の pattern に絶対パスやディレクトリを書いて抜ける経路も塞ぐ
    extra = args.get("pattern", "") if tool == "Glob" else ""
    if extra.startswith("/") or ".." in extra.split("/"):
        deny("Glob の pattern に絶対パスや .. は使えません")

    for prefix in allow[kind]:
        base = os.path.realpath(os.path.join(root, prefix))
        if path == base or path.startswith(base.rstrip("/") + "/"):
            sys.exit(0)
    rel = os.path.relpath(path, root)
    deny(f"このエージェントは {rel} を{'読め' if kind == 'read' else '書け'}ません。"
         f"許可: {', '.join(allow[kind]) or 'なし'}")


if __name__ == "__main__":
    main()
