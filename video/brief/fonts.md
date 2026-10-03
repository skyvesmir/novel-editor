# 採用フォント（`video/tools/fetch_fonts.py` が生成）

確認に使った文字：`video/brief/*.md` に出てくる非 ASCII 文字 862 種。

| 書体 | ファイル | ウェイト | ライセンス | 役割 | 欠けた字 |
|---|---|---|---|---|---|
| Dela Gothic One | `video/assets/fonts/DelaGothicOne/DelaGothicOne-400.ttf` | 400 | OFL | 叩きつけ見出し・数字 | ✓✗＋ |
| Shippori Mincho B1 | `video/assets/fonts/ShipporiMinchoB1/ShipporiMinchoB1-400.ttf` | 400 | OFL | 原稿の本文・出力カード | ↔✓✗ |
| Shippori Mincho B1 | `video/assets/fonts/ShipporiMinchoB1/ShipporiMinchoB1-700.ttf` | 700 | OFL | 原稿の本文・出力カード | ↔✓✗ |
| Klee One | `video/assets/fonts/KleeOne/KleeOne-600.ttf` | 600 | OFL | 赤ペンの書き込み | ✓✗ |
| Zen Kaku Gothic New | `video/assets/fonts/ZenKakuGothicNew/ZenKakuGothicNew-500.ttf` | 500 | OFL | UI・小さな補足 | ↔✓✗ |
| Zen Kaku Gothic New | `video/assets/fonts/ZenKakuGothicNew/ZenKakuGothicNew-900.ttf` | 900 | OFL | UI・小さな補足 | ↔✓✗ |

Noto Sans JP（`video/assets/fonts/NotoSansJP.ttf`、可変・OFL）は試作で使用済み。
欠けた字がある書体でその字を出す場面は、同じ役割の別書体に落とさず、文言か書体を変える。
