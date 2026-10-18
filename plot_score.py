# -*- coding: utf-8 -*-
# 《光落之处》 Where the Light Rests — Copyright (C) 2026 kms413
# Licensed under the GNU Affero General Public License, version 3 or later.
# See LICENSE for the full text.  This program comes with NO WARRANTY.
"""Draw the piano roll of 《光落之处》 to inspect the counterpoint."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = __file__.rsplit("/", 1)[0]
d = json.load(open(HERE + "/score.json"))
ev = d["events"]
T = max(e[0] for e in ev) + 3

COL = {"mel": "#ffd479", "arp": "#5aa9e6", "pad": "#7ee0c0",
       "bass": "#c98bdb", "glass": "#ff9aa2"}

fig, (ax, ax2) = plt.subplots(2, 1, figsize=(22, 11), sharex=False,
                              gridspec_kw={"height_ratios": [1.15, 1]})
for (t, note, vel, dur, stem) in ev:
    if stem == "glass":
        continue
    h = 0.42 if stem != "pad" else 0.9
    ax.add_patch(Rectangle((t, note - h / 2), max(dur * 0.55, 0.16), h,
                           color=COL[stem], alpha=0.35 if stem in ("pad", "arp") else 0.95,
                           linewidth=0))
ax.set_ylim(30, 100)
ax.set_xlim(0, T)
ax.set_xlabel("time (s)")
ax.set_ylabel("MIDI note")
ax.set_title("Where the Light Rests — full piano roll (orange=melody, blue=arpeggio, "
             "green=pad, violet=sub)", fontsize=13)
ax.grid(alpha=0.15, linestyle=":")
for b, name in [(0, "intro"), (15.2, "theme A"), (60.8, "theme A'"),
                (106.4, "lift"), (136, "climax"), (172, "coda")]:
    ax.axvline(b, color="w", alpha=0.25, lw=0.8)

# zoom on the theme (bars 5-12): 15.2 s .. 45.6 s
t0, t1 = 14.0, 46.5
for (t, note, vel, dur, stem) in ev:
    if stem == "glass" or not (t0 <= t <= t1):
        continue
    h = 0.42 if stem != "pad" else 0.9
    ax2.add_patch(Rectangle((t, note - h / 2), max(dur * 0.55, 0.16), h,
                            color=COL[stem], alpha=0.35 if stem in ("pad", "arp") else 0.95,
                            linewidth=0))
ax2.set_ylim(36, 90)
ax2.set_xlim(t0, t1)
ax2.set_xlabel("time (s)")
ax2.set_ylabel("MIDI note")
ax2.set_title("Theme A, bars 5–12 — melody against the open voicings", fontsize=12)
ax2.grid(alpha=0.18, linestyle=":")
ax2.set_yticks(range(36, 91, 4))
plt.tight_layout()
plt.savefig(HERE + "/pianoroll.png", dpi=110, facecolor="#14161c")
print("wrote pianoroll.png")
