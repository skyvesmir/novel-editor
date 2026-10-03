#!/usr/bin/env node
// cues.json（時間の正本）から index.html と scenes/cues.js を生成する。手で index.html を編集しない。
//
//   node tools/build.mjs                 本番（全シーン・64秒）: index.html, scenes/cues.js
//   node tools/build.mjs --solo s01-hook  1シーンだけ: _solo-s01-hook.html（時刻はシーン頭=0 にずらす）
//   node tools/build.mjs --solo s01-hook,s02-title   連続する複数シーン（つなぎ目の確認用）
//
// 秒はすべて cues.json の frame / fps から計算する（直書きしない）。
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PROJ = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const VIDEO = path.dirname(PROJ);
const CUES_PATH = path.join(VIDEO, "brief", "cues.json");
const MIX_SRC = path.join(VIDEO, "out", "audio", "mix.wav");
const MIX_DST = path.join(PROJ, "assets", "audio", "mix.wav");

const cues = JSON.parse(fs.readFileSync(CUES_PATH, "utf8"));
const fps = cues.fps;
const fpb = (fps * 60) / cues.bpm; // 1拍のフレーム数（150BPM・30fps → 12）
const beatToFrame = (b) => Math.round(b * fpb);
const sec = (frames) => +(frames / fps).toFixed(6);

const args = process.argv.slice(2);
const soloArg = args.includes("--solo") ? args[args.indexOf("--solo") + 1] : null;

// --- 音：mix.wav があればプロジェクト内に写す（無ければ無音で書き出す）
let hasMix = false;
if (fs.existsSync(MIX_SRC)) {
  fs.mkdirSync(path.dirname(MIX_DST), { recursive: true });
  const s = fs.statSync(MIX_SRC);
  const d = fs.existsSync(MIX_DST) ? fs.statSync(MIX_DST) : null;
  if (!d || d.size !== s.size || d.mtimeMs < s.mtimeMs) fs.copyFileSync(MIX_SRC, MIX_DST);
  hasMix = true;
} else if (fs.existsSync(MIX_DST)) {
  hasMix = true; // 前に写したもの
}

// --- scenes/cues.js（cues.json をそのまま埋め込む。fetch は決定的でないので使わない）
const cuesJs = `// 生成物（tools/build.mjs）。編集しない。正本は video/brief/cues.json\nwindow.CUES = ${JSON.stringify(cues, null, 1)};\n`;
const cuesJsPath = path.join(PROJ, "scenes", "cues.js");
if (!fs.existsSync(cuesJsPath) || fs.readFileSync(cuesJsPath, "utf8") !== cuesJs) fs.writeFileSync(cuesJsPath, cuesJs);

// --- 対象シーン
let scenes = cues.scenes;
if (soloArg) {
  const ids = soloArg.split(",");
  const idx = ids.map((id) => cues.scenes.findIndex((s) => s.id === id || s.id.startsWith(id + "-") || s.id.split("-")[0] === id));
  if (idx.some((i) => i < 0)) {
    console.error(`シーンが見つかりません: ${soloArg}\n候補: ${cues.scenes.map((s) => s.id).join(" ")}`);
    process.exit(2);
  }
  const lo = Math.min(...idx), hi = Math.max(...idx);
  scenes = cues.scenes.slice(lo, hi + 1);
}
const offsetFrame = beatToFrame(scenes[0].startBeat);
const endFrame = beatToFrame(scenes[scenes.length - 1].startBeat + scenes[scenes.length - 1].lengthBeats);
const totalFrames = endFrame - offsetFrame;

const sceneDivs = scenes
  .map((s, i) => {
    const st = beatToFrame(s.startBeat) - offsetFrame;
    const du = beatToFrame(s.lengthBeats);
    return `      <div id="scene-${s.id}" class="clip scene" data-start="${sec(st)}" data-duration="${sec(du)}" data-track-index="${1 + (i % 2)}"></div>`;
  })
  .join("\n");

const audio = hasMix
  ? `      <audio id="mix" src="assets/audio/mix.wav" data-start="0" data-duration="${sec(totalFrames)}"${offsetFrame ? ` data-media-start="${sec(offsetFrame)}"` : ""} data-volume="1" data-track-index="0"></audio>\n`
  : "";

const sceneScripts = cues.scenes.map((s) => `    <script src="scenes/${s.id}.js"></script>`).join("\n");
const baseCss = fs.readFileSync(path.join(PROJ, "scenes", "base.css"), "utf8");
const config = { only: scenes.map((s) => s.id), offsetFrame, totalFrames, solo: !!soloArg };

const html = `<!doctype html>
<!-- 生成物（tools/build.mjs）。手で編集しない。シーンは scenes/<id>.js、共通部品は scenes/lib.js -->
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${cues.width}, height=${cues.height}" />
    <script src="assets/gsap.min.js"></script>
    <style>
${baseCss}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${sec(totalFrames)}" data-fps="${fps}" data-width="${cues.width}" data-height="${cues.height}" data-hf-config="${JSON.stringify(config).replace(/"/g, "&quot;")}">
${sceneDivs}
${audio}    </div>
    <script>
      window.HF_CONFIG = ${JSON.stringify(config)};
      window.__timelines = window.__timelines || {}; // 登録は scenes/main.js（window.__timelines["main"] = tl）
    </script>
    <script src="scenes/cues.js"></script>
    <script src="scenes/lib.js"></script>
${sceneScripts}
    <script src="scenes/main.js"></script>
  </body>
</html>
`;

const outName = soloArg ? `_solo-${scenes.map((s) => s.id.split("-")[0]).join("-")}.html` : "index.html";
fs.writeFileSync(path.join(PROJ, outName), html);
console.log(
  `${outName}: ${scenes.map((s) => s.id).join(", ")} / ${sec(totalFrames)}s (${totalFrames}f) / 音 ${hasMix ? "mix.wav" : "なし（無音）"}`
);
