# -*- coding: utf-8 -*-
"""
《光落之处》 Where the Light Rests  (D minor, 63 BPM)

Form:  intro 4 | theme 16 | lift 8 | climax 10 | coda 6  (44 bars)

    python arrange.py             # render instruments + mix
    python arrange.py --mix-only  # re-mix cached stems (fast)
"""
import os
import sys
import wave
import numpy as np

from synth import (SR, F32, RNG, mtof, db, lowpass, highpass, pan_gains, shelf,
                   peaking, smoothstep, rms_of, get_piano, get_pad, get_bass,
                   get_glass, cache_report)

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ score
BPM = 63.0
N_BARS = 44

tempo = np.ones(N_BARS)
rng_t = np.random.default_rng(7)
walk = 0.0
for b in range(N_BARS):
    walk = 0.985 * walk + 0.010 * rng_t.standard_normal()
    tempo[b] = 1.0 + float(np.clip(walk, -0.026, 0.028))
for i, m in enumerate([1.00, 1.00, 1.00, 0.995, 0.985, 0.965, 0.940, 0.910, 0.870, 0.815]):
    tempo[34 + i] = m * 0.975          # ritardando through the coda
tempo[20] = 0.965                      # breath before the lift
tempo[28] = 0.980                      # breath before the climax

gaps = np.zeros(N_BARS)
gaps[4] = 0.35
gaps[20] = 0.55
gaps[28] = 0.45

bar_start = np.zeros(N_BARS + 1)
bar_dur = np.zeros(N_BARS)
for b in range(N_BARS):
    bar_dur[b] = 4.0 * 60.0 / (BPM * tempo[b])
    bar_start[b + 1] = bar_start[b] + bar_dur[b] + gaps[b]
TOTAL = bar_start[-1]

# name -> (bass midi, four-note arpeggio voicing)
CH = {
    "Dm":     (38, [50, 57, 65, 69, 74]),
    "Bb":     (46, [46, 53, 62, 65, 70]),
    "F":      (41, [45, 53, 60, 65, 69]),
    "C":      (36, [48, 55, 64, 67, 72]),
    "Gm":     (43, [43, 50, 58, 62, 67]),
    "A":      (45, [45, 52, 61, 64, 69]),
    "F/A":    (45, [45, 53, 60, 65, 69]),
    "C/E":    (40, [40, 48, 55, 64, 67]),
    "Gm7":    (43, [43, 50, 58, 62, 65]),
    "Bbadd9": (46, [46, 53, 62, 65, 72]),
    "Dmadd9": (38, [50, 57, 64, 69, 74]),
    "Fadd9":  (41, [41, 48, 55, 60, 65]),
}

PROG = [
    "Dm", "Bb", "F", "C",
    "Dm", "Bb", "F", "C",
    "Dm", "Gm", "Bb", "A",
    "Dm", "Bb", "F/A", "C",
    "Dm", "Gm7", "Bbadd9", "A",
    "F", "C/E", "Dm", "Bb",
    "F/A", "Gm7", "C", "C",
    "Bbadd9", "F/A", "Gm", "Dm",
    "Bb", "C", "Dmadd9", "Bbadd9",
    "Gm7", "A", "Dmadd9", "Bbadd9",
    "Fadd9", "Dmadd9", "Dm", "Dm",
]
assert len(PROG) == N_BARS

