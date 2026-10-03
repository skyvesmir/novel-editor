"""BGM v5：150BPM のまま、体感 75BPM のハーフタイム（フューチャーベース／チル・トラップ寄り）。D マイナー。
主役は効果音と字幕。BGM は「洒落た床」：中域（1〜4kHz）は空け、低域はモノラル。

和声（4つの循環）：Dm9 → Bbmaj9 → Gm9 → A7(b9)。ベースは根音。掴みのスタブだけ Bbmaj9 → Cadd9 → Dm9
（効果音の slam の根音 Bb・C・D と同じ）。上声は 3・5・7・9 度のルートレス・ボイシング。

音色：
  chords ：7声のわずかにデチューンした鋸波（PolyBLEP）×4音。ステレオに散らし、時間で動くローパスで角を取る
  stab   ：同じ鋸波の和音を、打鍵ごとのフィルタ・エンベロープで弾く（掴み・ドロップ・締めのリズム）
  bass   ：サブ（正弦＋2・3倍音＋軽い飽和）。モノラル。音の切り替えで短いグライド
  lead   ：2声の鋸波を 1.6kHz で丸めた柔らかいリード。3〜4音の動機だけ。付点8分のピンポン
  kick   ：短くタイト（200→50Hz、減衰 0.1秒）。ハーフタイムの型で、全拍は叩かない
  snare  ：胴＋雑音＋クラップの重ね。小節の3拍目（＝ハーフタイムの2拍目の裏拍ではなく、体感の3拍目）
  hat    ：808 系の金属音（6つの矩形の和を 7.5kHz 以上で）。16分にスウィングとベロシティの揺れ、三連と32分のロール
  riser  ：拍124〜131 の上昇（ピッチ＋1オクターブ、フィルタ 600Hz→7kHz）
仕上げ：キックと（デモでは聞こえない）ゴーストのトリガーでコード・ベース・リードをサイドチェイン。
テープ風の飽和（偶数次をわずかに）とごく薄いヒス。拍130.25〜131 はテープストップ。

展開（拍）：
  0–12   hook    ：Dm9 スタブ×3 → 溜め → 4拍の溜め（フィルタが開く）→ Bb・C・Dm のスタブ → 拍10 でフィルタが閉じる → 溜め
  12–24  drop    ：最大の密度。フィルタが一気に開き、ドラム・スタブのリズム・ベース・動機
  24–88  demo    ：和音・ハット・ベースだけの床（ドラムなし。ポンプはゴーストのトリガー）
  88–116 section ：フィルタを開けて揺らし、ハットを三連の型に替える
  116–124 pullback：和音とベースだけ、フィルタを閉じる
  124–131 build  ：フィルタとピッチを上げ、ハットが密になる。拍131 の頭へテープストップで断ち切る
  132–152 peak/outro：全部入り
  152–160 final  ：Dm9 の余韻で閉じる
"""
import numpy as np
from synth import (SR, midi_hz, secs, env_exp, sine_sweep, noise, fft_filter, pan, make_ir, convolve, sat, place)

SPB = 19200  # 1拍のサンプル数（0.4s × 48000）


def b2s(beat):
    return int(round(beat * SPB))


# ------------------------------------------------------------------ 和声
CH = {  # 名前: (ベースの根音 MIDI, 上声のボイシング)
    "Dm9": (38, (53, 57, 60, 64)),      # F A C E   / D
    "Bbmaj9": (34, (50, 53, 57, 60)),   # D F A C   / Bb
    "Gm9": (31, (53, 58, 62, 69)),      # F Bb D A  / G
    "A7b9": (33, (49, 55, 58, 64)),     # C# G Bb E / A
    "A7sus": (33, (50, 55, 59, 64)),    # D G B E   / A（9・sus4）
    "Cadd9": (36, (52, 55, 60, 62)),    # E G C D   / C
    "Dm9f": (38, (53, 57, 60, 64, 69)),  # 最後の和音（上に A を足す）
}

TL = [  # (開始拍, 終了拍, 和音)
    (0, 8, "Dm9"), (8, 9, "Bbmaj9"), (9, 10, "Cadd9"), (10, 12, "Dm9"),
    (12, 16, "Dm9"), (16, 20, "Bbmaj9"), (20, 22, "Gm9"), (22, 24, "A7b9"),
    (24, 32, "Dm9"), (32, 40, "Bbmaj9"), (40, 48, "Gm9"), (48, 56, "A7b9"),
    (56, 64, "Dm9"), (64, 72, "Bbmaj9"), (72, 80, "Gm9"), (80, 88, "A7b9"),
    (88, 96, "Dm9"), (96, 104, "Bbmaj9"), (104, 112, "Gm9"), (112, 116, "A7b9"),
    (116, 120, "Dm9"), (120, 124, "Bbmaj9"),
    (124, 128, "Gm9"), (128, 131, "A7sus"),
    (132, 136, "Dm9"),
    (136, 140, "Dm9"), (140, 144, "Bbmaj9"), (144, 148, "Gm9"), (148, 152, "A7b9"),
    (152, 160, "Dm9f"),
]


