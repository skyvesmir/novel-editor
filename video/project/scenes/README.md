# scenes/ 実装の手引き（s06〜s15 の担当向け）

s01〜s05 と共通部品は実装・確認済み。担当は **自分のシーンのファイル `scenes/<id>.js` だけ** を書く。
読む順：`video/brief/storyboard.md` → `style-brief.md` → このファイル → 手本の `s01-hook.js`（刺す・判子・色替え）、`s03-request.js`（吹き出し・赤丸）、`s05-rule.js`（出力カード・動画の声）。

## 0. ファイルと持ち主

| ファイル | 中身 | 編集 |
|---|---|---|
| `scenes/<id>.js`（s06〜s15） | 1シーンの組み立て | **担当だけ**。中の雛形コメントにそのシーンの cues 一覧がある |
| `scenes/lib.js` / `base.css` / `main.js` | 共通部品・共通の見た目・起動 | **触らない**（2人が並列で書くため）。足りない部品は自分のシーンの中に書き、共通化したければ返答で提案する |
| `scenes/cues.js`, `index.html` | `node video/project/tools/build.mjs` の生成物 | 手で編集しない |
| `video/brief/cues.json` | 時間の正本 | 編集しない（変更はオーケストレーターが `gen_cues.py` で行う） |

シーン固有の CSS は `S.css(...)` で入れ、id／class は必ずシーン名を頭に付ける（`#s06-ms`、`.s06-row`）。他のシーンとぶつからないようにする。

## 1. 1シーンだけ書き出して確かめる

```bash
bash /home/user/novel-editor/video/project/tools/render-scene.sh s06              # draft 画質。約10〜20秒
bash /home/user/novel-editor/video/project/tools/render-scene.sh s05,s06          # 前のシーンとのつなぎ目も見る
bash /home/user/novel-editor/video/project/tools/render-scene.sh s06 standard     # 画質指定
```

出力（上書き。本番の `video/out/render/v<N>.mp4` とは別）:

- `video/out/scenes/s06.mp4`
- `video/out/inspect/scene-s06/sheet.png` … 縮小一覧（3フレーム＝1/4拍ごと。ラベル `f<本番の絶対フレーム> b<拍>`）。**まずこれを Read で見る**
- `video/out/inspect/scene-s06/summary.md`, `overview.png`, `bands/ev###.png` … `av_inspect.py` の結果

細部は原寸の1コマで見る：
```bash
ffmpeg -v error -y -i /home/user/novel-editor/video/out/scenes/s06.mp4 -vf "select=eq(n\,30)" -frames:v 1 <scratchpad>/s06_f30.png   # n はシーン頭からのフレーム
```

`summary.md` の読み方：
- **「絵−イベント」列**が 0.0 なら絵は拍に乗っている（n/a は変化が小さいか拍0）。
- **「音−イベント」が −100ms 前後で「超過」**と出るのは、検出窓の頭で前の音（BGM・余韻）を拾う誤検出。効果音は `video/out/audio/placement.json` のとおり標本単位で拍頭に置かれており、s01〜s05 では書き出した音と mix.wav の相互相関のずれは 0.0ms だった。これは直さなくてよい。
- 「黒画面」「静止」が 0 であること。

並列で走らせてよい：`render-scene.sh` は `_solo-<名>.html` を作って書き出し、終わったら消す（直下に入口の HTML が複数残ると `check` が落ちる）。

仕上げに全体の検査（書き出しはしない）:
```bash
cd /home/user/novel-editor/video/project && node tools/build.mjs && npx hyperframes check .
```
**error 0 で通すこと**。警告 `timeline_track_too_dense`（1ファイルにシーンを並べている構造上のもの）は既知。

## 2. シーンの書き方（骨組み）

