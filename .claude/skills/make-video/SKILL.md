---
name: make-video
description: novel-editor の紹介動画（HyperFrames・音ハメ）を、素材探し→絵コンテ承認→音と実装→評価のループで作る。メイン会話はオーケストレーターとして各役に振り分け、結論だけを受け取る。
---

# 紹介動画の制作手順

置き場所と受け渡しは `video/README.md`。メイン会話は振り分けと判断だけを行い、素材・コード・講評の本文は読み込まない（返答の要約と、必要な箇所だけを読む）。

## 役とモデル

| 役 | エージェント | モデル／effort | 理由 |
|---|---|---|---|
| 素材：技術 | video-tech-scout | Sonnet 5.5／medium | 導入と試作の書き出し、検査スクリプト。手順的なコード作業 |
| 素材：見た目の参照 | video-ref-scout | Sonnet 5.5／medium | 調査とコマの分解。最終の取捨はオーケストレーターが決める |
| 素材：フォント | video-font-scout | Haiku 4.5／low | 取得とライセンス・字形の機械確認だけ |
| 素材：デモ原稿 | fixture-writer（既存） | Opus 5.5／medium | 欠点を狙って仕込んだオリジナル原稿 |
| 素材：skill の実出力 | eval-generator（既存） | Sonnet 5.5／medium | 無料枠と同じ Sonnet で skill を実際に動かす |
| 音作成 | video-sound | Opus 5.5／medium | 聴けない前提で、拍に揃った音をコードで設計する |
| 実行 | video-builder | Opus 5.5／high | 最も重い創作コード |
| 評価 | video-critic | Opus 5.5／high | 合否の関門。画像を見て厳しく判定する |

**呼び方**：役は必ず登録済みの agentType で呼ぶ（frontmatter のツール制限とフックが効く）。未登録のときに定義ファイルを読ませて汎用エージェントに代行させない。代行役は全ツールを持ち、別セッションを勝手に起こした前例がある。モデルは frontmatter で版まで固定している（Opus 5.5・Sonnet 5.5）。

**上位モデルへの切り替え**：同じシーンが評価で2回続けて 🔴 のままなら、そのシーンの修正だけ video-builder を `fable` で呼ぶ。解決したら Opus 5.5 に戻す（CLAUDE.md の切り替え規則と同じ）。

## フェーズ

1. **素材探し**（並列）：tech-scout／ref-scout／font-scout と、fixture-writer→eval-generator の連鎖。
   - デモ原稿：`evals/.work/video/demo-manuscript.md` に本文、仕込みの一覧は返答だけで返す。skill の例文と `evals/fixtures/` の仕込みを流用しない（AGENTS.md「例文の保守規則」の逆向き）。
   - 実出力：eval-generator に `evals/.work/video/input-*.md` を読ませ、`evals/.work/scratch/video-output-*.md` に保存させる。オーケストレーターが `video/brief/` に写す（無加工）。
2. **絵コンテ**（オーケストレーター → **ユーザー承認**）：`storyboard.md` と `cues.json`。承認前に音と実装を始めない（作り直しが一番高くつく所）。
3. **音と実装**（並列）：video-sound と video-builder。どちらも `cues.json` だけを時間の正本にする。
4. **評価ループ**：video-critic → 🔴 があれば builder（音の 🔴 なら sound）に講評のパスを渡して直させる → 再評価。合格するか、3巡で止めてユーザーに判断を仰ぐ。
5. **人の確認**：音は誰も聴けていない。最後の判断は、ユーザーが実際に視聴して行う。

## cues.json の形

```json
{
  "bpm": 128, "beatsPerBar": 4, "fps": 30, "width": 1920, "height": 1080,
  "scenes": [
    {"id": "s01-hook", "startBeat": 0, "lengthBeats": 8, "purpose": "掴み"}
  ],
  "events": [
    {"beat": 0, "scene": "s01-hook", "kind": "slam", "visual": "赤ペンが原稿に刺さる", "text": "画面に出す文字（あれば）"}
  ]
}
```

- 秒は `拍 × 60 / bpm`。`beat` は小数可（裏拍 0.5 など）。
- `kind` は効果音パレットの名前（slam／pen／stamp／score／riser／whoosh／silence など）。音と絵が同じ名前で対応を取る。

## 予算の目安

調査では、30秒の動画を1体で作って $10〜$19 かかった実例がある。評価ループは3巡を上限とし、巡ごとに直すのは 🔴 に限る（🟡 は最後に1回だけまとめて直す）。
