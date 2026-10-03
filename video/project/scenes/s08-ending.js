// s08-ending：牽引力：章末の一文（拍 64〜72）
// 拍64 原稿の最後の1文と札（牽引力の点数）が右から滑り込む → 拍65 赤の取り消し線（strike）
// → 拍66 その1文が上へ押し上げられ「最後」の位置を空ける → 拍68 出力カード「…は最後に置かない。」が落ちてくる（drop-in）→ 止め
// 札の点数は出力の点数行どおり「5（回収未検証）/10」（s04 と同じ。数字→注記→/10 の順）
HF.scene("s08-ending", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const sent = S.find("whoosh"); // 拍64。text は原稿の最後の1文（manuscript）
  const slash = S.find("slash"); // 拍65
  const fall = S.find("fall"); // 拍68。text は出力（output:score）

  S.css(`
    #s08-g { position:absolute; left:0; right:0; top:330px; display:flex; justify-content:center; }
    #s08-gu, #s08-gb { position:relative; display:block; }
    #s08-gb > .hf-tag { position:absolute; left:0; top:0; }
    #s08-ms { display:block; padding-top:96px; font-size:96px; line-height:1.4; white-space:nowrap; }
    #s08-cw { position:absolute; left:0; right:0; top:600px; display:flex; justify-content:center; }
    #s08-card { display:block; }
  `);
  S.html(`
    <div class="hf-bg hf-paper"></div>
    <div id="s08-g"><div id="s08-gu"><div id="s08-gb">
      ${UI.tag("牽引力 5（回収未検証）/10")}
      <div id="s08-ms" class="hf-ms"><span id="s08-s" class="hf-strike">${HF.esc(sent.text)}</span></div>
    </div></div></div>
    <div id="s08-cw"><div id="s08-card" class="hf-hidden">${UI.card(fall.text, { size: 110 })}</div></div>
  `);

  const s = S.q("#s08-s");
  // 意図した重ね：落ちてくるカードが、打ち消した1文と札の上を約3フレーム通過する
  HF.allowOverlap(S.qa("#s08-s, #s08-gb > .hf-tag, #s08-card .hf-tag, #s08-card .hf-card-body"));
  // 拍64：右から滑り込む（whoosh）。1文が横に長いので、1フレーム目に文末が画面外へ出ない距離（120px）にする
  tl.fromTo("#s08-g", { x: 120 }, { x: 0, duration: HF.beats(0.5), ease: "power4.out", immediateRender: false }, sent.t);
  // 拍65：赤線
  M.strike(tl, s, slash.t, { thick: "0.12em" });
  tl.set(s, { color: "rgba(20,17,15,0.55)" }, slash.t + HF.beats(0.25));
  // 拍66〜67：最後の1文が上へ押し上げられる（「最後に置かない」＝最後の位置から退かせる）
  const t66 = S.at(slash.beat + 1);
  tl.fromTo("#s08-gu", { y: 0 }, { y: -190, duration: HF.beats(1.5), ease: "power2.inOut", immediateRender: false }, t66);
  // 拍68：出力カードが上から落ちてくる（bounce で着地）。1フレーム目にカードの大半が見える高さ（-150%）から落とし、拍頭で絵が変わる
  M.dropIn(tl, "#s08-card", fall.t, { from: -150 });
  M.breathe(tl, "#s08-cw", fall.t + HF.beats(1), S.end, { amt: 0.015 });
  M.breathe(tl, "#s08-gb", S.at(slash.beat + 2.5), S.end, { amt: 0.012, period: HF.beats(3) });
});
