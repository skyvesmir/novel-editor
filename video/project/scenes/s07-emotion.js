// s07-emotion：感情設計：即答の受諾（拍 56〜64、8拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍56 f672 whoosh: 原稿の受諾の台詞。札「感情設計 4.5/10」 ／text「「はい。行きます」」(manuscript)
//   拍57 f684 pen: 台詞に赤丸
//   拍59 f708 silence: 溜め：1拍
//   拍60 f720 stamp: 出力カード ／text「…頂点が即答で通過するため。」(output:score)
//
// HF.scene("s07-emotion", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
