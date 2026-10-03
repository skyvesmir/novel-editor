// 起動：フォントを読み込んでから各シーンの組み立て関数を呼び、1本の paused timeline を登録する。
(function () {
  "use strict";
  const C = window.CUES, CFG = window.HF_CONFIG, HF = window.HF;
  const FONTS = ['400 60px "Dela"', '400 60px "Mincho"', '700 60px "Mincho"', '600 60px "Klee"', '500 60px "ZenKaku"', '900 60px "ZenKaku"'];

  function placeholder(S) {
    S.html(`<div class="hf-placeholder"><b>${HF.esc(S.id)}</b><div>${HF.esc(S.purpose || "")}</div><div>（未実装）</div></div>`);
  }

  function build() {
    const tl = gsap.timeline({ paused: true });
    for (const s of C.scenes) {
      if (!CFG.only.includes(s.id)) continue;
      const el = document.getElementById("scene-" + s.id);
      const stage = document.createElement("div");
      stage.className = "hf-stage";
      stage.id = s.id + "-stage";
      el.appendChild(stage);
      const S = {
        id: s.id,
        purpose: s.purpose,
        el, // .clip（動かさない）
        stage, // シーンの中身を入れる包み（shake などはここか子に掛ける）
        tl,
        startBeat: s.startBeat,
        lengthBeats: s.lengthBeats,
        start: HF.at(s.startBeat),
        end: HF.at(s.startBeat + s.lengthBeats),
        ev: HF.events(s.id),
        at: HF.at,
        // kind（と text）でイベントを探す。n 番目（0始まり）
        find(kind, n = 0) {
          return this.ev.filter((e) => e.kind === kind)[n];
        },
        html(str) {
          stage.innerHTML = str;
          return stage;
        },
        q: (sel) => stage.querySelector(sel),
        qa: (sel) => Array.from(stage.querySelectorAll(sel)),
        css(text) {
          const st = document.createElement("style");
          st.textContent = text;
          document.head.appendChild(st);
        },
      };
      const fn = HF._scenes[s.id];
      if (fn) fn(S);
      else placeholder(S);
    }
    window.__timelines["main"] = tl;
    if (typeof window.__hfForceTimelineRebind === "function") window.__hfForceTimelineRebind();
  }

  Promise.all(FONTS.map((f) => document.fonts.load(f, "あ漢A1")))
    .catch(() => null)
    .then(build);
})();
