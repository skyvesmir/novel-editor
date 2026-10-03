// s09-fix3：今回直すのはこの3件（拍 72〜80）
// 拍72 硬い切りで墨の画面、出力の見出し「今回直すのはこの3件」を出力カードで叩きつけ
// → 拍74・75・76 番号札「改善案4」「改善案5」「改善案7」を判子で押す（3つ目で衝撃）→ 止め
HF.scene("s09-fix3", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const head = S.find("slam"); // 拍72。text は出力の見出し（output:score）
  const stamps = S.ev.filter((e) => e.kind === "stamp"); // 拍74・75・76（output:score）
  const ROT = [-4, 3, -2]; // 押した判子が揃いすぎないよう角度を散らす

  S.css(`
    #s09-cw { position:absolute; left:0; right:0; top:150px; display:flex; justify-content:center; }
    #s09-card { display:block; }
    #s09-card .hf-card { box-shadow:16px 16px 0 var(--red); border-color:var(--paper); }
    #s09-row { position:absolute; left:0; right:0; top:640px; display:flex; justify-content:center; gap:60px; }
    .s09-sw { display:block; }
  `);
  S.html(`
    <div class="hf-bg hf-ink"></div>
    <div id="s09-cw"><div id="s09-card" class="hf-hidden">${UI.card(head.text, { size: 120 })}</div></div>
    <div id="s09-row">${stamps.map((e) => `<div class="s09-sw"><div class="s09-st hf-hidden">${UI.stampBox(e.text, { size: 96 })}</div></div>`).join("")}</div>
  `);

  const sts = S.qa(".s09-st");
  // 拍72：見出しを叩きつける（1フレーム目から着地寸前の形で出る）
  M.slam(tl, "#s09-card", head.t, { from: 1.4, y: -30 });
  M.breathe(tl, "#s09-cw", head.t + HF.beats(0.75), S.end, { amt: 0.012, period: HF.beats(2) });
  // 拍74・75・76：番号札を判子で
  stamps.forEach((e, i) => M.stamp(tl, sts[i], e.t, { fromScale: 2.2, fromRot: ROT[i] * 2, rot: ROT[i] }));
  M.shake(tl, "#s09-row", stamps[2].t, { amp: 12, seed: 76 });
  S.qa(".s09-sw").forEach((w, i) => M.breathe(tl, w, stamps[2].t + HF.beats(0.5), S.end, { amt: 0.02, period: HF.beats(2) }));
});
