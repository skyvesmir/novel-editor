// 共通部品。API は scenes/README.md。ここを変えるときは全シーンに効くので README も直す。
// 決まり：Date.now・毎フレームの更新ループ・種なし乱数を使わない。すべて GSAP の時間軸（tl）に載せる。
(function () {
  "use strict";
  const C = window.CUES;
  const CFG = window.HF_CONFIG;
  const FPS = C.fps;
  const FPB = (FPS * 60) / C.bpm; // 1拍のフレーム数（12）
  const SPB = 60 / C.bpm; // 1拍の秒（0.4）
  const FR = 1 / FPS; // 1フレームの秒

  const HF = (window.HF = {});
  HF.CUES = C;
  HF.CFG = CFG;
  HF.FPS = FPS;
  HF.FPB = FPB;
  HF.BEAT = SPB;
  HF.FR = FR;
  HF.COLORS = { paper: "#F3EEE3", ink: "#14110F", red: "#E5321B", blue: "#2442FF", yellow: "#FFD02E" };
  HF.FONTS = { slam: '"Dela", sans-serif', mincho: '"Mincho", serif', pen: '"Klee", sans-serif', ui: '"ZenKaku", sans-serif' };

  // ---- 拍 → フレーム → 時間軸の秒（単独書き出しのときはシーン頭が 0 になるようにずらす）
  HF.frameOf = (beat) => Math.round(beat * FPB);
  HF.timeOfFrame = (frame) => (frame - CFG.offsetFrame) / FPS;
  HF.at = (beat) => HF.timeOfFrame(HF.frameOf(beat));
  HF.beats = (n) => Math.round(n * FPB) / FPS; // 長さ（拍）→ 秒。フレームに丸める
  HF.frames = (n) => n / FPS; // 長さ（フレーム）→ 秒

  // ---- cues のイベント（t = 時間軸の秒。frame をそのまま使う）
  HF.events = (sceneId) =>
    C.events
      .filter((e) => e.scene === sceneId)
      .map((e, i) => Object.assign({}, e, { i, t: HF.timeOfFrame(e.frame) }));

  // ---- 種つき乱数（mulberry32）
  HF.rng = function (seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  HF.esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  // 要素の位置（anc 基準・px）。GSAP の変形を掛ける前に測る
  HF.rel = function (el, anc) {
    const r = el.getBoundingClientRect();
    const a = anc.getBoundingClientRect();
    const k = anc.offsetWidth ? a.width / anc.offsetWidth : 1;
    return { x: (r.left - a.left) / k, y: (r.top - a.top) / k, w: r.width / k, h: r.height / k };
  };

  HF._scenes = {};
  HF.scene = function (id, fn) {
    HF._scenes[id] = fn;
  };

  // =====================================================================
  // 動き（style-brief §4 の語彙）。すべて (tl, 対象, 時刻t[秒], opts)
  // 出る前は CSS で opacity:0（.hf-hidden）にしておき、show で出す。set は逆 seek でも戻る
  // =====================================================================
  const M = (HF.M = {});
  const snap = (t) => Math.round(t * FPS) / FPS;

  M.show = (tl, el, t) => tl.set(el, { opacity: 1 }, t);
  M.hide = (tl, el, t) => tl.set(el, { opacity: 0 }, t);

  // 1 slam：scale 1.6→1、y -40→0、2フレームで着地（power4.out）→ recoil（elastic で僅かに揺れて静止）
  M.slam = function (tl, el, t, o = {}) {
    const from = o.from ?? 1.6, y = o.y ?? -40;
    M.show(tl, el, t);
    tl.fromTo(el, { scale: from, y }, { scale: 0.96, y: 6, duration: 2 * FR, ease: "power4.out", immediateRender: false }, t);
    if (o.recoil !== false) {
      tl.fromTo(el, { scale: 0.96, y: 6 }, { scale: 1, y: 0, duration: HF.beats(0.5), ease: "elastic.out(1,0.4)", immediateRender: false }, t + 2 * FR);
    } else {
      tl.set(el, { scale: 1, y: 0 }, t + 2 * FR);
    }
    return tl;
  };

  // 3 stamp：scale 2→1、rotation -8→-4、1/4拍（back.out(3)）
  M.stamp = function (tl, el, t, o = {}) {
    M.show(tl, el, t);
    tl.fromTo(
      el,
      { scale: o.fromScale ?? 2, rotation: o.fromRot ?? -8 },
      { scale: 1, rotation: o.rot ?? -4, duration: HF.beats(0.25), ease: "back.out(3)", immediateRender: false },
      t
    );
    return tl;
  };

  // 4 strike：.hf-strike の赤線を左から伸ばす（拍頭に先端が着く）。1/4拍（power3.inOut）
  M.strike = function (tl, el, t, o = {}) {
    const th = o.thick || "0.13em";
    tl.fromTo(el, { backgroundSize: `0% ${th}` }, { backgroundSize: `100% ${th}`, duration: o.dur ?? HF.beats(0.25), ease: "power3.inOut", immediateRender: false }, t);
    return tl;
  };

  // 5 scribble：SVG path を等速で描く（唯一の linear）。1/2〜1拍
  M.scribble = function (tl, path, t, dur) {
    const len = Math.ceil(path.getTotalLength()) + 2;
    path.style.strokeDasharray = `${len}`;
    path.style.strokeDashoffset = `${len}`;
    tl.fromTo(path, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: dur ?? HF.beats(0.5), ease: "none", immediateRender: false }, t);
    return tl;
  };

  // 6 count-up：values を順に出す（power2.out の間隔。最後の値は t1 ちょうど）。el は .hf-num
  M.countUp = function (tl, el, values, t0, t1) {
    el.innerHTML = values.map((v) => `<span>${HF.esc(v)}</span>`).join("");
    const spans = Array.from(el.children);
    const n = spans.length;
    let prev = null, last = -1;
    spans.forEach((sp, k) => {
      const p = n === 1 ? 1 : k / (n - 1);
      let t = snap(t0 + (t1 - t0) * (1 - Math.sqrt(1 - p))); // power2.out の逆関数
      if (k === n - 1) t = snap(t1);
      if (t <= last && k !== n - 1) return; // 同じフレームに重なる値は飛ばす
      if (prev) tl.set(prev, { opacity: 0 }, t);
      tl.set(sp, { opacity: 1 }, t);
      prev = sp;
      last = t;
    });
    return tl;
  };

  // 7 shake：振幅 amp px、1/2拍で減衰。種つき乱数でフレームごとに置く（毎拍は使わない）
  M.shake = function (tl, el, t, o = {}) {
    const amp = o.amp ?? 12, n = Math.round((o.dur ?? HF.beats(0.5)) * FPS), r = HF.rng(o.seed ?? 7);
    for (let k = 0; k < n; k++) {
      const d = amp * (1 - k / n);
      tl.set(el, { x: (r() * 2 - 1) * d, y: (r() * 2 - 1) * d * 0.6 }, t + k * FR);
    }
    tl.set(el, { x: 0, y: 0 }, t + n * FR);
    return tl;
  };

  // 8 drop-in：上から落ちて bounce.out で着地。1拍
  M.dropIn = function (tl, el, t, o = {}) {
    M.show(tl, el, t);
    tl.fromTo(el, { yPercent: o.from ?? -120 }, { yPercent: 0, duration: o.dur ?? HF.beats(1), ease: "bounce.out", immediateRender: false }, t);
    return tl;
  };

  // 9 wipe-reveal：左から開示（clip-path）。1/2拍。要素に style="clip-path: inset(0 100% 0 0)" を付けておく
  M.wipe = function (tl, el, t, o = {}) {
    tl.fromTo(el, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: o.dur ?? HF.beats(0.5), ease: "power2.inOut", immediateRender: false }, t);
    return tl;
  };

  // 10 blur-snap：ブレ→焦点。1/4拍（expo.out）
  M.blurSnap = function (tl, el, t, o = {}) {
    M.show(tl, el, t);
    tl.fromTo(el, { filter: `blur(${o.blur ?? 20}px)` }, { filter: "blur(0px)", duration: o.dur ?? HF.beats(0.25), ease: "expo.out", immediateRender: false }, t);
    return tl;
  };

  // 11 pop-stagger：els を each 間隔（既定 1/8拍、フレームに丸め）で back.out(2) で出す
  M.popStagger = function (tl, els, t, o = {}) {
    const each = o.each ?? HF.BEAT / 8;
    Array.from(els).forEach((el, i) => {
      const ti = snap(t + i * each);
      M.show(tl, el, ti);
      tl.fromTo(el, { scale: o.from ?? 0.3 }, { scale: 1, duration: o.dur ?? HF.beats(0.5), ease: "back.out(2)", immediateRender: false }, ti);
    });
    return tl;
  };

  // 12 squash：scaleY 1→0.7→1。1/4拍
  M.squash = function (tl, el, t, o = {}) {
    const h = HF.beats(0.125);
    tl.fromTo(el, { scaleY: 1 }, { scaleY: o.to ?? 0.7, duration: h, ease: "power2.in", immediateRender: false }, t);
    tl.fromTo(el, { scaleY: o.to ?? 0.7 }, { scaleY: 1, duration: h, ease: "power2.out", immediateRender: false }, t + h);
    return tl;
  };

  // 13 breathe：scale 1↔1+amt（sine.inOut）を t0〜t1 で繰り返す（1往復 2拍）。slam と別の包みに掛ける
  M.breathe = function (tl, el, t0, t1, o = {}) {
    const amt = o.amt ?? 0.02, period = o.period ?? HF.beats(2), half = period / 2;
    for (let s = t0; s + half <= t1 + 1e-6; s += period) {
      tl.fromTo(el, { scale: 1 }, { scale: 1 + amt, duration: half, ease: "sine.inOut", immediateRender: false }, s);
      if (s + period <= t1 + 1e-6) tl.fromTo(el, { scale: 1 + amt }, { scale: 1, duration: half, ease: "sine.inOut", immediateRender: false }, s + half);
    }
    return tl;
  };

  // 14 tick-flash：重ね要素を2フレームだけ出す（1小節に1回まで）
  M.flash = function (tl, el, t, o = {}) {
    if (o.color) tl.set(el, { backgroundColor: o.color }, t);
    tl.set(el, { opacity: o.opacity ?? 1 }, t);
    tl.set(el, { opacity: 0 }, t + (o.frames ?? 2) * FR);
    return tl;
  };

  // T1 color-slam：背景を1フレームで替える
  M.bg = (tl, el, t, color) => tl.set(el, { backgroundColor: color }, t);

  // ふわっと置く（静かな出現。power2.out、y と opacity）。語彙外の補助：静かに置くカード用
  M.place = function (tl, el, t, o = {}) {
    tl.fromTo(el, { opacity: 0, y: o.y ?? 24 }, { opacity: 1, y: 0, duration: o.dur ?? HF.beats(0.5), ease: "power2.out", immediateRender: false }, t);
    return tl;
  };

  // =====================================================================
  // 部品（HTML 文字列を返す。S.html() で入れてから S.q() で掴む）
  // =====================================================================
  const UI = (HF.ui = {});
  const cls = (c) => (c ? " " + c : "");

  UI.tag = (text, c) => `<span class="hf-tag${cls(c)}">${HF.esc(text)}</span>`;
  // 出力カード：skill の実出力を一字一句。札は既定で「novel-editor の出力」
  UI.card = (text, o = {}) =>
    `<div class="hf-card${cls(o.cls)}"${o.id ? ` id="${o.id}"` : ""}>${UI.tag(o.tag ?? "novel-editor の出力")}<div class="hf-card-body"${o.size ? ` style="font-size:${o.size}px"` : ""}>${o.html ?? HF.esc(text)}</div></div>`;
  // 動画の声（Dela Gothic One の叩きつけ）
  UI.voice = (text, o = {}) =>
    `<div class="hf-voice${cls(o.cls)}"${o.id ? ` id="${o.id}"` : ""} style="font-size:${o.size ?? 160}px;${o.color ? `color:${o.color};` : ""}">${HF.esc(text)}</div>`;
  // 赤い判子
  UI.stampBox = (text, o = {}) =>
    `<div class="hf-stamp${cls(o.cls)}"${o.id ? ` id="${o.id}"` : ""} style="font-size:${o.size ?? 120}px">${HF.esc(text)}</div>`;
  // チャットの吹き出し：chunks（文字列の配列）を .hf-chunk に分ける。強調は {text, cls}、改行して始めるなら {text, nl:true}
  UI.bubble = (chunks, o = {}) =>
    `<div class="hf-bubble${cls(o.cls)}"${o.id ? ` id="${o.id}"` : ""}>` +
    chunks
      .map((c, i) => {
        const t = typeof c === "string" ? { text: c } : c;
        return (t.nl ? `<span class="hf-nl"></span>` : "") + `<span class="hf-chunk${cls(t.cls)}" data-i="${i}">${HF.esc(t.text)}</span>`;
      })
      .join("") +
    `<span class="hf-caret"></span></div>`;
  // 赤ペン（先端が左端中央。left/top に先端の座標を入れ、top は高さの半分を引く）
  UI.pen = (o = {}) =>
    `<svg class="hf-pen${cls(o.cls)}"${o.id ? ` id="${o.id}"` : ""} viewBox="0 0 640 72" width="640" height="72">` +
    `<polygon points="0,36 46,22 46,50" fill="#14110F"/>` +
    `<polygon points="46,22 92,14 92,58 46,50" fill="#B9200E"/>` +
    `<rect x="92" y="10" width="420" height="52" rx="6" fill="#E5321B"/>` +
    `<rect x="120" y="18" width="300" height="8" rx="4" fill="rgba(255,255,255,0.35)"/>` +
    `<rect x="512" y="6" width="128" height="60" rx="10" fill="#14110F"/></svg>`;

  // 手書きの楕円（target を囲む）を host に足して path を返す。scribble() で描く
  UI.circleAround = function (host, target, o = {}) {
    const b = HF.rel(target, host), pad = o.pad ?? 26, r = HF.rng(o.seed ?? 3);
    const cx = b.x + b.w / 2, cy = b.y + b.h / 2, rx = b.w / 2 + pad, ry = b.h / 2 + pad * 0.6;
    const pts = [];
    const turns = 1.12, steps = 48;
    for (let k = 0; k <= steps; k++) {
      const a = -Math.PI * 0.75 + (k / steps) * Math.PI * 2 * turns;
      const j = 1 + (r() - 0.5) * 0.05;
      pts.push([cx + Math.cos(a) * rx * j * (1 + k * 0.0015), cy + Math.sin(a) * ry * j]);
    }
    return UI._path(host, pts, o.width ?? 9);
  };
  // 手書きの下線（target の下）
  UI.underline = function (host, target, o = {}) {
    const b = HF.rel(target, host), r = HF.rng(o.seed ?? 5), y = b.y + b.h + (o.gap ?? 6);
    const pts = [];
    for (let k = 0; k <= 16; k++) pts.push([b.x - 8 + (k / 16) * (b.w + 16), y + (r() - 0.5) * 6 + Math.sin(k / 2.5) * 2]);
    return UI._path(host, pts, o.width ?? 10);
  };
  UI._path = function (host, pts, width) {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("class", "hf-scrib");
    svg.setAttribute("width", host.offsetWidth);
    svg.setAttribute("height", host.offsetHeight);
    svg.style.left = "0px";
    svg.style.top = "0px";
    const p = document.createElementNS(ns, "path");
    let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
    for (let k = 1; k < pts.length; k++) d += ` L${pts[k][0].toFixed(1)},${pts[k][1].toFixed(1)}`;
    p.setAttribute("d", d);
    p.setAttribute("stroke-width", width);
    svg.appendChild(p);
    host.appendChild(svg);
    return p;
  };
})();
