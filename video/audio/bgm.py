"""BGM：150BPM・D マイナー。cues.json の accent を展開の切れ目にした譜面を作り、楽器ごとに合成する。
展開（拍）：
  0–12   hook     ：スタブ（拍0,1,2）→溜め→低いドローン（判子を4拍止める）→上昇スタブ Bb,C,D（拍8,9,10）→溜め
  12–24  drop     ：最大の音圧。四つ打ち・裏のベース・パッド・リード
  24–32  halftime ：ハーフタイム（スネアは小節の3拍目）。依頼文を読ませる
  32–88  groove   ：デモ本体。密度を下げた四つ打ち以外のグルーヴ（字幕を読ませる）
  88–116 section  ：新しい進行 Bb-C-Am-Dm、16分のアルペジオ
  116–124 pullback：ドラムを抜く
  124–132 build   ：スネアロール・フィルタが開く
  132–136 peak    ：最大の一撃のあとの全開
  136–152 outro   ：締めのフレーズ（リード）で再び上げる
  152–160 final   ：最後の和音と余韻
"""
import numpy as np
from synth import (SR, midi_hz, secs, env_exp, env_adsr, additive, sine_sweep, fm, noise, fft_filter,
                   pan, widen, make_ir, convolve, pingpong, sat, place)

SPB = 19200  # 1拍のサンプル数（0.4s × 48000）


def b2s(beat):
    return int(round(beat * SPB))


CH = {  # 和音：(ルートの MIDI（ベース用、オクターブ2付近）, 構成音の半音)
    "Dm": (38, (0, 3, 7)), "Bb": (34, (0, 4, 7)), "F": (41, (0, 4, 7)), "C": (36, (0, 4, 7)),
    "Gm": (43, (0, 3, 7)), "A": (33, (0, 4, 7, 10)), "Am": (45, (0, 3, 7)),
}


