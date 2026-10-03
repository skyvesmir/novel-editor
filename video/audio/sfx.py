"""効果音のパレット。各関数は「頭＝配列の先頭サンプル」のステレオ (n,2) を返す（riser だけは末尾が山）。
乱数は呼び出し側が種を固定した Generator を渡す。"""
import numpy as np
from synth import (SR, midi_hz, secs, env_exp, additive, sine_sweep, fm, noise, fft_filter,
                   swept_noise, pan, widen, make_ir, convolve, sat, fade_tail)

ROOM = make_ir(0.9, 0.5, 0.45, 0.3, 0.006, seed=11)
HALL = make_ir(2.8, 2.6, 2.2, 1.2, 0.018, seed=12)


def _n(sec):
    return int(sec * SR)


def _verb(dry, ir, wet):
    return dry + convolve(dry, ir) * wet


def slash(rng, i=0):
    """赤ペンで刺す：紙を裂く高域の擦過（6k→1.5k に落ちる）＋先端の硬いクリック＋小さな胴鳴り。左→右に走る。"""
    n = _n(0.45)
    t = secs(n)
    fc = 1500 + 5500 * np.exp(-t / 0.05)
    sw = swept_noise(n, fc, 0.5, rng) * env_exp(n, 0.0015, 0.07) * 0.55
    clk = fft_filter(noise(n, rng), 2500, 12000, 2) * env_exp(n, 0.0005, 0.004) * 0.9
    thump = sine_sweep(n, 160, 55, 0.03) * env_exp(n, 0.001, 0.06) * 0.55
    p = np.clip(-0.6 + t / 0.12 * 1.2, -0.6, 0.6)
    st = pan(sw, p) + pan(clk + thump, 0.0)
    return fade_tail(_verb(st, ROOM, 0.18))


def stamp(rng, weight=1.0):
    """判子：低い胴の沈み込み（110→42Hz）＋ゴム面の打撃（中域）＋紙の張り（高域）。部屋鳴りは短く。"""
    n = _n(0.9)
    body = sat(sine_sweep(n, 115, 42, 0.04) * env_exp(n, 0.001, 0.16), 1.8) * 0.9
    knock = fft_filter(noise(n, rng), 150, 900, 2) * env_exp(n, 0.0008, 0.035) * 0.8
    thock = np.sin(2 * np.pi * 185 * secs(n)) * env_exp(n, 0.001, 0.05) * 0.35
    slap = fft_filter(noise(n, rng), 1200, 5000, 2) * env_exp(n, 0.0005, 0.012) * 0.45
    st = pan((body + knock + thock) * weight, 0.0) + pan(slap, 0.0)
    return fade_tail(_verb(widen(st, 1.0), ROOM, 0.35))


SLAM_ROOT = 50  # D3


def slam(rng, midi=SLAM_ROOT, big=1.0):
    """叩きつけ：サブの沈み込み＋割れた中域のクラック＋音程つきの金管風スタブ（midi で音程を上げる）。"""
    n = _n(1.2)
    t = secs(n)
    sub = sat(sine_sweep(n, 90, 36, 0.05) * env_exp(n, 0.001, 0.22), 2.0) * 0.85
    crack = fft_filter(noise(n, rng), 300, 6000, 2) * env_exp(n, 0.0005, 0.06) * 0.7
    f = midi_hz(midi)
    cut = 600 + 3200 * np.exp(-t / 0.12)
    stab = np.zeros(n)
    for m_off, det in ((0, 0.0), (7, 0.0), (12, 0.004), (0, -0.006)):
        stab += additive(f * 2 ** (m_off / 12) * (1 + det), n, cut, "saw", res=0.6)
    stab = sat(stab * env_exp(n, 0.002, 0.25) * 0.35, 1.5)
    st = pan(sub + crack, 0.0) + widen(pan(stab, -0.25) * 0.5 + pan(stab, 0.25) * 0.5, 1.0)
    return fade_tail(_verb(st * big, HALL, 0.22))


