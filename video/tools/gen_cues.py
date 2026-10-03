#!/usr/bin/env python3
"""承認済みの絵コンテ（video/brief/storyboard.md）から video/brief/cues.json を作る。

cues.json は時間の唯一の正本。絵（video-builder）と音（video-sound）がこれだけを読む。
直すときはこのファイルを直して再生成する（cues.json を手で直さない）。
  python3 video/tools/gen_cues.py

text_source の意味（評価役が一字一句の一致を確かめるため）:
  output:score / output:proof … video/brief/skill-output-*.md の連続した一部（「…」は省略）
  manuscript … video/brief/demo-manuscript.md の連続した一部
  input … skill に渡した依頼文（evals/.work/video/input-*.md の1行目）
  video … 動画のコピー（skill の出力のふりをしない書体で出す）
"""
import json
import pathlib
import re

BPM, FPS = 150, 30
ROOT = pathlib.Path(__file__).resolve().parents[2]

SCENES = [  # id, 開始小節(1始まり), 小節数, 目的
    ("s01-hook", 1, 4, "掴み「刺す」：冒頭の設定説明を赤ペンで刺し、掴みなしの判定を叩きつける"),
    ("s02-title", 5, 2, "題字"),
    ("s03-request", 7, 2, "採点の依頼（実際の依頼文）"),
    ("s04-axes", 9, 2, "7軸の点数"),
    ("s05-rule", 11, 2, "点の動かし方の原則"),
    ("s06-prose", 13, 2, "文章：要約的な締めの一文×3"),
    ("s07-emotion", 15, 2, "感情設計：即答の受諾"),
    ("s08-ending", 17, 2, "牽引力：章末の一文"),
    ("s09-fix3", 19, 2, "今回直すのはこの3件"),
    ("s10-drill", 21, 2, "練習の題"),
    ("s11-proof-request", 23, 2, "校正の依頼（実際の依頼文）"),
    ("s12-typos", 25, 5, "誤字5件"),
    ("s13-norewrite", 30, 2, "書き換えない"),
    ("s14-rapid", 32, 3, "連打 → 白フラッシュ"),
    ("s15-outro", 35, 6, "締め：題字・導入3手順・URL"),
]

E = []


def ev(beat, scene, kind, visual, text=None, src=None, **kw):
    e = {"beat": round(beat, 6), "frame": round(beat * FPS * 60 / BPM), "scene": scene, "kind": kind, "visual": visual}
    if text is not None:
        e["text"], e["text_source"] = text, src
    e.update(kw)
    E.append(e)


# s01 掴み（小節1–4 = 拍0–15）
L1 = "このアルセリオ大陸には、七つの王国と三つの自由都市がある。"
ev(0, "s01-hook", "slash", "1フレーム目から生成りの紙に冒頭3文が表示済み。1文目に取り消し線＋shake", L1, "manuscript")
ev(1, "s01-hook", "slash", "2文目に取り消し線", "かつて大陸全土を治めた古代魔導帝国が千年前に滅びてから、人々は帝国の残した魔導遺構を掘り起こし、その力を分け合うことで暮らしてきた。", "manuscript")
ev(2, "s01-hook", "slash", "3文目に取り消し線", "魔導遺構から取り出される魔石は灯りにも武器にもなり、王国同士の争いの火種にもなった。", "manuscript")
ev(3, "s01-hook", "silence", "溜め：赤ペンが持ち上がる。画面はほぼ静止（微動のみ）")
ev(4, "s01-hook", "stamp", "巨大な赤い判子。4拍止める", "冒頭の掴み：提示なし。", "output:score")
ev(8, "s01-hook", "slam", "T1 全面色替え（黄）＋叩きつけ", "疑問", "output:score")
ev(9, "s01-hook", "slam", "T1 全面色替え（青）＋叩きつけ", "異常", "output:score")
ev(10, "s01-hook", "slam", "T1 全面色替え（墨）＋叩きつけ", "危機", "output:score")
ev(11, "s01-hook", "silence", "溜め：1拍")
ev(12, "s01-hook", "stamp", "赤い判子＋shake。ここが最初の山（ドロップ）", "…を示す箇所を引用できない。", "output:score", accent="drop")

# s02 題字（小節5–6 = 拍16–23）
ev(16, "s02-title", "impact", "T3 硬い切りで墨の画面。題字を叩きつけ", "novel-editor", "video")
ev(18, "s02-title", "slam", "題字の下に一言", "その1話、投稿する前に。", "video")

# s03 依頼（小節7–8 = 拍24–31）。ハーフタイムに落とす
REQ = "これ、来週なろうに投稿する予定の1話です。厳しめで評価してください。"
ev(24, "s03-request", "whoosh", "T3 硬い切りで生成り。チャットの吹き出しが入る", REQ, "input", accent="halftime")
for b in (24.5, 25, 25.5, 26, 26.5, 27):
    ev(b, "s03-request", "type", "吹き出しの文字が打たれていく（文字送り）")