```js
// s06-prose：……（何をするシーンか、拍ごとの段取りを2〜3行）
HF.scene("s06-prose", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const head = S.find("whoosh");                       // 拍48
  const hits = S.ev.filter((e) => e.kind === "slash"); // 拍49・50・51（text は原稿の文）

  S.css(`#s06-ms { position:absolute; left:120px; top:200px; width:1680px; }`);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s06-ms" class="hf-ms">${hits.map((e) => `<p><span class="hf-strike s06-s">${HF.esc(e.text)}</span></p>`).join("")}</div>
  `);
  // 位置を測る部品（circleAround など）は S.html の後・動かす前に呼ぶ
  hits.forEach((e, i) => M.strike(tl, S.qa(".s06-s")[i], e.t));
});
```

### S（シーンごとに main.js が渡す）

| 名前 | 中身 |
|---|---|
| `S.tl` | 全体で1本の paused timeline。すべての動きをここに載せる |
| `S.ev` | このシーンの cues イベントの配列。各要素は cues.json の項目に `t`（時間軸の秒。`frame` から計算済み）と `i`（シーン内の通し番号）を足したもの |
| `S.find(kind, n=0)` | kind が一致する n 番目のイベント |
| `S.start` / `S.end` | シーン頭・終わりの時刻（秒） |
| `S.at(beat)` | 拍（cues の絶対拍）→ 時間軸の秒 |
| `S.html(str)` / `S.q(sel)` / `S.qa(sel)` | 中身を入れる／シーン内で探す（`qa` は配列） |
| `S.css(text)` | シーン固有の CSS を足す |
| `S.stage` | シーンの包み（1920×1080）。`S.el`（.clip）は動かさない |

### 時刻（秒を直書きしない）

| 関数 | 用途 |
|---|---|
| `e.t` | イベントの時刻。**基本はこれ** |
| `S.at(beat)` / `HF.at(beat)` | 拍→秒（単独書き出し時はシーン頭=0 に自動でずれる） |
| `HF.beats(n)` | 長さ n 拍 → 秒（フレームに丸める）。`e.t + HF.beats(0.5)` のように使う |
| `HF.frames(n)` / `HF.FR` | n フレーム → 秒 / 1フレームの秒 |
| `HF.BEAT`, `HF.FPB`, `HF.FPS` | 1拍の秒（0.4）、1拍のフレーム数（12）、30 |
| `HF.frameOf(beat)` | 拍 → 絶対フレーム |

## 3. 色・書体・文字の大きさ

- 色：`HF.COLORS.{paper, ink, red, blue, yellow}` ＝ CSS 変数 `var(--paper)` `--ink` `--red` `--blue` `--yellow`。**1場面3色まで**。赤は「刺す」瞬間と指摘にだけ。黄は掴みと最高点だけ（s06 以降は原則使わない）。
- 書体（CSS 変数／`HF.FONTS`）：`--f-slam`（Dela Gothic One。動画の声・数字）、`--f-mincho`（Shippori Mincho B1 400/700。原稿・出力カード本文）、`--f-pen`（Klee One 600。赤ペンの書き込み）、`--f-ui`（Zen Kaku Gothic New 500/900。札・UI）。
- 欠けた字：Dela は `✓✗＋`、Mincho と ZenKaku は `↔✓✗`、Klee は `✓✗` が無い。出さない。
- 書体は使う字だけに絞ってある（`brief/*.md` と `cues.json` の全字）。それ以外の字を出すなら `scenes/extra-chars.txt` に足して `python3 /home/user/novel-editor/video/project/tools/subset_fonts.py`（両担当が走らせても結果は同じ）。原則は不要。
- 大きさ：読ませる字は **50px 以上**（`--min-read`）。見出しは 160〜380px。1画面に読ませる文は1つ。1拍に新しく出す読ませる字は2字まで・1小節8字までが目安（超えるときは返答に書く）。

## 4. 画面の文字（最重要）