def impact(rng, size=1.0):
    """最大の一撃：長いサブブーム（60→28Hz）＋クラック＋クラッシュの尾＋低い D のオクターブ。大きな残響。"""
    n = _n(3.2)
    t = secs(n)
    boom = sat(sine_sweep(n, 65, 28, 0.12) * env_exp(n, 0.001, 0.6 * size), 2.2) * 1.0
    crack = fft_filter(noise(n, rng), 200, 8000, 2) * env_exp(n, 0.0005, 0.07) * 0.8
    crash_l = fft_filter(noise(n, rng), 3500, 16000, 2)
    crash_r = fft_filter(noise(n, rng), 3500, 16000, 2)
    ce = env_exp(n, 0.001, 0.9 * size) * 0.22
    oct_ = (additive(midi_hz(38), n, 300 + 1500 * np.exp(-t / 0.3), "saw") +
            additive(midi_hz(50), n, 400 + 2000 * np.exp(-t / 0.3), "saw")) * env_exp(n, 0.002, 0.8) * 0.3
    st = pan(boom + crack + oct_, 0.0) + np.stack([crash_l * ce, crash_r * ce], axis=1)
    return fade_tail(_verb(st, HALL, 0.35), 0.2)


def whoosh(rng):
    """場面の切り替え：帯域が 1.2k→5k→0.9k と抜ける風切り。頭は拍に、右→左へ流れる。"""
    n = _n(0.6)
    t = secs(n)
    fc = 900 + 4000 * np.exp(-((t - 0.05) / 0.12) ** 2) + 300 * np.exp(-t / 0.02)
    w = swept_noise(n, fc, 0.6, rng) * env_exp(n, 0.003, 0.16) * 0.45
    low = fft_filter(noise(n, rng), 60, 300, 2) * env_exp(n, 0.003, 0.08) * 0.3
    p = np.clip(0.7 - t / 0.35 * 1.4, -0.7, 0.7)
    return fade_tail(_verb(pan(w, p) + pan(low, 0.0), ROOM, 0.25))


def type_(rng):
    """打鍵：短い樹脂のクリック＋底打ちの低い音。音量・定位・高さを種つき乱数で少し揺らす。"""
    n = _n(0.09)
    t = secs(n)
    k = 10 ** (rng.uniform(-2.5, 0) / 20)
    hi = fft_filter(noise(n, rng), 2000, 7000, 2) * env_exp(n, 0.0003, 0.006) * 0.55
    tick = np.sin(2 * np.pi * rng.uniform(1100, 1500) * t) * env_exp(n, 0.0003, 0.005) * 0.3
    bot = np.sin(2 * np.pi * 240 * t) * env_exp(n, 0.0005, 0.018) * 0.3
    return fade_tail(_verb(pan((hi + tick + bot) * k, rng.uniform(-0.3, 0.3)), ROOM, 0.12))


def pen(rng):
    """赤ペンの書き込み：紙を擦る高域雑音を 10〜14Hz のストロークで刻む（1画目が拍）。0.6秒。"""
    n = _n(0.75)
    t = secs(n)
    rate = rng.uniform(10, 13)
    ph = 2 * np.pi * np.cumsum(rate * (1 + 0.15 * np.sin(2 * np.pi * 1.7 * t))) / SR
    strokes = np.abs(np.sin(ph / 2)) ** 1.5
    strokes[: _n(0.02)] = np.maximum(strokes[: _n(0.02)], 1.0)  # 1画目は頭から最大
    gate = np.where(t < 0.55, 1.0, np.exp(-(t - 0.55) / 0.04))
    e = env_exp(n, 0.002, 10.0) * gate
    scratch = fft_filter(noise(n, rng), 2500, 8000, 2) * 0.32
    fric = fft_filter(noise(n, rng), 300, 1200, 1) * 0.12
    m = (scratch + fric) * strokes * e
    p = 0.3 * np.sin(2 * np.pi * 1.2 * t)
    return fade_tail(_verb(pan(m, p), ROOM, 0.1))


def drop(rng):
    """展開の切れ目：808 風のサブ（55→30Hz、長め）＋雑音の破裂。"""
    n = _n(1.6)
    sub = sat(sine_sweep(n, 70, 33, 0.07) * env_exp(n, 0.001, 0.45), 1.6) * 0.8
    burst = fft_filter(noise(n, rng), 400, 9000, 2) * env_exp(n, 0.0005, 0.09) * 0.5
    return fade_tail(_verb(pan(sub, 0.0) + widen(pan(burst, 0.0), 1.0), HALL, 0.2), 0.1)


