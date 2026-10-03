// s15-outro：締め：題字・導入3手順・URL（拍 136〜160、24拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍136 f1632 title: 題字「novel-editor」と一言 ／text「novel-editor」(video)
//   拍140 f1680 stamp: 導入の手順（1つずつ積む） ／text「① 設定でコード実行をオン」(video)
//   拍142 f1704 stamp: 導入の手順（1つずつ積む） ／text「② novel-editor.skill をアップロード」(video)
//   拍144 f1728 stamp: 導入の手順（1つずつ積む） ／text「③ 原稿を貼って「厳しめで」」(video)
//   拍148 f1776 slam: URL ／text「github.com/skyvesmir/novel-editor」(video)
//   拍152 f1824 end: 最後の一撃。以降は題字とURLだけで止める（breathe）
//
// HF.scene("s15-outro", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