MELODY = [
    (4, 3.5, 0.5, 69, 0.40),          # lead-in from the intro
    (5, 0, 1.5, 74, 0.60), (5, 1.5, 1, 77, 0.66), (5, 2.5, 1, 76, 0.60), (5, 3.5, 0.5, 74, 0.56),
    (6, 0, 2, 74, 0.58), (6, 2, 1, 72, 0.55), (6, 3, 1, 70, 0.54),
    (7, 0, 1.5, 69, 0.56), (7, 1.5, 1, 72, 0.60), (7, 2.5, 1.5, 74, 0.62),
    (8, 0, 2, 72, 0.58), (8, 2, 1, 74, 0.60), (8, 3, 1, 76, 0.64),

    (9, 0, 1.5, 77, 0.68), (9, 1.5, 1, 76, 0.60), (9, 2.5, 1.5, 74, 0.58),
    (10, 0, 1, 74, 0.58), (10, 1, 1, 70, 0.55), (10, 2, 2, 69, 0.54),
    (11, 0, 1.5, 70, 0.56), (11, 1.5, 1, 74, 0.60), (11, 2.5, 1.5, 72, 0.58),
    (12, 0, 3, 73, 0.64), (12, 3, 1, 76, 0.58),

    (13, 0, 2, 74, 0.58), (13, 2, 1, 77, 0.62), (13, 3, 1, 79, 0.64),
    (14, 0, 2.5, 77, 0.66), (14, 2.5, 1.5, 74, 0.58),
    (15, 0, 1, 72, 0.56), (15, 1, 1, 76, 0.60), (15, 2, 1, 77, 0.63), (15, 3, 1, 79, 0.66),
    (16, 0, 3, 76, 0.64), (16, 3, 1, 74, 0.58),
    (17, 0, 1.5, 77, 0.66), (17, 1.5, 1, 79, 0.70), (17, 2.5, 1.5, 81, 0.76),
    (18, 0, 2, 79, 0.68), (18, 2, 1, 77, 0.62), (18, 3, 1, 74, 0.58),
    (19, 0, 1.5, 74, 0.58), (19, 1.5, 1, 77, 0.64), (19, 2.5, 1.5, 79, 0.68),
    (20, 0, 3, 76, 0.64), (20, 3, 1, 73, 0.58),

    (21, 0, 2, 77, 0.66), (21, 2, 2, 81, 0.78),
    (22, 0, 1.5, 79, 0.70), (22, 1.5, 1, 76, 0.62), (22, 2.5, 1.5, 72, 0.58),
    (23, 0, 2, 74, 0.60), (23, 2, 1, 77, 0.66), (23, 3, 1, 81, 0.78),
    (24, 0, 3, 79, 0.70), (24, 3, 1, 77, 0.64),
    (25, 0, 1.5, 76, 0.64), (25, 1.5, 1, 77, 0.66), (25, 2.5, 1.5, 81, 0.78),
    (26, 0, 2, 79, 0.70), (26, 2, 1.5, 77, 0.64),
    (27, 0, 1, 76, 0.62), (27, 1, 1, 74, 0.58), (27, 2, 2, 72, 0.58),
    (28, 0, 2, 72, 0.64), (28, 2, 1, 74, 0.68), (28, 3, 1, 77, 0.74),

    (29, 0, 3, 82, 0.86), (29, 3, 1, 81, 0.74),
    (30, 0, 2, 81, 0.80), (30, 2, 2, 77, 0.70),
    (31, 0, 1.5, 79, 0.74), (31, 1.5, 1, 82, 0.82), (31, 2.5, 1.5, 84, 0.88),
    (32, 0, 2.5, 84, 0.90), (32, 2.5, 1.5, 81, 0.78),
    (33, 0, 2, 82, 0.84), (33, 2, 2, 79, 0.74),
    (34, 0, 1.5, 79, 0.74), (34, 1.5, 1, 81, 0.78), (34, 2.5, 1.5, 84, 0.88),
    (35, 0, 3, 81, 0.78), (35, 3, 1, 79, 0.70),
    (36, 0, 2, 82, 0.84), (36, 2, 2, 84, 0.88),
    (37, 0, 2, 82, 0.78), (37, 2, 2, 79, 0.70),
    (38, 0, 4, 81, 0.86),

    (39, 0, 2, 77, 0.62), (39, 2, 2, 76, 0.56),
    (40, 0, 2, 74, 0.56), (40, 2, 2, 72, 0.52),
    (41, 0, 2, 72, 0.50), (41, 2, 2, 69, 0.46),
    (42, 0, 4, 74, 0.52),
]


def t_of(bar, beat):
    return bar_start[bar - 1] + beat * (60.0 / (BPM * tempo[bar - 1]))


def section_of(b):
    return ("intro" if b <= 4 else "theme" if b <= 20 else
            "lift" if b <= 28 else "climax" if b <= 38 else "outro")


# --------------------------------------------------------------- arrangement
TAIL = 11.0
N = int((TOTAL + TAIL) * SR)
STEMS = {k: (np.zeros(N, dtype=F32), np.zeros(N, dtype=F32))
         for k in ("mel", "arp", "pad", "bass", "glass")}