- **文字は `e.text` をそのまま使う**。打ち直さない。分割して出すときは、つなげると原文に戻ることを実行時に確かめる（`s03-request.js` の `throw` の形）。
- `text_source` が `output:*` の文 ＝ skill の実出力 → **出力カード**（`UI.card`）か判子。札「novel-editor の出力」を付ける。出力の語順・注記もそのまま（s04 の「5（回収未検証）/10」は数字→注記→/10 の順で出している）。
- `video` ＝ 動画の声 → `UI.voice`（Dela の叩きつけ）。出力のふりをしない（札を付けない）。
- `manuscript` ＝ 原稿 → 明朝（`.hf-ms`）。`input` ＝ 依頼文 → 吹き出し（`UI.bubble`、札「依頼」）。
- 省略は「…」。cues の text に既に入っている（例「…頂点が即答で通過するため。」）。
- 札などに cues に無い文言（例「文章 5/10」「誤変換」）を出すときは、`skill-output-*.md` にある形と一字一句同じか確かめる。cues の `label` は使ってよい。

## 5. 動き `HF.M`（style-brief §4 の語彙）

すべて `(tl, 対象, 時刻t, opts)`。対象は要素か selector。**入る前の要素には `class="hf-hidden"`（opacity 0）を付けておく**。`slam`・`stamp`・`dropIn`・`blurSnap`・`popStagger` は自分で表示する。

| 関数 | 動き | 主な opts |
|---|---|---|
| `M.show(tl, el, t)` / `M.hide(...)` | その時刻に出す／消す（`tl.set`。逆 seek でも戻る） | |
| `M.slam(tl, el, t, o)` | 1 叩きつけ：scale 1.6→1・y −40→0 を2フレームで着地 → recoil（elastic で静止） | `from`, `y`, `recoil:false` |
| `M.stamp(tl, el, t, o)` | 3 判子：scale 2→1・rotation −8→−4、1/4拍 back.out(3) | `fromScale`, `fromRot`, `rot` |
| `M.strike(tl, el, t, o)` | 4 取り消し線：`.hf-strike` の赤線を左から（行をまたいで順に走る）、1/4拍 | `dur`, `thick` |
| `M.scribble(tl, path, t, dur)` | 5 書き込み：SVG path を等速で描く（唯一の linear）。既定 1/2拍 | |
| `M.countUp(tl, el, values, t0, t1)` | 6 数値：`values` を順に出し、最後の値が t1 ちょうど。el は `.hf-num` | |
| `M.shake(tl, el, t, o)` | 7 衝撃：種つき乱数で減衰。既定 振幅12px・1/2拍。**毎拍は使わない** | `amp`, `dur`, `seed` |
| `M.dropIn(tl, el, t, o)` | 8 落下：yPercent −120→0、bounce.out、1拍 | `from`, `dur` |
| `M.wipe(tl, el, t, o)` | 9 行の開示：clip-path を左から、1/2拍。要素に `style="clip-path:inset(0 100% 0 0)"` を付けておく | `dur` |
| `M.blurSnap(tl, el, t, o)` | 10 ブレ→焦点：blur 20px→0、1/4拍 | `blur`, `dur` |
| `M.popStagger(tl, els, t, o)` | 11 連続出現：1/8拍刻みで back.out(2) | `each`, `from`, `dur` |
| `M.squash(tl, el, t, o)` | 12 潰れ：scaleY 1→0.7→1、1/4拍 | `to` |
| `M.breathe(tl, el, t0, t1, o)` | 13 呼吸：scale 1↔1.02（1往復2拍）を t0〜t1 で繰り返す。止めの区間に | `amt`, `period` |
| `M.flash(tl, el, t, o)` | 14 拍フラッシュ：重ね要素（`.hf-flash`）を2フレーム出す。1小節に1回まで | `color`, `opacity`, `frames` |
| `M.bg(tl, el, t, color)` | T1 全面色替え：背景色を1フレームで替える | |
| `M.place(tl, el, t, o)` | 語彙外の補助：静かに置く（opacity と y、power2.out、1/2拍）。s13 の「静かに置く」カード用 | `y`, `dur` |