def chord_at(beat):
    bar = int(beat // 4)
    if bar <= 2:
        return "Dm"
    if bar == 3:
        return "Dm"
    if bar in (4, 5):
        return ["Bb", "C"][bar - 4]
    if bar in (6, 7):
        return ["Dm", "Bb"][bar - 6]
    if 8 <= bar <= 19:
        return ["Dm", "Bb", "F", "C"][(bar - 8) % 4]
    if bar in (20, 21):
        return ["Gm", "A"][bar - 20]
    if 22 <= bar <= 28:
        return ["Bb", "C", "Am", "Dm"][(bar - 22) % 4]
    if bar in (29, 30):
        return ["Bb", "Gm"][bar - 29]
    if bar == 31:
        return "Bb"
    if bar == 32:
        return "A"
    if bar == 33:
        return "Dm"
    if 34 <= bar <= 37:
        return ["Dm", "Bb", "F", "C"][bar - 34]
    return "Dm"


def voicing(name, lo=57, hi=74):
    root, iv = CH[name]
    out = []
    for i in iv:
        m = root + i
        while m < lo:
            m += 12
        while m > hi:
            m -= 12
        out.append(m)
    return sorted(out)


def section(beat):
    for name, a, b in (("hook", 0, 12), ("drop", 12, 24), ("halftime", 24, 32), ("groove", 32, 88),
                       ("section", 88, 116), ("pullback", 116, 124), ("build", 124, 132),
                       ("peak", 132, 136), ("outro", 136, 152), ("final", 152, 160)):
        if a <= beat < b:
            return name
    return "final"


# ------------------------------------------------------------------ 譜面
def score(silences):
    S = {k: [] for k in ("kick", "clap", "snare", "hat", "ohat", "shaker", "bass", "sub", "pad", "pluck",
                         "lead", "stab", "drone", "crash", "rim")}

    def add(inst, beat, length=0.25, midi=0, vel=1.0, **kw):
        if any(s <= beat < s + 1 for s in silences):  # 溜めの拍には何も置かない
            return
        S[inst].append(dict(beat=beat, len=length, midi=midi, vel=vel, **kw))

    # hook
    for b in (0, 1, 2):
        add("stab", b, 0.6, chord="Dm", vel=1.0)
        add("kick", b, vel=0.9)
    add("drone", 4, 4.0, midi=26, vel=1.0)
    add("kick", 4, vel=1.0)
    for b in np.arange(4.5, 8, 0.5):
        add("hat", b, vel=0.35)
    for b, c in zip((8, 9, 10), ("Bb", "C", "Dm")):
        add("stab", b, 0.6, chord=c, vel=1.0)
        add("kick", b, vel=0.9)

    def full_bar(bar0, chord, lead=False, energy=1.0):
        for i in range(4):
            add("kick", bar0 + i, vel=1.0 * energy)
        for i in (1, 3):
            add("clap", bar0 + i, vel=0.9 * energy)
        for k in range(16):
            b = bar0 + k * 0.25
            if k % 4 == 2:
                add("ohat", b, vel=0.55 * energy)
            elif k % 4 != 0:
                add("hat", b, vel=(0.5 if k % 2 else 0.3) * energy)
        root = CH[chord][0]
        for k, off in enumerate((0.5, 1.5, 2.5, 3.5)):
            add("bass", bar0 + off, 0.42, midi=root + (12 if k == 3 else 0), vel=1.0 * energy)
        add("sub", bar0, 4.0, midi=root, vel=0.8 * energy)
        add("pad", bar0, 4.0, chord=chord, vel=0.8 * energy, cut=2600)
        tones = voicing(chord, 62, 79)
        for k in range(8):
            add("pluck", bar0 + k * 0.5, 0.4, midi=tones[k % len(tones)] + (12 if k in (3, 7) else 0),
                vel=0.45 * energy, cut=3200)

    # drop 12–24
    add("crash", 12, vel=1.0)
    for bar0 in (12, 16, 20):
        full_bar(bar0, chord_at(bar0))

    # halftime 24–32
    add("crash", 24, vel=0.6)
    for bar0 in (24, 28):
        c = chord_at(bar0)
        add("kick", bar0, vel=0.85); add("kick", bar0 + 2.5, vel=0.6)
        add("snare", bar0 + 2, vel=0.75)
        for k in range(8):
            add("hat", bar0 + k * 0.5, vel=0.22 + (0.1 if k % 2 else 0))
        add("bass", bar0, 3.6, midi=CH[c][0], vel=0.7, cut=500)
        add("sub", bar0, 4.0, midi=CH[c][0], vel=0.6)
        add("pad", bar0, 4.0, chord=c, vel=0.6, cut=1400)

    # groove 32–88（デモ：読ませるために密度を下げる）
    add("crash", 32, vel=0.55)
    for bar0 in range(32, 88, 4):
        c = chord_at(bar0)
        if bar0 >= 84:  # 拍86からライザー：ドラムを抜いてスネアロールで 88 へ
            add("kick", bar0, vel=0.8); add("kick", bar0 + 1, vel=0.7)
            for k in range(8):
                add("snare", 86 + k * 0.25, vel=0.2 + 0.08 * k)
            add("pad", bar0, 4.0, chord=c, vel=0.55, cut=1200, cut_end=4000)
            add("sub", bar0, 2.0, midi=CH[c][0], vel=0.6)
            continue
        add("kick", bar0, vel=0.8); add("kick", bar0 + 2, vel=0.75)
        if (bar0 // 4) % 2:
            add("kick", bar0 + 2.75, vel=0.45)
        add("rim", bar0 + 1, vel=0.45); add("rim", bar0 + 3, vel=0.45)
        for k in range(8):
            add("hat", bar0 + k * 0.5 + 0.5 * (k % 2 == 0) * 0, vel=0.18 + (0.12 if k % 2 else 0))
        for k in range(16):
            add("shaker", bar0 + k * 0.25, vel=0.08 + 0.05 * (k % 2))
        root = CH[c][0]
        for off, ln, oc in ((0, 0.9, 0), (1.5, 0.4, 0), (2, 0.9, 0), (3.5, 0.4, 12)):
            add("bass", bar0 + off, ln, midi=root + oc, vel=0.6, cut=420)
        add("pad", bar0, 4.0, chord=c, vel=0.5, cut=1300)
        tones = voicing(c, 62, 79)
        for k, off in enumerate((0, 0.75, 1.5, 2.5, 3.25)):
            add("pluck", bar0 + off, 0.35, midi=tones[k % len(tones)] + 12 * (k == 4), vel=0.3, cut=2200)

    # section 88–116：新しいグルーヴ
    add("crash", 88, vel=0.8)
    for bar0 in range(88, 116, 4):
        c = chord_at(bar0)
        for i in range(4):
            add("kick", bar0 + i, vel=0.75)
        add("clap", bar0 + 1, vel=0.5); add("clap", bar0 + 3, vel=0.5)
        for k in range(16):
            if k % 4 == 2:
                add("ohat", bar0 + k * 0.25, vel=0.3)
            else:
                add("hat", bar0 + k * 0.25, vel=0.14 + 0.1 * (k % 2))
        root = CH[c][0]
        for off, oc in ((0, 0), (0.75, 0), (1.5, 12), (2, 0), (2.75, 0), (3.5, 12)):
            add("bass", bar0 + off, 0.4, midi=root + oc, vel=0.65, cut=650)
        add("sub", bar0, 4.0, midi=root, vel=0.6)
        add("pad", bar0, 4.0, chord=c, vel=0.45, cut=1600)
        tones = voicing(c, 64, 81)
        seq = [0, 1, 2, 1, 2, 0, 1, 2]
        for k in range(16):
            add("pluck", bar0 + k * 0.25, 0.2, midi=tones[seq[k % 8] % len(tones)] + (12 if k % 8 == 7 else 0),
                vel=0.22 + 0.08 * (k % 4 == 0), cut=2600)

    # pullback 116–124
    for bar0 in (116, 120):
        c = chord_at(bar0)
        add("pad", bar0, 4.0, chord=c, vel=0.45, cut=900)
        add("sub", bar0, 4.0, midi=CH[c][0], vel=0.45)
        tones = voicing(c, 69, 86)
        for k in range(4):
            add("pluck", bar0 + k, 0.8, midi=tones[k % len(tones)], vel=0.25, cut=1800)

    # build 124–132（拍131は溜め）
    for bar0 in (124, 128):
        c = chord_at(bar0)
        step = 0.5 if bar0 == 124 else 0.25
        for b in np.arange(bar0, bar0 + 4, step):
            x = (b - 124) / 7
            add("kick", b, vel=0.55 + 0.35 * x)
            add("snare", b, vel=0.25 + 0.6 * x)
        for b in np.arange(bar0, bar0 + 4, 0.5):
            add("bass", b, 0.4, midi=CH[c][0] + (12 if (b * 2) % 2 else 0), vel=0.75, cut=500 + 1500 * (b - 124) / 7)
        add("pad", bar0, 4.0, chord=c, vel=0.6, cut=900 + 1200 * (bar0 - 124) / 4, cut_end=2100 + 2000 * (bar0 - 124) / 4)
        add("sub", bar0, 4.0, midi=CH[c][0], vel=0.6)

    # peak 132–136 と outro 136–152
    add("crash", 132, vel=1.0)
    full_bar(132, "Dm")
    add("crash", 136, vel=0.8)
    for bar0 in range(136, 152, 4):
        full_bar(bar0, chord_at(bar0), lead=True)
    motif = {"Dm": [(0, 1.5, 69), (1.5, 1, 74), (2.5, 1.5, 77)], "Bb": [(0, 1.5, 77), (1.5, 1, 74), (2.5, 1.5, 70)],
             "F": [(0, 1.5, 69), (1.5, 1, 72), (2.5, 1.5, 77)], "C": [(0, 1.5, 76), (1.5, 1, 79), (2.5, 1.5, 76)]}
    for bar0 in list(range(12, 24, 4)) + list(range(136, 152, 4)):
        c = chord_at(bar0)
        for off, ln, m in motif.get(c, motif["Dm"]):
            add("lead", bar0 + off, ln * 0.92, midi=m, vel=0.75 if bar0 < 100 else 0.9)

    # final 152–
    add("crash", 152, vel=1.0)
    add("kick", 152, vel=1.0)
    add("stab", 152, 1.5, chord="Dm", vel=1.0)
    add("pad", 152, 8.0, chord="Dm", vel=0.7, cut=2200, cut_end=500)
    add("sub", 152, 6.0, midi=38, vel=0.8)
    add("lead", 152, 6.0, midi=74, vel=0.6)
    return S


# ------------------------------------------------------------------ 楽器
def r_kick(n, v, rng):
    t = secs(n)
    body = sine_sweep(n, 160, 47, 0.035) * env_exp(n, 0.0008, 0.22)
    click = fft_filter(noise(n, rng), 1500, 9000, 2) * env_exp(n, 0.0003, 0.003) * 0.35
    return pan(sat((body + click) * v, 1.6) * 0.9, 0.0)


def r_clap(n, v, rng):
    nz = fft_filter(noise(n, rng), 900, 6500, 2)
    e = np.zeros(n)
    for k, d in enumerate((0, 0.009, 0.019, 0.028)):
        s = int(d * SR)
        e[s:] += env_exp(n - s, 0.0005, 0.006 if k < 3 else 0.11) * (0.7 if k < 3 else 1.0)
    tone = np.sin(2 * np.pi * 210 * secs(n)) * env_exp(n, 0.0005, 0.03) * 0.3
    return pan((nz * e * 0.45 + tone) * v, 0.0)


def r_snare(n, v, rng):
    nz = fft_filter(noise(n, rng), 1500, 9000, 2) * env_exp(n, 0.0005, 0.12) * 0.45
    body = (np.sin(2 * np.pi * 185 * secs(n)) + 0.5 * np.sin(2 * np.pi * 330 * secs(n))) * env_exp(n, 0.0005, 0.05) * 0.35
    return pan((nz + body) * v, 0.05)


def r_rim(n, v, rng):
    t = secs(n)
    x = (np.sin(2 * np.pi * 1700 * t) * 0.5 + fft_filter(noise(n, rng), 2000, 6000, 2) * 0.4) * env_exp(n, 0.0003, 0.012)
    return pan(x * v, -0.25)


HATBANK = None


def r_hat(n, v, rng, open_=False):
    nz = fft_filter(noise(n, rng), 7000, 16000, 2)
    e = env_exp(n, 0.0005, 0.12 if open_ else 0.025)
    return pan(nz * e * 0.35 * v, -0.25 if open_ else 0.3)


def r_shaker(n, v, rng):
    nz = fft_filter(noise(n, rng), 5000, 12000, 2)
    return pan(nz * env_exp(n, 0.006, 0.03) * 0.3 * v, 0.55)


def r_crash(n, v, rng):
    L = fft_filter(noise(n, rng), 4000, 16000, 2)
    R = fft_filter(noise(n, rng), 4000, 16000, 2)
    e = env_exp(n, 0.001, 1.1) * 0.22 * v
    return np.stack([L * e, R * e], axis=1)


def r_bass(n, note, rng):
    f = midi_hz(note["midi"])
    gate = note["len"] * 0.4
    c0 = note.get("cut", 900)
    t = secs(n)
    cut = c0 * 0.6 + c0 * 1.6 * np.exp(-t / 0.08)
    x = additive(f, n, cut, "saw", res=0.9) * 0.6 + np.sin(2 * np.pi * f * t) * 0.35
    x = sat(x * env_adsr(n, 0.003, 0.15, 0.7, gate, 0.03), 1.4)
    return pan(x * note["vel"] * 0.75, 0.0)


def r_sub(n, note, rng):
    f = midi_hz(note["midi"])
    x = np.sin(2 * np.pi * f * secs(n)) * env_adsr(n, 0.01, 0.3, 0.85, note["len"] * 0.4, 0.08)
    return pan(x * note["vel"] * 0.55, 0.0)


def r_pad(n, note, rng):
    gate = note["len"] * 0.4
    t = secs(n)
    c0 = note.get("cut", 1500)
    c1 = note.get("cut_end", c0)
    cut = c0 + (c1 - c0) * np.clip(t / gate, 0, 1)
    cut = cut * (1 + 0.12 * np.sin(2 * np.pi * 0.35 * t))
    out = np.zeros((n, 2))
    for m in voicing(note["chord"]):
        f = midi_hz(m)
        for det, p in ((-0.007, -0.75), (0.0, 0.0), (0.007, 0.75)):
            out += pan(additive(f * (1 + det), n, cut, "saw", slope=6, kcap=60), p) * 0.33
    e = env_adsr(n, 0.08, 0.6, 0.8, gate, 0.35)
    return out * e[:, None] * note["vel"] * 0.16


def r_pluck(n, note, rng):
    f = midi_hz(note["midi"])
    t = secs(n)
    cut = 500 + note.get("cut", 2500) * np.exp(-t / 0.06)
    x = additive(f, n, cut, "square", res=0.5, kcap=40) * env_exp(n, 0.002, 0.16)
    return pan(x * note["vel"] * 0.35, 0.0)


def r_lead(n, note, rng):
    f = midi_hz(note["midi"])
    gate = note["len"] * 0.4
    t = secs(n)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) / 0.2, 0, 1)
    cut = 1400 + 1800 * np.exp(-t / 0.2)
    x = additive(f * vib, n, cut, "saw", res=0.4, kcap=60) * 0.5 + additive(f * vib * 1.005, n, cut, "saw", kcap=60) * 0.5
    x *= env_adsr(n, 0.008, 0.3, 0.75, gate, 0.12)
    return widen(pan(x, -0.15) * 0.5 + pan(x, 0.15) * 0.5, 1.0) * note["vel"] * 0.28


