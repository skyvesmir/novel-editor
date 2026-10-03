// s13-norewrite：書き換えない（拍 116〜124、8拍。音は一旦引く）
// 拍116 T3 硬い切り：出力カード「大事な原稿は人の目でも確かめてください。」を1フレーム目から完成形で置き、
//   その上に動画の声「直すのは、誤字だけ。」を叩きつけ → 拍118「誤字だけ」に赤の下線（何に限るのかを指す）
// → 拍120（whoosh）声を一段引き、カードを前へ押し出して主役を渡す → 拍121〜124 止め（呼吸）
// v2：カードは proof の限界を伝える但し書き（20字）なので、v1 の拍120〜（1.6秒）でなく拍116〜124 の 2小節（3.2秒）出す
// 色は生成り・墨・赤の3色
HF.scene("s13-norewrite", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const voice = S.find("slam"); // 拍116。text は動画の声（video）
  const card = S.find("whoosh"); // 拍120。text は出力（output:proof）

  // 声の強調「誤字だけ」（声の連続した一部）。つなげると原文に戻ることを確かめる
  const KEY = "誤字だけ";
  const kk = voice.text.indexOf(KEY);
  if (kk < 0) throw new Error("s13: 声に「誤字だけ」がない");
  const vHtml = `${HF.esc(voice.text.slice(0, kk))}<span class="s13-key">${HF.esc(KEY)}</span>${HF.esc(voice.text.slice(kk + KEY.length))}`;

  S.css(`
    #s13-vg { position:absolute; left:0; right:0; top:0; height:560px; display:flex; align-items:center; justify-content:center; padding-top:20px; }
    #s13-vw { position:relative; display:block; }
    #s13-v { display:block; }
    #s13-cw { position:absolute; left:0; right:0; top:560px; display:flex; justify-content:center; }
    #s13-card { transform-origin:50% 40%; }
    #s13-card .hf-card { padding:88px 64px 52px; }
    #s13-card .hf-card-body { white-space:nowrap; }
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s13-vg"><div id="s13-vw"><div id="s13-v" class="hf-hidden"><div class="hf-voice" style="font-size:124px">${vHtml}</div></div></div></div>
    <div id="s13-cw"><div id="s13-card" class="hf-hidden">${UI.card(card.text, { size: 76 })}</div></div>
  `);
  if (S.q("#s13-v .hf-voice").textContent !== voice.text) throw new Error("s13: 声の文字が原文と一致しない");
  if (S.q("#s13-card .hf-card-body").textContent !== card.text) throw new Error("s13: カード本文が出力と一致しない");

  const vw = S.q("#s13-vw"), vEl = S.q("#s13-v");
  const ul = UI.underline(vw, S.q(".s13-key"), { gap: 2, width: 12, seed: 17 });

  // 拍116：硬い切り（T3）。カードは1フレーム目から完成形で置き、声を叩きつける
  M.show(tl, "#s13-card", voice.t);
  M.slam(tl, vEl, voice.t, { from: 1.4, y: -30 });
  // 拍118：「誤字だけ」に赤の下線（直す範囲が誤字に限られることを指す）
  const t118 = S.at(voice.beat + 2);
  tl.set(".s13-key", { color: HF.COLORS.red }, t118);
  M.scribble(tl, ul, t118, HF.beats(0.5));
  M.breathe(tl, vw, voice.t + HF.beats(0.5), card.t, { amt: 0.015 });
  // 拍120（whoosh）：声を一段引いて（薄く）、カードを前へ押し出す。語彙外：読む主役が声から但し書きに移ったことを示す
  tl.fromTo("#s13-vg", { opacity: 1 }, { opacity: 0.45, duration: HF.beats(0.5), ease: "power2.out", immediateRender: false }, card.t);
  tl.fromTo("#s13-card", { scale: 1, y: 0 }, { scale: 1.04, y: -24, duration: HF.beats(0.5), ease: "power3.out", immediateRender: false }, card.t);
  M.breathe(tl, "#s13-cw", voice.t + HF.beats(0.5), S.end, { amt: 0.01, period: HF.beats(3) });
});
