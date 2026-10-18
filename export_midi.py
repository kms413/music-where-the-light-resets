# -*- coding: utf-8 -*-
"""Export the score (score.json) as a tempo-mapped MIDI file."""
import json
import struct

HERE = __file__.rsplit("/", 1)[0]
d = json.load(open(HERE + "/score.json"))
BPM = d["bpm"]
bar_start = d["bar_start"]
gaps = d["gaps"]
tempo = d["tempo"]
events = d["events"]

PPQ = 480
BAR_TICKS = 4 * PPQ

# bar durations as actually heard (tempo + breath pauses)
bar_total = []
for i, t in enumerate(tempo):
    dur = 4.0 * 60.0 / (BPM * t)
    if i < len(gaps):
        dur += gaps[i]
    bar_total.append(dur)

bar_tick = [0]
for i, dur in enumerate(bar_total):
    bar_tick.append(bar_tick[-1] + BAR_TICKS)


def to_tick(t):
    b = len(bar_total) - 1
    while b > 0 and t < bar_start[b]:
        b -= 1
    frac = max(0.0, (t - bar_start[b]) / bar_total[b])
    return int(round(bar_tick[b] + frac * BAR_TICKS))


def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def track(events, channel, program):
    """events: list of (tick, kind, note, velocity)"""
    ev = [b"\x00\xc0" + bytes([program])]
    ev.append((0, b"\x00\xff\x51\x03" + (int(bar_total[0] / 4 * 1_000_000)).to_bytes(3, "big")))
    out = []
    last = 0
    for (tick, kind, note, vel) in sorted(events, key=lambda e: (e[0], e[1])):
        delta = tick - last
        last = tick
        if kind == "on":
            out.append(vlq(delta) + bytes([0x90 | channel, note, vel]))
        else:
            out.append(vlq(delta) + bytes([0x80 | channel, note, 0]))
    return b"".join(ev[:1]) + b"".join(out)


# The pad and the sub are placed directly (not through play()), so their notes
# are rebuilt here from the same tables the arrangement uses.
src = open(HERE + "/arrange.py").read()
_ns = {}
_st = src.index("CH = {"); _en = src.index("}\n", _st) + 2
exec(src[_st:_en], _ns)
_st = src.index("PROG = ["); _en = src.index("]\n", _st) + 2
exec(src[_st:_en], _ns)
CH, PROG = _ns["CH"], _ns["PROG"]

for i, name in enumerate(PROG):
    bass, voicing = CH[name]
    t0 = bar_start[i]
    dur = bar_total[i]
    # string pad: chord tones folded into the tenor register
    notes = []
    for v in voicing[:4]:
        m = v
        while m < 45:
            m += 12
        while m > 64:
            m -= 12
        if m not in notes:
            notes.append(m)
    for m in sorted(notes):
        events.append((t0, m, 0.50, dur * 1.05, "pad"))
    if i >= 4:                                    # sub bass from bar 5
        bb = bass - 12 if bass >= 45 else bass
        events.append((t0, bb, 0.62, dur * 0.95, "bass"))

tracks_spec = [
    ("melody", {"mel"}, 0, 0),
    ("arpeggio", {"arp"}, 1, 0),
    ("strings", {"pad"}, 2, 48),
    ("bass", {"bass"}, 3, 42),
]

TRACK_BYTES = []
for name, stems, ch, prog in tracks_spec:
    ev = []
    for (t, note, vel, dur, stem) in events:
        if stem not in stems:
            continue
        dur = max(0.18, min(dur * 0.9, 6.0))
        ev.append((to_tick(t), "on", note, max(1, min(127, int(vel * 118)))))
        ev.append((to_tick(t + dur), "off", note, 0))
    TRACK_BYTES.append(track(ev, ch, prog))

# tempo map track
tempo_ev = []
for b in range(1, len(bar_total)):
    us = int(bar_total[b] / 4 * 1_000_000)
    tempo_ev.append((bar_tick[b], b"\xff\x51\x03" + us.to_bytes(3, "big")))
body = b""
last = 0
for (tick, msg) in sorted(tempo_ev):
    body += vlq(tick - last) + msg
    last = tick
TRACK_BYTES.insert(0, body)

hdr = b"MThd" + struct.pack(">IHHH", 6, 1, len(TRACK_BYTES), PPQ)
out = hdr + b"".join(b"MTrk" + struct.pack(">I", len(t)) + t for t in TRACK_BYTES)
open(HERE + "/where-the-light-rests.mid", "wb").write(out)
print(f"wrote where-the-light-rests.mid  ({len(out)} bytes, {len(TRACK_BYTES)} tracks)")
