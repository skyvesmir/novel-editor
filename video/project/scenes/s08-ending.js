// s08-ending：牽引力：章末の一文（拍 64〜72、8拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍64 f768 whoosh: 原稿の最後の1文。札「牽引力 5/10」 ／text「そう心に決めて、カイは目を閉じた。」(manuscript)
//   拍65 f780 slash: 最後の1文に赤線
//   拍68 f816 fall: 出力カードが落ちてくる（drop-in） ／text「…は最後に置かない。」(output:score)
//
// HF.scene("s08-ending", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
