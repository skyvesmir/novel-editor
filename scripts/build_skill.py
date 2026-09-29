#!/usr/bin/env python3
"""novel-editor.skill の再構築と整合検証（LLM不要・トークン消費ゼロ）。

使い方:
  python3 scripts/build_skill.py          # 検証し、zipがtreeとずれていれば再構築
  python3 scripts/build_skill.py --check  # 検証のみ（ずれていたら exit 1、書き換えない）

検証項目:
  1. zip の中身 == novel-editor/ tree（ファイル集合と SHA-256）
  2. zip の破損チェック（testzip）
  3. SKILL.md frontmatter: name / description の存在、description ≤ 1024 文字
  4. SKILL.md / references/*.md 内で言及された references/*.md が実在するか
"""
import hashlib
import io
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TREE = ROOT / "novel-editor"
ARCHIVE = ROOT / "novel-editor.skill"
DESC_LIMIT = 1024


def tree_files():
    # 配布対象は .md と scripts/*.py のみ（.DS_Store・__pycache__ 等の混入防止）
    return sorted(p for p in TREE.rglob("*") if p.is_file() and (p.suffix == ".md" or (p.suffix == ".py" and p.parent.name == "scripts")))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive_matches_tree():
    """(一致したか, 差分メッセージのリスト)"""
    if not ARCHIVE.exists():
        return False, ["novel-editor.skill が存在しない"]
    want = {p.relative_to(TREE).as_posix(): sha(p.read_bytes()) for p in tree_files()}
    problems = []
    with zipfile.ZipFile(ARCHIVE) as z:
        bad = z.testzip()
        if bad is not None:
            problems.append(f"zip破損: {bad}")
        have = {n: sha(z.read(n)) for n in z.namelist() if not n.endswith("/")}
    for name in sorted(set(want) | set(have)):
        if name not in have:
            problems.append(f"zipに無い: {name}")
        elif name not in want:
            problems.append(f"treeに無い（zipだけにある）: {name}")
        elif want[name] != have[name]:
            problems.append(f"内容が不一致: {name}")
    return not problems, problems


def check_frontmatter():
    problems = []
    text = (TREE / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return ["SKILL.md に frontmatter が無い"], None
    fm = m.group(1)
    if not re.search(r"^name:\s*\S", fm, re.M):
        problems.append("frontmatter に name が無い")
    d = re.search(r"^description:\s*(.*?)(?=^\w[\w-]*:|\Z)", fm, re.S | re.M)
    if not d:
        problems.append("frontmatter に description が無い")
        return problems, None
    desc = d.group(1).strip()
    if len(desc) > DESC_LIMIT:
        problems.append(f"description が {len(desc)} 文字（上限 {DESC_LIMIT}）")
    return problems, len(desc)


# skill 外（リポジトリ直下）を指すと分かっている言及。配布zipには入らないので存在チェック対象外
REPO_LEVEL_REFS = {"notes.md"}


def check_references():
    """`references/x.md` と素の `x.md`（バッククォート内）の両表記を検査する。"""
    problems = []
    existing = {p.relative_to(TREE).as_posix() for p in tree_files()}
    basenames = {Path(e).name for e in existing}
    for p in tree_files():
        for ref in set(re.findall(r"`([\w./-]+\.md)`", p.read_text(encoding="utf-8"))):
            if ref in REPO_LEVEL_REFS or ref.startswith("evals/"):
                continue
            ok = ref in existing if "/" in ref else ref in basenames
            if not ok:
                problems.append(f"{p.relative_to(TREE)} が存在しない {ref} を参照")
    return problems


def rebuild():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in tree_files():
            z.write(p, p.relative_to(TREE).as_posix())
    ARCHIVE.write_bytes(buf.getvalue())


def main():
    check_only = "--check" in sys.argv[1:]
    fm_problems, desc_len = check_frontmatter()
    ref_problems = check_references()
    ok, diff = archive_matches_tree()

    if not ok and not check_only:
        print("zip が tree とずれているため再構築します:")
        for line in diff:
            print("  -", line)
        rebuild()
        ok, diff = archive_matches_tree()

    print(f"files in tree : {len(tree_files())}")
    print(f"description   : {desc_len}/{DESC_LIMIT} 文字" if desc_len is not None else "description   : (取得不可)")
    print(f"archive sync  : {'OK' if ok else 'NG'}")
    for line in diff:
        print("  -", line)
    for line in fm_problems + ref_problems:
        print("  !", line)
    sys.exit(0 if ok and not fm_problems and not ref_problems else 1)


if __name__ == "__main__":
    main()
