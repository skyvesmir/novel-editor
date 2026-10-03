// s01-hook：掴み「刺す」（拍 0〜16）
// 1フレーム目から原稿の冒頭3文。拍0・1・2で赤ペンが1文ずつ刺す → 拍3 溜め → 拍4 判子「冒頭の掴み：提示なし。」
// → 拍8・9・10「疑問」「異常」「危機」を T1 で slam → 拍11 溜め → 拍12 判子「…を示す箇所を引用できない。」（ドロップ）
HF.scene("s01-hook", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui, B = HF.BEAT, FR = HF.FR, COL = HF.COLORS;
  const slash = S.ev.filter((e) => e.kind === "slash"); // 拍0・1・2（text は原稿の3文）
  const stamps = S.ev.filter((e) => e.kind === "stamp"); // 拍4・12
  const slams = S.ev.filter((e) => e.kind === "slam"); // 拍8・9・10
  const rests = S.ev.filter((e) => e.kind === "silence"); // 拍3・11

  S.css(`
    #s01-ms { position:absolute; left:110px; top:47%; width:1700px; transform:translateY(-50%); }
    #s01-ms p { font-size:70px; line-height:1.62; }
    #s01-dim { position:absolute; inset:0; background:var(--paper); opacity:0; }
    #s01-st1o, #s01-st2o { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; }
    #s01-st2o { padding-top:250px; }
    .s01-stw { position:relative; display:block; }
    .s01-stw > .hf-tag { position:absolute; left:-10px; top:-92px; }
    #s01-words { position:absolute; left:0; right:0; top:215px; display:flex; justify-content:center; gap:44px; opacity:0; }
    #s01-words span { font-family:var(--f-slam); font-size:120px; line-height:1; color:var(--ink); padding:14px 30px 22px; border:6px solid var(--ink); background:var(--paper); }
    #s01-slam { position:absolute; inset:0; opacity:0; background:var(--yellow); }
    .s01-w { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; opacity:0; }
    #s01-flash { background:var(--red); }
  `);

  // 原稿は cues の text（manuscript）を一字一句。段落頭の全角空白は原稿どおり
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s01-shake" class="hf-layer">
      <div id="s01-ms" class="hf-ms"><p>　${slash.map((e, i) => `<span class="hf-strike s01-s" data-i="${i}">${HF.esc(e.text)}</span>`).join("")}</p></div>
      <div id="s01-dim"></div>
      ${UI.pen({ id: "s01-pen" })}
      <div id="s01-st1o"><div id="s01-st1" class="s01-stw hf-hidden">${UI.tag("novel-editor の出力")}${UI.stampBox(stamps[0].text, { size: 124 })}</div></div>
      <div id="s01-words">${slams.map((e) => `<span>${HF.esc(e.text)}</span>`).join("")}</div>
      <div id="s01-st2o"><div id="s01-st2" class="s01-stw hf-hidden">${UI.tag("novel-editor の出力")}${UI.stampBox(stamps[1].text, { size: 104 })}</div></div>
    </div>
    <div id="s01-slam">${slams.map((e, i) => `<div class="s01-w" data-i="${i}"><div class="s01-wi">${UI.voice(e.text, { size: 380 })}</div></div>`).join("")}</div>
    <div id="s01-flash" class="hf-flash"></div>
  `);

  // 意図した重ね：取り消して薄くした原稿の上に判子・札・3語を載せる。色替え層は判子を覆う
  HF.allowOverlap(S.qa(".s01-s, .s01-stw .hf-tag, .s01-stw .hf-stamp, #s01-words span, .s01-w .hf-voice"));

  const stage = S.stage, shakeEl = S.q("#s01-shake"), pen = S.q("#s01-pen");
  const sents = S.qa(".s01-s");

  // ---- 赤ペンの先端を置く座標：各文の最初の行の左端・行の中央（測ってから動かす）
  const sb = stage.getBoundingClientRect(), k = sb.width / stage.offsetWidth;
  const tips = sents.map((sp) => {
    const r = sp.getClientRects()[0];
    return { x: (r.left - sb.left) / k + 6, y: (r.top - sb.top) / k + r.height / k * 0.58 };
  });
  const PEN_H = 72, ROT = -32;
  const penAt = (p) => ({ x: p.x, y: p.y - PEN_H / 2 });
  pen.style.left = "0px";
  pen.style.top = "0px";

  // ---- 拍0・1・2：刺す（strike＋shake）
  slash.forEach((e, i) => {
    const p = penAt(tips[i]);
    if (i === 0) {
      // 1フレーム目：ペンはもう刺さっていて、線は走り出している（「何かが起きた後」から始める）
      tl.set(pen, { opacity: 1, x: p.x, y: p.y, rotation: ROT }, e.t);
      tl.fromTo(sents[i], { backgroundSize: "30% 0.13em" }, { backgroundSize: "100% 0.13em", duration: HF.beats(0.25), ease: "power3.out", immediateRender: false }, e.t);
      M.shake(tl, shakeEl, e.t, { amp: 14, seed: 11 });
    } else {
      // 前の文から持ち上げて運び、最後の4フレームで加速して刺す（拍頭に先端が着く）
      const prev = slash[i - 1].t;
      tl.fromTo(pen, { x: penAt(tips[i - 1]).x, y: penAt(tips[i - 1]).y }, { x: p.x + 40, y: p.y - 70, duration: e.t - 4 * FR - (prev + 3 * FR), ease: "power2.inOut", immediateRender: false }, prev + 3 * FR);
      tl.fromTo(pen, { x: p.x + 40, y: p.y - 70 }, { x: p.x, y: p.y, duration: 4 * FR, ease: "power4.in", immediateRender: false }, e.t - 4 * FR);
      M.strike(tl, sents[i], e.t);
      // 2文目は shake を省き（毎拍は使わない）、3文目でもう一度強く揺らす
      if (i === 2) M.shake(tl, shakeEl, e.t, { amp: 12, seed: 23 });
      else M.squash(tl, pen, e.t, { to: 0.8 }); // ペン先が押し込まれる（刺した手応え）
    }
    // 刺された文は墨を薄くする（取り消された印）
    tl.set(sents[i], { color: "rgba(20,17,15,0.5)" }, e.t + 3 * FR);
  });

  // ---- 拍3：溜め。ペンがゆっくり持ち上がる（逆方向の小さな動き）
  const lift = penAt(tips[2]);
  tl.fromTo(pen, { x: lift.x, y: lift.y, rotation: ROT }, { x: lift.x + 90, y: lift.y - 150, rotation: ROT - 10, duration: HF.beats(1.5), ease: "power2.out", immediateRender: false }, slash[2].t + 3 * FR);

  // ---- 拍4：判子「冒頭の掴み：提示なし。」（4拍止める）
  const st1 = S.q("#s01-st1"), st1o = S.q("#s01-st1o");
  M.hide(tl, pen, stamps[0].t);
  tl.set("#s01-dim", { opacity: 0.6 }, stamps[0].t);
  M.stamp(tl, st1, stamps[0].t, { fromScale: 2.2 });
  M.shake(tl, shakeEl, stamps[0].t, { amp: 14, seed: 41 });
  M.breathe(tl, st1o, stamps[0].t + HF.beats(0.5), slams[0].t, { amt: 0.025 }); // 止めの微動

  // ---- 拍8・9・10：T1 全面色替え＋slam（黄・青・墨）
  const bgs = [COL.yellow, COL.blue, COL.ink], fgs = [COL.ink, COL.paper, COL.paper];
  const slamLayer = S.q("#s01-slam"), words = S.qa(".s01-w");
  M.show(tl, slamLayer, slams[0].t);
  M.hide(tl, st1, slams[0].t); // 色替え層の下に隠れる判子は消しておく（覆われた文字のコントラスト警告を出さない）
  slams.forEach((e, i) => {
    M.bg(tl, slamLayer, e.t, bgs[i]);
    if (i > 0) M.hide(tl, words[i - 1], e.t);
    tl.set(words[i].querySelector(".hf-voice"), { color: fgs[i] }, e.t);
    M.slam(tl, words[i], e.t, { from: 1.7 });
  });
  // ---- 拍11：溜め。「危機」が僅かに縮む（次の一撃の前の逆向きの動き）
  tl.fromTo(words[2].querySelector(".s01-wi"), { scale: 1 }, { scale: 0.9, duration: HF.beats(1), ease: "power2.in", immediateRender: false }, rests[1].t);

  // ---- 拍12：ドロップ。紙に戻り、判子「…を示す箇所を引用できない。」＋shake＋拍フラッシュ
  const st2 = S.q("#s01-st2"), st2o = S.q("#s01-st2o"), t12 = stamps[1].t;
  M.hide(tl, slamLayer, t12);
  tl.set("#s01-dim", { opacity: 0.8 }, t12);
  M.show(tl, "#s01-words", t12);
  M.flash(tl, "#s01-flash", t12, { opacity: 0.9 });
  M.stamp(tl, st2, t12, { fromScale: 2.4, rot: -3 });
  M.shake(tl, shakeEl, t12, { amp: 14, seed: 77, dur: HF.beats(0.75) });
  M.breathe(tl, st2o, t12 + HF.beats(0.75), S.end, { amt: 0.02 });
});
