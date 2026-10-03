// s13-norewrite：書き換えない（拍 116〜124、8拍。音は一旦引く）
// 拍116 T3 硬い切りで、動画の声「直すのは、誤字だけ。」を叩きつけ → 拍118「誤字だけ」に赤の下線（何に限るのかを指す）
// → 拍120 声が上へ退き、出力カード「大事な原稿は人の目でも確かめてください。」を静かに置く（whoosh）→ 拍121〜124 止め（呼吸）
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
    #s13-vg { position:absolute; left:0; right:0; top:0; height:1080px; display:flex; align-items:center; justify-content:center; padding-bottom:40px; }
    #s13-vw { position:relative; display:block; }
    #s13-v { display:block; }
    #s13-cw { position:absolute; left:0; right:0; top:560px; display:flex; justify-content:center; }
    #s13-card .hf-card { padding:88px 64px 52px; }
    #s13-card .hf-card-body { white-space:nowrap; }
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s13-vg"><div id="s13-vw"><div id="s13-v" class="hf-hidden"><div class="hf-voice" style="font-size:150px">${vHtml}</div></div></div></div>
    <div id="s13-cw"><div id="s13-card" class="hf-hidden">${UI.card(card.text, { size: 76 })}</div></div>
  `);
  if (S.q("#s13-v .hf-voice").textContent !== voice.text) throw new Error("s13: 声の文字が原文と一致しない");
  if (S.q("#s13-card .hf-card-body").textContent !== card.text) throw new Error("s13: カード本文が出力と一致しない");

  const vw = S.q("#s13-vw"), vEl = S.q("#s13-v");
  const ul = UI.underline(vw, S.q(".s13-key"), { gap: 2, width: 14, seed: 17 });

  // 拍116：硬い切りで声を叩きつける（1フレーム目で着地寸前の完成形）
  M.slam(tl, vEl, voice.t, { from: 1.4, y: -30 });
  // 拍118：「誤字だけ」に赤の下線（直す範囲が誤字に限られることを指す）
  const t118 = S.at(voice.beat + 2);
  tl.set(".s13-key", { color: HF.COLORS.red }, t118);
  M.scribble(tl, ul, t118, HF.beats(0.5));
  M.breathe(tl, vw, voice.t + HF.beats(0.5), card.t, { amt: 0.015 });
  // 拍120：声が上へ退いて場所を空ける（主役がカードに移る）→ カードを静かに置く
  tl.fromTo("#s13-vg", { y: 0, scale: 1 }, { y: -260, scale: 0.8, duration: HF.beats(0.5), ease: "power3.out", immediateRender: false }, card.t);
  M.place(tl, "#s13-card", card.t, { y: 30, dur: HF.beats(0.75) });
  M.breathe(tl, "#s13-cw", card.t + HF.beats(0.75), S.end, { amt: 0.01, period: HF.beats(3) });
});