def place(stem, buf, start, gain, pan):
    i = int(round(start * SR))
    if i < 0:
        buf, i = buf[-i:], 0
    if i >= N or len(buf) == 0:
        return
    j = min(N, i + len(buf))
    seg = buf[: j - i] * gain
    l, r = pan_gains(pan)
    L, R = STEMS[stem]
    L[i:j] += seg * l
    R[i:j] += seg * r


EVENTS = []


def play(note, t, vel, dur_hint, pan, gain, stem="arp"):
    place(stem, get_piano(note, vel, dur_hint),
          t, gain * (0.30 + 0.78 * vel ** 1.2), pan)
    EVENTS.append((round(float(t), 4), int(note), round(float(vel), 3),
                   round(float(dur_hint), 3), stem))


def render_bar(b, section):
    bass, voicing = CH[PROG[b - 1]]
    t0, dur = bar_start[b - 1], bar_dur[b - 1]
    ext = list(voicing) + [x + 12 for x in voicing]

    if section in ("intro", "outro"):
        vel = 0.46 if section == "intro" else 0.32
        pat, div = [0, 2, 4, 2], 4
        for i, idx in enumerate(pat):
            tb = t0 + i * dur / div + RNG.standard_normal() * 0.012
            play(ext[idx], tb, vel * (0.86 + 0.2 * RNG.random()),
                 dur / div * 2.2, -0.30 + 0.12 * (idx % 3), 0.48)
        play(voicing[0], t0 + 0.01, vel * 0.95, dur * 0.9, -0.18, 0.46)
        return

    if section == "climax":
        pat, div, vel = [0, 2, 1, 3, 2, 4, 3, 5, 4, 3, 2, 4, 3, 5, 2, 1], 16, 0.46
    elif section == "lift":
        pat, div, vel = [0, 2, 1, 3, 2, 4, 3, 5], 8, 0.40
    else:
        pat = [5, 4, 3, 2, 1, 2, 3, 4] if b >= 17 else [0, 1, 2, 3, 4, 3, 2, 1]
        div, vel = 8, 0.35

    for i, idx in enumerate(pat):
        tb = t0 + i * dur / div + RNG.standard_normal() * 0.010
        accent = 1.10 if i % div == 0 else (1.02 if i % (div // 2) == 0 else 0.92)
        v = vel * accent * (0.88 + 0.18 * RNG.random())
        play(ext[idx], tb, min(0.85, v), dur / div * 3.0,
             -0.30 + 0.10 * (i % 4), 0.38)

    root = voicing[0]
    play(root, t0, 0.46, dur * 0.95, -0.22, 0.52)
    if section == "climax":
        play(root, t0 + dur * 0.5, 0.40, dur * 0.50, -0.20, 0.44)
    else:
        upper = [n for n in voicing if n > root + 4]
        if upper:
            play(min(upper), t0 + dur * 0.5, 0.33, dur * 0.50, -0.24, 0.36)


MIX_ONLY = "--mix-only" in sys.argv
STEMFILE = os.path.join(HERE, "stems.npz")


def build_stems():
    for b in range(1, N_BARS + 1):
        render_bar(b, section_of(b))

    for (bar, beat, durb, note, vel) in MELODY:
        t = t_of(bar, beat) + RNG.standard_normal() * 0.012
        dt = durb * (60.0 / (BPM * tempo[bar - 1]))
        play(note, t, vel, dt * 1.25, 0.06 + 0.03 * RNG.standard_normal(), 1.0, "mel")
        if 29 <= bar <= 38 and note < 84:
            play(note + 12, t + 0.004, vel * 0.58, dt * 1.0, -0.05, 0.58, "mel")
        if 21 <= bar <= 28 and note >= 77:
            play(note + 12, t + 0.006, vel * 0.40, dt * 0.9, 0.12, 0.22, "mel")

    PAD_GAIN = {"intro": 0.60, "theme": 0.78, "lift": 1.02, "climax": 1.62, "outro": 0.55}
    WIDTH = {"intro": 0.35, "theme": 0.50, "lift": 0.62, "climax": 0.78, "outro": 0.45}
    for b in range(1, N_BARS + 1):
        sec = section_of(b)
        if sec == "intro" and b < 3:
            continue
        bass, voicing = CH[PROG[b - 1]]
        t0 = bar_start[b - 1]
        dur = bar_dur[b - 1] * 1.08
        notes = []
        for v in voicing[:4]:
            m = v
            while m < 45:
                m += 12
            while m > 64:
                m -= 12
            if m not in notes:
                notes.append(m)
        notes.sort()
        w = WIDTH[sec]
        for k, m in enumerate(notes):
            p = (-w + 2 * w * (k / max(1, len(notes) - 1))) * 0.9
            place("pad", get_pad(m, dur), t0, 0.11 * PAD_GAIN[sec], p)

    for b in range(5, N_BARS + 1):
        bass = CH[PROG[b - 1]][0]
        if bass >= 45:
            bass -= 12
        t0, dur = bar_start[b - 1], bar_dur[b - 1]
        g = 0.42 if b <= 20 else (0.50 if b <= 28 else (0.56 if b <= 38 else 0.30))
        place("bass", get_bass(bass, dur), t0, g, 0.0)
        if 29 <= b <= 38:
            place("bass", get_bass(bass, dur * 0.5), t0 + dur * 0.5, g * 0.5, 0.0)

    sparkles = [
        (4, 3.5, 86, 0.55), (8, 3.0, 93, 0.40), (12, 2.0, 89, 0.45),
        (16, 1.5, 93, 0.36), (20, 2.5, 86, 0.50), (24, 1.0, 88, 0.42),
        (28, 2.0, 91, 0.45), (32, 0.0, 96, 0.42), (35, 3.0, 93, 0.38),
        (38, 2.0, 89, 0.50), (40, 1.0, 86, 0.42), (42, 2.0, 93, 0.34),
        (43, 1.5, 98, 0.26), (43, 3.0, 93, 0.22), (44, 0.5, 86, 0.24),
    ]
    for (bar, beat, note, vel) in sparkles:
        place("glass", get_glass(note), t_of(bar, beat), vel * 0.30,
              float(np.sin(bar * 1.7)) * 0.55)
    for i, m in enumerate([74, 81, 86, 89]):
        place("glass", get_glass(m), t_of(44, 0.0) + 0.06 * i,
              0.16 - 0.02 * i, -0.4 + 0.27 * i)

    import json
    with open(os.path.join(HERE, "score.json"), "w") as f:
        json.dump({"bpm": BPM, "tempo": tempo.tolist(),
                   "bar_start": bar_start.tolist(), "gaps": gaps.tolist(),
                   "events": EVENTS}, f)
    np.savez(STEMFILE, **{k + "_L": v[0] for k, v in STEMS.items()},
             **{k + "_R": v[1] for k, v in STEMS.items()})
    print("stems saved  ->", cache_report())


if MIX_ONLY and os.path.exists(STEMFILE):
    z = np.load(STEMFILE)
    for k in STEMS:
        STEMS[k] = (z[k + "_L"], z[k + "_R"])
    print("loaded cached stems")
else:
    build_stems()

# --------------------------------------------------------------------- mix
STEM_LEVEL = {"mel": 0.0, "arp": -3.4, "pad": 9.1, "bass": -6.6, "glass": 3.2}
SEND = {"mel": 0.55, "arp": 0.75, "pad": 1.0, "bass": 0.0, "glass": 1.0}

dryL = np.zeros(N)
dryR = np.zeros(N)
sendL = np.zeros(N)
sendR = np.zeros(N)
print("stem level (dBFS rms):")
for k, (L, R) in STEMS.items():
    g = db(STEM_LEVEL[k])
    dryL += L * g
    dryR += R * g
    sendL += L * g * SEND[k]
    sendR += R * g * SEND[k]
    mono = (L + R) * 0.5 * g
    print(f"  {k:6s} {20*np.log10(rms_of(mono) + 1e-12):7.2f}")


def make_ir(seconds=4.2, predelay=0.026, seed=3):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n))
    for ch in range(2):
        x = r.standard_normal(n)
        low = lowpass(x, 1100, 2) * np.exp(-t / 1.75)
        mid = (x - lowpass(x, 1100, 2)) * np.exp(-t / 1.30)
        hi = highpass(x, 2400, 1) * np.exp(-t / 1.25)
        ir[ch] = (low * 0.80 + mid + hi * 0.75) * (1.0 - np.exp(-t / 0.005))
    for ch in range(2):
        for d, g in ((0.011, 0.45), (0.019, 0.32), (0.029, 0.24), (0.041, 0.16), (0.057, 0.10)):
            i = int((predelay + d + 0.003 * ch) * SR)
            if i < n:
                ir[ch, i] += g * (1 if r.random() > 0.5 else -1)
    ir[0] /= np.sqrt(np.sum(ir[0] ** 2))
    ir[1] /= np.sqrt(np.sum(ir[1] ** 2))
    return np.concatenate([np.zeros((2, int(predelay * SR))), ir * 0.80], axis=1)