def chord_at(beat):
    for a, b, c in TL:
        if a <= beat < b:
            return c
    return "Dm9"


SECTIONS = [("hook", 0, 12), ("drop", 12, 24), ("demo", 24, 88), ("section", 88, 116), ("pullback", 116, 124),
            ("build", 124, 132), ("peak", 132, 136), ("outro", 136, 152), ("final", 152, 161)]


def section(beat):
    for name, a, b in SECTIONS:
        if a <= beat < b:
            return name
    return "final"


# ------------------------------------------------------------------ 発振器・フィルタ
def saw(f, n, ph0=0.0):
    """PolyBLEP の鋸波（折り返しを抑える）。f はスカラーか長さ n の配列。"""
    dt = np.broadcast_to(np.asarray(f, float), (n,)) / SR
    ph = (ph0 + np.cumsum(dt)) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    x = ph[m] / dt[m]
    y[m] -= 2 * x - x * x - 1
    m = ph > 1 - dt
    x = (ph[m] - 1) / dt[m]
    y[m] -= x * x + 2 * x + 1
    return y


def supersaw(f, n, rng, voices=7, cents=12.0, width=0.85):
    """デチューンした鋸波 voices 本をステレオに散らす。中央の声を少し強く。(n,2)"""
    f = np.broadcast_to(np.asarray(f, float), (n,))
    det = np.linspace(-1, 1, voices) * cents
    pans = np.linspace(-width, width, voices)
    rng.shuffle(pans)
    out = np.zeros((n, 2))
    for k in range(voices):
        g = 1.0 if abs(det[k]) > 1e-9 else 1.4
        x = saw(f * 2 ** (det[k] / 1200), n, rng.uniform())
        a = (pans[k] + 1) * np.pi / 4
        out[:, 0] += x * np.cos(a) * g
        out[:, 1] += x * np.sin(a) * g
    return out / np.sqrt(voices)