ev(28, "s03-request", "pen", "「厳しめで」に赤丸", "厳しめで", "input")

# s04 7軸（小節9–10 = 拍32–39）
AXES = [("構成", "5"), ("キャラクター", "5"), ("世界観", "5"), ("感情設計", "4.5"),
        ("牽引力", "5"), ("独自性", "5"), ("文章", "5")]
ev(32, "s04-axes", "drop", "グルーヴに戻る。7軸の枠が並ぶ（数字はまだ空）", accent="groove")
for i, (ax, sc) in enumerate(AXES):
    ev(32 + i, "s04-axes", "tick", f"{ax}の数字が count-up して着地（pop）", ax, "output:score", score=sc, pitch_step=i)
ev(39, "s04-axes", "silence", "溜め：7つの数字が並んだまま1拍")

# s05 原則（小節11–12 = 拍40–47）
ev(40, "s05-rule", "stamp", "出力カード。明朝。判子のように置く", "点は達成条件と引用でのみ動く。", "output:score")
ev(44, "s05-rule", "slam", "動画の声", "褒めない。", "video")
ev(45, "s05-rule", "slam", "動画の声", "盛らない。", "video")

# s06 文章（小節13–14 = 拍48–55）
ev(48, "s06-prose", "whoosh", "原稿の3文と、出力の札（文章 5/10）", "要約的な締めの一文が3箇所ある", "output:score")
for b, s in ((49, "いつか父のような測量士になりたい、とカイは思った。"),
             (50, "本当に自分にできるのだろうか、と思った。"),
             (51, "ミアはいつも自分のことを心配してくれる、とカイは思った。")):
    ev(b, "s06-prose", "slash", "該当の1文に赤丸→取り消し", s, "manuscript")

# s07 感情設計（小節15–16 = 拍56–63）
ev(56, "s07-emotion", "whoosh", "原稿の受諾の台詞。札「感情設計 4.5/10」", "「はい。行きます」", "manuscript")
ev(57, "s07-emotion", "pen", "台詞に赤丸")
ev(59, "s07-emotion", "silence", "溜め：1拍")
ev(60, "s07-emotion", "stamp", "出力カード", "…頂点が即答で通過するため。", "output:score")

# s08 章末（小節17–18 = 拍64–71）
ev(64, "s08-ending", "whoosh", "原稿の最後の1文。札「牽引力 5/10」", "そう心に決めて、カイは目を閉じた。", "manuscript")
ev(65, "s08-ending", "slash", "最後の1文に赤線")
ev(68, "s08-ending", "fall", "出力カードが落ちてくる（drop-in）", "…は最後に置かない。", "output:score")

# s09 今回直すのはこの3件（小節19–20 = 拍72–79）
ev(72, "s09-fix3", "slam", "出力の見出し", "今回直すのはこの3件", "output:score")
for b, t in ((74, "改善案4"), (75, "改善案5"), (76, "改善案7")):
    ev(b, "s09-fix3", "stamp", "番号札の判子", t, "output:score")

# s10 練習の題（小節21–22 = 拍80–87）
ev(80, "s10-drill", "whoosh", "出力カード。「感情語を使わず」に赤の下線（scribble）",
   "練習の題：評価を待つ数秒の緊張を、感情語を使わず、…300字で書く。", "output:score")
ev(84, "s10-drill", "slam", "動画の声", "弱点から、練習の題まで。", "video")
ev(86, "s10-drill", "riser", "次のセクションへの上昇。山は拍88", length_beats=2)

# s11 校正の依頼（小節23–24 = 拍88–95）
PROOF = "誤字脱字だけチェックしてください。書き換えはいらないです。"
ev(88, "s11-proof-request", "drop", "T1 全面色替え（青）。チャットの吹き出し", PROOF, "input", accent="section")
for b in (88.5, 89, 89.5, 90):
    ev(b, "s11-proof-request", "type", "吹き出しの文字送り")
ev(92, "s11-proof-request", "pen", "「書き換えはいらない」に赤線", "書き換えはいらない", "input")

# s12 誤字5件（小節25–29 = 拍96–115）
TYPOS = [("見慣れた後継だった。", "後継", "光景", "誤変換"),
         ("学院で受けた測量術の抗議では", "抗議", "講義", "誤変換"),
         ("「ありがとうござます」", "ござます", "ございます", "脱字"),
         ("秋の短かい日", "短かい", "短い", "誤字（送り仮名）"),
         ("微笑んだ／ほほえんだ", "微笑んだ／ほほえんだ", "どちらかに統一", "表記ゆれ")]
