// s05-rule：点の動かし方の原則（拍 40〜48）
// 拍40 出力カード「点は達成条件と引用でのみ動く。」を判子のように置く → 拍44・45 動画の声「褒めない。」「盛らない。」
HF.scene("s05-rule", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const card = S.find("stamp");
  const voices = S.ev.filter((e) => e.kind === "slam");

  S.css(`
    #s05-shake { position:absolute; inset:0; }
    #s05-cw { position:absolute; left:0; right:0; top:190px; display:flex; justify-content:center; }
    #s05-card .hf-card { box-shadow:16px 16px 0 var(--red); border-color:var(--paper); }
    #s05-vs { position:absolute; left:0; right:0; top:690px; display:flex; justify-content:center; gap:120px; }
    #s05-vs .hf-voice { color:var(--paper); }
  `);
  S.html(`
    <div class="hf-bg hf-ink"></div>
    <div id="s05-shake">
      <div id="s05-cw"><div id="s05-card" class="hf-hidden">${UI.card(card.text, { size: 92 })}</div></div>
      <div id="s05-vs">${voices.map((e, i) => `<div class="s05-v hf-hidden">${UI.voice(e.text, { size: 170 })}</div>`).join("")}</div>
    </div>
  `);

  const cardEl = S.q("#s05-card"), vs = S.qa(".s05-v");
  // 拍40：カードを判子のように押す＋衝撃
  M.stamp(tl, cardEl, card.t, { fromScale: 1.7, fromRot: -6, rot: -1.5 });
  M.shake(tl, "#s05-shake", card.t, { amp: 10, seed: 5 });
  M.breathe(tl, "#s05-cw", card.t + HF.beats(0.5), voices[0].t, { amt: 0.012 });
  // 拍44・45：動画の声を1拍ずつ叩きつける
  voices.forEach((e) => M.slam(tl, vs[e.i - voices[0].i], e.t));
  M.breathe(tl, "#s05-vs", voices[1].t + HF.beats(0.5), S.end, { amt: 0.015 });
});