def tv_lowpass(x, cut, res=0.0, order=2, nfft=2048, hop=512):
    """時間で動くローパス（STFT のマスク、重ね合わせで戻す）。cut は長さ n の Hz 配列。res は遮断付近の山。"""
    squeeze = x.ndim == 1
    if squeeze:
        x = x[:, None]
    n, C = x.shape
    R = nfft // hop
    win = np.hanning(nfft + 1)[:-1]
    pad = np.concatenate([np.zeros((nfft, C)), x, np.zeros((nfft + hop, C))])
    F = 1 + (len(pad) - nfft) // hop
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    cut = np.asarray(cut, float)
    acc = np.zeros((F + R - 1, hop, C))
    wsq = (win ** 2).reshape(R, hop)
    norm = np.zeros((F + R - 1, hop))
    for r in range(R):
        norm[r:r + F] += wsq[r]
    B = 1024
    for f0 in range(0, F, B):
        f1 = min(F, f0 + B)
        fi = np.arange(f0, f1)
        idx = fi[:, None] * hop + np.arange(nfft)[None, :]
        centers = np.clip(fi * hop + nfft // 2 - nfft, 0, n - 1)
        rr = freqs[None, :] / cut[centers][:, None]
        m = 1 / np.sqrt(1 + rr ** (2 * order))
        if res:
            m = m * (1 + res * np.exp(-((np.log2(np.maximum(rr, 1e-6))) ** 2) / 0.08))
        for ch in range(C):
            Y = np.fft.irfft(np.fft.rfft(pad[idx, ch] * win, axis=1) * m, nfft, axis=1) * win
            Y = Y.reshape(len(fi), R, hop)
            for r in range(R):
                acc[f0 + r:f1 + r, :, ch] += Y[:, r, :]
    out = acc.reshape(-1, C) / np.maximum(norm.reshape(-1), 1e-3)[:, None]
    out = out[nfft:nfft + n]
    return out[:, 0] if squeeze else out


def bell_eq(x, fc, gain_db, width_oct):
    """FFT のベル型 EQ（ゼロ位相）。"""
    n = len(x)
    N = 1 << int(np.ceil(np.log2(n)))
    f = np.maximum(np.fft.rfftfreq(N, 1 / SR), 1.0)
    g = 10 ** (gain_db / 20 * np.exp(-0.5 * (np.log2(f / fc) / width_oct) ** 2))
    X = np.fft.rfft(x, N, axis=0)
    return np.fft.irfft(X * g[:, None], N, axis=0)[:n]


def env_ar(n, attack, gate, release, decay_to=1.0, decay_tau=1.0):
    """立ち上がり attack → 減衰（decay_to へ時定数 decay_tau）→ gate 秒で離して release で消える。"""
    t = secs(n)
    a = np.clip(t / max(attack, 1 / SR), 0, 1)
    d = decay_to + (1 - decay_to) * np.exp(-np.clip(t - attack, 0, None) / decay_tau)
    e = a * d
    g = np.interp(gate, t, e) if gate < t[-1] else e[-1]
    return np.where(t < gate, e, g * np.exp(-(t - gate) / max(release, 1e-4)))


# ------------------------------------------------------------------ 譜面
def score(silences):
    S = {k: [] for k in ("kick", "snare", "hat", "ohat", "crash", "bass", "pad", "stab", "lead", "riser", "trig")}

    def silent(b):
        return any(s <= b < s + 1 for s in silences)

    def add(inst, beat, length=0.25, **kw):
        if silent(beat):
            return
        S[inst].append(dict(beat=float(beat), len=length, **kw))

    def add_sus(inst, a, b, **kw):
        """a〜b 拍の持続音。溜めの拍で切って、溜めの後に弾き直す。"""
        cuts = sorted(s for s in silences if a < s + 1 and s < b)
        cur = a
        for s in cuts:
            if s > cur:
                add(inst, cur, s - cur, **kw)
            cur = max(cur, s + 1)
        if b > cur:
            add(inst, cur, b - cur, **kw)

    def trig(beat, depth):
        add("trig", beat, depth=depth)

    # ---------- 和音の床（pad）：区間ごとに
    for a, b, c in TL:
        sec = section(a)
        if sec == "hook" and a < 4:
            continue  # 拍0〜2 はスタブだけ
        if sec == "hook" and a >= 8:
            continue
        if sec == "hook":
            add_sus("pad", 4, 8, chord=c, attack=0.6, vel=0.8)
            continue
        vel = {"drop": 0.55, "demo": 0.9, "section": 0.85, "pullback": 0.9, "build": 0.8,
               "peak": 0.55, "outro": 0.55, "final": 1.0}[sec]
        att = {"demo": 0.25, "section": 0.18, "pullback": 0.4, "final": 0.004}.get(sec, 0.03)
        if a == 88:
            att = 0.35  # 打鍵音の邪魔をしないよう、静かに入る
        add_sus("pad", a, b, chord=c, attack=att, vel=vel)

    # ---------- hook
    for bt in (0, 1, 2):
        add("stab", bt, 0.7, chord="Dm9", vel=1.0, bright=1.0)
        add("kick", bt, vel=0.95); trig(bt, 0.6)
        add("bass", bt, 0.6, midi=38, vel=0.9)
    add("kick", 4, vel=1.0); trig(4, 0.6)
    add("bass", 4, 3.6, midi=38, vel=0.9)
    add("kick", 5.5, vel=0.7); trig(5.5, 0.45)
    add("snare", 6, vel=0.8)
    hat_line(add, 4.5, 8, "hook")
    for bt, c, r in zip((8, 9, 10), ("Bbmaj9", "Cadd9", "Dm9"), (34, 36, 38)):
        add("stab", bt, 0.85 if bt < 10 else 1.0, chord=c, vel=1.0, bright=1.0, close=(bt == 10))
        add("kick", bt, vel=0.95); trig(bt, 0.6)
        add("bass", bt, 0.8 if bt < 10 else 1.0, midi=r, vel=0.95)
    add("crash", 12, vel=0.9)

    # ---------- ドラムつきの小節（drop・peak・outro）
    KICK_A, KICK_B = (0, 1.5, 2.75), (0, 0.75, 2.5, 3.25)
    CHOP = ((0, 0.55), (0.75, 0.55), (1.5, 0.9), (2.5, 0.55), (3.25, 0.6))

    def full_bar(bar0, k, energy=1.0):
        c = chord_at(bar0)
        root = CH[c][0]
        kicks = KICK_A if k % 2 == 0 else KICK_B
        for i, off in enumerate(kicks):
            add("kick", bar0 + off, vel=(1.0 if off == 0 else 0.8) * energy)
            trig(bar0 + off, 0.7 if off == 0 else 0.55)
        add("snare", bar0 + 2, vel=0.9 * energy)
        if k % 4 == 3:
            add("snare", bar0 + 3.75, vel=0.35 * energy)  # 4小節目の終わりに軽いゴースト
        # ベース：キックに沿う。最後の音から次の小節の根音へ短いグライド
        for i, off in enumerate(kicks):
            nxt = kicks[i + 1] if i + 1 < len(kicks) else 4.0
            m = root + (12 if (k % 2 == 1 and i == len(kicks) - 1) else 0)
            add("bass", bar0 + off, max(0.25, nxt - off - 0.08), midi=m, vel=0.95 * energy)
        for off, ln in CHOP:
            add("stab", bar0 + off, ln, chord=c, vel=0.75 * energy, bright=0.7)
        hat_line(add, bar0, bar0 + 4, "full", k)
        if k % 2 == 1:
            add("ohat", bar0 + 1.5, vel=0.5 * energy)

    for k, bar0 in enumerate((12, 16, 20)):
        full_bar(bar0, k + (1 if bar0 == 12 else 0))
    add("crash", 132, vel=0.8)
    full_bar(132, 0)
    for k, bar0 in enumerate(range(136, 152, 4)):
        full_bar(bar0, k, energy=0.95)

    # 動機（3〜4音）：ドロップと締めで少しだけ
    MOT_A = ((0.5, 0.45, 69), (1.0, 0.7, 72), (1.75, 0.7, 76), (2.5, 1.3, 74))   # A C E D（Dm9 の 5・7・9・1）
    MOT_B = ((0.5, 0.45, 70), (1.0, 0.7, 74), (1.75, 1.6, 69))                    # Bb D A（Gm9 の 3・5・9）
    for bar0, mot in ((12, MOT_A), (20, MOT_B), (136, MOT_A), (144, MOT_B)):
        for off, ln, m in mot:
            add("lead", bar0 + off, ln, midi=m, vel=0.85)

    # ---------- demo 24–88：和音・ハット・ベースだけ
    for bar0 in range(24, 88, 4):
        k = (bar0 - 24) // 4
        c = chord_at(bar0)
        root = CH[c][0]
        trig(bar0, 0.55); trig(bar0 + 1.5, 0.4); trig(bar0 + 2.75, 0.4)
        add("bass", bar0, 1.4, midi=root, vel=0.75)
        add("bass", bar0 + 1.5, 1.1, midi=root, vel=0.6)
        add("bass", bar0 + 2.75, 0.9 if k % 2 else 1.1, midi=root + (12 if k % 2 else 0), vel=0.55)
        hat_line(add, bar0, bar0 + 4, "demo", k)

    # ---------- section 88–116：質感を変える（フィルタを開けて揺らし、ハットは三連の型）
    for bar0 in range(88, 116, 4):
        k = (bar0 - 88) // 4
        c = chord_at(bar0)
        root = CH[c][0]
        trig(bar0, 0.55); trig(bar0 + 1.5, 0.4); trig(bar0 + 2.5, 0.45)
        if bar0 == 88:
            add("bass", 88, 1.4, midi=root, vel=0.5, attack=0.08)  # drop の効果音のサブと重ねない
        else:
            add("bass", bar0, 1.4, midi=root, vel=0.75)
        add("bass", bar0 + 1.5, 0.9, midi=root, vel=0.6)
        add("bass", bar0 + 2.5, 0.6, midi=root + 12, vel=0.5)
        add("bass", bar0 + 3.25, 0.6, midi=root + 7, vel=0.45)
        hat_line(add, max(bar0, 90), bar0 + 4, "section", k)

    # ---------- pullback 116–124
    for bar0 in (116, 120):
        root = CH[chord_at(bar0)][0]
        trig(bar0, 0.3)
        add("bass", bar0, 3.8, midi=root, vel=0.6, attack=0.05)
        for j in range(8):
            add("hat", bar0 + 0.5 + j * 0.5 if j < 7 else bar0 + 3.75, vel=0.5 + 0.12 * (j % 2), dec=0.03)

    # ---------- build 124–131
    add("riser", 124, 7.0, vel=1.0)
    for bar0 in (124, 128):
        root = CH[chord_at(bar0)][0]
        for off in ((0, 1.5, 2.0, 3.0) if bar0 == 124 else (0, 0.75, 1.5, 2.0, 2.5)):
            add("kick", bar0 + off, vel=0.7 + 0.25 * (bar0 - 124 + off) / 7)
            trig(bar0 + off, 0.55)
            add("bass", bar0 + off, 0.45, midi=root + (12 if off % 1 else 0), vel=0.85)
    for b in np.arange(124, 128, 0.5):
        add("hat", b, vel=0.35 + 0.05 * (b - 124), dec=0.03)
    for b in np.arange(128, 130, 0.25):
        add("hat", b, vel=0.4 + 0.08 * (b - 128), dec=0.025)
    for b in np.arange(130, 131, 1 / 8):
        add("hat", b, vel=0.45 + 0.3 * (b - 130), dec=0.02)
    for j, b in enumerate(np.arange(128, 131, 0.5)):
        add("snare", b, vel=0.25 + 0.08 * j)
    for b in np.arange(130, 131, 0.25):
        add("snare", b, vel=0.55 + 0.3 * (b - 130))

    # ---------- final 152–
    add("crash", 152, vel=0.9)
    add("kick", 152, vel=1.0); trig(152, 0.5)
    add("stab", 152, 2.0, chord="Dm9f", vel=0.9, bright=0.8)
    add("bass", 152, 5.0, midi=38, vel=0.9, release=0.6)
    add("lead", 152.5, 0.45, midi=69, vel=0.7)
    add("lead", 153, 4.0, midi=74, vel=0.75)
    return S


def hat_line(add0, a, b, kind, k=0):
    """ハットの型。16分の格子から一部だけ叩き、スウィングとロールで「抜け」を出す。
    rng は譜面の段階では使わず、ベロシティの揺れは描画時に種つきで掛ける。"""
    boost = {"demo": 1.9, "section": 1.8}.get(kind, 1.0)  # 床の区間はハットが高域の主役（ほかはほぼ鳴らない）

    def add(inst, beat, **kw):
        kw["vel"] = kw["vel"] * boost
        add0(inst, beat, **kw)

    bar_beats = np.arange(a, b, 0.25)
    for st in bar_beats:
        pos = round((st - np.floor(st / 4) * 4) * 4) % 16  # 小節内の16分の位置 0..15
        if kind == "full":
            if pos in (14, 15) and k % 2 == 1:
                continue  # ロールに替える
            if pos % 4 == 2 and k % 2 == 1 and pos == 6:
                continue
            add("hat", st, vel=0.55 if pos % 4 == 0 else (0.42 if pos % 2 == 0 else 0.3), dec=0.03)
        elif kind == "hook":
            add("hat", st, vel=0.35 + 0.25 * ((st - a) / max(b - a, 1)), dec=0.028)
        elif kind == "demo":
            # 8分を基本に、ところどころ16分を足す（読む邪魔をしない）
            if pos % 2 == 0 and pos not in (0,):
                add("hat", st, vel=0.5 if pos % 4 == 2 else 0.36, dec=0.026)
            elif pos in (7, 11) and k % 2 == 0:
                add("hat", st, vel=0.26, dec=0.02)
        elif kind == "section":
            pass
    if kind == "section":
        # 8分の三連の型（1拍に3つ、ところどころ抜く）
        for st in np.arange(a, b, 1 / 3):
            j = int(round((st - a) * 3))
            if j % 6 == 4:
                continue
            add("hat", st, vel=0.5 if j % 3 == 0 else 0.3, dec=0.024, swing=False)
    # ロール
    bar0 = np.floor(a / 4) * 4
    if kind == "full" and k % 2 == 1:
        for j in range(6):
            add("hat", bar0 + 3.5 + j / 12, vel=0.25 + 0.06 * j, dec=0.018, swing=False)  # 32分の三連
    if kind == "hook":
        for j in range(8):
            add("hat", 7.5 + j / 16, vel=0.25 + 0.06 * j, dec=0.016, swing=False)  # 64分（拍12へ向けて）
    if kind == "demo" and k % 2 == 1:
        for j in range(3):
            add("hat", bar0 + 3.5 + j / 6, vel=0.3 + 0.06 * j, dec=0.02, swing=False)  # 16分三連
    if kind == "demo" and k % 4 == 3:
        for j in range(4):
            add("hat", bar0 + 1.5 + j / 8, vel=0.24 + 0.05 * j, dec=0.016, swing=False)  # 32分
    if kind == "section" and k % 2 == 1:
        for j in range(4):
            add("hat", bar0 + 3.5 + j / 8, vel=0.3 + 0.07 * j, dec=0.016, swing=False)


# ------------------------------------------------------------------ 楽器
def r_kick(n, v, rng):
    body = sine_sweep(n, 200, 50, 0.022) * env_ar(n, 0.0006, 0.06, 0.05)
    click = fft_filter(noise(n, rng), 2500, 9000, 2) * env_exp(n, 0.0003, 0.0022) * 0.3
    return sat((body + click) * v, 1.8) * 0.95


def r_snare(n, v, rng):
    t = secs(n)
    body = (np.sin(2 * np.pi * 190 * t) + 0.4 * np.sin(2 * np.pi * 330 * t)) * env_exp(n, 0.0005, 0.04) * 0.5
    nz = fft_filter(noise(n, rng), 1800, 11000, 2) * env_exp(n, 0.0005, 0.085) * 0.45
    clap = fft_filter(noise(n, rng), 1100, 7000, 2)
    e = np.zeros(n)
    for j, d in enumerate((0.0, 0.008, 0.017)):
        s = int(d * SR)
        e[s:] += env_exp(n - s, 0.0004, 0.005 if j < 2 else 0.07) * (0.6 if j < 2 else 1.0)
    x = body + nz + clap * e * 0.35
    st = np.stack([x, x], 1)
    st[:, 0] += clap * e * 0.08  # ほんの少しの左右差
    return st * v


HAT_BANK = None


def hat_bank(rng):
    global HAT_BANK
    if HAT_BANK is None:
        n = int(0.5 * SR)
        t = secs(n)
        bank = []
        for _ in range(6):
            fr = np.array([205.3, 304.4, 369.6, 522.7, 540.0, 800.0]) * rng.uniform(1.6, 1.75)
            sq = sum(np.sign(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))) for f in fr)
            metal = fft_filter(sq, 7500, 17000, 2)
            nz = fft_filter(noise(n, rng), 8500, 18000, 2)
            x = metal / np.abs(metal).max() * 0.6 + nz / np.abs(nz).max() * 0.5
            bank.append(x)
        HAT_BANK = bank
    return HAT_BANK


