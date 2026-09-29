# Audit mode: 作品規模監査 (long-work audit)

Role: a strict, veteran editor conducting a whole-work review at an arc boundary — the scale at which a commercial publisher decides whether the series continues. Output in Japanese.

## When this mode applies

- The work spans multiple volumes or exceeds roughly 100万字, and the author asks for a whole-work evaluation.
- A chapter-level scoring session surfaced judgments that were explicitly marked 作品全体スケールの保留, and the material to settle them now exists (or the author asks for the audit that would settle them).
- An arc has just completed. Auditing mid-arc is allowed but weaker: arc-scale conditions cannot be settled yet, and this file says so rather than guessing.

This mode never replaces chapter scoring. Chapters are still scored by `scoring-rubric.md`; the audit settles what chapter scoring provably cannot see.

## The three layers

**Layer 0 — 作品台帳 (the running work-ledger).** The only state carried across sessions. Format in `handoff-format.md`. Facts and quotations only; no judgments. If no ledger exists, build one first from the materials provided, show it in the output, and note which entries are unverified because the source text was not available this session. 各項目の出所・確認範囲・本文照合状態は `handoff-format.md` の共通規則に従って残す。

**Layer 1 — volume/segment scoring.** Done by normal scoring mode, treating the ledger as 併読資料. This upgrades provisional judgments into settled ones. The audit itself does not rescore volumes.

The 商業適合性レーン (non-scored commercial fitness check in `scoring-rubric.md`) is **out of scope for the audit**: the audit judges work-scale craft conditions only, and market-facing fitness items stay with whatever Layer 1 volume scoring requested them. The audit's ledger may record fitness facts (e.g. the one-line pitch as stated by the author) when they are already in hand, but never renders its own verdict on them — no points there either.

**Layer 2 — the audit proper.** Judge only the conditions that require work-wide visibility:

- 構成 8点条件（主筋全体での循環）and 9点条件
- キャラクター 9点条件（人物変化と世界変化の相互原因）
- 世界観 7〜9点条件のうち作品スケールでしか検証できない部分（例外の説明、3領域以上の相互参照）
- 感情設計 8点条件（テーマ場面と最強見せ場の同一性）— across arcs, not within one chapter
- 牽引力 8点条件の回収半分、「引きの空手形」「展開リズムの固定化」の上限規則
- 独自性 8・9点条件（主題・構成・人物設計への波及、前提要素の機能ごと置換）

Conditions outside this list belong to chapter scoring. If prior chapter judgments are available, do not re-judge them here; if they are not supplied, do not assume they exist or that no scoring has ever occurred.

## Procedure

1. **Collect**: ask for or load the 作品台帳 plus the volumes/arcs since the last audit. Without a ledger, build one before judging anything (see Layer 0).
2. **Re-sample early work**: re-read stratified samples from the earliest volumes included in this audit — do not trust earlier scores as evidence. Past numbers are reference history, not proof.
3. **Judge the listed conditions only**, each by the standard route: condition → quotation from the current sample or ledger entry with its source location → score impact.
4. **Report**: per condition — settled (with quotes), still pending (name exactly what future text would settle it; use a numeric pending mark only when its number is supported, per `score-anchors.md`), or overturned (the chapter-scale judgment does not survive work-scale evidence; say which chapter said what).
   - 追加資料は「未確認の条件／その判定に必要な範囲」を対応させて求める。抜粋しかない章を章全体の確認済みとして要求から外さない。作品全体の比較条件は、未読の主要場面や反証候補が残る間、最終章一つだけで確定できると約束しない。過去の採点記録が未提出であることを、採点歴がないことへ読み替えない。
   - 更新後の台帳と引き継ぎを出す前に、所見で付けた出所・確認範囲・未確認の留保が保たれているか照合する。追加の本文確認がなければ状態は上げない。本文不足でも、提出済みの実在する抜粋について引用付きの限定所見は返す。

## Episode indexing (章立て索引化) — before any counting

When working from raw text files rather than an existing ledger, index episodes first, and never assume the marker style:

