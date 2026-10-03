// s10-drill：練習の題（拍 80〜88）
// 拍80 出力カード「練習の題：…300字で書く。」が右から滑り込む → 拍81「感情語を使わず」を赤くして下線（scribble）
// → 拍84 動画の声「弱点から、練習の題まで。」を叩きつけ → 拍86〜88 上昇音に合わせて画面が迫る（拍88 で s11 の青へ硬く切る）
HF.scene("s10-drill", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const card = S.find("whoosh"); // 拍80。text は出力（output:score）
  const voice = S.find("slam"); // 拍84。text は動画の声（video）
  const riser = S.find("riser"); // 拍86〜88

  // カード本文：強調「感情語を使わず」と改行位置（「緊張を、」の後）。つなげると出力と同じことを確かめる
  const KEY = "感情語を使わず", BR = "緊張を、";
  const ik = card.text.indexOf(KEY), ib = card.text.indexOf(BR) + BR.length;
  if (ik < 0 || ib < BR.length || ib > ik) throw new Error("s10: 出力の分割位置が見つからない");
  const html =
    HF.esc(card.text.slice(0, ib)) + "<br>" + HF.esc(card.text.slice(ib, ik)) +
    `<span class="s10-key">${HF.esc(KEY)}</span>` + HF.esc(card.text.slice(ik + KEY.length));

  S.css(`
    #s10-zoom { position:absolute; inset:0; transform-origin:50% 45%; }
    #s10-cw { position:absolute; left:0; right:0; top:130px; display:flex; justify-content:center; }
    #s10-card { position:relative; display:block; }
    #s10-card .hf-card-body { white-space:nowrap; line-height:1.5; }
    #s10-vw { position:absolute; left:0; right:0; top:720px; display:flex; justify-content:center; }
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s10-zoom">
      <div id="s10-cw"><div id="s10-card">${UI.card(card.text, { size: 80, html })}</div></div>
      <div id="s10-vw"><div id="s10-v" class="hf-hidden">${UI.voice(voice.text, { size: 130 })}</div></div>
    </div>
  `);
  if (S.q("#s10-card .hf-card-body").textContent !== card.text) throw new Error("s10: カード本文が出力と一致しない");

  const key = S.q(".s10-key");
  const ul = UI.underline(S.q("#s10-card"), key, { gap: 0, width: 10, seed: 81 });

  // 拍80：カードが右から滑り込む（whoosh）。カードが横に長いので、1フレーム目に右端が画面外へ出ない距離（120px）にする
  tl.fromTo("#s10-cw", { x: 120 }, { x: 0, duration: HF.beats(0.5), ease: "power4.out", immediateRender: false }, card.t);
  // 拍81：「感情語を使わず」に赤の下線
  const t81 = S.at(card.beat + 1);
  tl.set(key, { color: HF.COLORS.red }, t81);
  M.scribble(tl, ul, t81, HF.beats(0.75));
  M.breathe(tl, "#s10-card", S.at(card.beat + 2), S.end, { amt: 0.012, period: HF.beats(2) });
  // 拍84：動画の声
  M.slam(tl, "#s10-v", voice.t);
  // 拍86〜88：上昇音に合わせて画面全体がじわりと迫る（次のセクションへの溜め。拍88 で硬く切る）
  const tEnd = S.at(riser.beat + riser.length_beats);
  tl.fromTo("#s10-zoom", { scale: 1 }, { scale: 1.07, duration: tEnd - riser.t, ease: "power2.in", immediateRender: false }, riser.t);
});
