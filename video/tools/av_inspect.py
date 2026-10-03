#!/usr/bin/env python3
"""動画の決定的な検査（LLM不使用）。

使い方:  python3 video/tools/av_inspect.py <video.mp4> <cues.json> [--out DIR] [--tol-frames 1] [--stems DIR|none]
音の立ち上がり：BGM が鳴り続ける mix では、効果音の立ち上がりが埋もれて測れない。
  --stems（既定 video/out/audio/）に mix.wav と sfx.wav があれば、まず動画の音と mix.wav の
  ずれを相互相関で確かめ（一致すれば）、効果音だけの sfx.wav で立ち上がりを測る。
  立ち上がり＝「直後8ms − 直前20ms」の平均レベル差が最大の点（6dB 以上）。無ければ「検出不能」（ずれ扱いにしない）。
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
    """窓 [t0,t1] 秒で、音が最もはっきり立ち上がる点の時刻と状態を返す。
    点 τ の強さ＝「直後 8ms の平均レベル」−「直前 20ms の平均レベル」（dB、1ms 刻みのエネルギーで計算）。
    最大の点が 6dB 未満なら「検出不能」（ずれ扱いにしない）。ファイルの先頭より前は無音として扱う。
    旧方式（窓内ピークの15%を最初に超える点）は、BGM が鳴り続ける mix では窓の左端を返し、
    -100ms の偽のずれを大量に出した（v1 で 71 件）。3ms の差だけで見る方式も、ノイズ系の音の
    細かな揺れ（±6dB）を立ち上がりと取り違えた。"""
    PRE, POST, hop = 20, 8, SR // 1000
    a, b = int(t0 * SR) - PRE * hop, int(t1 * SR) + POST * hop
    pad_l = max(0, -a)
    seg = np.concatenate([np.zeros(pad_l, np.float32), x[max(0, a):min(len(x), b)]])
    if len(seg) == 0 or np.abs(seg).max() < 0.01:
        return None, "無音"
    m = len(seg) // hop
    le = 10 * np.log10(np.mean(seg[: m * hop].reshape(m, hop).astype(np.float64) ** 2, axis=1) + 1e-12)
    cs = np.concatenate([[0.0], np.cumsum(le)])
    best, best_k = -1e9, None
    for k in range(PRE, m - POST + 1):
        score = (cs[k + POST] - cs[k]) / POST - (cs[k] - cs[k - PRE]) / PRE
        if score > best:
            best, best_k = score, k
    if best_k is None or best < 6.0:
        return None, "検出不能"
    return (a + best_k * hop) / SR, "ok"


def align_lag(x, y):
    """x（動画の音）に対する y（stem の mix）の遅れ（秒）と相関。±0.2秒を探す。"""
    n = min(len(x), len(y))
    if n == 0:
        return None, 0.0
    N = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(x[:n], N) * np.conj(np.fft.rfft(y[:n], N)), N)
    L = int(0.2 * SR)
    w = np.concatenate([c[-L:], c[: L + 1]])
    lag = int(np.argmax(w)) - L
    ys = np.roll(y[:n], lag)
    corr = float(np.corrcoef(x[:n], ys)[0, 1])
    return lag / SR, corr


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
    ap.add_argument("--stems", default=str(Path(__file__).resolve().parents[1] / "out" / "audio"),
                    help="mix.wav と sfx.wav のあるディレクトリ。none で使わない")
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
    # 生の PCM に書き出すと、コンテナ上の音声の開始位置（start_time）が捨てられる。
    # 音声が映像より遅れて始まるファイルを「ずれなし」と見逃すので、開始位置の差を無音で埋めて戻す
    a_off = (info["a_start"] - info["v_start"]) if info["has_audio"] else 0.0
    if len(x) and abs(a_off) > 0.5 / SR:
        k = int(round(a_off * SR))
        x = np.concatenate([np.zeros(k, np.float32), x]) if k > 0 else x[-k:]
    # 立ち上がりを測る音：stem が動画の音と一致すれば sfx.wav（効果音だけ）、でなければ動画の音
    meas, meas_src, stem_note, lag_s, mix = x, "動画の音（mix）", "stem 不使用", 0.0, None
    sd = None if a.stems == "none" else Path(a.stems)
    if len(x) and sd and (sd / "mix.wav").exists() and (sd / "sfx.wav").exists():
        mix = decode_audio(sd / "mix.wav")
        lag_s, corr = align_lag(x, mix)
        if lag_s is not None and corr >= 0.95:
            sfx = decode_audio(sd / "sfx.wav")
            shift = int(round(lag_s * SR))
            meas = np.roll(np.pad(sfx, (0, max(0, len(x) - len(sfx)))), shift)[: len(x)]
            meas_src = "sfx.wav（効果音だけ）"
            stem_note = f"動画の音と {sd}/mix.wav のずれ {lag_s * 1000:+.2f}ms・相関 {corr:.3f} → 一致。立ち上がりは sfx.wav で測定"
        else:
            stem_note = f"動画の音と {sd}/mix.wav が一致しない（ずれ {0 if lag_s is None else lag_s * 1000:+.1f}ms・相関 {corr:.3f}）→ 動画の音で測定（BGM で検出不能が増える）"

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
        kind = e.get("kind")
        if kind == "silence":
            # 溜め：その拍のあいだ、mix がほぼ無音か（-30dBFS 未満）
            src = mix if mix is not None else x
            lo_s, hi_s = int((e["t"] + 0.02) * SR), int((e["t"] + spb - 0.02) * SR)
            pk = float(np.abs(src[lo_s:hi_s]).max()) if len(src) and hi_s > lo_s else 0.0
            a_t, a_status = None, ("無音（ok）" if pk < 10 ** (-30 / 20) else f"無音のはずが {20 * np.log10(pk + 1e-9):.1f}dBFS")
        elif kind == "riser":
            a_t, a_status = None, "対象外（上昇音。山は次の拍頭）"
        elif len(meas):
            a_t, a_status = audio_onset(meas, e["t"] - 0.1, e["t"] + 0.1)
        else:
            a_t, a_status = None, "音声なし"
        rows.append({
            "i": e["i"], "beat": e["beat"], "kind": kind, "event_s": round(e["t"], 4), "audio_status": a_status,
            "audio_onset_s": None if a_t is None else round(a_t, 4),
            "audio_minus_event_ms": None if a_t is None else round((a_t - e["t"]) * 1000, 1),
            "visual_change_s": None if v_t is None else round(v_t, 4),
            "visual_minus_event_ms": None if v_t is None else round((v_t - e["t"]) * 1000, 1),
            "audio_minus_visual_ms": None if (a_t is None or v_t is None) else round((a_t - v_t) * 1000, 1),
        })
    # 1フレーム超のずれ（音とイベント、音と絵）。音の無いイベント(silence)は対象外
    def bad(r):
        if r["kind"] == "silence":
            return not r["audio_status"].startswith("無音（ok）")
        for k in ("audio_minus_event_ms", "audio_minus_visual_ms", "visual_minus_event_ms"):
            if r[k] is not None and abs(r[k]) > tol_ms + 0.5:
                return True
        return False  # 検出不能は「ずれ」に数えない（別に件数を出す）
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
    undetected = [r for r in rows if r["audio_status"] == "検出不能"]
    if over: flags.append(f"ずれ・溜めの不成立 {len(over)} 件 (許容 {tol_ms:.1f}ms)")
    if loud["clipped_samples"]: flags.append(f"クリップ {loud['clipped_samples']} サンプル")
    if loud["true_peak_dbfs"] is not None and loud["true_peak_dbfs"] > -1.0: flags.append(f"True Peak {loud['true_peak_dbfs']} dBFS > -1.0")
    if bl: flags.append(f"黒画面 {len(bl)} 箇所")
    if fz: flags.append(f"静止 {len(fz)} 箇所")
    if abs(info["duration"] - n / fps) > 2 / fps: flags.append(f"尺と映像フレーム数の食い違い ({info['duration']}s / {n}f)")
    if not info["has_audio"]: flags.append("音声トラックなし")

    summary = {"video": str(vp), "cues": a.cues, "duration_s": info["duration"], "fps": fps, "size": [info["w"], info["h"]],
               "frames": n, "frame_ms": round(frame_ms, 2), "tolerance_ms": round(tol_ms, 2),
               "stream_start": {"video": info["v_start"], "audio": info["a_start"]},
               "audio_measured_on": meas_src, "stems": stem_note, "undetected": len(undetected),
               "events": rows, "scenes": scene_rows, "cuts_s": cuts, "loudness": loud,
               "black": bl, "freeze": fz, "flags": flags, "ok": not flags}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    md = [f"# 検査 {vp.name}", "",
          f"- 尺 {info['duration']:.3f}s / {info['w']}x{info['h']} / {fps:g}fps / {n}フレーム（1フレーム={frame_ms:.1f}ms、許容 {tol_ms:.1f}ms）",
          f"- 音量 {loud['integrated_lufs']} LUFS / True Peak {loud['true_peak_dbfs']} dBFS / サンプルピーク {loud['sample_peak']} / クリップ {loud['clipped_samples']}",
          f"- 黒画面 {len(bl)} / 静止 {len(fz)}" + (" （" + ", ".join(f"{z['start']:.2f}s〜{z['duration']:.2f}s間" for z in fz) + "）" if fz else ""),
          f"- 音の立ち上がりの測定：{meas_src}。{stem_note}。検出不能 {len(undetected)} 件（ずれには数えない）",
          f"- 判定: {'異常なし' if not flags else '要確認 — ' + '; '.join(flags)}", "",
          "## 音と拍のずれ（ms。+は遅れ）", "",
          "| # | 拍 | kind | イベント s | 音−イベント | 絵−イベント | 音−絵 | 音の状態 | 超過 |", "|---|---|---|---|---|---|---|---|---|"]
    f = lambda v: "n/a" if v is None else f"{v:+.1f}"
    for r in rows:
        md.append(f"| {r['i']} | {r['beat']} | {r['kind']} | {r['event_s']:.3f} | {f(r['audio_minus_event_ms'])} | {f(r['visual_minus_event_ms'])} | {f(r['audio_minus_visual_ms'])} | {r['audio_status']} | {'超過' if r['over_tol'] else ''} |")
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
