// s12-typos：誤字5件（拍 96〜116、20拍。1小節に1件）
// 各件：小節頭（slash）で原稿の該当箇所の語に赤の取り消し線＋種類の札を押す → 2拍後（pen）の直前に引き出し線、pen の拍頭から正しい形を書き込む
// 件の切り替えは小節頭の硬い切り（T3）。赤ペンは刺した位置から書き込む位置へゆっくり移り（溜め）、書く拍で正しい形をなぞる。
// 5件目（表記ゆれ）はどちらも誤りではないので、取り消し線でなく2語を赤丸で囲む（出力「どちらかに統一」と矛盾させない）
// 色は生成り・墨・赤の3色
HF.scene("s12-typos", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui, FR = HF.FR;
  const slash = S.ev.filter((e) => e.kind === "slash"); // 拍96・100・104・108・112（text＝原稿の語、label＝出力の種類）
  const pens = S.ev.filter((e) => e.kind === "pen"); // 拍98・102・106・110・114（text＝出力の正しい形）
  if (slash.length !== 5 || pens.length !== 5) throw new Error("s12: 5件の cues がそろっていない");

  // 原稿の該当箇所は cues の visual の「該当箇所「…」の語に」から取る（原稿 demo-manuscript.md と一字一句同じことを確認済み）。
  // 語の前後に分け、つなげると該当箇所に戻ることを確かめる
  const items = slash.map((e, i) => {
    const m = /該当箇所「(.*)」の語に/.exec(e.visual || "");
    if (!m) throw new Error("s12: 該当箇所が cues に無い: " + e.visual);
    const ctx = m[1];
    let segs;
    if (ctx === e.text && ctx.includes("／")) {
      // 表記ゆれ：2語を「／」でつないだもの（原稿では別々の場面）。語ごとに分ける
      const k = ctx.indexOf("／");
      segs = [{ t: ctx.slice(0, k), w: true }, { t: "／", sep: true }, { t: ctx.slice(k + 1), w: true }];
    } else {
      const k = ctx.indexOf(e.text);
      if (k < 0) throw new Error("s12: 語が該当箇所に無い: " + e.text);
      segs = [{ t: ctx.slice(0, k) }, { t: e.text, w: true }, { t: ctx.slice(k + e.text.length) }].filter((s) => s.t);
    }
    if (segs.map((s) => s.t).join("") !== ctx) throw new Error("s12: 該当箇所の分割が原文と一致しない: " + ctx);
    const size = Math.min(128, Math.floor(1640 / [...ctx].length)); // 1行に収める（最長14字で117px）
    return { ctx, segs, size, sl: e, pn: pens[i], circle: segs.filter((s) => s.w).length > 1 };
  });

  S.css(`
    #s12-head { position:absolute; left:110px; top:84px; display:flex; align-items:center; gap:22px; }
    #s12-labs { position:relative; display:inline-grid; }
    #s12-labs > .hf-tag { grid-area:1 / 1; justify-self:start; background:var(--red); color:var(--paper); transform-origin:0% 50%; }
    #s12-prog { position:absolute; right:110px; top:96px; display:flex; gap:16px; }
    #s12-prog span { display:block; width:34px; height:34px; border:5px solid var(--ink); background:transparent; }
    #s12-shake { position:absolute; inset:0; }
    #s12-pen { left:0; top:0; z-index:5; }
    .s12-item { position:absolute; left:0; right:0; top:0; height:1080px; display:flex; align-items:center; justify-content:center; padding-top:170px; }
    .s12-iw { position:relative; display:block; }
    .s12-line { display:block; white-space:nowrap; line-height:1.3; }
    .s12-sep { color:rgba(20,17,15,0.62); margin:0 0.7em; }
    .s12-fix { position:absolute; left:0; top:0; display:block; white-space:nowrap; font-size:112px; line-height:1.1; transform:rotate(-4deg); transform-origin:50% 100%; }
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s12-head">${UI.tag("novel-editor の出力")}<span id="s12-labs">${items
      .map((it, i) => UI.tag(it.sl.label, "s12-lab hf-hidden"))
      .join("")}</span></div>
    <div id="s12-prog">${items.map(() => "<span></span>").join("")}</div>
    <div id="s12-shake">${UI.pen({ id: "s12-pen" })}${items
      .map(
        (it, i) => `<div class="s12-item${i ? " hf-hidden" : ""}" data-i="${i}"><div class="s12-iw">
          <div class="s12-line hf-ms" style="font-size:${it.size}px">${it.segs
            .map((s) => (s.w ? `<span class="${it.circle ? "s12-w" : "hf-strike s12-w"}">${HF.esc(s.t)}</span>` : s.sep ? `<span class="s12-sep">${HF.esc(s.t)}</span>` : `<span>${HF.esc(s.t)}</span>`))
            .join("")}</div>
          <div class="s12-fix hf-pen-text" style="clip-path:inset(0% 100% 0% 0%)">${HF.esc(it.pn.text)}</div>
        </div></div>`
      )
      .join("")}</div>
  `);

  const labs = S.qa(".s12-lab"), boxes = S.qa("#s12-prog span"), itemEls = S.qa(".s12-item");

  // ---- 位置を測る（動かす前に）：正しい形は語の真上（2語のときは2語の間の上）、引き出し線は語の上端から正しい形の下端へ
  items.forEach((it, i) => {
    const iw = itemEls[i].querySelector(".s12-iw"), line = iw.querySelector(".s12-line"), fix = iw.querySelector(".s12-fix");
    const words = Array.from(iw.querySelectorAll(".s12-w"));
    const lb = HF.rel(line, iw), fw = fix.offsetWidth, fh = fix.offsetHeight;
    const wb = words.map((w) => HF.rel(w, iw));
    const cx = (wb[0].x + wb[wb.length - 1].x + wb[wb.length - 1].w) / 2;
    // 画面の左右からはみ出さない（iw は中央寄せ。iw の左端の画面座標で補正する）
    const iwLeft = (1920 - iw.offsetWidth) / 2;
    const left = Math.max(120 - iwLeft, Math.min(1800 - iwLeft - fw, cx - fw / 2));
    const top = lb.y - fh - 70;
    fix.style.left = left + "px";
    fix.style.top = top + "px";
    const fx = left + fw / 2, fy = top + fh + 6;
    it.fix = fix;
    it.words = words;
    it.iw = iw;
    // 引き出し線（語ごと）：語の上端の中央から、正しい形の下へ緩く曲がって上る
    it.leads = wb.map((b, k) => {
      const x0 = b.x + b.w / 2, y0 = it.circle ? b.y - 34 : b.y + b.h * 0.12; // 丸で囲む件は丸の外から出す
      const pts = [];
      for (let s = 0; s <= 12; s++) {
        const u = s / 12;
        pts.push([x0 + (fx - x0) * u + Math.sin(u * Math.PI) * 18 * (k ? -1 : 1), y0 + (fy - y0) * u]);
      }
      return UI._path(iw, pts, 8);
    });
    // 赤ペンの先端を置く座標（シーンの包み基準）：刺した語の右端 → 引き出し線の始点 → 正しい形の左端 → 右端
    const st = S.stage, fb = HF.rel(fix, st), w0 = HF.rel(words[0], st), wl = HF.rel(words[words.length - 1], st);
    const ib = HF.rel(iw, st);
    it.tip = {
      struck: { x: wl.x + wl.w, y: wl.y + wl.h * 0.58 },
      lead: { x: ib.x + (wb[0].x + wb[0].w / 2 + (words.length > 1 ? (wb[1].x + wb[1].w / 2 - wb[0].x - wb[0].w / 2) / 2 : 0)), y: w0.y + w0.h * 0.1 },
      fixL: { x: fb.x + 6, y: fb.y + fb.h * 0.62 },
      fixR: { x: fb.x + fb.w - 4, y: fb.y + fb.h * 0.42 },
    };
    // 表記ゆれ：2語を赤丸
    it.circles = it.circle ? words.map((w, k) => UI.circleAround(iw, w, { pad: 14, width: 8, seed: 50 + k })) : [];
  });

  // 意図した重ね：引き出し線・丸は語の上に重ねて描く（SVG は文字ではないので付けない）。札は同じ位置に順に出す
  HF.allowOverlap(labs);

  const pen = S.q("#s12-pen"), PEN_H = 72, ROT = -32;
  const P = (p, dx = 0, dy = 0) => ({ x: p.x + dx, y: p.y - PEN_H / 2 + dy });
  const movePen = (from, to, t0, dur, ease) =>
    tl.fromTo(pen, { x: from.x, y: from.y }, { x: to.x, y: to.y, duration: dur, ease, immediateRender: false }, t0);

  items.forEach((it, i) => {
    const t = it.sl.t, tp = it.pn.t, item = itemEls[i], T = it.tip;
    const tNext = i < items.length - 1 ? items[i + 1].sl.t : S.end;
    // ---- 入り：硬い切り（T3）。1件目はシーン頭の1フレーム目から置いてある
    if (i > 0) {
      M.hide(tl, itemEls[i - 1], t);
      M.show(tl, item, t);
      M.hide(tl, labs[i - 1], t);
    }
    // ---- 小節頭：刺す（取り消し線）か、表記ゆれは2語を赤丸。種類の札を押す。進み具合の枠を赤で埋める
    if (it.circle) {
      it.circles.forEach((c) => M.scribble(tl, c, t, HF.beats(0.5)));
    } else {
      M.strike(tl, it.words[0], t);
      tl.set(it.words[0], { color: "rgba(20,17,15,0.55)" }, t + 3 * FR);
    }
    M.stamp(tl, labs[i], t, { fromScale: 1.5, fromRot: -8, rot: -3 });
    tl.set(boxes[i], { backgroundColor: HF.COLORS.red, borderColor: HF.COLORS.red }, t);
    M.squash(tl, boxes[i], t, { to: 0.6 }); // 1件を数えた手応え
    // 衝撃は最初と最後の件だけ（毎小節は使わない）
    if (i === 0 || i === items.length - 1) M.shake(tl, "#s12-shake", t, { amp: 11, seed: 90 + i });

    // ---- 赤ペン：刺した直後は語の右端（線を引き終えた位置）。そこから書き込む位置へゆっくり持ち上がる（書く前の溜め）
    // 書く拍（pen）より前はインクを一切出さない（v1 は引き出し線が拍の 1〜2 フレーム前に見え始めていた）
    tl.set(pen, { opacity: 1, rotation: ROT, x: P(T.struck).x, y: P(T.struck).y }, t);
    const tDown = tp - HF.beats(0.25);
    movePen(P(T.struck), P(T.lead, 30, -40), t + HF.beats(0.25), tDown - t - HF.beats(0.25), "power2.inOut");
    // 書く拍の直前 1/4拍：ペン先が引き出し線の始点へ降りる（インクなし）
    movePen(P(T.lead, 30, -40), P(T.lead), tDown, HF.beats(0.25), "power3.in");
    // ---- 2拍後（pen）：最初のインクは拍頭のフレームに出す。引き出し線を 1/4拍で引き（ペン先が線をたどって正しい形の書き出しへ）、
    // 続けて正しい形を左から右へ等速で書く（語彙5 scribble と同じ「手書きが書かれる」動き。字の開示なので clip-path で描く）
    // scribble は始点の時刻では長さ 0 なので、1フレーム前から 2フレームで引く：拍頭の前のコマは 0、拍頭のコマで半分、次のコマで引き終わる
    it.leads.forEach((p) => M.scribble(tl, p, tp - FR, 2 * FR));
    movePen(P(T.lead), P(T.fixL), tp - FR, 2 * FR, "none");
    const tWrite = tp + FR;
    tl.fromTo(it.fix, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: HF.beats(0.5), ease: "none", immediateRender: false }, tWrite);
    movePen(P(T.fixL), P(T.fixR), tWrite, HF.beats(0.5), "none");
    // 書き終えたら離れる（右上へ逃げて、次の件の頭で次の語に移る）
    movePen(P(T.fixR), P(T.fixR, 120, -110), tWrite + HF.beats(0.5), HF.beats(0.75), "power2.out");
    if (i === items.length - 1) M.hide(tl, pen, tp + HF.beats(1.5));
    // 止めの微動（刺した後から次の件まで）
    M.breathe(tl, it.iw, t + HF.beats(0.5), tNext, { amt: 0.012, period: HF.beats(2) });
  });
});
