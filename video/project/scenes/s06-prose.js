// s06-prose：文章：要約的な締めの一文×3（拍 48〜56、8拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍48 f576 whoosh: 原稿の3文と、出力の札（文章 5/10） ／text「要約的な締めの一文が3箇所ある」(output:score)
//   拍49 f588 slash: 該当の1文に赤丸→取り消し ／text「いつか父のような測量士になりたい、とカイは思った。」(manuscript)
//   拍50 f600 slash: 該当の1文に赤丸→取り消し ／text「本当に自分にできるのだろうか、と思った。」(manuscript)
//   拍51 f612 slash: 該当の1文に赤丸→取り消し ／text「ミアはいつも自分のことを心配してくれる、とカイは思った。」(manuscript)
//
// HF.scene("s06-prose", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
