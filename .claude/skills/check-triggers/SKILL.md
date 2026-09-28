---
name: check-triggers
description: novel-editor の description が、trigger-evals の21件で正しく発火・非発火するかを検査する。description を変えたときに使う。
---

# 発火判定の検査

1. 正解ラベル抜きのクエリ一覧を作る。

   ```bash
   python3 scripts/eval_prep.py trigger
   ```

2. **trigger-judge** を1体呼ぶ。依頼文は「evals/.work/trigger-queries.md を判定して」だけでよい。ラベルや期待値は書かない。
3. 答え合わせをする。

   ```bash
   python3 scripts/eval_prep.py trigger-score
   ```

4. NG の行だけをユーザーに報告する。そのとき、description のどの語が効いたか・欠けていたかを推定して添える。

注意：これは claude.ai の実際の振り分けの近似にすぎない。最終確認は、claude.ai 上で数件を実際に投げて行う。
