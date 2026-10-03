# 紹介動画（novel-editor）制作ワークスペース

HyperFrames（HTML + GSAP → Puppeteer で1コマずつ撮影 → ffmpeg）で、音ハメの紹介動画を作る。手順は `/make-video`（`.claude/skills/make-video/SKILL.md`）。

## 置き場所と受け渡し（ファイルの契約）

| パス | 書く役 | 中身 | git |
|---|---|---|---|
| `brief/tech-cheatsheet.md` | video-tech-scout | HyperFrames の使い方の要約（この環境で動いた手順だけ） | 上げる |
| `brief/style-brief.md` | video-ref-scout | 色・書体・動き・切り替え・掴みの型（数値つき） | 上げる |
| `brief/fonts.md` | video-font-scout | 採用フォント、ライセンス、字形の網羅確認 | 上げる |
| `brief/demo-manuscript.md` | fixture-writer（→オーケストレーターが写す） | 動画用のオリジナル原稿 | 上げる |
| `brief/skill-output-*.md` | eval-generator（→オーケストレーターが写す） | skill の実出力（無加工） | 上げる |
| `brief/storyboard.md` | オーケストレーター（ユーザー承認） | 絵コンテと字幕 | 上げる |
| `brief/cues.json` | オーケストレーター（ユーザー承認） | **時間の唯一の正本**。BPM と拍で書く | 上げる |
| `audio/` | video-sound | 合成コード | 上げる |
| `project/` | video-builder | HyperFrames のプロジェクト | 上げる（node_modules 除く） |
| `tools/av_inspect.py` | video-tech-scout | 決定的な検査（縮小一覧・音と拍のずれ・音量） | 上げる |
| `assets/fonts/` | video-font-scout | フォント本体（OFL） | 上げない |
| `out/` | 各役 | 書き出し、参照動画、検査結果、講評 | 上げない |

## 時間の決まり

- 時刻はすべて `cues.json` の拍から計算する（`秒 = 拍 × 60 / bpm`）。コードに秒を直書きしない。
- 絵と音は同じ `cues.json` を読む。音ハメのずれは `tools/av_inspect.py` が数値で出す。

## 著作権

- 画面に出す原稿は `brief/demo-manuscript.md`（オリジナル）だけ。`local/` の原稿と `evals/fixtures/` は使わない。
- skill の出力は実際の出力から抜粋する。作り話の出力を「実際の出力」として見せない。
- 音はすべてコードで合成する（外部の音源・BGM 素材は使わない）。フォントは OFL などの再配布可のものだけ。
