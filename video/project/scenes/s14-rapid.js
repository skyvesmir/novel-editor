// s14-rapid：連打 → 白フラッシュ（拍 124〜136、12拍）
// 拍124〜127 4分音符ごとに T1 全面色替え＋7軸の名前を叩きつけ → 拍128・128⅓・128⅔ T7 連打（三連符＝4フレーム）
// → 拍129〜131 最後の「文章」がライザーに合わせて迫ってくる → 拍131 溜め（無音。僅かに引く）
// → 拍132 白フラッシュ（最大の一撃）→ 生成りに7軸すべてを一度に叩きつけ、拍136 まで止め（連打で読めなかった7つを読ませる）
// 色は青・墨・生成りの3色（＋白フラッシュ2フレーム）
HF.scene("s14-rapid", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui, COL = HF.COLORS;
  const slams = S.ev.filter((e) => e.kind === "slam"); // 7つ。text は出力の軸名（output:score）
  const rest = S.find("silence"); // 拍131
  const peak = S.find("impact"); // 拍132
  if (slams.length !== 7) throw new Error("s14: 軸名の slam が7つでない");

  const BG = [COL.blue, COL.ink, COL.paper, COL.blue, COL.ink, COL.paper, COL.blue];
  const FG = [COL.paper, COL.paper, COL.ink, COL.paper, COL.paper, COL.ink, COL.paper];
  const sizeOf = (s) => Math.min(380, Math.floor(1600 / [...s].length));

  S.css(`
    #s14-bg { background:var(--blue); }
    .s14-w { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding-bottom:30px; }
    .s14-wi { position:relative; display:block; }
    #s14-end { position:absolute; inset:0; background:var(--paper); opacity:0; }
    #s14-shake { position:absolute; inset:0; }
    #s14-gw { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; }
    #s14-g { display:flex; flex-direction:column; align-items:center; gap:40px; }
    .s14-row { display:flex; justify-content:center; gap:34px; }
    .s14-row span { font-family:var(--f-slam); font-size:124px; line-height:1; color:var(--ink); padding:20px 36px 30px;
      border:6px solid var(--ink); background:var(--paper); white-space:nowrap; }
  `);
  const rows = [slams.slice(0, 3), slams.slice(3, 5), slams.slice(5)]; // 3・2・2 段（字を大きく保つ）
  S.html(`
    <div id="s14-bg" class="hf-bg"></div>
    ${slams.map((e, i) => `<div class="s14-w hf-hidden" data-i="${i}"><div class="s14-wi">${UI.voice(e.text, { size: sizeOf(e.text) })}</div></div>`).join("")}
    <div id="s14-end" class="hf-paper">
      <div id="s14-shake"><div id="s14-gw"><div id="s14-g" class="hf-hidden">${rows
        .map((r) => `<div class="s14-row">${r.map((e) => `<span>${HF.esc(e.text)}</span>`).join("")}</div>`)
        .join("")}</div></div></div>
    </div>
    <div id="s14-flash" class="hf-flash"></div>
  `);

  const ws = S.qa(".s14-w"), bg = S.q("#s14-bg");

  // ---- 拍124〜128⅔：色替え＋叩きつけ。前の語はその拍で消す（1語ずつ別要素。逆 seek でも戻る）
  slams.forEach((e, i) => {
    M.bg(tl, bg, e.t, BG[i]);
    if (i > 0) M.hide(tl, ws[i - 1], e.t);
    tl.set(ws[i].querySelector(".hf-voice"), { color: FG[i] }, e.t);
    // 4分音符は大きく、三連の連打は小さめの振れ幅（4フレームに収める）
    M.slam(tl, ws[i], e.t, i < 4 ? { from: 1.6 } : { from: 1.3, y: -20 });
  });

  // ---- 拍129〜131：最後の「文章」がライザーに合わせて迫る（上昇の緊張を絵にする）
  const last = ws[6].querySelector(".s14-wi");
  const t129 = S.at(Math.ceil(slams[6].beat)); // 「文章」の次の拍頭（拍129）
  tl.fromTo(last, { scale: 1 }, { scale: 1.45, duration: rest.t - t129, ease: "power2.in", immediateRender: false }, t129);
  // ---- 拍131：溜め（無音）。僅かに引く（一撃の前の逆向きの動き）
  tl.fromTo(last, { scale: 1.45 }, { scale: 1.3, duration: peak.t - rest.t, ease: "power2.out", immediateRender: false }, rest.t);

  // ---- 拍132：白フラッシュ → 生成りに7軸を一度に叩きつけ＋衝撃 → 止め
  M.hide(tl, ws[6], peak.t);
  M.flash(tl, "#s14-flash", peak.t, { frames: 3 });
  M.show(tl, "#s14-end", peak.t);
  M.slam(tl, "#s14-g", peak.t, { from: 1.35, y: -30 });
  M.shake(tl, "#s14-shake", peak.t, { amp: 14, seed: 132, dur: HF.beats(0.75) });
  M.breathe(tl, "#s14-gw", peak.t + HF.beats(0.75), S.end, { amt: 0.015 });
});