def r_hat(v, dec, rng, open_=False):
    bank = hat_bank(rng)
    x = bank[int(rng.integers(len(bank)))]
    n = int((0.45 if open_ else 0.12) * SR)
    x = x[:n] * env_exp(n, 0.0004, 0.16 if open_ else dec)
    return x * v * 0.9


def r_crash(n, v, rng):
    L = fft_filter(noise(n, rng), 5000, 16000, 2)
    R = fft_filter(noise(n, rng), 5000, 16000, 2)
    e = env_exp(n, 0.002, 1.0) * 0.18 * v
    return np.stack([L * e, R * e], 1)


def r_bass(nt, prev_midi, rng):
    gate = nt["len"] * 0.4
    rel = nt.get("release", 0.05)
    n = int((gate + rel * 5) * SR)
    f1 = midi_hz(nt["midi"])
    t = secs(n)
    if prev_midi is not None and prev_midi != nt["midi"]:
        f0 = midi_hz(prev_midi)
        f = f1 + (f0 - f1) * np.exp(-t / 0.025)  # 短いグライド
    else:
        f = np.full(n, f1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph)
    x = sat(x * 1.2, 1.4)
    e = env_ar(n, nt.get("attack", 0.004), gate, rel, decay_to=0.75, decay_tau=0.35)
    return x * e * nt["vel"]


