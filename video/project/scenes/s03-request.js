// s03-request：採点の依頼（拍 24〜32）。実際の依頼文を吹き出しで打つ → 拍28「厳しめで」に赤丸
HF.scene("s03-request", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const req = S.find("whoosh"); // 拍24。text = 依頼文（input）
  const types = S.ev.filter((e) => e.kind === "type"); // 拍24.5〜27 の6回
  const pen = S.find("pen"); // 拍28。text =「厳しめで」

  // 依頼文を6つに分けて打つ（つなげると依頼文と一字一句同じになることを下で確かめる）
  const chunks = [
    { text: "これ、" },
    { text: "来週なろうに" },
    { text: "投稿する予定の" },
    { text: "1話です。" },
    { text: pen.text, cls: "s03-key", nl: true },
    { text: "評価してください。" },
  ];
  if (chunks.map((c) => c.text).join("") !== req.text) throw new Error("s03: 依頼文の分割が原文と一致しない");
  if (chunks.length !== types.length) throw new Error("s03: 文字送りの回数と分割数が合わない");

  S.css(`
    #s03-wrap { position:absolute; inset:0; display:flex; align-items:center; justify-content:flex-end; padding:0 100px 40px 0; }
    #s03-b { position:relative; display:block; }
    #s03-b .hf-bubble { width:1720px; font-size:74px; }
    #s03-b .s03-key { margin:0 0.45em 0 0.2em; } /* 赤丸が隣の字に掛からないための間 */
    #s03-b > .hf-tag { position:absolute; left:40px; top:-36px; z-index:2; }
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s03-wrap"><div id="s03-b" class="hf-hidden">${UI.tag("依頼")}${UI.bubble(chunks)}</div></div>
  `);

  const box = S.q("#s03-b"), spans = S.qa(".hf-chunk");
  const key = S.q(".s03-key");
  const circle = UI.circleAround(S.q("#s03-b"), key, { pad: 20, width: 10, seed: 4 });

  // 拍24：吹き出しが右から滑り込む（whoosh。入りは急、止めは長め）
  M.show(tl, box, req.t);
  tl.fromTo(box, { x: 260, scale: 0.92 }, { x: 0, scale: 1, duration: HF.beats(0.5), ease: "power4.out", immediateRender: false }, req.t);
  // 拍24.5〜27：文字送り（裏拍ごとに1かたまり）
  types.forEach((e, i) => M.show(tl, spans[i], e.t));

  // 拍28：「厳しめで」だけ赤くし、赤丸を手で描く
  tl.set(key, { color: HF.COLORS.red }, pen.t);
  M.scribble(tl, circle, pen.t, HF.beats(0.75));
  // ハーフタイムの止め：吹き出しがゆっくり呼吸
  M.breathe(tl, box, req.t + HF.beats(1), S.end, { amt: 0.012, period: HF.beats(4) });
});