for k, (ctx, wrong, right, kind) in enumerate(TYPOS):
    b = 96 + 4 * k
    ev(b, "s12-typos", "slash", f"原稿の該当箇所「{ctx}」の語に取り消し線。種類の札「{kind}」", wrong, "manuscript", label=kind, label_source="output:proof")
    ev(b + 2, "s12-typos", "pen", "赤ペンで正しい形を書き込む（Klee One・scribble）", right, "output:proof")

# s13 書き換えない（小節30–31 = 拍116–123）
ev(116, "s13-norewrite", "slam", "動画の声", "直すのは、誤字だけ。", "video", accent="pullback")
ev(120, "s13-norewrite", "whoosh", "出力カード（静かに置く）", "大事な原稿は人の目でも確かめてください。", "output:proof")

# s14 連打（小節32–34 = 拍124–135）
ev(124, "s14-rapid", "riser", "上昇の開始。山は拍132", length_beats=8)
for i, (ax, _) in enumerate(AXES[:4]):
    ev(124 + i, "s14-rapid", "slam", "全面色替え＋軸名（4分音符）", ax, "output:score")
for i, (ax, _) in enumerate(AXES[4:]):
    ev(128 + i / 3, "s14-rapid", "slam", "T7 連打（三連符＝4フレーム）", ax, "output:score")
ev(131, "s14-rapid", "silence", "溜め：1拍の無音")
ev(132, "s14-rapid", "impact", "白フラッシュ（最大の一撃）→ 生成りへ", accent="peak")

# s15 締め（小節35–40 = 拍136–159）
ev(136, "s15-outro", "title", "題字「novel-editor」と一言", "novel-editor", "video")
for b, t in ((140, "① 設定でコード実行をオン"), (142, "② novel-editor.skill をアップロード"), (144, "③ 原稿を貼って「厳しめで」")):
    ev(b, "s15-outro", "stamp", "導入の手順（1つずつ積む）", t, "video")
ev(148, "s15-outro", "slam", "URL", "github.com/skyvesmir/novel-editor", "video")
ev(152, "s15-outro", "end", "最後の一撃。以降は題字とURLだけで止める（breathe）", accent="final")


SOURCES = {
    "output:score": "video/brief/skill-output-score.md",
    "output:proof": "video/brief/skill-output-proof.md",
    "manuscript": "video/brief/demo-manuscript.md",
    "input": None,  # 依頼文は下の INPUTS と照合
}
INPUTS = [REQ, PROOF]


def verify_text(e):
    """出力・原稿・依頼文の文字が、出典の連続した一部か（「…」で区切った各片、「／」は並記）。"""
    for key in ("text", "label"):
        src = e.get(f"{key}_source" if key == "label" else "text_source")
        if key not in e or src in (None, "video"):
            continue
        hay = "\n".join(INPUTS) if src == "input" else (ROOT / SOURCES[src]).read_text(encoding="utf-8")
        for piece in re.split(r"…|／", e[key]):
            assert piece == "" or piece in hay, f"出典と一致しない（{src}）: {piece!r} in {e}"


def main():
    end_beat = 4 * (SCENES[-1][1] - 1 + SCENES[-1][2])
    cues = {
        "bpm": BPM, "beatsPerBar": 4, "fps": FPS, "width": 1920, "height": 1080,
        "seconds_per_beat": 60 / BPM, "frames_per_beat": FPS * 60 / BPM,
        "duration_beats": end_beat, "duration_seconds": end_beat * 60 / BPM,
        "scenes": [{"id": i, "startBeat": 4 * (b - 1), "lengthBeats": 4 * n, "purpose": p} for i, b, n, p in SCENES],
        "events": sorted(E, key=lambda e: e["beat"]),
    }
    # 自己検査：拍がフレームに乗る／シーン範囲内／シーンが隙間なく並ぶ
    fpb = FPS * 60 / BPM
    for e in cues["events"]:
        f = e["beat"] * fpb
        assert abs(f - e["frame"]) < 1e-3, f"フレームに乗らない拍: {e}"
        sc = next(s for s in cues["scenes"] if s["id"] == e["scene"])
        assert sc["startBeat"] <= e["beat"] < sc["startBeat"] + sc["lengthBeats"], f"シーン外: {e}"
    for e in cues["events"]:
        verify_text(e)
    pos = 0
    for s in cues["scenes"]:
        assert s["startBeat"] == pos, s
        pos += s["lengthBeats"]
    out = ROOT / "video/brief/cues.json"
    out.write_text(json.dumps(cues, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{out.relative_to(ROOT)}: {len(cues['scenes'])} scenes, {len(E)} events, {cues['duration_seconds']}s")


if __name__ == "__main__":
    main()