def r_lead(nt, rng):
    gate = nt["len"] * 0.4
    n = int((gate + 0.5) * SR)
    t = secs(n)
    f = midi_hz(nt["midi"])
    vib = 1 + 0.0035 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.18) / 0.25, 0, 1)
    a = saw(f * vib * 2 ** (-5 / 1200), n, rng.uniform())
    b = saw(f * vib * 2 ** (5 / 1200), n, rng.uniform())
    tri = np.abs(((np.cumsum(f * vib / SR) + 0.25) % 1.0) * 4 - 2) - 1
    a = fft_filter(a, 180, 1600, 2); b = fft_filter(b, 180, 1600, 2)
    e = env_ar(n, 0.012, gate, 0.09, decay_to=0.7, decay_tau=0.3)
    L = (a * 0.5 + tri * 0.35) * e
    R = (b * 0.5 + tri * 0.35) * e
    return np.stack([L, R], 1) * nt["vel"]


def chord_notes(name):
    return CH[name][1]


def r_chord(name, n, rng, voices=7, cents=12.0):
    out = np.zeros((n, 2))
    notes = chord_notes(name)
    for m in notes:
        out += supersaw(midi_hz(m), n, rng, voices, cents)
    return out / np.sqrt(len(notes))


def r_riser(nt, rng):
    gate = nt["len"] * 0.4
    n = int(gate * SR)
    t = secs(n)
    x = t / gate
    out = np.zeros((n, 2))
    for m in (45, 52, 57):
        f = midi_hz(m) * 2 ** (x ** 1.6)  # 1オクターブ上がる
        out += supersaw(f, n, rng, 5, 18.0, 0.9)
    cut = 500 * (7000 / 500) ** (x ** 1.2)
    out = tv_lowpass(out, cut, res=0.6, nfft=1024, hop=256)
    amp = 10 ** ((-26 + 22 * x ** 1.2) / 20)
    return out * amp[:, None] * 0.5