def r_stab(n, note, rng):
    t = secs(n)
    cut = 350 + 3000 * np.exp(-t / 0.09)
    out = np.zeros((n, 2))
    root = CH[note["chord"]][0]
    for m, p in ((root, 0.0), (root + 12, 0.0)):
        out += pan(sat(additive(midi_hz(m), n, cut, "saw", res=1.0) * 0.6, 1.8), p)
    for m in voicing(note["chord"], 50, 66):
        for det, p in ((-0.006, -0.6), (0.006, 0.6)):
            out += pan(additive(midi_hz(m) * (1 + det), n, cut, "saw", kcap=80), p) * 0.3
    e = env_adsr(n, 0.002, 0.25, 0.3, note["len"] * 0.4, 0.15)
    return out * e[:, None] * note["vel"] * 0.32


def r_drone(n, note, rng):
    t = secs(n)
    f = midi_hz(note["midi"])
    gate = note["len"] * 0.4
    cut = 180 + 900 * np.clip(t / gate, 0, 1) ** 2
    x = additive(f * 2, n, cut, "saw", res=1.2) * 0.5 + additive(f * 2 * 1.004, n, cut, "saw") * 0.5
    x = sat(x * 0.9, 1.5) + np.sin(2 * np.pi * f * 2 * t) * 0.5
    x *= env_adsr(n, 0.004, 1.0, 0.9, gate, 0.05)
    return widen(pan(x, -0.2) * 0.5 + pan(x, 0.2) * 0.5, 1.2) * 0.5


