# HyperFrames 技術早見表（この環境で実測したもの）

環境：Node 22.22 / ffmpeg 6.1.1 / hyperframes 0.8.114 / Chrome Headless Shell 152（下記で取得）。試作 4秒・1920x1080・30fps・120BPM は書き出し約12秒。
実測した音と絵のずれ：**8イベントすべて 0.0ms（許容33.3ms）**。負の対照（音を50ms遅らせた mp4）は av_inspect.py が +50.0ms と検出して exit 1。

## 1. 導入

```bash
cd video/project            # 既に初期化済み。作り直すなら:
npx hyperframes init <名前> -e blank --non-interactive   # 空の足場（index.html, AGENTS.md, hyperframes.json 他）
npm i hyperframes gsap
npx hyperframes browser ensure   # 初回のみ。Chrome Headless Shell を ~/.cache/hyperframes に落とす（プロキシ越しで通った）
npx hyperframes doctor           # Chrome ✗ は ensure 後に ✓。Docker は動いていない（不要）。whisper/TTS/BGM は使わない
npm run check                    # lint+実行時検査+配置+動き+コントラスト。書き出し前に毎回
```
- `/opt/pw-browsers` の Chromium は使っていない。`browser ensure` で足りた。
- 足場の `package.json` のスクリプトは `npx --yes hyperframes@0.8.114` 固定（初回はネット要）。
- 公式の詳しい手引きは `npx hyperframes docs <topic>`（data-attributes / gsap / rendering / compositions / troubleshooting）と、足場の `AGENTS.md`。

## 2. コンポジションの最小形（実際に通った）

```html
<script src="assets/gsap.min.js"></script>   <!-- CDN でなくローカルに置く（node_modules/gsap/dist/gsap.min.js をコピー） -->
<div id="root" data-composition-id="main" data-start="0" data-duration="4" data-width="1920" data-height="1080">
  <div id="flash" class="clip" data-start="0" data-duration="4" data-track-index="0"></div>
  <div id="word"  class="clip" data-start="0" data-duration="4" data-track-index="1"></div>
  <audio src="assets/audio/click.wav" data-start="0" data-duration="4" data-track-index="2"></audio>
</div>
<script>
  const tl = gsap.timeline({ paused: true });          // 必ず paused
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = tl;                      // キーは data-composition-id
</script>
```
- 時間要素には `data-start` と `data-duration`（秒）。見える要素には `class="clip"`。
- 音声は `<audio data-start data-duration>`。音量は `data-volume`（1=0dB。0.5 で実測どおり -6dB）。フェードは `data-fade-in/out`。
- 動かせる GSAP の対象プロパティ：opacity, x, y, scale, scaleX/Y, rotation, width, height, visibility（公式 docs の記載。試作は opacity と scale のみ使用）。

## 3. 時刻は cues.json から計算（秒の直書き禁止）

```js
const t = (e.beat * 60) / CUES.bpm;      // 拍→秒
tl.call(() => { word.textContent = e.text; }, null, t);                       // 文字の差し替えはその時刻ちょうど
tl.fromTo("#word",  {opacity:1, scale:1.7}, {opacity:1, scale:1, duration:0.18, ease:"power4.out", immediateRender:false}, t);
tl.fromTo("#flash", {opacity:0.9}, {opacity:0, duration:0.12, ease:"none", immediateRender:false}, t);
```
- 同じ要素に複数回 `fromTo` するときは `immediateRender:false` を付ける（先頭の状態が最後の fromTo で上書きされるのを避ける）。試作では付けて正常。付けない場合の挙動は未検証。
- 秒は 30fps で 1/30 の倍数に乗せる。120BPM の拍（0.5s）はちょうどフレーム境界（15フレーム）。128BPM など割り切れない拍は最寄りフレームに丸まる（未検証）。
- cues.json をコンポジションが直接 `fetch` することは禁止（決定的でない）。値を HTML に埋め込むか、`--variables-file` を使う（後者は未検証）。

## 4. 決定的な描画の禁止事項

公式の規則（AGENTS.md）：`Date.now()`、`Math.random()`、ネットワーク取得は使わない。タイムラインは paused で、ランタイムが seek して1コマずつ撮る。
- 毎フレームの更新ループ（`requestAnimationFrame`、`setInterval`）：撮影と無関係に動くので使わない（公式の方針に基づく。単独の検証は未検証）。
- 乱数が要るなら種つきの自前関数（mulberry32 など）。未検証。
- CSS transition / CSS animation：時間軸に乗らないので使わず、GSAP のみ（CSS keyframes のアダプタはあるが未検証）。
- 文字の差し替えは `tl.call` で seek 順序に依存する。**後ろへ seek してもテキストが戻らない**可能性がある（試作は前進のみの書き出しで問題なし。逆 seek は未検証）。安全策は、1語ごとに別要素を作り `visibility`/`opacity` を `tl.set` で切り替える方式（未検証）。

