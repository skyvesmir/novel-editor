// s11-proof-request：校正の依頼（拍 88〜96）
// 拍88 T1 全面色替え（青）。吹き出しが滑り込み、依頼文の最初の片が出る → 拍88.5〜90 裏拍ごとに文字送り
// → 拍92「書き換えはいらない」を赤くし、赤ペンの下線を手で引く（刺す）→ 拍93〜96 止め（呼吸）
// 色は青・生成り・赤の3色に絞る（青の場面に墨を足すと4色になるため、吹き出しの文字は青で書く。指示書「補助の青＝2周目以降の強調」）
HF.scene("s11-proof-request", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const req = S.find("drop"); // 拍88。text = 依頼文（input）
  const types = S.ev.filter((e) => e.kind === "type"); // 拍88.5・89・89.5・90
  const pen = S.find("pen"); // 拍92。text =「書き換えはいらない」

  // 依頼文を5つに分けて打つ（最初の片は拍88で出る）。つなげると依頼文と一字一句同じになることを確かめる
  const chunks = [
    { text: "誤字脱字だけ" },
    { text: "チェック" },
    { text: "してください。" },
    { text: pen.text, cls: "s11-key", nl: true },
    { text: "です。" },
  ];
  if (chunks.map((c) => c.text).join("") !== req.text) throw new Error("s11: 依頼文の分割が原文と一致しない");
  if (chunks.length !== types.length + 1) throw new Error("s11: 文字送りの回数と分割数が合わない");

  S.css(`
    #s11-bg { background:var(--blue); }
    #s11-shake { position:absolute; inset:0; }
    #s11-wrap { position:absolute; inset:0; display:flex; align-items:center; justify-content:flex-end; padding:0 130px 30px 0; }
    #s11-b { position:relative; display:block; }
    #s11-b .hf-bubble { width:1600px; font-size:84px; color:var(--blue); background:var(--paper); border-color:var(--paper);
      box-shadow:none; padding:64px 72px 70px; }
    #s11-b > .hf-tag { position:absolute; left:44px; top:-38px; z-index:2; background:var(--paper); color:var(--blue);
      box-shadow:0 0 0 6px var(--blue); }
    #s11-b .s11-key { margin-right:0.08em; }
  `);
  S.html(`
    <div id="s11-bg" class="hf-bg"></div>
    <div id="s11-shake">
      <div id="s11-wrap"><div id="s11-b">${UI.tag("依頼")}${UI.bubble(chunks)}</div></div>
    </div>
  `);

  const box = S.q("#s11-b"), spans = S.qa(".hf-chunk"), key = S.q(".s11-key");
  const line = UI.underline(box, key, { gap: 2, width: 12, seed: 21 });

  // 拍88：T1 青の全面（シーン頭の1フレーム目から）。吹き出しは右から滑り込み、最初の片はもう出ている
  M.show(tl, spans[0], req.t);
  tl.fromTo(box, { x: 220, scale: 0.94 }, { x: 0, scale: 1, duration: HF.beats(0.5), ease: "power4.out", immediateRender: false }, req.t);
  // 拍88.5〜90：文字送り（裏拍ごとに1かたまり）
  types.forEach((e, i) => M.show(tl, spans[i + 1], e.t));

  // 拍92：「書き換えはいらない」を赤くし、下線を手で引く。刺した手応えに小さく揺らす
  tl.set(key, { color: HF.COLORS.red }, pen.t);
  M.scribble(tl, line, pen.t, HF.beats(0.5));
  M.shake(tl, "#s11-shake", pen.t, { amp: 9, seed: 31 });

  // 止めの微動（文字送りの後と、下線の後）
  // 周期 3.5拍：拍89〜96 の7拍をちょうど2往復で埋める（v2 は周期4拍で拍95〜96 が完全に止まっていた）
  M.breathe(tl, "#s11-wrap", req.t + HF.beats(1), S.end, { amt: 0.012, period: HF.beats(3.5) });
});
