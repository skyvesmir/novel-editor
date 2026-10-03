// s13-norewrite：書き換えない（拍 116〜124、8拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍116 f1392 slam: 動画の声 ／text「直すのは、誤字だけ。」(video)
//   拍120 f1440 whoosh: 出力カード（静かに置く） ／text「大事な原稿は人の目でも確かめてください。」(output:proof)
//
// HF.scene("s13-norewrite", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
