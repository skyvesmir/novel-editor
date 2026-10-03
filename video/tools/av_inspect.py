#!/usr/bin/env python3
"""動画の決定的な検査（LLM不使用）。

使い方:  python3 video/tools/av_inspect.py <video.mp4> <cues.json> [--out DIR] [--tol-frames 1]
出力先:  video/out/inspect/<動画名>/  （既定）
  overview.png        2fps の縮小一覧（タイル、時刻つき）
  bands/ev###.png     cues の各イベント時刻の前後±2フレームの帯
  summary.json / summary.md
終了コード: 0=異常なし / 1=音ズレ・クリップ・黒画面・静止などの指摘あり / 2=入力不備
依存: ffmpeg/ffprobe, numpy, pillow
"""
import os, sys
# このファイル名 av_inspect.py が標準ライブラリ inspect を隠して numpy が壊れるのを防ぐ（実測済みの落とし穴）
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
import argparse, json, re, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

SR = 48000          # 音声解析のサンプルレート
GW, GH = 96, 54     # 画面差分用のグレー縮小サイズ
TW, TH = 480, 270   # 一覧・帯のタイルサイズ


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, **kw)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)])
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    n, d = map(int, v["r_frame_rate"].split("/"))
    return {"fps": n / d, "w": int(v["width"]), "h": int(v["height"]),
            "duration": float(j["format"]["duration"]), "has_audio": a is not None,
            "v_start": float(v.get("start_time", 0)), "a_start": float(a.get("start_time", 0)) if a else 0.0,
            "nb_frames": int(v.get("nb_frames") or 0)}


def decode_video(path, fps, keep, need_tiles):
    """全フレームをストリームで読み、グレー縮小は全部、カラータイルは必要なものだけ保持。"""
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={TW}:{TH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = TW * TH * 3
    grays, tiles, i = [], {}, 0
    while True:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        arr = np.frombuffer(buf, np.uint8).reshape(TH, TW, 3)
        img = Image.fromarray(arr)
        g = np.asarray(img.convert("L").resize((GW, GH), Image.BILINEAR), dtype=np.float32)
        grays.append(g)
        if i in need_tiles:
            tiles[i] = img
        i += 1
    p.wait()
    return np.stack(grays), tiles


def decode_audio(path):
    # -ac 1 は同じ内容の2chを足し合わせて +3dB になり、クリップの誤検出を生む（実測）。チャンネルは保ったまま読み、絶対値の最大で1本にする
    ch = int(json.loads(run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "json", str(path)]).stdout)["streams"][0]["channels"])
    r = run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ar", str(SR), "-f", "f32le", "-"])
    y = np.frombuffer(r.stdout, np.float32)
    y = y[: len(y) // ch * ch].reshape(-1, ch)
    return y[np.arange(len(y)), np.abs(y).argmax(axis=1)]  # 符号つきで、各時刻の最大振幅のチャンネルを採る


def audio_onset(x, t0, t1):
    """窓 [t0,t1] 秒で、窓内ピークの 15% を最初に超えるサンプルの時刻を返す。無音なら None。"""
    a, b = max(0, int(t0 * SR)), min(len(x), int(t1 * SR))
    seg = np.abs(x[a:b])
    if len(seg) == 0 or seg.max() < 0.01:
        return None
    thr = seg.max() * 0.15
    return (a + int(np.argmax(seg >= thr))) / SR


def label(img, text):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 8 * len(text) + 8, 16], fill=(0, 0, 0))
    d.text((4, 2), text, fill=(255, 255, 0))
    return img


