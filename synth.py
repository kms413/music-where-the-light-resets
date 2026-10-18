# -*- coding: utf-8 -*-
"""Additive instrument models used by 《光落之处》.

Every sound is generated from sine partials plus noise transients; there are
no samples.  Instruments are cached per parameter set, like a sampler.
"""
import numpy as np

SR = 44100
F32 = np.float32
RNG = np.random.default_rng(20240517)

try:
    from scipy.signal import sosfilt, butter
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


# ---------------------------------------------------------------- utilities
def mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def db(x):
    return 10.0 ** (x / 20.0)


def lowpass(x, cutoff, order=2):
    cutoff = min(cutoff, SR * 0.45)
    if HAVE_SCIPY:
        return sosfilt(butter(order, cutoff / (SR / 2), btype="low", output="sos"), x)
    n = len(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x) / np.sqrt(1 + (f / cutoff) ** (2 * order)), n)


def highpass(x, cutoff, order=2):
    cutoff = max(cutoff, 10.0)
    if HAVE_SCIPY:
        return sosfilt(butter(order, cutoff / (SR / 2), btype="high", output="sos"), x)
    n = len(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x) / np.sqrt(1 + (cutoff / np.maximum(f, 1e-9)) ** (2 * order)), n)


def pan_gains(pan):
    a = (pan + 1.0) * 0.25 * np.pi
    return np.cos(a), np.sin(a)


def shelf(x, f0, gain_db, kind="high"):
    """Zero-phase shelving EQ over a whole buffer."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = db(gain_db) - 1.0
    k = np.clip(np.log2(np.maximum(f, 1.0) / f0) * 0.5 + 0.5, 0, 1)
    k = k * k * (3 - 2 * k)
    resp = 1.0 + (g * k if kind == "high" else g * (1 - k))
    return np.fft.irfft(np.fft.rfft(x) * resp, n)


def peaking(x, f0, gain_db, width=1.0):
    """Zero-phase bell EQ, width in octaves."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    resp = 1.0 + (db(gain_db) - 1.0) * \
        np.exp(-0.5 * (np.log2(np.maximum(f, 1.0) / f0) / width) ** 2)
    return np.fft.irfft(np.fft.rfft(x) * resp, n)


def smoothstep(x):
    return x * x * (3.0 - 2.0 * x)


def rms_of(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)) + 1e-12)


# ---------------------------------------------------------------- piano
def piano_body(f0, vel, dur_hint, rng):
    """Struck string: stretched partials, three strings, hammer, felt thump.

    The amplitude envelope has two stages (a fast initial drop then a long
    tail), which is both more realistic and keeps dense figuration from
    turning into a wash.
    """
    tau0 = 3.4 * (261.63 / f0) ** 0.5
    tau0 = float(np.clip(tau0, 0.55, 3.6)) * (1.0 - 0.10 * (vel - 0.5))
    length = float(np.clip(max(tau0 * 2.6, dur_hint * 1.3), 0.30, 5.6))
    n = int(length * SR)
    t = np.arange(n, dtype=np.float64) / SR

    B = 0.00020 + 0.00040 * (261.63 / f0) ** 1.3
    nmax = int(min(24, 15500.0 / f0))
    damp = 0.23 * (1.0 - 0.92 * vel) ** 1.15 + 0.012

    decay = (0.42 * np.exp(-t / (0.34 * (261.63 / f0) ** 0.30))
             + 0.58 * np.exp(-t / tau0))
    sig = np.zeros(n)
    strings = [(0.55, 0.55), (-0.6, 0.45)]
    if f0 < 180:
        strings.append((1.8, 0.20))
    for ct, w in strings:
        det = 2.0 ** (ct / 1200.0)
        for k in range(1, nmax + 1):
            fk = k * f0 * det * np.sqrt(1.0 + B * k * k)
            if fk > 15500:
                break
            amp = w / k ** 1.02 * np.exp(-(k - 1) * damp)
            sig += amp * np.power(decay, 1.0 + 0.26 * (k - 1) ** 1.1) * \
                np.sin(2 * np.pi * fk * t + rng.random() * 6.283)

    click = rng.standard_normal(n) * np.exp(-t / 0.016)
    click = lowpass(click, 5500 + 6500 * vel, 2) - lowpass(click, 400, 1) * 0.35
    sig += click * 0.15 * (0.45 + vel)
    sig += np.sin(2 * np.pi * f0 * 0.5 * t) * np.exp(-t / 0.018) * 0.035 * vel

    sig *= 1.0 - np.exp(-t / 0.0035)
    fl = min(n, int(0.30 * SR))
    sig[-fl:] *= np.linspace(1, 0, fl) ** 1.5
    return (sig / rms_of(sig) * 0.08).astype(F32)


