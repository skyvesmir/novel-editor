// s04-axes：7軸の点数（拍 32〜40）
// 拍32 7軸の枠が pop-stagger で並ぶ（数字は空）。数字は裏拍から count-up して拍頭に着地（拍32〜38）。拍39 溜め
// 点数は skill-output-score.md の「点数：N/10」を写す。牽引力だけ出力が「5（回収未検証）/10」なので注記も同じ順（数字→注記→/10）で写す
HF.scene("s04-axes", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const ticks = S.ev.filter((e) => e.kind === "tick"); // 7件。text=軸名、score=点
  const drop = S.find("drop");
  const NOTE = { 牽引力: "（回収未検証）" }; // 出力の点数行の注記（一字一句）

  S.css(`
    #s04-head { position:absolute; left:330px; top:56px; }
    #s04-list { position:absolute; left:330px; right:330px; top:160px; bottom:40px; display:flex; flex-direction:column; }
    .s04-row { flex:1; display:flex; align-items:center; border-bottom:4px solid rgba(20,17,15,0.18); }
    .s04-row:first-child { border-top:4px solid rgba(20,17,15,0.18); }
    .s04-name { flex:none; width:540px; padding-left:20px; font-family:var(--f-ui); font-weight:900; font-size:66px; color:var(--ink); line-height:1; }
    .s04-sc { flex:none; display:flex; align-items:flex-end; gap:8px; }
    /* 「/10」の列を全行でそろえる：注記は「/10」の上に積む（読む順は 数字→注記→/10 のまま） */
    .s04-tail { position:relative; display:flex; flex-direction:column; align-items:flex-start; padding-bottom:6px; }
    .s04-tail > .s04-note { position:absolute; left:0; bottom:100%; margin:0 0 2px 0; }
    .s04-row.s04-tall { flex:1.3; padding-top:16px; } /* 注記を積む行だけ少し高くして、注記が罫線と「/10」に触れないようにする */
    .s04-num { width:190px; justify-content:end; font-size:100px; line-height:1; color:var(--red); }
    .s04-num > span { text-align:right; }
    .s04-den { font-family:var(--f-slam); font-size:60px; color:var(--ink); line-height:1; }
    .s04-note { font-family:var(--f-ui); font-weight:500; font-size:52px; color:var(--ink); line-height:1; margin:0 4px 0 -4px; flex:none; white-space:nowrap; }
    .s04-in { display:flex; align-items:center; width:100%; transform-origin:0% 50%; }
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s04-head" class="hf-hidden">${UI.tag("novel-editor の出力")}</div>
    <div id="s04-list">
      ${ticks
        .map(
          (e) => `<div class="s04-row${NOTE[e.text] ? " s04-tall" : ""}"><div class="s04-in hf-hidden">
            <div class="s04-name">${HF.esc(e.text)}</div>
            <div class="s04-sc"><div class="s04-nw"><span class="hf-num s04-num"></span></div><div class="s04-tail">${NOTE[e.text] ? `<span class="s04-note s04-nt hf-hidden">${HF.esc(NOTE[e.text])}</span>` : ""}<span class="s04-den">/10</span></div></div>
          </div></div>`
        )
        .join("")}
    </div>
  `);

  const rows = S.qa(".s04-in"), nums = S.qa(".s04-num"), wraps = S.qa(".s04-nw");
  // 注記は「/10」の真上に積んでいる。字面は離れているが（原寸で約13px）、字の箱（line-height 1 を超える高さ）が「/10」に触れるので check に意図を伝える
  HF.allowOverlap(S.qa(".s04-nt"));

  // 拍32：札と7軸の枠が裏拍刻み（1/8拍）で次々に出る
  M.show(tl, "#s04-head", drop.t);
  M.popStagger(tl, rows, drop.t, { from: 0.6 });

  // 数字：count-up（1→点。0 を出すと0点に見えるので1から）。裏拍で走り出し、拍頭（チックの音）に着地して判子のように弾む
  ticks.forEach((e, i) => {
    const target = e.score;
    const whole = Math.floor(parseFloat(target));
    const values = [];
    for (let v = 1; v <= whole; v++) values.push(String(v));
    if (values[values.length - 1] !== target) values.push(target); // 4.5 は 4 の次に 4.5
    const t0 = i === 0 ? e.t : e.t - HF.beats(0.5); // 最初の軸は拍32ちょうどに着地（前の拍は s03）
    if (i === 0) M.countUp(tl, nums[i], [target], e.t, e.t);
    else M.countUp(tl, nums[i], values, t0, e.t);
    M.stamp(tl, wraps[i], e.t, { fromScale: 1.6, fromRot: -6, rot: 0 });
    const note = rows[i].querySelector(".s04-nt");
    if (note) M.show(tl, note, e.t);
  });

  // 拍39：溜め。並んだ数字の列が僅かに呼吸
  M.breathe(tl, "#s04-list", S.find("silence").t, S.end, { amt: 0.01, period: HF.beats(2) });
});