## 5. 日本語フォント

```css
@font-face { font-family:"NotoJP"; src:url("assets/fonts/NotoSansJP.ttf") format("truetype"); font-weight:100 900; }
#word { font-family:"NotoJP", sans-serif; font-weight:900; }
```
- 取得：`https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf`（可変フォント 9.6MB、OFL）。置き場所は `video/assets/fonts/` と、`video/project/assets/fonts/` にコピー（プロジェクト内でないと参照できない）。
- この環境のシステムの日本語フォントは IPAゴシックだけ。置き換えが起きると細い明朝調でなくゴシックの細字になるので、見た目で区別できる。書き出しフレーム（`bands/ev003.png`）で Noto Sans JP の極太（Black）が出ていることを目視確認済み。
- `check` が「2MB 超なので埋め込まない」と警告するが、書き出しは通る。重いなら fonttools で使う文字だけにサブセット化して woff2 にする（`pip install fonttools brotli`、未検証）。
- 実際の動画では、使う全文字を含むかを font-scout が確認すること。

## 6. 書き出し

```bash
cd video/project
npx hyperframes render . -o ../out/proto.mp4 -f 30 -q standard    # 約12秒/4秒動画（4コア、2ワーカー）
```
- 出力：h264 1920x1080 30fps + aac 48kHz **ステレオ**（入力が mono でも）。映像・音声とも start_time=0、尺 4.000s。
- 品質：`draft | standard(looks) | high(delivery)`。`--crf` / `--video-bitrate` で個別指定。
- `--quiet` を付けても進捗ログが出る。ログは `| tail` で切ること。
- 書き出しの音は mp4 に既にミックス済み。別に ffmpeg で音を足す必要はない。

## 7. 検査

```bash
python3 video/tools/av_inspect.py video/out/proto.mp4 video/brief/cues-proto.json   # 出力: video/out/inspect/proto/
```
`overview.png`（2fps 一覧）、`bands/ev###.png`（イベント±2フレーム）、`summary.json`、`summary.md`。終了コード 0=異常なし / 1=指摘あり。
- 音の立ち上がり：窓（イベント-0.1s〜+0.25s）内のピークの15%を最初に超えた時刻。絵の変化：イベント付近の最大フレーム差分の50%を超えた最初のフレーム。**拍0（t=0）は直前フレームがないので絵の測定は n/a**。
- 試作用 cues：`video/brief/cues-proto.json`。音の合成：`python3 video/tools/make_click_wav.py cues.json out.wav 4`。

## 8. つまずいた点と回避策

1. **`av_inspect.py` という名前が標準ライブラリ `inspect` を隠す**：`python3 tools/av_inspect.py` で numpy が `AttributeError: module 'inspect' has no attribute 'cleandoc'` で落ちる。両スクリプトの冒頭で、自分のあるディレクトリを `sys.path` から除く。`tools/` 内の他のスクリプトにも同じ処理が要る（`make_click_wav.py` でも発生）。
2. **`ffmpeg -ac 1` でステレオ→mono すると +3dB**（同内容の2chを足す）：サンプルピークが 1.13 になりクリップを誤検出した。チャンネルを保ったまま読む（av_inspect.py に反映済み）。
3. **コントラスト警告**：白い文字に白いフラッシュを重ねると `check` が 1.12:1 と警告（書き出し自体は通る）。フラッシュを赤に変えて解消。
4. GSAP を CDN から読む足場の既定は、ネットがない環境で止まる。ローカルコピーを使う。
5. `hyperframes check` の Snapshots は無効（disabled）。見た目の確認は書き出し後の inspect の帯で行う。
6. 書き出した AAC のピークは元の wav より僅かに上がる（0.787 → 0.797）。True Peak は -1.9dBFS。音を大きく作るときは余裕を見る。

## 9. 未検証

- 逆 seek・コンポジション分割（`data-composition-src`）・サブコンポジション内の時刻。
- 128BPM 等、拍がフレームに乗らない場合の丸め方向。
- 長尺（30秒以上）の書き出し時間とメモリ。試作 4秒で 2ワーカー。
- `--docker` 書き出し（Docker は起動していない）。
- ブラウザのプレビュー（`preview --background`）。
