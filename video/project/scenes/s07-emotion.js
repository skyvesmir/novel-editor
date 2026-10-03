// s07-emotion：感情設計：即答の受諾（拍 56〜64）
// 拍56 原稿の台詞「「はい。行きます」」と札「感情設計 4.5/10」が右から滑り込む → 拍57 台詞に赤丸（scribble）
// → 拍59 溜め（台詞が縮んで上へ退き、カードの場所を空ける）→ 拍60 出力カード「…頂点が即答で通過するため。」を判子のように押す＋衝撃 → 止め
HF.scene("s07-emotion", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const line = S.find("whoosh"); // 拍56。text は原稿の台詞（manuscript）
  const pen = S.find("pen"); // 拍57
  const rest = S.find("silence"); // 拍59
  const card = S.find("stamp"); // 拍60。text は出力（output:score）

  S.css(`
    #s07-shake { position:absolute; inset:0; }
    #s07-g { position:absolute; left:0; right:0; top:330px; display:flex; justify-content:center; }
    #s07-gt, #s07-gb { position:relative; display:block; }
    #s07-gt { transform-origin:50% 0%; }
    #s07-gb > .hf-tag { position:absolute; left:0; top:-20px; }
    #s07-line { display:block; padding:100px 20px 0; font-size:150px; line-height:1.3; white-space:nowrap; }
    #s07-cw { position:absolute; left:0; right:0; top:560px; display:flex; justify-content:center; }
    #s07-card { display:block; }
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s07-shake">
      <div id="s07-g"><div id="s07-gt"><div id="s07-gb">
        ${UI.tag("感情設計 4.5/10")}
        <div id="s07-line" class="hf-ms">${HF.esc(line.text)}</div>
      </div></div></div>
      <div id="s07-cw"><div id="s07-card" class="hf-hidden">${UI.card(card.text, { size: 92 })}</div></div>
    </div>
  `);

  const gb = S.q("#s07-gb"), lineEl = S.q("#s07-line");
  // 台詞の字だけを囲む（札と余白は除く）
  const range = document.createElement("span");
  range.textContent = lineEl.textContent;
  lineEl.textContent = "";
  lineEl.appendChild(range);
  if (lineEl.textContent !== line.text) throw new Error("s07: 台詞が原稿と一致しない");
  const circle = UI.circleAround(gb, range, { pad: 14, width: 10, seed: 57 });

  // 拍56：台詞と札が右から滑り込む（whoosh。s03・s06 と同じ入り）
  tl.fromTo("#s07-g", { x: 260 }, { x: 0, duration: HF.beats(0.5), ease: "power4.out", immediateRender: false }, line.t);
  // 拍57：赤丸
  M.scribble(tl, circle, pen.t, HF.beats(0.75));
  M.breathe(tl, gb, pen.t + HF.beats(0.75), rest.t, { amt: 0.015, period: HF.beats(1) });
  // 拍59：溜め。台詞が縮んで上へ退く（次の一撃の前の逆向きの小さな動き）
  tl.fromTo("#s07-gt", { scale: 1, y: 0 }, { scale: 0.86, y: -230, duration: HF.beats(1), ease: "power2.in", immediateRender: false }, rest.t);
  // 拍60：出力カードを押す＋衝撃。台詞は墨を薄くして後ろに下げる
  M.stamp(tl, "#s07-card", card.t, { fromScale: 1.8, fromRot: -6, rot: -1.5 });
  M.shake(tl, "#s07-shake", card.t, { amp: 12, seed: 19 });
  tl.set(lineEl, { color: "rgba(20,17,15,0.55)" }, card.t);
  M.breathe(tl, "#s07-cw", card.t + HF.beats(0.5), S.end, { amt: 0.015 });
});
