// s12-typos：誤字5件（拍 96〜116、20拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍96 f1152 slash: 原稿の該当箇所「見慣れた後継だった。」の語に取り消し線。種類の札「誤変換」 ／text「後継」(manuscript)
//   拍98 f1176 pen: 赤ペンで正しい形を書き込む（Klee One・scribble） ／text「光景」(output:proof)
//   拍100 f1200 slash: 原稿の該当箇所「学院で受けた測量術の抗議では」の語に取り消し線。種類の札「誤変換」 ／text「抗議」(manuscript)
//   拍102 f1224 pen: 赤ペンで正しい形を書き込む（Klee One・scribble） ／text「講義」(output:proof)
//   拍104 f1248 slash: 原稿の該当箇所「「ありがとうござます」」の語に取り消し線。種類の札「脱字」 ／text「ござます」(manuscript)
//   拍106 f1272 pen: 赤ペンで正しい形を書き込む（Klee One・scribble） ／text「ございます」(output:proof)
//   拍108 f1296 slash: 原稿の該当箇所「秋の短かい日」の語に取り消し線。種類の札「誤字（送り仮名）」 ／text「短かい」(manuscript)
//   拍110 f1320 pen: 赤ペンで正しい形を書き込む（Klee One・scribble） ／text「短い」(output:proof)
//   拍112 f1344 slash: 原稿の該当箇所「微笑んだ／ほほえんだ」の語に取り消し線。種類の札「表記ゆれ」 ／text「微笑んだ／ほほえんだ」(manuscript)
//   拍114 f1368 pen: 赤ペンで正しい形を書き込む（Klee One・scribble） ／text「どちらかに統一」(output:proof)
//
// HF.scene("s12-typos", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
