// s09-fix3：今回直すのはこの3件（拍 72〜80、8拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍72 f864 slam: 出力の見出し ／text「今回直すのはこの3件」(output:score)
//   拍74 f888 stamp: 番号札の判子 ／text「改善案4」(output:score)
//   拍75 f900 stamp: 番号札の判子 ／text「改善案5」(output:score)
//   拍76 f912 stamp: 番号札の判子 ／text「改善案7」(output:score)
//
// HF.scene("s09-fix3", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