INST = {  # 名前: (関数, 長さ秒, バス, 定位処理)
    "kick": r_kick, "clap": r_clap, "snare": r_snare, "rim": r_rim, "shaker": r_shaker, "crash": r_crash,
    "bass": r_bass, "sub": r_sub, "pad": r_pad, "pluck": r_pluck, "lead": r_lead, "stab": r_stab, "drone": r_drone,
}
TAIL = {"kick": 0.45, "clap": 0.4, "snare": 0.35, "rim": 0.08, "hat": 0.12, "ohat": 0.45, "shaker": 0.15,
        "crash": 2.5, "bass": 0.1, "sub": 0.3, "pad": 1.2, "pluck": 0.6, "lead": 0.4, "stab": 0.6, "drone": 0.2}
DRUM = {"kick", "clap", "snare", "rim", "hat", "ohat", "shaker", "crash"}
SEND = {"clap": 0.35, "snare": 0.3, "rim": 0.25, "ohat": 0.1, "pad": 0.35, "pluck": 0.3, "lead": 0.35,
        "stab": 0.5, "drone": 0.3, "crash": 0.2, "kick": 0.03}
LEVEL = {"kick": 1.0, "clap": 0.8, "snare": 0.8, "rim": 0.6, "hat": 0.6, "ohat": 0.55, "shaker": 0.5,
         "crash": 0.7, "bass": 0.85, "sub": 0.8, "pad": 0.9, "pluck": 0.7, "lead": 0.8, "stab": 1.0, "drone": 1.0}
