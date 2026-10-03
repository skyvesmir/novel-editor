// s02-title：題字（拍 16〜24）
// 拍16 T3 硬い切りで墨の画面、「novel-editor」を叩きつけ → 拍18 動画の声「その1話、投稿する前に。」
HF.scene("s02-title", function (S) {
  const { tl } = S, M = HF.M, UI = HF.ui;
  const title = S.find("impact"), line = S.find("slam");

  S.css(`
    #s02-wrap { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:70px; padding-bottom:20px; }
    #s02-tw { position:relative; display:block; }
    #s02-title .hf-voice, #s02-line .hf-voice { color:var(--paper); }
  `);
  S.html(`
    <div class="hf-bg hf-ink"></div>
    <div id="s02-wrap">
      <div id="s02-tw"><div id="s02-title" class="hf-hidden">${UI.voice(title.text, { size: 210 })}</div></div>
      <div id="s02-line" class="hf-hidden">${UI.voice(line.text, { size: 112 })}</div>
    </div>
  `);

  const tw = S.q("#s02-tw"), titleEl = S.q("#s02-title");
  // 題字の下の赤線（題字が着地した直後に赤ペンで引く）
  const ul = UI.underline(S.stage, titleEl, { gap: 4, width: 16, seed: 9 });

  // 拍16：硬い切り（シーン頭の1フレーム目で題字はもう着地寸前）
  M.slam(tl, titleEl, title.t, { from: 1.5, y: -30 });
  M.scribble(tl, ul, title.t + HF.beats(0.5), HF.beats(0.75));
  // 拍18：一言
  M.slam(tl, "#s02-line", line.t, { from: 1.4, y: -24 });
  // 止めの微動（題字の包みが呼吸）
  M.breathe(tl, tw, title.t + HF.beats(1), S.end, { amt: 0.015 });
});