def convolve(x, h):
    n = len(x) + len(h) - 1
    nfft = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(h, nfft), nfft)[:n]


ir = make_ir()
wetL = highpass(convolve(sendL, ir[0])[:N], 220, 2)
wetR = highpass(convolve(sendR, ir[1])[:N], 220, 2)
print(f"wet/dry energy ratio {(np.mean(wetL**2)+np.mean(wetR**2))/(np.mean(dryL**2)+np.mean(dryR**2)):.3f}")

outL = dryL + wetL
outR = dryR + wetR

outL = highpass(outL, 34, 2)
outR = highpass(outR, 34, 2)
for ch in (0, 1):
    y = outL if ch == 0 else outR
    y = peaking(y, 330, -1.6, 1.1)          # clear the boxy low-mid
    y = peaking(y, 1000, -0.8, 1.4)
    y = peaking(y, 3400, 2.2, 1.0)          # presence / bow rosin
    y = shelf(y, 8500, 2.6, "high")         # air
    y = shelf(y, 90, -1.2, "low")
    y = lowpass(y, 18000, 1)
    if ch == 0:
        outL = y
    else:
        outR = y

fi = int(2.2 * SR)
env = np.ones(N)
env[:fi] = smoothstep(np.linspace(0, 1, fi)) ** 0.8
fo = int((TOTAL + 2.4) * SR)
env[fo:] = smoothstep(np.linspace(1, 0, N - fo)) ** 1.2
outL *= env
outR *= env