PUMPED = {"bass", "sub", "pad", "pluck", "lead"}

# 区間ごとの全体の音量（dB）：掴み・ドロップ・締めが最大、デモは下げる、pullback はさらに下げる
SECTION_DB = {"hook": 0.0, "drop": 0.0, "halftime": -4.5, "groove": -5.5, "section": -4.5, "pullback": -9.0,
              "build": -6.0, "peak": 0.0, "outro": -0.5, "final": 0.0}


def render(total_n, silences, seed=1234):
    rng = np.random.default_rng(seed)
    S = score(silences)
    dry = np.zeros((total_n, 2))
    send = np.zeros((total_n, 2))
    pluck_bus = np.zeros((total_n, 2))
    lead_bus = np.zeros((total_n, 2))
    pumped = np.zeros((total_n, 2))
    for inst, notes in S.items():
        for nt in notes:
            n = int((nt["len"] * 0.4 + TAIL[inst]) * SR) if inst not in DRUM else int(TAIL[inst] * SR)
            if inst == "hat":
                sig = r_hat(n, nt["vel"], rng)
            elif inst == "ohat":
                sig = r_hat(n, nt["vel"], rng, open_=True)
            elif inst in DRUM:
                sig = INST[inst](n, nt["vel"], rng)
            else:
                sig = INST[inst](n, nt, rng)
            sig = sig * LEVEL[inst]
            s = b2s(nt["beat"])
            if inst in PUMPED:
                place(pumped, sig, s)
                if inst == "pluck":
                    place(pluck_bus, sig, s)
                if inst == "lead":
                    place(lead_bus, sig, s)
            else:
                place(dry, sig, s)
            place(send, sig * SEND.get(inst, 0.0), s)
    # キックに合わせたポンピング（ベース・パッド・リード）
    pump = np.ones(total_n)
    kl = int(0.25 * SR)
    curve = 1 - 0.55 * np.exp(-secs(kl) / 0.07) * np.clip(secs(kl) / 0.004, 0, 1)
    for nt in S["kick"]:
        s = b2s(nt["beat"])
        m = min(kl, total_n - s)
        pump[s:s + m] = np.minimum(pump[s:s + m], 1 - (1 - curve[:m]) * min(1.0, nt["vel"]))
    pumped *= pump[:, None]
    # 付点8分のピンポン・ディレイ（プラック・リード）
    dl = pingpong(pluck_bus * pump[:, None] + lead_bus * pump[:, None] * 0.7, 0.3, 0.42, 5)
    hall = make_ir(2.4, 2.0, 1.7, 0.9, 0.02, seed=21)
    wet = convolve(send, hall) * 0.55
    bus = dry + pumped + dl * 0.5 + wet
    bus = fft_filter(bus, 28, None, 2)  # 低すぎる成分を切る
    # 区間の音量（境界は 20ms で繋ぐ）
    g = np.ones(total_n)
    for i in range(total_n // SPB + 1):
        a, b = i * SPB, min((i + 1) * SPB, total_n)
        g[a:b] = 10 ** (SECTION_DB[section(i)] / 20)
    k = int(0.02 * SR)
    g = np.convolve(np.concatenate([np.full(k, g[0]), g]), np.ones(k) / k, mode="valid")[:total_n]
    return bus * g[:, None], S