def pad_body(f0, dur, rng, harm=8):
    """Bowed strings: three detuned additive stacks, vibrato, slow swell."""
    att, rel = 0.7, 1.6
    n = int((dur + att + rel) * SR)
    t = np.arange(n, dtype=np.float64) / SR
    vib = 0.0030 * np.sin(2 * np.pi * (4.6 + rng.random() * 0.8) * t + rng.random() * 6.28)
    drift = 0.0010 * np.sin(2 * np.pi * 0.09 * t + rng.random() * 6.28)
    sig = np.zeros(n)
    for det, w in ((0.0, 1.0), (7.0, 0.62), (-5.5, 0.52)):
        ratio = 2.0 ** ((det + vib + drift) / 1200.0)
        for k in range(1, harm + 1):
            if k * f0 > 5200:
                break
            sig += (w / k ** 1.3 * (0.6 + 0.4 / k)) * \
                np.sin(2 * np.pi * k * f0 * ratio * t + rng.random() * 6.28)
    e = np.ones(n)
    na, nr = max(2, min(int(att * SR), n // 2)), max(2, min(int(rel * SR), n // 2))
    e[:na] = smoothstep(np.linspace(0, 1, na))
    e[-nr:] = smoothstep(np.linspace(1, 0, nr))
    sig = lowpass(sig * e, 3000)
    return (sig / rms_of(sig) * 0.05).astype(F32)


def bass_body(f0, dur, rng):
    n = int((dur + 0.8) * SR)
    t = np.arange(n, dtype=np.float64) / SR
    sig = np.sin(2 * np.pi * f0 * t) + 0.16 * np.sin(2 * np.pi * 2 * f0 * t + 0.4)
    e = np.exp(-t / (dur * 1.3 + 0.30)) * (1.0 - np.exp(-t / 0.035))
    nr = int(0.25 * SR)
    e[-nr:] *= np.linspace(1, 0, nr)
    return (sig * e / rms_of(sig * e) * 0.12).astype(F32)


def glass_body(f0, rng):
    n = int(4.5 * SR)
    t = np.arange(n, dtype=np.float64) / SR
    sig = np.zeros(n)
    for k, a, tk in ((1, 1.0, 2.0), (2.01, 0.42, 1.0), (3.02, 0.16, 0.5), (5.04, 0.05, 0.3)):
        sig += a * np.sin(2 * np.pi * f0 * k * t + rng.random() * 6.28) * np.exp(-t / tk)
    sig *= 1.0 - np.exp(-t / 0.003)
    return (sig / rms_of(sig) * 0.06).astype(F32)


# ---------------------------------------------------------------- cache
_cache_piano, _cache_pad, _cache_bass, _cache_glass = {}, {}, {}, {}


def get_piano(midi, vel, dur_hint):
    key = (midi, round(vel * 40), round(dur_hint * 4))
    if key not in _cache_piano:
        _cache_piano[key] = piano_body(mtof(midi), vel, dur_hint, RNG)
    return _cache_piano[key]


def get_pad(midi, dur):
    key = (midi, round(dur * 4))
    if key not in _cache_pad:
        _cache_pad[key] = pad_body(mtof(midi), dur, RNG)
    return _cache_pad[key]


def get_bass(midi, dur):
    key = (midi, round(dur * 4))
    if key not in _cache_bass:
        _cache_bass[key] = bass_body(mtof(midi), dur, RNG)
    return _cache_bass[key]


def get_glass(midi):
    if midi not in _cache_glass:
        _cache_glass[midi] = glass_body(mtof(midi), RNG)
    return _cache_glass[midi]


def cache_report():
    return (f"piano {len(_cache_piano)}  pad {len(_cache_pad)}  "
            f"bass {len(_cache_bass)}  glass {len(_cache_glass)}")