target_rms = db(-19.0)
cur = np.sqrt((rms_of(outL) ** 2 + rms_of(outR) ** 2) / 2)
outL *= target_rms / cur
outR *= target_rms / cur
print(f"pre-limit peak {20*np.log10(max(abs(outL).max(), abs(outR).max())):.2f} dBFS")

# look-ahead peak limiter (vectorised): gain reduction that dips before peaks
from scipy.ndimage import minimum_filter1d

thr = db(-1.3)
need = np.maximum(np.maximum(np.abs(outL), np.abs(outR)) / thr, 1.0)
g = 1.0 / need
w_min = max(3, int(0.025 * SR))
g = minimum_filter1d(g, size=w_min, mode="nearest")
w_avg = max(3, int(0.008 * SR))
g = np.convolve(np.pad(g, w_avg, mode="edge"), np.ones(w_avg) / w_avg,
                mode="same")[w_avg:-w_avg]
outL *= g
outR *= g
peak = max(np.abs(outL).max(), np.abs(outR).max())
print(f"post-limit peak {20*np.log10(peak):.2f} dBFS  "
      f"max reduction {20*np.log10(g.min()):.2f} dB")
x = np.clip(np.stack([outL, outR]), -0.999, 0.999)

path = os.path.join(HERE, "where-the-light-rests.wav")
q = np.round(np.clip(x.T, -1, 1) * 8388607.0).astype("<i4")
q = np.ascontiguousarray(q)
b = q.view(np.uint8).reshape(q.shape[0], q.shape[1], 4)[:, :, :3]
pcm24 = b.reshape(q.shape[0], q.shape[1] * 3)
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(3)
    w.setframerate(SR)
    w.writeframes(pcm24.tobytes())

print(f"\nduration {N/SR:.1f}s  peak {np.abs(x).max():.3f}  "
      f"rms {20*np.log10(rms_of(x)):.1f} dBFS  -> {path}")