# ------------------------------------------------------------------ 自動化（拍の関数）
def pad_cut(beat):
    b = beat
    if b < 4:
        return 2200
    if b < 8:
        return 600 * (2600 / 600) ** ((b - 4) / 4) ** 1.5
    if b < 10:
        return 2600
    if b < 12:
        return 2600 * (250 / 2600) ** min(1.0, (b - 10))  # 拍10の1拍で閉じる
    if b < 24:
        return 250 * (3000 / 250) ** min(1.0, (b - 12) / 0.4) if b < 12.4 else 3000
    if b < 84:
        return 1150 + 120 * np.sin(2 * np.pi * (b - 24) / 32)
    if b < 88:
        return 1150 * (1800 / 1150) ** ((b - 84) / 4)
    if b < 116:
        return 2100 * (1 + 0.3 * np.sin(2 * np.pi * (b - 88) / 4 - np.pi / 2))  # 1小節で開いて閉じる
    if b < 124:
        return 800 - 200 * (b - 116) / 8
    if b < 131:
        return 600 * (7000 / 600) ** ((b - 124) / 7) ** 1.3
    if b < 152:
        return 3200
    return 3000 * (450 / 3000) ** min(1.0, (b - 152) / 8)


SECTION_DB = {"hook": 0.0, "drop": 0.0, "demo": -6.0, "section": -5.5, "pullback": -9.0, "build": -6.0,
              "peak": 0.0, "outro": -0.5, "final": 0.0}