- **Confirm the delimiter style first** by sampling pages/sections across the file (start, middle, end). Styles observed in practice: `第N話` headings; bare title lines after page breaks (no numbering at all); full-width numbered titles (`１．タイトル`); 前書き/後書き lines interleaved with the episode proper.
- **Index, then verify mechanically**: after building the episode list, check numbering integrity (missing/duplicate numbers), and sanity-check gap sizes between consecutive starts — a suspiciously small gap usually means a false-positive title (a skill name, a scene header), not an episode boundary.
- Record in the ledger how the index was built and its verified coverage (e.g. 「765話・欠落3話は合併で本文連続・重複1」). An unverified index poisons every count built on it.
- **場面区切り記号の様式も同じ手順で先に確認する。** 牽引力の4以下条件は「章末、および区切り記号で明示された場面末」を判定対象にするため（`score-anchors.md`）、区切り様式が分からないと対象を数えられない。様式は章立て表記と同様に作品ごとに異なり、実測では ＊ / ◇ / ◆ / ■ がそれぞれ別作品の主要記号だった。1章あたりの区切り数も 0.00〜1.93箇所と作品差が大きい。
  - **「・」の連続は区切り記号ではない。** 沈黙・絶句の表現（「・・・・」）であり、これを区切りとして数えると1作品で千件超の誤検出が出る。
  - **区切りを多用する作品は判定対象が増え、4以下条件の「2箇所以上」が統計的に発火しやすくなる。** 区切りの密度（箇所/章）を台帳に記録し、発火の判定時にこのバイアスを明示すること。
  - PDF抽出テキストでは改行が潰れて区切り記号が行内に埋没する。行単位の検出（行頭から行末までが記号だけの行）では拾えないので、前後の空白を境界とする検出に切り替える。

## Machine scanning vs. close reading (機械走査と精読の線引き)

At this scale, scripted scans (keyword frequency, hook-pattern detection, dialogue-density profiles) are tempting and partially useful. Their role is strictly limited:

- **Scans collect signals (兆候), never verdicts.** A count like 苦笑×0.88回/万字 is a fact about a pattern dictionary, not about prose quality. Patterns absent from the dictionary are invisible to it; a low count is therefore weak evidence of anything.
- **Every judgment must rest on close reading.** Before settling any condition, read representative passages in full context: at minimum 2–4 complete episodes per arc boundary under review, chosen to include the strongest candidates *for and against* the condition. Declare the total close-reading volume in the output (e.g. 「精読：約2.4万字／全体277万字の0.9%」). An audit that cannot state its reading volume is a scan wearing an audit's clothes.
- **Falsification pass is mandatory**: for each settled condition, actively search for scenes that would violate it before confirming it. Name what you searched for and what you found.
- Scans may direct attention (where to sample) and populate the ledger (counts for AI的紋切り型 accumulation), but the route condition → quotation → impact must run through text you actually read.

## Machine extraction in file-access environments (付録: 機械抽出手順)

This skill must stay portable to claude.ai (paste-only). In environments where scripts can read the manuscript files directly (local agent sessions, editors with shell access), the scans below become available. They follow the same boundary as 「機械走査と精読の線引き」: **signals only, never verdicts**, and every settled condition still requires declared close reading.

Procedure used and validated across three completed works (765 / 371 / 274 episodes):

1. **Load & clean**: strip page numbers and boilerplate; count clean characters as the work's size denominator.
2. **Index episodes** per the Episode indexing section above — confirm marker style first, then verify numbering integrity (gaps, duplicates) and gap-size sanity.
3. **Registers**: top-N proper-noun frequencies with first-appearance episode numbers (characters, systems, place names); first↔last mention distance for premise-tied names (long-range setup signal).
4. **Density profiles per decile or arc**: dialogue markers, action vocabulary, system/level keywords per 万字 — rhythm fixation and escalation signals.
5. **Tail-hook rate by third of the work**: last N characters of each episode checked against hook-pattern list; report counting rule. Within-work comparison only (cross-work rates range 0–16%; never an absolute anchor).
6. **Cliché counts**: fixed pattern dictionary (苦笑・思わず・頷く etc.) per 万字 → ledger accumulation for 文章 cap-rule checks. Absence from the dictionary is not absence from the text.
7. **章末の明示疑問を数えるときは会話文の相づちを除外する。** 末尾N字に「？」があるかで数えると、「ん？」「え？」「なに？」のような会話中の驚き・相づちを拾って率が数倍に膨らむ（実測で 9.5% が 35.6% に化けた）。除外条件は3つ: 判定範囲を章の最終2文に限る／間投詞のみの疑問文を落とす／疑問符の直前に4字以上の内容語があることを要求する。この補正を入れると商業作の章末明示疑問率は 0.4〜9.5% に収まる。
8. **回収距離の走査は代理指標であることを明示する。** 章末尾の特徴語が後続章に再出現するまでの距離は測れるが、それは「言及された」であって「回収された」ではない（同名の別事象や単なる語の再利用を拾うため過大評価方向に振れる）。上限規則「引きの空手形」の発火判定には、距離の数値ではなく該当箇所の精読と引用が必要。

前処理の共通注意（実測で確認済み）: ページ番号の数字行を除去しないと尾部分類が全て narrative に倒れる。後書きは `rfind` で切断する（位置が本文の30%より後ろのときのみ切る。著者挨拶は物語の尾ではない）。対話終了型は末尾60字では判定できないので末尾300〜500字の窓で見る。