TICK_SCALE = [74, 76, 77, 79, 81, 82, 84]  # D5 E5 F5 G5 A5 Bb5 C6（D ナチュラルマイナー）


def tick(rng, step):
    """点数のチック：FM のベル（比 2、変調指数が速く落ちる）。pitch_step ごとに音階を1段上げ、定位も左→右へ。"""
    n = _n(0.7)
    f = midi_hz(TICK_SCALE[min(step, len(TICK_SCALE) - 1)])
    b = fm(n, f, 2.0, 2.2, 0.05) * env_exp(n, 0.001, 0.22) * 0.45
    b += np.sin(2 * np.pi * f * 2 * secs(n)) * env_exp(n, 0.001, 0.08) * 0.12
    clk = fft_filter(noise(n, rng), 4000, 12000, 2) * env_exp(n, 0.0003, 0.003) * 0.35
    p = -0.6 + 1.2 * step / 6
    return fade_tail(_verb(pan(b + clk, p), HALL, 0.15))


def fall(rng):
    """下降音：鋸波が D5→D2 へ滑り落ち、フィルタも閉じる。下降する帯域雑音を重ねる。約1.4秒。"""
    n = _n(1.6)
    t = secs(n)
    f = midi_hz(38) * 2 ** (3 * np.exp(-t / 0.45))
    cut = 400 + 3500 * np.exp(-t / 0.5)
    tone = (additive(f, n, cut, "saw", res=0.8) + additive(f * 1.006, n, cut, "saw")) * 0.22
    nz = swept_noise(n, 300 + 4000 * np.exp(-t / 0.35), 0.5, rng) * 0.12
    e = env_exp(n, 0.003, 10.0) * np.where(t < 1.1, 1.0, np.exp(-(t - 1.1) / 0.12))
    st = widen(pan(tone * e, -0.2) + pan(nz * e, 0.2), 1.3)
    return fade_tail(_verb(st, HALL, 0.25), 0.05)


def riser(rng, length_s):
    """上昇音：帯域雑音（300→9kHz）と鋸波（D3→D5）が指数的にふくらみ、末尾サンプルで最大（＝山）。
    配列の末尾を次の拍の頭に置く。"""
    n = _n(length_s)
    t = secs(n)
    x = t / length_s
    fc = 300 * (9000 / 300) ** (x ** 1.4)
    nz = swept_noise(n, fc, 0.7, rng) * 0.35
    f = midi_hz(50) * 2 ** (2 * x ** 1.6)
    tone = (additive(f, n, 500 + 4000 * x ** 2, "saw") + additive(f * 1.008, n, 500 + 4000 * x ** 2, "saw")) * 0.18
    amp = 10 ** ((-34 + 34 * x ** 1.3) / 20)
    p = 0.6 * np.sin(2 * np.pi * (2 + 6 * x) * t) * x  # 左右の揺れが速くなる
    st = pan(nz * amp, p) + pan(tone * amp, -p)
    st = st + convolve(st, ROOM) * 0.2
    st[-_n(0.003):] *= np.linspace(1, 0, _n(0.003))[:, None]
    return st


def title(rng):
    """題字：D・F・A・D のベル和音が同時に鳴り、残響で広がる。やわらかな低い打撃つき。"""
    n = _n(2.5)
    t = secs(n)
    out = np.zeros((n, 2))
    for k, m in enumerate((62, 69, 74, 77, 81)):
        b = fm(n, midi_hz(m), 3.0, 1.6, 0.12) * env_exp(n, 0.002, 0.9) * 0.16
        out += pan(b, -0.6 + 0.3 * k)
    low = sine_sweep(n, 100, 45, 0.05) * env_exp(n, 0.001, 0.2) * 0.5
    out += pan(low, 0.0)
    return fade_tail(_verb(out, HALL, 0.4), 0.2)


def end(rng):
    """最後の一撃：impact の低域＋Dm(add9) のベル和音、長い残響。"""
    n = _n(3.2)
    st = impact(rng, size=1.3)[:n] * 0.85
    for k, m in enumerate((50, 57, 62, 64, 65, 69)):
        b = fm(n, midi_hz(m), 2.0, 1.2, 0.2) * env_exp(n, 0.002, 1.4) * 0.11
        st += pan(b, -0.7 + 0.28 * k)
    return fade_tail(st + convolve(st, HALL) * 0.2, 0.3)
