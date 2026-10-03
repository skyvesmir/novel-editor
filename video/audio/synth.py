"""DSP の部品（numpy のみ）。すべて 48kHz・float64、ステレオは (n, 2)。
方針：フィルタは「音源を先に濾してから振幅エンベロープを掛ける」。ゼロ位相の FFT フィルタの前鳴りが
立ち上がりの頭より前に漏れないようにするため（頭＝エンベロープの開始サンプル）。"""
import numpy as np

SR = 48000


def midi_hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def secs(n):
    return np.arange(n) / SR


# ---------------------------------------------------------------- エンベロープ
def env_exp(n, attack, tau, hold=0.0):
    """直線の立ち上がり attack 秒 → hold 秒 → 時定数 tau 秒の指数減衰。先頭サンプルは 0 から。"""
    t = secs(n)
    a = max(attack, 1.0 / SR)
    e = np.where(t < a, t / a, 1.0)
    rel = np.clip(t - a - hold, 0, None)
    return e * np.exp(-rel / tau)


def env_adsr(n, a, d, s, gate, r):
    """gate 秒で離す ADSR（指数カーブ）。"""
    t = secs(n)
    a = max(a, 1.0 / SR)
    e = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    g_val = (s + (1 - s) * np.exp(-(gate - a) / max(d, 1e-4))) if gate > a else gate / a
    e = np.where(t < gate, e, g_val * np.exp(-(t - gate) / max(r, 1e-4)))
    return e


def fade_tail(x, sec=0.005):
    m = min(len(x), int(sec * SR))
    if m > 0:
        w = np.linspace(1, 0, m)
        x[-m:] *= w if x.ndim == 1 else w[:, None]
    return x


# ---------------------------------------------------------------- 発音体
def additive(f, n, cutoff, shape="saw", res=0.0, slope=8, kcap=400):
    """帯域制限された鋸波/矩形波を倍音の加算で作り、各倍音に可変ローパスの利得を掛ける。
    f, cutoff はスカラーか長さ n の配列。res は共振の山（cutoff 付近の倍音を持ち上げる）。"""
    f = np.broadcast_to(np.asarray(f, float), (n,))
    c = np.broadcast_to(np.asarray(cutoff, float), (n,))
    ph = 2 * np.pi * np.cumsum(f) / SR
    fmin = max(f.min(), 1.0)
    K = int(min(SR * 0.45 / max(f.max(), 1.0), 7.0 * c.max() / fmin, kcap))
    out = np.zeros(n)
    for k in range(1, max(K, 1) + 1):
        if shape == "square" and k % 2 == 0:
            continue
        x = k * f / c
        g = 1.0 / np.sqrt(1.0 + x ** slope)
        if res:
            g = g * (1.0 + res * np.exp(-((x - 1.0) ** 2) / 0.04))
        g = np.where(k * f < SR * 0.45, g, 0.0)
        out += g / k * np.sin(k * ph)
    return out


def sine_sweep(n, f0, f1, tau, phase0=0.0):
    """周波数が f0 から f1 へ時定数 tau で指数的に落ちる正弦（キック・ブーム用）。"""
    t = secs(n)
    f = f1 + (f0 - f1) * np.exp(-t / tau)
    return np.sin(phase0 + 2 * np.pi * np.cumsum(f) / SR)


def fm(n, fc, ratio, index, index_tau, phase_mod=0.0):
    t = secs(n)
    I = index * np.exp(-t / index_tau)
    return np.sin(2 * np.pi * fc * t + I * np.sin(2 * np.pi * fc * ratio * t + phase_mod))


def noise(n, rng):
    return rng.standard_normal(n)


# ---------------------------------------------------------------- フィルタ（FFT・ゼロ位相）
def fft_filter(x, lo=None, hi=None, order=2):
    """Butterworth 相当の振幅特性。lo=ハイパス、hi=ローパス（Hz）。"""
    n = len(x)
    N = 1 << int(np.ceil(np.log2(max(n, 2))))
    X = np.fft.rfft(x, N, axis=0)
    f = np.fft.rfftfreq(N, 1 / SR)
    g = np.ones_like(f)
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        fz = np.maximum(f, 1e-3)
        g *= 1 / np.sqrt(1 + (lo / fz) ** (2 * order))
    if x.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, N, axis=0)[:n]


