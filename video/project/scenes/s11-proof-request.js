// s11-proof-request：校正の依頼（実際の依頼文）（拍 88〜96、8拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍88 f1056 drop: T1 全面色替え（青）。チャットの吹き出し ／text「誤字脱字だけチェックしてください。書き換えはいらないです。」(input)
//   拍88.5 f1062 type: 吹き出しの文字送り
//   拍89 f1068 type: 吹き出しの文字送り
//   拍89.5 f1074 type: 吹き出しの文字送り
//   拍90 f1080 type: 吹き出しの文字送り
//   拍92 f1104 pen: 「書き換えはいらない」に赤線 ／text「書き換えはいらない」(input)
//
// HF.scene("s11-proof-request", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