注意：
- 同じ要素に `slam`/`stamp`（scale・y・rotation）と `shake`（x・y）や `breathe`（scale）を重ねない。**包みを分ける**（例：`#s05-shake` に shake、中の `#s05-card` に stamp、`#s05-cw` に breathe）。
- 自分で `tl.fromTo` を書くときは `immediateRender:false` を付ける。
- 語彙に無い動きを足すときは、何を伝える動きかを1行コメントで書く。linear は scribble 以外使わない。
- 切り替えは T1（全面色替え）・T3（硬い切り＝シーン頭の1フレーム目で主役が完成形で出る）・T7（連打、s14 だけ）の3種だけ。フェードで始めない。

## 6. 部品 `HF.ui`（HTML 文字列を返す。`S.html` に入れてから `S.q` で掴む）

| 関数 | 見た目 |
|---|---|
| `UI.card(text, {tag, size, id, cls, html})` | **出力カード**：生成りのカード＋札（既定「novel-editor の出力」）、本文は明朝700・既定 84px。`html` を渡すと本文を差し替え（強調の `<span>` を入れたいとき。中身の文字は text と同じにする） |
| `UI.voice(text, {size, color, id, cls})` | **動画の声**：Dela の叩きつけ（既定 160px、1行） |
| `UI.stampBox(text, {size, id, cls})` | 赤い判子の枠（明朝700、既定 120px） |
| `UI.tag(text, cls)` | 墨の札（ZenKaku 900・50px）。例 `UI.tag("文章 5/10")` |
| `UI.bubble(chunks, {id, cls})` | **吹き出し**（依頼文）。`chunks` は文字列か `{text, cls, nl}` の配列で、各片は `.hf-chunk`（opacity 0）。`M.show` で順に出す（文字送り）。`nl:true` でその片の前で改行 |
| `UI.pen({id, cls})` | 赤ペンの SVG（640×72、先端が左端中央）。`tl.set(pen,{opacity:1,x,y:先端y−36,rotation})` で置く |
| `UI.circleAround(host, target, {pad, width, seed})` | target を囲む手書きの楕円 path を host に足して返す → `M.scribble` で描く。隣の字に掛かるときは target に左右の margin を足す（s03） |
| `UI.underline(host, target, {gap, width, seed})` | target の下の手書きの線 path |
| `HF.allowOverlap(els)` | 意図した重ね（薄くした原稿の上の判子など）を check に伝える。**重ねている文字要素だけ**に付ける |
| `HF.rel(el, anc)` | el の位置（anc 基準・px）。動かす前に測る |
| `HF.rng(seed)` | 種つき乱数（mulberry32）。`Math.random` は使わない |
| `HF.esc(s)` | HTML の escape。テキストを HTML 文字列に入れるときは必ず通す |

共通クラス（base.css）：`.hf-bg`＋`.hf-paper`（罫線つきの紙）／`.hf-ink`（墨）、`.hf-layer`・`.hf-center`（全面の重ね・中央寄せ）、`.hf-ms`（原稿の明朝 60px）、`.hf-strike`、`.hf-pen-text`（赤ペンの書き込み文字。Klee、`rotate(-3〜-6deg)` で置く）、`.hf-num`、`.hf-flash`（全面の白。`M.flash`）、`.hf-hidden`。

## 7. 決定的な描画（破ると書き出しが毎回変わる）

- `Date.now`、`Math.random`、`requestAnimationFrame`、`setInterval`、CSS transition / animation を使わない。すべて `S.tl` に載せる。
- 出す・消す・文字の差し替えは `tl.set`（`M.show`/`M.hide`）。`tl.call` で textContent を書き換えない（逆 seek で戻らない）。差し替える語は1語ずつ別要素にする。
- fetch しない（cues は `window.CUES` に埋め込み済み）。

## 8. 仕上げの確かめ（シーンごと）

1. `sheet.png` で：1フレーム目に主役が出ている／重なり・はみ出しがない／文字が 50px 以上で読める／止まって見える区間（2拍以上まったく動かない）がない。
2. 原寸の1コマで：文字が `e.text` と一字一句同じ。欠けた字（豆腐）がない。
3. `summary.md` の「絵−イベント」が各イベントで 0.0（n/a は可）。
4. `npx hyperframes check .` が error 0。