def swept_noise(n, fc, bw_oct, rng, nfft=1024, hop=256):
    """中心周波数が時間で動く帯域雑音（STFT のマスク）。fc は長さ n の配列。"""
    x = noise(n + nfft, rng)
    win = np.hanning(nfft)
    frames = 1 + (len(x) - nfft) // hop
    idx = np.arange(nfft)[None, :] + hop * np.arange(frames)[:, None]
    F = np.fft.rfft(x[idx] * win, axis=1)
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    centers = np.clip(np.arange(frames) * hop, 0, n - 1)
    c = np.asarray(fc)[centers][:, None]
    bw = np.broadcast_to(np.asarray(bw_oct, float), (n,))[centers][:, None]
    m = np.exp(-0.5 * (np.log2(np.maximum(freqs[None, :], 1) / c) / bw) ** 2)
    y_fr = np.fft.irfft(F * m, nfft, axis=1) * win
    y = np.zeros(len(x))
    norm = np.zeros(len(x))
    np.add.at(y, idx, y_fr)
    np.add.at(norm, idx, np.broadcast_to(win ** 2, idx.shape))
    y = y / np.maximum(norm, 1e-3)
    y = y[nfft // 2: nfft // 2 + n]
    return y / (np.std(y) + 1e-9)


# ---------------------------------------------------------------- 空間
def pan(x, p):
    """定パワーの定位。p は -1（左）〜 +1（右）、スカラーか配列。"""
    p = np.asarray(p, float)
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * np.sqrt(2)


def widen(st, amount):
    m = (st[:, 0] + st[:, 1]) / 2
    s = (st[:, 0] - st[:, 1]) / 2 * amount
    return np.stack([m + s, m - s], axis=1)


def make_ir(dur, rt_low, rt_mid, rt_high, predelay, seed, early=True):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = secs(n)
    ir = np.zeros((n, 2))
    for ch in range(2):
        for lo, hi, rt in ((None, 400, rt_low), (400, 3500, rt_mid), (3500, None, rt_high)):
            b = fft_filter(noise(n, rng), lo, hi, 2)
            ir[:, ch] += b * 10 ** (-3 * t / rt)
    ir *= np.clip(t / 0.008, 0, 1)[:, None]  # 拡散音の立ち上がりをなだらかに
    if early:
        for k in range(10):  # 初期反射
            d = int(rng.uniform(0.004, 0.035) * SR)
            ir[d, rng.integers(2)] += rng.uniform(0.3, 0.8) * (1 - k / 12)
    pd = int(predelay * SR)
    ir = np.concatenate([np.zeros((pd, 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def convolve(x, ir):
    """x: (n,) または (n,2)。ir: (m,2)。出力は (n,2)、長さ n（尾は切る）。"""
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    n = len(x)
    N = 1 << int(np.ceil(np.log2(n + len(ir))))
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = np.fft.irfft(np.fft.rfft(x[:, ch], N) * np.fft.rfft(ir[:, ch], N), N)[:n]
    return out


def pingpong(st, delay, fb, taps, lp=3500):
    """テンポ同期のピンポン・ディレイ。繰り返しごとに高域を落とす。"""
    n = len(st)
    m = st.mean(axis=1)
    d = int(delay * SR)
    out = np.zeros((n, 2))
    src = m
    for i in range(1, taps + 1):
        src = fft_filter(src, 120, lp, 1)
        s = i * d
        if s >= n:
            break
        out[s:, i % 2] += src[: n - s] * fb ** i
    return out


def sat(x, drive):
    return np.tanh(x * drive) / np.tanh(drive)


def place(buf, sig, start):
    """buf の start サンプルから sig を足す（はみ出しは切る）。"""
    if start >= len(buf):
        return
    if start < 0:
        sig = sig[-start:]
        start = 0
    m = min(len(sig), len(buf) - start)
    buf[start:start + m] += sig[:m]


# ---------------------------------------------------------------- マスタリング
def oversample_peak(x, factor=4):
    """各サンプル周辺の真のピーク（factor 倍の補間で検出）。x: (n,2) → (n,)"""
    n = len(x)
    N = 1 << int(np.ceil(np.log2(n)))
    out = np.zeros(n)
    for ch in range(x.shape[1]):
        X = np.fft.rfft(x[:, ch], N)
        Y = np.zeros(N * factor // 2 + 1, complex)
        Y[: len(X)] = X
        y = np.fft.irfft(Y, N * factor) * factor
        y = np.abs(y[: n * factor]).reshape(n, factor).max(axis=1)
        out = np.maximum(out, y)
    return out


def limiter(x, ceiling_db=-1.3, look=0.0015, release=0.08):
    """先読みの真ピーク・リミッタ。信号は遅らせない（ゲインを先に下げ始める）ので時刻はずれない。"""
    from numpy.lib.stride_tricks import sliding_window_view as swv
    c = 10 ** (ceiling_db / 20)
    d = np.maximum(oversample_peak(x), np.abs(x).max(axis=1))
    r = np.minimum(1.0, c / np.maximum(d, 1e-9))
    W = max(2, int(look * SR))
    g1 = swv(np.concatenate([r, np.ones(W - 1)]), W).min(axis=1)
    g2 = swv(np.concatenate([np.ones(W - 1), g1]), W).mean(axis=1)
    g2 = np.minimum(g2, r)
    a = 1 - np.exp(-1 / (release * SR))
    y = g2.copy()
    idx = np.nonzero(g2 < 1.0)[0]
    if len(idx):
        prev = 1.0
        # ゲインが 1 未満の区間とその後の戻りだけ逐次処理
        i = idx[0]
        n = len(g2)
        while i < n:
            v = g2[i]
            rec = prev + (1 - prev) * a
            prev = v if v < rec else rec
            y[i] = prev
            i += 1
            if prev > 0.99999 and i < n and g2[i] >= 1.0:
                nxt = np.searchsorted(idx, i)
                if nxt >= len(idx):
                    break
                y[i:idx[nxt]] = 1.0
                i = idx[nxt]
                prev = 1.0
    return x * y[:, None], y


def write_wav24(path, x):
    import wave
    x = np.clip(x, -1, 1 - 1 / 8388608)
    q = np.round(x * 8388607).astype("<i4")
    b = q.reshape(-1).view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(3); w.setframerate(SR); w.writeframes(b)
