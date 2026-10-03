// 生成物（tools/build.mjs）。編集しない。正本は video/brief/cues.json
window.CUES = {
 "bpm": 150,
 "beatsPerBar": 4,
 "fps": 30,
 "width": 1920,
 "height": 1080,
 "seconds_per_beat": 0.4,
 "frames_per_beat": 12,
 "duration_beats": 160,
 "duration_seconds": 64,
 "scenes": [
  {
   "id": "s01-hook",
   "startBeat": 0,
   "lengthBeats": 16,
   "purpose": "掴み「刺す」：冒頭の設定説明を赤ペンで刺し、掴みなしの判定を叩きつける"
  },
  {
   "id": "s02-title",
   "startBeat": 16,
   "lengthBeats": 8,
   "purpose": "題字"
  },
  {
   "id": "s03-request",
   "startBeat": 24,
   "lengthBeats": 8,
   "purpose": "採点の依頼（実際の依頼文）"
  },
  {
   "id": "s04-axes",
   "startBeat": 32,
   "lengthBeats": 8,
   "purpose": "7軸の点数"
  },
  {
   "id": "s05-rule",
   "startBeat": 40,
   "lengthBeats": 8,
   "purpose": "点の動かし方の原則"
  },
  {
   "id": "s06-prose",
   "startBeat": 48,
   "lengthBeats": 8,
   "purpose": "文章：要約的な締めの一文×3"
  },
  {
   "id": "s07-emotion",
   "startBeat": 56,
   "lengthBeats": 8,
   "purpose": "感情設計：即答の受諾"
  },
  {
   "id": "s08-ending",
   "startBeat": 64,
   "lengthBeats": 8,
   "purpose": "牽引力：章末の一文"
  },
  {
   "id": "s09-fix3",
   "startBeat": 72,
   "lengthBeats": 8,
   "purpose": "今回直すのはこの3件"
  },
  {
   "id": "s10-drill",
   "startBeat": 80,
   "lengthBeats": 8,
   "purpose": "練習の題"
  },
  {
   "id": "s11-proof-request",
   "startBeat": 88,
   "lengthBeats": 8,
   "purpose": "校正の依頼（実際の依頼文）"
  },
  {
   "id": "s12-typos",
   "startBeat": 96,
   "lengthBeats": 20,
   "purpose": "誤字5件"
  },
  {
   "id": "s13-norewrite",
   "startBeat": 116,
   "lengthBeats": 8,
   "purpose": "書き換えない"
  },
  {
   "id": "s14-rapid",
   "startBeat": 124,
   "lengthBeats": 12,
   "purpose": "連打 → 白フラッシュ"
  },
  {
   "id": "s15-outro",
   "startBeat": 136,
   "lengthBeats": 24,
   "purpose": "締め：題字・導入3手順・URL"
  }
 ],
 "events": [
  {
   "beat": 0,
   "frame": 0,
   "scene": "s01-hook",
   "kind": "slash",
   "visual": "1フレーム目から生成りの紙に冒頭3文が表示済み。1文目に取り消し線＋shake",
   "text": "このアルセリオ大陸には、七つの王国と三つの自由都市がある。",
   "text_source": "manuscript"
  },
  {
   "beat": 1,
   "frame": 12,
   "scene": "s01-hook",
   "kind": "slash",
   "visual": "2文目に取り消し線",
   "text": "かつて大陸全土を治めた古代魔導帝国が千年前に滅びてから、人々は帝国の残した魔導遺構を掘り起こし、その力を分け合うことで暮らしてきた。",
   "text_source": "manuscript"
  },
  {
   "beat": 2,
   "frame": 24,
   "scene": "s01-hook",
   "kind": "slash",
   "visual": "3文目に取り消し線",
   "text": "魔導遺構から取り出される魔石は灯りにも武器にもなり、王国同士の争いの火種にもなった。",
   "text_source": "manuscript"
  },
  {
   "beat": 3,
   "frame": 36,
   "scene": "s01-hook",
   "kind": "silence",
   "visual": "溜め：赤ペンが持ち上がる。画面はほぼ静止（微動のみ）"
  },
  {
   "beat": 4,
   "frame": 48,
   "scene": "s01-hook",
   "kind": "stamp",
   "visual": "巨大な赤い判子。4拍止める",
   "text": "冒頭の掴み：提示なし。",
   "text_source": "output:score"
  },
  {
   "beat": 8,
   "frame": 96,
   "scene": "s01-hook",
   "kind": "slam",
   "visual": "T1 全面色替え（黄）＋叩きつけ",
   "text": "疑問",
   "text_source": "output:score"
  },
  {
   "beat": 9,
   "frame": 108,
   "scene": "s01-hook",
   "kind": "slam",
   "visual": "T1 全面色替え（青）＋叩きつけ",
   "text": "異常",
   "text_source": "output:score"
  },
  {
   "beat": 10,
   "frame": 120,
   "scene": "s01-hook",
   "kind": "slam",
   "visual": "T1 全面色替え（墨）＋叩きつけ",
   "text": "危機",
   "text_source": "output:score"
  },
  {
   "beat": 11,
   "frame": 132,
   "scene": "s01-hook",
   "kind": "silence",
   "visual": "溜め：1拍"
  },
  {
   "beat": 12,
   "frame": 144,
   "scene": "s01-hook",
   "kind": "stamp",
   "visual": "赤い判子＋shake。ここが最初の山（ドロップ）",
   "text": "…を示す箇所を引用できない。",
   "text_source": "output:score",
   "accent": "drop"
  },
  {
   "beat": 16,
   "frame": 192,
   "scene": "s02-title",
   "kind": "impact",
   "visual": "T3 硬い切りで墨の画面。題字を叩きつけ",
   "text": "novel-editor",
   "text_source": "video"
  },
  {
   "beat": 18,
   "frame": 216,
   "scene": "s02-title",
   "kind": "slam",
   "visual": "題字の下に一言",
   "text": "その1話、投稿する前に。",
   "text_source": "video"
  },
  {
   "beat": 24,
   "frame": 288,
   "scene": "s03-request",
   "kind": "whoosh",
   "visual": "T3 硬い切りで生成り。チャットの吹き出しが入る",
   "text": "これ、来週なろうに投稿する予定の1話です。厳しめで評価してください。",
   "text_source": "input",
   "accent": "halftime"
  },
  {
   "beat": 24.5,
   "frame": 294,
   "scene": "s03-request",
   "kind": "type",
   "visual": "吹き出しの文字が打たれていく（文字送り）"
  },
  {
   "beat": 25,
   "frame": 300,
   "scene": "s03-request",
   "kind": "type",
   "visual": "吹き出しの文字が打たれていく（文字送り）"
  },
  {
   "beat": 25.5,
   "frame": 306,
   "scene": "s03-request",
   "kind": "type",
   "visual": "吹き出しの文字が打たれていく（文字送り）"
  },
  {
   "beat": 26,
   "frame": 312,
   "scene": "s03-request",
   "kind": "type",
   "visual": "吹き出しの文字が打たれていく（文字送り）"
  },
  {
   "beat": 26.5,
   "frame": 318,
   "scene": "s03-request",
   "kind": "type",
   "visual": "吹き出しの文字が打たれていく（文字送り）"
  },
  {
   "beat": 27,
   "frame": 324,
   "scene": "s03-request",
   "kind": "type",
   "visual": "吹き出しの文字が打たれていく（文字送り）"
  },
  {
   "beat": 28,
   "frame": 336,
   "scene": "s03-request",
   "kind": "pen",
   "visual": "「厳しめで」に赤丸",
   "text": "厳しめで",
   "text_source": "input"
  },
  {
   "beat": 32,
   "frame": 384,
   "scene": "s04-axes",
   "kind": "drop",
   "visual": "グルーヴに戻る。7軸の枠が並ぶ（数字はまだ空）",
   "accent": "groove"
  },
  {
   "beat": 32,
   "frame": 384,
   "scene": "s04-axes",
   "kind": "tick",
   "visual": "構成の数字が count-up して着地（pop）",
   "text": "構成",
   "text_source": "output:score",
   "score": "5",
   "pitch_step": 0
  },
  {
   "beat": 33,
   "frame": 396,
   "scene": "s04-axes",
   "kind": "tick",
   "visual": "キャラクターの数字が count-up して着地（pop）",
   "text": "キャラクター",
   "text_source": "output:score",
   "score": "5",
   "pitch_step": 1
  },
  {
   "beat": 34,
   "frame": 408,
   "scene": "s04-axes",
   "kind": "tick",
   "visual": "世界観の数字が count-up して着地（pop）",
   "text": "世界観",
   "text_source": "output:score",
   "score": "5",
   "pitch_step": 2
  },
  {
   "beat": 35,
   "frame": 420,
   "scene": "s04-axes",
   "kind": "tick",
   "visual": "感情設計の数字が count-up して着地（pop）",
   "text": "感情設計",
   "text_source": "output:score",
   "score": "4.5",
   "pitch_step": 3
  },
  {
   "beat": 36,
   "frame": 432,
   "scene": "s04-axes",
   "kind": "tick",
   "visual": "牽引力の数字が count-up して着地（pop）",
   "text": "牽引力",
   "text_source": "output:score",
   "score": "5",
   "pitch_step": 4
  },
  {
   "beat": 37,
   "frame": 444,
   "scene": "s04-axes",
   "kind": "tick",
   "visual": "独自性の数字が count-up して着地（pop）",
   "text": "独自性",
   "text_source": "output:score",
   "score": "5",
   "pitch_step": 5
  },
  {
   "beat": 38,
   "frame": 456,
   "scene": "s04-axes",
   "kind": "tick",
   "visual": "文章の数字が count-up して着地（pop）",
   "text": "文章",
   "text_source": "output:score",
   "score": "5",
   "pitch_step": 6
  },
  {
   "beat": 39,
   "frame": 468,
   "scene": "s04-axes",
   "kind": "silence",
   "visual": "溜め：7つの数字が並んだまま1拍"
  },
  {
   "beat": 40,
   "frame": 480,
   "scene": "s05-rule",
   "kind": "stamp",
   "visual": "出力カード。明朝。判子のように置く",
   "text": "点は達成条件と引用でのみ動く。",
   "text_source": "output:score"
  },
  {
   "beat": 44,
   "frame": 528,
   "scene": "s05-rule",
   "kind": "slam",
   "visual": "動画の声",
   "text": "褒めない。",
   "text_source": "video"
  },
  {
   "beat": 45,
   "frame": 540,
   "scene": "s05-rule",
   "kind": "slam",
   "visual": "動画の声",
   "text": "盛らない。",
   "text_source": "video"
  },
  {
   "beat": 48,
   "frame": 576,
   "scene": "s06-prose",
   "kind": "whoosh",
   "visual": "原稿の3文と、出力の札（文章 5/10）",
   "text": "要約的な締めの一文が3箇所ある",
   "text_source": "output:score"
  },
  {
   "beat": 49,
   "frame": 588,
   "scene": "s06-prose",
   "kind": "slash",
   "visual": "該当の1文に赤丸→取り消し",
   "text": "いつか父のような測量士になりたい、とカイは思った。",
   "text_source": "manuscript"
  },
  {
   "beat": 50,
   "frame": 600,
   "scene": "s06-prose",
   "kind": "slash",
   "visual": "該当の1文に赤丸→取り消し",
   "text": "本当に自分にできるのだろうか、と思った。",
   "text_source": "manuscript"
  },
  {
   "beat": 51,
   "frame": 612,
   "scene": "s06-prose",
   "kind": "slash",
   "visual": "該当の1文に赤丸→取り消し",
   "text": "ミアはいつも自分のことを心配してくれる、とカイは思った。",
   "text_source": "manuscript"
  },
  {
   "beat": 56,
   "frame": 672,
   "scene": "s07-emotion",
   "kind": "whoosh",
   "visual": "原稿の受諾の台詞。札「感情設計 4.5/10」",
   "text": "「はい。行きます」",
   "text_source": "manuscript"
  },
  {
   "beat": 57,
   "frame": 684,
   "scene": "s07-emotion",
   "kind": "pen",
   "visual": "台詞に赤丸"
  },
  {
   "beat": 59,
   "frame": 708,
   "scene": "s07-emotion",
   "kind": "silence",
   "visual": "溜め：1拍"
  },
  {
   "beat": 60,
   "frame": 720,
   "scene": "s07-emotion",
   "kind": "stamp",
   "visual": "出力カード",
   "text": "…頂点が即答で通過するため。",
   "text_source": "output:score"
  },
  {
   "beat": 64,
   "frame": 768,
   "scene": "s08-ending",
   "kind": "whoosh",
   "visual": "原稿の最後の1文。札「牽引力 5/10」",
   "text": "そう心に決めて、カイは目を閉じた。",
   "text_source": "manuscript"
  },
  {
   "beat": 65,
   "frame": 780,
   "scene": "s08-ending",
   "kind": "slash",
   "visual": "最後の1文に赤線"
  },
  {
   "beat": 68,
   "frame": 816,
   "scene": "s08-ending",
   "kind": "fall",
   "visual": "出力カードが落ちてくる（drop-in）",
   "text": "…は最後に置かない。",
   "text_source": "output:score"
  },
  {
   "beat": 72,
   "frame": 864,
   "scene": "s09-fix3",
   "kind": "slam",
   "visual": "出力の見出し",
   "text": "今回直すのはこの3件",
   "text_source": "output:score"
  },
  {
   "beat": 74,
   "frame": 888,
   "scene": "s09-fix3",
   "kind": "stamp",
   "visual": "番号札の判子",
   "text": "改善案4",
   "text_source": "output:score"
  },
  {
   "beat": 75,
   "frame": 900,
   "scene": "s09-fix3",
   "kind": "stamp",
   "visual": "番号札の判子",
   "text": "改善案5",
   "text_source": "output:score"
  },
  {
   "beat": 76,
   "frame": 912,
   "scene": "s09-fix3",
   "kind": "stamp",
   "visual": "番号札の判子",
   "text": "改善案7",
   "text_source": "output:score"
  },
  {
   "beat": 80,
   "frame": 960,
   "scene": "s10-drill",
   "kind": "whoosh",
   "visual": "出力カード。「感情語を使わず」に赤の下線（scribble）",
   "text": "練習の題：評価を待つ数秒の緊張を、感情語を使わず、…300字で書く。",
   "text_source": "output:score"
  },
  {
   "beat": 84,
   "frame": 1008,
   "scene": "s10-drill",
   "kind": "slam",
   "visual": "動画の声",
   "text": "弱点から、練習の題まで。",
   "text_source": "video"
  },
  {
   "beat": 86,
   "frame": 1032,
   "scene": "s10-drill",
   "kind": "riser",
   "visual": "次のセクションへの上昇。山は拍88",
   "length_beats": 2
  },
  {
   "beat": 88,
   "frame": 1056,
   "scene": "s11-proof-request",
   "kind": "drop",
   "visual": "T1 全面色替え（青）。チャットの吹き出し",
   "text": "誤字脱字だけチェックしてください。書き換えはいらないです。",
   "text_source": "input",
   "accent": "section"
  },
  {
   "beat": 88.5,
   "frame": 1062,
   "scene": "s11-proof-request",
   "kind": "type",
   "visual": "吹き出しの文字送り"
  },
  {
   "beat": 89,
   "frame": 1068,
   "scene": "s11-proof-request",
   "kind": "type",
   "visual": "吹き出しの文字送り"
  },
  {
   "beat": 89.5,
   "frame": 1074,
   "scene": "s11-proof-request",
   "kind": "type",
   "visual": "吹き出しの文字送り"
  },
  {
   "beat": 90,
   "frame": 1080,
   "scene": "s11-proof-request",
   "kind": "type",
   "visual": "吹き出しの文字送り"
  },
  {
   "beat": 92,
   "frame": 1104,
   "scene": "s11-proof-request",
   "kind": "pen",
   "visual": "「書き換えはいらない」に赤線",
   "text": "書き換えはいらない",
   "text_source": "input"
  },
  {
   "beat": 96,
   "frame": 1152,
   "scene": "s12-typos",
   "kind": "slash",
   "visual": "原稿の該当箇所「見慣れた後継だった。」の語に取り消し線。種類の札「誤変換」",
   "text": "後継",
   "text_source": "manuscript",
   "label": "誤変換",
   "label_source": "output:proof"
  },
  {
   "beat": 98,
   "frame": 1176,
   "scene": "s12-typos",
   "kind": "pen",
   "visual": "赤ペンで正しい形を書き込む（Klee One・scribble）",
   "text": "光景",
   "text_source": "output:proof"
  },
  {
   "beat": 100,
   "frame": 1200,
   "scene": "s12-typos",
   "kind": "slash",
   "visual": "原稿の該当箇所「学院で受けた測量術の抗議では」の語に取り消し線。種類の札「誤変換」",
   "text": "抗議",
   "text_source": "manuscript",
   "label": "誤変換",
   "label_source": "output:proof"
  },
  {
   "beat": 102,
   "frame": 1224,
   "scene": "s12-typos",
   "kind": "pen",
   "visual": "赤ペンで正しい形を書き込む（Klee One・scribble）",
   "text": "講義",
   "text_source": "output:proof"
  },
  {
   "beat": 104,
   "frame": 1248,
   "scene": "s12-typos",
   "kind": "slash",
   "visual": "原稿の該当箇所「「ありがとうござます」」の語に取り消し線。種類の札「脱字」",
   "text": "ござます",
   "text_source": "manuscript",
   "label": "脱字",
   "label_source": "output:proof"
  },
  {
   "beat": 106,
   "frame": 1272,
   "scene": "s12-typos",
   "kind": "pen",
   "visual": "赤ペンで正しい形を書き込む（Klee One・scribble）",
   "text": "ございます",
   "text_source": "output:proof"
  },
  {
   "beat": 108,
   "frame": 1296,
   "scene": "s12-typos",
   "kind": "slash",
   "visual": "原稿の該当箇所「秋の短かい日」の語に取り消し線。種類の札「誤字（送り仮名）」",
   "text": "短かい",
   "text_source": "manuscript",
   "label": "誤字（送り仮名）",
   "label_source": "output:proof"
  },
  {
   "beat": 110,
   "frame": 1320,
   "scene": "s12-typos",
   "kind": "pen",
   "visual": "赤ペンで正しい形を書き込む（Klee One・scribble）",
   "text": "短い",
   "text_source": "output:proof"
  },
  {
   "beat": 112,
   "frame": 1344,
   "scene": "s12-typos",
   "kind": "slash",
   "visual": "原稿の該当箇所「微笑んだ／ほほえんだ」の語に取り消し線。種類の札「表記ゆれ」",
   "text": "微笑んだ／ほほえんだ",
   "text_source": "manuscript",
   "label": "表記ゆれ",
   "label_source": "output:proof"
  },
  {
   "beat": 114,
   "frame": 1368,
   "scene": "s12-typos",
   "kind": "pen",
   "visual": "赤ペンで正しい形を書き込む（Klee One・scribble）",
   "text": "どちらかに統一",
   "text_source": "output:proof"
  },
  {
   "beat": 116,
   "frame": 1392,
   "scene": "s13-norewrite",
   "kind": "slam",
   "visual": "動画の声",
   "text": "直すのは、誤字だけ。",
   "text_source": "video",
   "accent": "pullback"
  },
  {
   "beat": 120,
   "frame": 1440,
   "scene": "s13-norewrite",
   "kind": "whoosh",
   "visual": "出力カード（静かに置く）",
   "text": "大事な原稿は人の目でも確かめてください。",
   "text_source": "output:proof"
  },
  {
   "beat": 124,
   "frame": 1488,
   "scene": "s14-rapid",
   "kind": "riser",
   "visual": "上昇の開始。山は拍132",
   "length_beats": 8
  },
  {
   "beat": 124,
   "frame": 1488,
   "scene": "s14-rapid",
   "kind": "slam",
   "visual": "全面色替え＋軸名（4分音符）",
   "text": "構成",
   "text_source": "output:score"
  },
  {
   "beat": 125,
   "frame": 1500,
   "scene": "s14-rapid",
   "kind": "slam",
   "visual": "全面色替え＋軸名（4分音符）",
   "text": "キャラクター",
   "text_source": "output:score"
  },
  {
   "beat": 126,
   "frame": 1512,
   "scene": "s14-rapid",
   "kind": "slam",
   "visual": "全面色替え＋軸名（4分音符）",
   "text": "世界観",
   "text_source": "output:score"
  },
  {
   "beat": 127,
   "frame": 1524,
   "scene": "s14-rapid",
   "kind": "slam",
   "visual": "全面色替え＋軸名（4分音符）",
   "text": "感情設計",
   "text_source": "output:score"
  },
  {
   "beat": 128,
   "frame": 1536,
   "scene": "s14-rapid",
   "kind": "slam",
   "visual": "T7 連打（三連符＝4フレーム）",
   "text": "牽引力",
   "text_source": "output:score"
  },
  {
   "beat": 128.333333,
   "frame": 1540,
   "scene": "s14-rapid",
   "kind": "slam",
   "visual": "T7 連打（三連符＝4フレーム）",
   "text": "独自性",
   "text_source": "output:score"
  },
  {
   "beat": 128.666667,
   "frame": 1544,
   "scene": "s14-rapid",
   "kind": "slam",
   "visual": "T7 連打（三連符＝4フレーム）",
   "text": "文章",
   "text_source": "output:score"
  },
  {
   "beat": 131,
   "frame": 1572,
   "scene": "s14-rapid",
   "kind": "silence",
   "visual": "溜め：1拍の無音"
  },
  {
   "beat": 132,
   "frame": 1584,
   "scene": "s14-rapid",
   "kind": "impact",
   "visual": "白フラッシュ（最大の一撃）→ 生成りへ",
   "accent": "peak"
  },
  {
   "beat": 136,
   "frame": 1632,
   "scene": "s15-outro",
   "kind": "title",
   "visual": "題字「novel-editor」と一言",
   "text": "novel-editor",
   "text_source": "video"
  },
  {
   "beat": 140,
   "frame": 1680,
   "scene": "s15-outro",
   "kind": "stamp",
   "visual": "導入の手順（1つずつ積む）",
   "text": "① 設定でコード実行をオン",
   "text_source": "video"
  },
  {
   "beat": 142,
   "frame": 1704,
   "scene": "s15-outro",
   "kind": "stamp",
   "visual": "導入の手順（1つずつ積む）",
   "text": "② novel-editor.skill をアップロード",
   "text_source": "video"
  },
  {
   "beat": 144,
   "frame": 1728,
   "scene": "s15-outro",
   "kind": "stamp",
   "visual": "導入の手順（1つずつ積む）",
   "text": "③ 原稿を貼って「厳しめで」",
   "text_source": "video"
  },
  {
   "beat": 148,
   "frame": 1776,
   "scene": "s15-outro",
   "kind": "slam",
   "visual": "URL",
   "text": "github.com/skyvesmir/novel-editor",
   "text_source": "video"
  },
  {
   "beat": 152,
   "frame": 1824,
   "scene": "s15-outro",
   "kind": "end",
   "visual": "最後の一撃。以降は題字とURLだけで止める（breathe）",
   "accent": "final"
  }
 ]
};