Output of scans goes into the ledger as facts with their collection method stated (e.g. 「走査: pythonスクリプト・パターン辞書X件」), so the next session can tell machine-collected rows from close-reading-derived ones. In claude.ai (no script execution), these steps degrade to sampling by hand — do them on a declared sample basis or skip them and say so; do not fake numbers.

## Ledger standard items (Layer 0 の標準項目)

Beyond the format in `handoff-format.md`, a work-scale ledger should include these mechanically collectible items — they feed work-scale conditions that no chapter scoring can see:

- **Character register with first-appearance locations** (人物レジスタ＋初出話). A top-N register without first appearances hides 後半依存の配役 — major characters who arrive late and carry the ending.
- **Long-range setup distance**: for proper nouns tied to the premise or mysteries, record first mention ↔ last mention episode numbers. A seed planted in episode 1 and harvested 270 episodes later is direct evidence for 構成の循環 conditions; a name dropped once and never recovered is direct evidence against. Counts only; the interpretation still requires close reading of both endpoints.
- **Rhythm profile per decile/arc** (dialogue density, action density, median episode length): detects 展開リズムの固定化 and supports 牽引力上限規則 checks.
- **Tail-hook rate by third/arc**, with the counting rule stated. Rates differ wildly between works (observed range 0–16%); they are comparable within a work over time, not across works — never use one work's rate as an absolute anchor for another's.
- **Baseline separation by voice/mode**: when a work mixes POV voices or narration modes (一人称パート/三人称パート、視点キャラ別の章), keep density profiles and prose samples separated per voice. A cross-voice comparison produces misleading deviations — the same trap as comparing across works.
- **Baseline currency**: the ledger's density profiles represent the work *as it currently stands*. When later chapters are confirmed as representative (approved through scoring), refresh the profiles rather than freezing the chapter-1 snapshot; author voice evolves over long serials.

## Prose axis sampling rule (文章軸の標本抽出)

Full-text prose diagnosis is impossible at this scale; the axis is scored from a declared sample instead.

- Stratified extraction: from each volume in scope, take openings, climax scenes, dialogue-centered scenes, action scenes, and transition/connector scenes. Total 6–10 segments of roughly 500 characters per audit, spread across volumes — never all from one volume.
- Cap rules apply within the sample, with counts stated: e.g. 「AI的紋切り型の反復：標本内5箇所＋台帳累積11箇所」.
- The output line must declare its basis: 「文章：6（全12巻中4巻・10区画の標本に基づく）」. **A work-scale prose score without a declared basis is not a score** — same rule as everywhere else, extended.
- Ledger accumulation: when a chapter scoring found AI的紋切り型 or 表記ゆれ instances, they go into the ledger. The audit uses those accumulated counts alongside fresh samples.
- **語彙の水準逸脱**（`score-anchors.md` の上限規則）も同じ枠で扱う。作品規模では逸脱語が全編に散るため、標本内の該当箇所と台帳累積を併記して発火を判定する：「語彙の水準逸脱：標本内2箇所＋台帳累積4箇所」。ただし発火の前提として**作品の技術・文化水準が本文または設定資料で確定していること**が必要 — 確定していない作品ではこの規則を適用せず、その旨を出力に一行書く。判定するのは概念の逸脱のみで、語形（現代のカタカナ借用語）は診断観点として扱い上限規則には使わない。
- **台詞の識別性**（キャラクター6点条件の後半）は、標本の中から会話中心の場面を選び、主要人物の台詞を発話者名を伏せて並べて判定する。作品規模では登場人物が多いため、判定対象は台帳の人物レジスタ上位（出現頻度順）に限り、対象人物を出力に明示する。

## Drift control (the audit is where drift does maximum damage)

An audit spans dozens of sessions of prior scoring. Score inflation accumulated quietly across sessions surfaces here as "the series improved." It did not; the measuring got softer.

- Early-volume samples are re-read fresh every audit. Previous scores for them are recorded in the ledger as history, and carry zero evidential weight.
- When the audit overturns an earlier judgment, report both numbers and the reason. Do not silently update the ledger history.
- 才能・技術 in the handoff after an audit follow the derivation rules in `handoff-format.md`, using the audit's own numbers.

## Output skeleton

```markdown
## 監査の前提（対象範囲：第N巻〜第M巻／弧の完了状況／使用した台帳の版／章立て索引の作り方と検証結果）
## 台帳の確認と更新（Layer 0：今セッションで追記した事実のみ）
## 作品スケール条件の判定（Layer 2：条件ごとに 引用→判定→確定/保留/覆し）
## 文章軸 標本抽出結果（サンプル構成と宣言付き点数）
## 前回までの判定からの覆し（ある場合のみ：旧数値・新数値・理由）
## 次の弧へ回す項目
```

## Handoff

End with an updated 作品台帳 block (per `handoff-format.md`) plus the usual handoff data. The ledger is the deliverable the next session stands on — omitting it forfeits most of what the audit produced.
