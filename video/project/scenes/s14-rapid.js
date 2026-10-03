// s14-rapid：連打 → 白フラッシュ（拍 124〜136、12拍）
// 担当が実装する。API は scenes/README.md。未登録のあいだは main.js が仮表示を出す。
// このシーンの cues（S.ev に t=時間軸の秒つきで入る）:
//   拍124 f1488 riser: 上昇の開始。拍131の頭で断ち切って無音へ（山＝切れ目） ／length_beats 7
//   拍124 f1488 slam: 全面色替え＋軸名（4分音符） ／text「構成」(output:score)
//   拍125 f1500 slam: 全面色替え＋軸名（4分音符） ／text「キャラクター」(output:score)
//   拍126 f1512 slam: 全面色替え＋軸名（4分音符） ／text「世界観」(output:score)
//   拍127 f1524 slam: 全面色替え＋軸名（4分音符） ／text「感情設計」(output:score)
//   拍128.0 f1536 slam: T7 連打（三連符＝4フレーム） ／text「牽引力」(output:score)
//   拍128.333333 f1540 slam: T7 連打（三連符＝4フレーム） ／text「独自性」(output:score)
//   拍128.666667 f1544 slam: T7 連打（三連符＝4フレーム） ／text「文章」(output:score)
//   拍131 f1572 silence: 溜め：1拍の無音
//   拍132 f1584 impact: 白フラッシュ（最大の一撃）→ 生成りへ
//
// HF.scene("s14-rapid", function (S) {
//   const { tl } = S, M = HF.M, UI = HF.ui;
//   S.html(`...`);
// });
