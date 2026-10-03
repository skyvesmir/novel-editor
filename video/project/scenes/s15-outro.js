// s15-outro：締め：題字・導入3手順・URL（拍 136〜160、24拍）
// 拍136 T3 硬い切りで墨の画面、題字「novel-editor」を叩きつけ（s02 と同じ見た目）→ 拍138 一言（s02 の動画の声を再び）
// → 拍140 題字が上へ退き、導入の手順を1つずつ押す（拍140・142・144）→ 拍148 URL を叩きつけ
// → 拍152 最後の一撃：手順を消し、題字と URL だけを中央に寄せて止める（breathe）
// 色は墨・生成り・赤の3色
HF.scene("s15-outro", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const title = S.find("title"); // 拍136。text「novel-editor」（video）
  const steps = S.ev.filter((e) => e.kind === "stamp"); // 拍140・142・144（video）
  const url = S.find("slam"); // 拍148（video）
  const fin = S.find("end"); // 拍152
  // 一言：s02 の動画の声（cues の text をそのまま）。題字と組で出し、冒頭の約束を締めでもう一度言う
  const line = HF.CUES.events.find((e) => e.scene === "s02-title" && e.kind === "slam" && e.text_source === "video");
  if (!line) throw new Error("s15: 一言（s02 の動画の声）が cues に無い");

  // 手順の番号（①②③）だけ赤で書く。つなげると原文に戻ることを確かめる
  const stepParts = steps.map((e) => {
    const p = [[...e.text][0], e.text.slice([...e.text][0].length)];
    if (p.join("") !== e.text || !/^[①②③]$/.test(p[0])) throw new Error("s15: 手順の分割が原文と一致しない: " + e.text);
    return p;
  });

  S.css(`
    #s15-tg { position:absolute; left:0; right:0; top:0; height:1080px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:70px; padding-bottom:20px; }
    #s15-tw { position:relative; display:block; }
    #s15-title .hf-voice, #s15-line .hf-voice { color:var(--paper); }
    #s15-steps { position:absolute; left:0; right:0; top:330px; display:flex; justify-content:center; }
    #s15-sb { display:flex; flex-direction:column; align-items:flex-start; gap:42px; }
    .s15-step { display:block; transform-origin:0% 50%; }
    .s15-step .hf-voice { color:var(--paper); }
    .s15-n { color:var(--red); margin-right:0.35em; }
    #s15-ug { position:absolute; left:0; right:0; top:800px; display:flex; justify-content:center; }
    #s15-uw { position:relative; display:block; }
    #s15-url { display:block; }
    #s15-url .hf-voice { color:var(--ink); background:var(--paper); padding:22px 44px 30px; border-radius:18px; }
  `);
  S.html(`
    <div class="hf-bg hf-ink"></div>
    <div id="s15-tg">
      <div id="s15-tw"><div id="s15-title" class="hf-hidden">${UI.voice(title.text, { size: 210 })}</div></div>
      <div id="s15-line" class="hf-hidden">${UI.voice(line.text, { size: 100 })}</div>
    </div>
    <div id="s15-steps"><div id="s15-sb">${stepParts
      .map((p) => `<div class="s15-step hf-hidden"><div class="hf-voice" style="font-size:80px"><span class="s15-n">${HF.esc(p[0])}</span>${HF.esc(p[1])}</div></div>`)
      .join("")}</div></div>
    <div id="s15-ug"><div id="s15-uw"><div id="s15-url" class="hf-hidden">${UI.voice(url.text, { size: 80 })}</div></div></div>
  `);
  S.qa(".s15-step .hf-voice").forEach((el, i) => {
    if (el.textContent !== steps[i].text) throw new Error("s15: 手順の文字が原文と一致しない");
  });

  // 横幅に収める（1行で 1700px 以内。超えたら字を小さくする。下限 56px）
  const fit = (el, max) => {
    const fs = parseFloat(el.style.fontSize), w = el.scrollWidth;
    if (w > max) el.style.fontSize = Math.max(56, Math.floor((fs * max) / w)) + "px";
  };
  S.qa(".s15-step .hf-voice").forEach((el) => fit(el, 1700));
  fit(S.q("#s15-url .hf-voice"), 1700);

  const titleEl = S.q("#s15-title"), tw = S.q("#s15-tw");
  const ul = UI.underline(tw, titleEl, { gap: 4, width: 16, seed: 15 }); // 題字の包みに描く（題字と一緒に動き、最後の一撃でも一緒に叩きつける）

  const tUp = S.at(steps[0].beat - 0.5); // 題字が退く弱拍（拍139.5）
  // ---- 拍136：硬い切りで題字（1フレーム目で着地寸前）→ 赤の下線
  M.slam(tl, titleEl, title.t, { from: 1.5, y: -30 });
  M.scribble(tl, ul, title.t + HF.beats(0.5), HF.beats(0.75));
  // ---- 拍138：一言
  const t138 = S.at(title.beat + 2);
  M.slam(tl, "#s15-line", t138, { from: 1.4, y: -24 });
  M.breathe(tl, tw, title.t + HF.beats(1), tUp, { amt: 0.015 });

  // ---- 拍139.5（弱拍）：題字が上へ退いて手順の場所を空ける（一言は消す）→ 拍140 から手順を1つずつ押す
  M.hide(tl, "#s15-line", tUp);
  const up = { y: -350, scale: 0.55 };
  tl.fromTo("#s15-tg", { y: 0, scale: 1 }, { y: up.y, scale: up.scale, duration: HF.beats(0.5), ease: "power3.out", immediateRender: false }, tUp);
  const stepEls = S.qa(".s15-step");
  steps.forEach((e, i) => M.stamp(tl, stepEls[i], e.t, { fromScale: 1.25, fromRot: -4, rot: 0 }));
  M.breathe(tl, "#s15-sb", steps[0].t + HF.beats(0.25), fin.t, { amt: 0.02, period: HF.beats(2) });

  // ---- 拍148：URL を叩きつけ
  M.slam(tl, "#s15-url", url.t, { from: 1.4, y: -24 });

  // ---- 拍152：最後の一撃。手順を消し、題字と URL だけを中央に寄せて止める
  stepEls.forEach((el) => M.hide(tl, el, fin.t));
  const back = { y: -110, scale: 0.85 };
  tl.fromTo("#s15-tg", { y: up.y, scale: up.scale }, { y: back.y, scale: back.scale, duration: HF.beats(0.25), ease: "power4.out", immediateRender: false }, fin.t);
  tl.fromTo("#s15-ug", { y: 0 }, { y: -110, duration: HF.beats(0.25), ease: "power4.out", immediateRender: false }, fin.t);
  M.slam(tl, tw, fin.t, { from: 1.25, y: -20 });
  M.breathe(tl, tw, fin.t + HF.beats(0.75), S.end, { amt: 0.015 });
  M.breathe(tl, "#s15-uw", url.t + HF.beats(0.5), S.end, { amt: 0.012, period: HF.beats(3) });
});
