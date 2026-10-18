# -*- coding: utf-8 -*-
# 《光落之处》 Where the Light Rests — Copyright (C) 2026 kms413
# Licensed under the GNU Affero General Public License, version 3 or later.
# See LICENSE for the full text.  This program comes with NO WARRANTY.
"""Cover art for 《光落之处》."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle
from matplotlib.colors import LinearSegmentedColormap

W = H = 1600
yy, xx = np.mgrid[0:H, 0:W]
x = xx / W
y = yy / H

# night sky gradient
bg = np.zeros((H, W, 3))
top = np.array([0.024, 0.035, 0.055])
bot = np.array([0.075, 0.098, 0.125])
for c in range(3):
    bg[:, :, c] = top[c] + (bot[c] - top[c]) * (y ** 1.4)

# warm bloom low in the frame, off centre
cx, cy, rad = 0.62, 0.66, 0.55
d = np.sqrt(((x - cx) * 1.0) ** 2 + ((y - cy) * 1.35) ** 2)
glow = np.exp(-(d / rad) ** 2) * 0.85 + np.exp(-(d / (rad * 0.36)) ** 2) * 0.55
warm = np.array([0.95, 0.72, 0.42])
for c in range(3):
    bg[:, :, c] += warm[c] * glow * 0.22

# faint stars
rng = np.random.default_rng(11)
for _ in range(260):
    sx, sy = rng.random() * W, rng.random() * H * 0.75
    r = rng.random() ** 3 * 1.6 + 0.25
    a = rng.random() * 0.55 + 0.08
    y0, y1 = int(sy) - 3, int(sy) + 4
    x0, x1 = int(sx) - 3, int(sx) + 4
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            px, py = int(sx) + dx, int(sy) + dy
            if 0 <= px < W and 0 <= py < H:
                f = np.exp(-(dx * dx + dy * dy) / (2 * r * r)) * a
                bg[py, px] = np.clip(bg[py, px] + f, 0, 1)

fig = plt.figure(figsize=(8, 8), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(bg, extent=[0, 1, 0, 1], origin="lower", interpolation="bilinear")

# horizon line + ripples
ax.plot([0.05, 0.95], [0.395, 0.395], color="#e9c98b", lw=0.7, alpha=0.30)
for i, (r, a) in enumerate([(0.10, 0.20), (0.17, 0.15), (0.25, 0.11),
                           (0.35, 0.08), (0.47, 0.055), (0.62, 0.035)]):
    ax.add_patch(Arc((0.55, 0.30), r * 2.0, r * 0.85, theta1=8, theta2=172,
                     color="#f0d3a0", alpha=a, lw=1.0))

# a few falling light streaks
for i, (x0, ln, a) in enumerate([(0.30, 0.11, 0.10), (0.44, 0.16, 0.07),
                                 (0.71, 0.13, 0.08), (0.83, 0.08, 0.06)]):
    ax.plot([x0, x0 + 0.004], [0.86, 0.86 - ln], color="#ffe6bd", lw=1.2, alpha=a)

# text
ax.text(0.5, 0.723, "光 落 之 处", ha="center", va="center",
        fontsize=58, color="#f6efe3", family="Noto Serif CJK SC",
        weight="light")
ax.text(0.5, 0.641, "W H E R E   T H E   L I G H T   R E S T S", ha="center",
        va="center", fontsize=11.5, color="#d9b98a", family="DejaVu Serif")
ax.plot([0.42, 0.58], [0.604, 0.604], color="#b08d5f", lw=0.8, alpha=0.75)
ax.text(0.5, 0.560, "为钢琴、弦乐与玻璃而作", ha="center", va="center",
        fontsize=15, color="#cfc4b4", family="Noto Serif CJK SC")
ax.text(0.5, 0.510, "D minor   ·   3:06", ha="center", va="center",
        fontsize=10.5, color="#8f8779", family="DejaVu Serif")

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.savefig("cover.png", facecolor="#0a0d13")
print("wrote cover.png")