MID_DIP = {"demo": 1.0, "section": 1.0, "pullback": 1.0}  # 字幕の区間は中域をさらに空ける


def section_gain(beat):
    s = section(beat)
    if s == "build":
        return -6.0 + 5.0 * min(1.0, max(0.0, (beat - 124) / 7))
    return SECTION_DB[s]


def automation(fn, total_n, step=64):
    beats = np.arange(0, total_n + step, step) / SPB
    v = np.array([fn(b) for b in beats], float)
    return np.interp(np.arange(total_n), np.arange(len(beats)) * step, v)


# ------------------------------------------------------------------ 描画
def render(total_n, silences, seed=1234):
    rng = np.random.default_rng(seed)
    S = score(silences)
    Z = lambda: np.zeros((total_n, 2))
    drums, pad_bus, stab_bus, bass_bus, lead_bus, riser_bus = Z(), Z(), Z(), np.zeros(total_n), Z(), Z()
    verb_send = Z()

    # ---- ドラム
    for nt in S["kick"]:
        n = int(0.32 * SR)
        x = r_kick(n, nt["vel"], rng)
        place(drums, np.stack([x, x], 1), b2s(nt["beat"]))
    for nt in S["snare"]:
        n = int(0.4 * SR)
        x = r_snare(n, nt["vel"], rng)
        place(drums, x, b2s(nt["beat"]))
        place(verb_send, x * 0.45, b2s(nt["beat"]))
    swing = 0.012  # 裏の16分を 12ms 遅らせる
    for nt in S["hat"]:
        v = nt["vel"] * 10 ** (rng.normal(0, 1.5) / 20)  # ベロシティの揺れ（種つき）
        x = r_hat(v, nt.get("dec", 0.03), rng)
        b = nt["beat"]
        off = 0
        if nt.get("swing", True) and abs((b * 4) % 2 - 1) < 1e-6:
            off = int(swing * SR)
        p = 0.25 + rng.uniform(-0.08, 0.08)
        place(drums, pan(x, p), b2s(b) + off)
    for nt in S["ohat"]:
        x = r_hat(nt["vel"], 0.16, rng, open_=True)
        place(drums, pan(x, -0.3), b2s(nt["beat"]))
        place(verb_send, pan(x, -0.3) * 0.2, b2s(nt["beat"]))
    for nt in S["crash"]:
        x = r_crash(int(2.4 * SR), nt["vel"], rng)
        place(drums, x, b2s(nt["beat"]))

    # ---- 和音の床
    for nt in S["pad"]:
        gate = nt["len"] * 0.4
        rel = 2.2 if section(nt["beat"]) == "final" else 0.35
        n = int((gate + rel * 3) * SR)
        x = r_chord(nt["chord"], n, rng)
        e = env_ar(n, nt["attack"], gate, rel, decay_to=0.85, decay_tau=1.2)
        place(pad_bus, x * e[:, None] * nt["vel"], b2s(nt["beat"]))
    cut = automation(pad_cut, total_n)
    pad_bus = tv_lowpass(pad_bus, cut, res=0.35)
    place(verb_send, pad_bus * 0.35, 0)

    # ---- スタブ（打鍵ごとのフィルタ・エンベロープ）
    stab_env_cut = np.ones(total_n)
    for nt in S["stab"]:
        gate = nt["len"] * 0.4
        n = int((gate + 0.6) * SR)
        x = r_chord(nt["chord"], n, rng, voices=5, cents=9.0)
        e = env_ar(n, 0.003, gate, 0.12, decay_to=0.55, decay_tau=0.18)
        s = b2s(nt["beat"])
        place(stab_bus, x * e[:, None] * nt["vel"], s)
        t = secs(n)
        fe = 1 + 4.0 * nt.get("bright", 1.0) * np.exp(-t / 0.09)
        if nt.get("close"):
            fe = fe * (0.12 + 0.88 * np.exp(-t / 0.15))  # 拍10：1拍で閉じる
        m = min(n, total_n - s)
        stab_env_cut[s:s + m] = fe[:m]
    stab_cut = np.clip(700 * stab_env_cut, 150, 9000)
    stab_bus = tv_lowpass(stab_bus, stab_cut, res=0.5, nfft=1024, hop=128)
    place(verb_send, stab_bus * 0.45, 0)

    # ---- ベース
    prev = None
    for nt in S["bass"]:
        x = r_bass(nt, prev, rng)
        prev = nt["midi"]
        place(bass_bus, x, b2s(nt["beat"]))
    bass_bus = fft_filter(bass_bus, 25, 700, 2)

    # ---- 動機
    for nt in S["lead"]:
        x = r_lead(nt, rng)
        place(lead_bus, x, b2s(nt["beat"]))
    place(verb_send, lead_bus * 0.4, 0)

    # ---- 上昇
    for nt in S["riser"]:
        x = r_riser(nt, rng)
        place(riser_bus, x, b2s(nt["beat"]))

    # ---- サイドチェイン（キックとゴーストのトリガー）
    pump = np.ones(total_n)
    T = int(0.32 * SR)
    t = secs(T)
    shape = np.clip(t / 0.003, 0, 1) * (1 - np.clip(t / 0.32, 0, 1)) ** 2
    for nt in S["trig"]:
        s = b2s(nt["beat"])
        m = min(T, total_n - s)
        pump[s:s + m] = np.minimum(pump[s:s + m], 1 - nt["depth"] * shape[:m])

    # ---- 空間
    hall = make_ir(2.6, 2.2, 1.9, 1.0, 0.025, seed=31)
    wet = convolve(verb_send, hall)
    wet = fft_filter(wet, 250, 6000, 2)
    dl_src = lead_bus.mean(axis=1)
    dly = np.zeros((total_n, 2))
    d = int(0.3 * SR)  # 付点8分
    src = dl_src
    for i in range(1, 5):
        src = fft_filter(src, 300, 2500, 1)
        if i * d < total_n:
            dly[i * d:, i % 2] += src[: total_n - i * d] * 0.45 ** i

    LV = dict(pad=0.55, stab=0.6, bass=0.75, lead=0.32, riser=0.6, wet=0.32, dly=0.35, drums=0.75)
    pumped = (pad_bus * LV["pad"] + stab_bus * LV["stab"] + lead_bus * LV["lead"] + dly * LV["dly"]
              + np.stack([bass_bus, bass_bus], 1) * LV["bass"])
    pumped *= pump[:, None]
    wet_p = wet * (0.6 + 0.4 * pump)[:, None]
    bus = drums * LV["drums"] + pumped + riser_bus * LV["riser"] + wet_p * LV["wet"]

    # ---- 中域を空ける（効果音と字幕の帯域）・低域はモノラル
    bus = bell_eq(bus, 2300, -6.0, 0.75)
    dip = automation(lambda b: MID_DIP.get(section(b), 0.0), total_n, step=SPB // 8)
    k = int(0.05 * SR)
    dip = np.convolve(np.concatenate([np.full(k, dip[0]), dip]), np.ones(k) / k, mode="valid")[:total_n]
    bus = bus + (bell_eq(bus, 2000, -6.0, 0.9) - bus) * dip[:, None]
    mid = bus.mean(axis=1)
    side = (bus[:, 0] - bus[:, 1]) / 2
    side = fft_filter(side, 160, None, 4)
    bus = np.stack([mid + side, mid - side], 1)

    # ---- 区間の音量（境界は 20ms でつなぐ）
    g = automation(lambda b: 10 ** (section_gain(b) / 20), total_n, step=SPB // 8)
    k = int(0.02 * SR)
    g = np.convolve(np.concatenate([np.full(k, g[0]), g]), np.ones(k) / k, mode="valid")[:total_n]
    bus *= g[:, None]

    # ---- テープ風の飽和（偶数次をわずかに）とごく薄いヒス
    ref = np.sqrt(np.mean(bus[b2s(12):b2s(24)] ** 2)) + 1e-9
    y = bus / ref * 0.16
    y = np.tanh(1.3 * y + 0.04 * y ** 2) / 1.3 * 3.9  # 飽和は軽く、そのあと旧版と同じくらいの音量へ
    y = fft_filter(y, 22, 15000, 1)
    hiss = np.stack([fft_filter(noise(total_n, rng), 1500, 11000, 1) for _ in range(2)], 1) * 0.0012
    y = y + hiss

    # ---- テープストップ：拍130.25〜131 で回転が止まる（拍131 は build 側で無音）
    for sb in silences:
        if sb == 131:
            a, z = b2s(130.25), b2s(131)
            L = z - a
            tt = np.arange(L) / L
            speed = (1 - tt) ** 1.6
            pos = a + np.cumsum(speed)
            seg = np.stack([np.interp(pos, np.arange(total_n), y[:, c]) for c in range(2)], 1)
            seg *= np.clip((1 - tt) / 0.15, 0, 1)[:, None]
            seg = tv_lowpass(seg, 9000 * (1 - tt) ** 2 + 400, nfft=512, hop=64)
            y[a:z] = seg
    return y, S
