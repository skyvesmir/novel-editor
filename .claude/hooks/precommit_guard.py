#!/usr/bin/env python3
"""PreToolUse(Bash) フック: git commit の直前に3点を機械チェックし、違反なら止める。

1. 著作権: 原稿系ファイル（.pdf/.epub/.docx/.txt）、local/ 配下、300KB超のファイルが
   コミット対象に入っていないか（`git add -f` で .gitignore をすり抜けた場合も捕まえる）
2. skill 同期: novel-editor/ tree と novel-editor.skill の中身が一致しているか
3. SKILL.md の description が 1024 文字以内か
4. 構造検査（tools/skill_lint.py）が全件通るか

`git add ... && git commit` の1コマンド実行にも対応するため、ステージ済みだけでなく
未ステージの変更・未追跡ファイル（.gitignore 対象外）も検査対象に含める（保守的判定）。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BLOCK_EXT = {".pdf", ".epub", ".docx", ".txt"}
BLOCK_DIRS = ("local/",)
MAX_BYTES = 300_000


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout


def main():
    data = json.load(sys.stdin)
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not re.search(r"\bgit\b[^;&|]*\bcommit\b", cmd):
        sys.exit(0)
    root = Path(git("rev-parse", "--show-toplevel", cwd=data.get("cwd") or ".").strip() or ".")

    names = set(git("diff", "--cached", "--name-only", cwd=root).split("\n"))
    if re.search(r"\bgit\b[^;&|]*\badd\b", cmd) or re.search(r"\bcommit\b[^;&|]*\s(-\w*a|--all\b)", cmd):
        names |= set(git("diff", "--name-only", cwd=root).split("\n"))
        names |= set(git("ls-files", "--others", "--exclude-standard", cwd=root).split("\n"))
    names.discard("")

    problems = []
    for n in sorted(names):
        p = root / n
        if Path(n).suffix.lower() in BLOCK_EXT or n.startswith(BLOCK_DIRS):
            problems.append(f"原稿系ファイルはコミット禁止（AGENTS.md 著作権ルール）: {n}")
        elif p.is_file() and p.stat().st_size > MAX_BYTES:
            problems.append(f"{MAX_BYTES // 1000}KB 超のファイル（原稿混入の疑い）: {n}")

    if any(n.startswith("novel-editor/") or n == "novel-editor.skill" for n in names):
        r = subprocess.run([sys.executable, str(root / "scripts" / "build_skill.py"), "--check"],
                           cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("skill 検証 NG → `python3 scripts/build_skill.py` で再構築・確認してから commit:\n"
                            + r.stdout.strip())

    # 構造検査（条件表・上限規則・条項の保持・eval 定義・入力の漏洩・キー混入）
    lint = root / "tools" / "skill_lint.py"
    if lint.exists() and any(n.startswith(("novel-editor/", "evals/", "scripts/", "tools/")) for n in names):
        r = subprocess.run([sys.executable, str(lint), "--quiet"], cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("構造検査 NG（`python3 tools/skill_lint.py --quiet`）:\n" + r.stdout.strip()[-1500:])

    if problems:
        print("commit を止めました:\n- " + "\n- ".join(problems), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
