// s06-prose：文章：要約的な締めの一文×3（拍 48〜56）
// 拍48 出力カード「要約的な締めの一文が3箇所ある」（札「文章 5/10」）が右から滑り込み、下に原稿の3文
// → 拍49・50・51 各文の「…と思った。」を赤丸（scribble）→ 文全体に取り消し線（strike）。3つ目だけ shake
// → 拍52 カードの「3箇所」に赤の下線（3つの指摘と出力の数を結ぶ）→ 拍53〜56 止め（breathe）
HF.scene("s06-prose", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const head = S.find("whoosh"); // 拍48。text は出力（output:score）
  const hits = S.ev.filter((e) => e.kind === "slash"); // 拍49・50・51（text は原稿の文）

  // 各文を「本体」と「締め（最後の『、』の後ろ＝と…思った。）」に分ける。つなげると原文に戻ることを確かめる
  const parts = hits.map((e) => {
    const k = e.text.lastIndexOf("、") + 1;
    const p = [e.text.slice(0, k), e.text.slice(k)];
    if (k <= 0 || p.join("") !== e.text || !/思った。$/.test(p[1])) throw new Error("s06: 原稿の文の分割が原文と一致しない: " + e.text);
    return p;
  });
  // カード本文の強調「3箇所」（出力の連続した一部）。つなげると出力と同じことを確かめる
  const KEY = "3箇所";
  const kk = head.text.indexOf(KEY);
  if (kk < 0) throw new Error("s06: 出力に「3箇所」がない");
  const cardHtml = `${HF.esc(head.text.slice(0, kk))}<span class="s06-key">${HF.esc(KEY)}</span>${HF.esc(head.text.slice(kk + KEY.length))}`;

  S.css(`
    #s06-cw { position:absolute; left:90px; top:120px; }
    #s06-card { position:relative; display:block; }
    #s06-card .hf-card { padding:84px 64px 44px; }
    #s06-card .hf-card-body { white-space:nowrap; }
    #s06-card > .s06-score { position:absolute; right:40px; top:-36px; z-index:2; }
    #s06-msw { position:absolute; left:70px; top:500px; width:1760px; transform-origin:0% 0%; }
    #s06-ms { position:relative; width:1760px; }
    #s06-ms p { font-size:60px; line-height:1.5; margin-bottom:70px; white-space:nowrap; }
    .s06-end { margin-left:0.3em; } /* 赤丸が読点に掛からないための間 */
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s06-cw"><div id="s06-card">${UI.card(head.text, { size: 80, html: cardHtml })}${UI.tag("文章 5/10", "s06-score")}</div></div>
    <div id="s06-msw"><div id="s06-ms" class="hf-ms">${parts
      .map((p, i) => `<p><span class="hf-strike s06-s" data-i="${i}">${HF.esc(p[0])}<span class="s06-end">${HF.esc(p[1])}</span></span></p>`)
      .join("")}</div></div>
  `);
  if (S.q("#s06-card .hf-card-body").textContent !== head.text) throw new Error("s06: カード本文が出力と一致しない");

  const ms = S.q("#s06-ms"), sents = S.qa(".s06-s"), ends = S.qa(".s06-end");
  // 位置を測る部品は動かす前に
  const circles = ends.map((el, i) => UI.circleAround(ms, el, { pad: 8, width: 8, seed: 31 + i }));
  const cardIn = S.q("#s06-card");
  const keyLine = UI.underline(cardIn, S.q(".s06-key"), { gap: 2, width: 9, seed: 12 });

  // 拍48：カードが右から滑り込む（whoosh。s03 の吹き出しと同じ入り）。原稿の3文は1フレーム目から置いてある
  tl.fromTo("#s06-cw", { x: 260, scale: 0.94 }, { x: 0, scale: 1, duration: HF.beats(0.5), ease: "power4.out", immediateRender: false }, head.t);

  // 拍49・50・51：締めを赤くして赤丸 → 半拍後に文全体を取り消し → 墨を薄く
  hits.forEach((e, i) => {
    tl.set(ends[i], { color: HF.COLORS.red }, e.t);
    M.scribble(tl, circles[i], e.t, HF.beats(0.5));
    M.strike(tl, sents[i], e.t + HF.beats(0.5));
    tl.set(sents[i], { color: "rgba(20,17,15,0.5)" }, e.t + HF.beats(0.75));
  });
  M.shake(tl, ms, hits[2].t + HF.beats(0.5), { amp: 10, seed: 63 }); // 3つ目が刺さった衝撃（毎拍は使わない）

  // 拍52：出力の「3箇所」に赤の下線（いま刺した3文が出力の数と一致することを示す）
  const t52 = S.at(hits[2].beat + 1);
  tl.set(".s06-key", { color: HF.COLORS.red }, t52);
  M.scribble(tl, keyLine, t52, HF.beats(0.5));
  // 止めの微動
  M.breathe(tl, "#s06-card", head.t + HF.beats(0.5), S.end, { amt: 0.012, period: HF.beats(4) });
  M.breathe(tl, "#s06-msw", S.at(hits[2].beat + 1.5), S.end, { amt: 0.015 });
});