def tile(imgs, cols):
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TW, rows * TH), (0, 0, 0))
    for k, im in enumerate(imgs):
        sheet.paste(im, ((k % cols) * TW, (k // cols) * TH))
    return sheet


def ffmpeg_filter_log(path, vf=None, af=None):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path)]
    if vf: cmd += ["-vf", vf, "-an"]
    if af: cmd += ["-af", af, "-vn"]
    cmd += ["-f", "null", "-"]
    return run(cmd, text=True).stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("cues")
    ap.add_argument("--out"); ap.add_argument("--tol-frames", type=float, default=1.0)
    a = ap.parse_args()
    vp = Path(a.video)
    if not vp.exists() or not Path(a.cues).exists():
        print("入力が見つかりません", file=sys.stderr); return 2
    cues = json.load(open(a.cues))
    out = Path(a.out) if a.out else Path(__file__).resolve().parents[1] / "out" / "inspect" / vp.stem
    (out / "bands").mkdir(parents=True, exist_ok=True)

    info = probe(vp); fps = info["fps"]; frame_ms = 1000 / fps; tol_ms = a.tol_frames * frame_ms
    spb = 60 / cues["bpm"]
    events = [{"i": i, "t": e["beat"] * spb, **e} for i, e in enumerate(cues["events"])]
    scenes = [{"id": s["id"], "t": s["startBeat"] * spb} for s in cues.get("scenes", [])]

    # --- 映像
    step = max(1, round(fps / 2))
    need = set()
    for e in events:
        c = round(e["t"] * fps)
        need.update(range(max(0, c - 2), c + 3))
    nframes_est = int(info["duration"] * fps) + 2
    need.update(range(0, nframes_est, step))
    grays, tiles = decode_video(vp, fps, set(), need)
    n = len(grays)
    diff = np.zeros(n); diff[1:] = np.abs(grays[1:] - grays[:-1]).mean(axis=(1, 2))  # diff[k]: フレーム k-1→k の変化量

    ov = [label(tiles[k].copy(), f"{k / fps:.2f}s #{k}") for k in range(0, n, step) if k in tiles]
    tile(ov, 6).save(out / "overview.png")

    # --- 音声
    x = decode_audio(vp) if info["has_audio"] else np.zeros(0, np.float32)

    rows = []
    for e in events:
        c = round(e["t"] * fps)
        # 帯
        frames = [k for k in range(c - 2, c + 3) if 0 <= k < n and k in tiles]
        if frames:
            tile([label(tiles[k].copy(), f"{k / fps:.3f}s #{k}" + (" <=EV" if k == c else "")) for k in frames], 5).save(out / "bands" / f"ev{e['i']:03d}.png")
        # 画の変化：窓内の最大差分の 50% を最初に超えたフレーム
        lo, hi = max(1, c - 2), min(n - 1, c + 4)
        v_t = None
        if c >= 1 and lo <= hi:
            w = diff[lo:hi + 1]
            if w.max() > 2.0:
                v_t = (lo + int(np.argmax(w >= w.max() * 0.5))) / fps
        a_t = audio_onset(x, e["t"] - 0.1, e["t"] + 0.25) if len(x) else None
        rows.append({
            "i": e["i"], "beat": e["beat"], "kind": e.get("kind"), "event_s": round(e["t"], 4),
            "audio_onset_s": None if a_t is None else round(a_t, 4),
            "audio_minus_event_ms": None if a_t is None else round((a_t - e["t"]) * 1000, 1),
            "visual_change_s": None if v_t is None else round(v_t, 4),
            "visual_minus_event_ms": None if v_t is None else round((v_t - e["t"]) * 1000, 1),
            "audio_minus_visual_ms": None if (a_t is None or v_t is None) else round((a_t - v_t) * 1000, 1),
        })
    # 1フレーム超のずれ（音とイベント、音と絵）。音の無いイベント(silence)は対象外
    def bad(r):
        if r["kind"] == "silence":
            return False
        for k in ("audio_minus_event_ms", "audio_minus_visual_ms", "visual_minus_event_ms"):
            if r[k] is not None and abs(r[k]) > tol_ms + 0.5:
                return True
        return r["audio_onset_s"] is None and r["kind"] != "silence"
    for r in rows:
        r["over_tol"] = bad(r)

    # --- 画面の切り替わり（差分が中央値の数倍かつ絶対値が大きいフレーム）
    thr = max(8.0, float(np.median(diff)) * 6)
    cuts = [round(k / fps, 4) for k in range(1, n) if diff[k] >= thr]
    scene_rows = []
    for s in scenes:
        near = min(cuts, key=lambda t: abs(t - s["t"]), default=None)
        scene_rows.append({"id": s["id"], "start_s": round(s["t"], 4), "nearest_cut_s": near,
                           "cut_minus_start_ms": None if near is None else round((near - s["t"]) * 1000, 1)})

    # --- 音量
    loud = {}
    log = ffmpeg_filter_log(vp, af="ebur128=peak=true") if info["has_audio"] else ""
    m = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+) LUFS", log)
    p = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+) dBFS", log)
    loud["integrated_lufs"] = float(m.group(1)) if m else None
    loud["true_peak_dbfs"] = float(p.group(1)) if p else None
    loud["sample_peak"] = round(float(np.abs(x).max()), 4) if len(x) else None
    loud["clipped_samples"] = int((np.abs(x) >= 0.999).sum()) if len(x) else 0
    loud["has_audio"] = info["has_audio"]

    # --- 黒・静止
    bl = [{"start": float(s), "end": float(e)} for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", ffmpeg_filter_log(vp, vf="blackdetect=d=0.1:pic_th=0.98"))]
    fz_log = ffmpeg_filter_log(vp, vf="freezedetect=n=-60dB:d=0.5")
    fz_s = [float(v) for v in re.findall(r"freeze_start: ([\d.]+)", fz_log)]
    fz_d = [float(v) for v in re.findall(r"freeze_duration: ([\d.]+)", fz_log)]
    fz = [{"start": s, "duration": d} for s, d in zip(fz_s, fz_d)]
    if len(fz_s) > len(fz_d):  # 末尾まで静止
        fz.append({"start": fz_s[-1], "duration": round(info["duration"] - fz_s[-1], 3)})

    expected = (max([e["t"] for e in events] + [s["t"] for s in scenes] + [0]))
    flags = []
    over = [r for r in rows if r["over_tol"]]
    if over: flags.append(f"音ズレ/検出失敗 {len(over)} 件 (許容 {tol_ms:.1f}ms)")
    if loud["clipped_samples"]: flags.append(f"クリップ {loud['clipped_samples']} サンプル")
    if loud["true_peak_dbfs"] is not None and loud["true_peak_dbfs"] > -1.0: flags.append(f"True Peak {loud['true_peak_dbfs']} dBFS > -1.0")
    if bl: flags.append(f"黒画面 {len(bl)} 箇所")
    if fz: flags.append(f"静止 {len(fz)} 箇所")
    if abs(info["duration"] - n / fps) > 2 / fps: flags.append(f"尺と映像フレーム数の食い違い ({info['duration']}s / {n}f)")
    if not info["has_audio"]: flags.append("音声トラックなし")

    summary = {"video": str(vp), "cues": a.cues, "duration_s": info["duration"], "fps": fps, "size": [info["w"], info["h"]],
               "frames": n, "frame_ms": round(frame_ms, 2), "tolerance_ms": round(tol_ms, 2),
               "stream_start": {"video": info["v_start"], "audio": info["a_start"]},
               "events": rows, "scenes": scene_rows, "cuts_s": cuts, "loudness": loud,
               "black": bl, "freeze": fz, "flags": flags, "ok": not flags}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    md = [f"# 検査 {vp.name}", "",
          f"- 尺 {info['duration']:.3f}s / {info['w']}x{info['h']} / {fps:g}fps / {n}フレーム（1フレーム={frame_ms:.1f}ms、許容 {tol_ms:.1f}ms）",
          f"- 音量 {loud['integrated_lufs']} LUFS / True Peak {loud['true_peak_dbfs']} dBFS / サンプルピーク {loud['sample_peak']} / クリップ {loud['clipped_samples']}",
          f"- 黒画面 {len(bl)} / 静止 {len(fz)}",
          f"- 判定: {'異常なし' if not flags else '要確認 — ' + '; '.join(flags)}", "",
          "## 音と拍のずれ（ms。+は遅れ）", "",
          "| # | 拍 | kind | イベント s | 音−イベント | 絵−イベント | 音−絵 | 超過 |", "|---|---|---|---|---|---|---|---|"]
    f = lambda v: "n/a" if v is None else f"{v:+.1f}"
    for r in rows:
        md.append(f"| {r['i']} | {r['beat']} | {r['kind']} | {r['event_s']:.3f} | {f(r['audio_minus_event_ms'])} | {f(r['visual_minus_event_ms'])} | {f(r['audio_minus_visual_ms'])} | {'超過' if r['over_tol'] else ''} |")
    md += ["", "## シーン開始と画面切り替え", "", "| シーン | 開始 s | 最寄りの切り替え s | 差 ms |", "|---|---|---|---|"]
    for s in scene_rows:
        md.append(f"| {s['id']} | {s['start_s']:.3f} | {s['nearest_cut_s']} | {f(s['cut_minus_start_ms'])} |")
    md += ["", f"画面切り替え（差分が閾値 {thr:.1f} 以上のフレーム）: {len(cuts)} 回", "",
           "画像: `overview.png`（2fps 一覧）、`bands/ev###.png`（イベント±2フレーム）", ""]
    (out / "summary.md").write_text("\n".join(md))
    print("\n".join(md[:6]))
    print(f"-> {out}")
    return 0 if not flags else 1


if __name__ == "__main__":
    sys.exit(main())
