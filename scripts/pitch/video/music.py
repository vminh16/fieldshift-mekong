"""Synthesize a 30 s ambient underscore (royalty-free by construction).

Usage: python music.py <timeline.json> <out.wav>
Pad (Am–F–C–G), soft plucked arpeggio at 100 BPM, sub pulse, swell into the answer,
resolve on the end card, airy whooshes on scene cuts.
"""

import json
import sys

import numpy as np
import soundfile as sf

SR = 48000
tl = json.load(open(sys.argv[1]))
DUR = tl["duration"]
S = tl["scenes"]
t = np.arange(int(DUR * SR)) / SR
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lowpass(x, cutoff):
    # one-pole low-pass, cutoff in Hz (scalar)
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


bpm = 100
beat = 60 / bpm
bar = 4 * beat
chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]  # Am F C G
out = np.zeros_like(t)

# Pad: detuned saws softened, slow crossfade between chords
pad = np.zeros_like(t)
nbars = int(np.ceil(DUR / bar)) + 1
for b in range(nbars):
    ch = chords[b % 4]
    a, z = b * bar, (b + 1) * bar
    seg = (t >= a - 0.6) & (t < z + 0.6)
    tt = t[seg]
    env = np.clip((tt - (a - 0.6)) / 1.2, 0, 1) * np.clip(((z + 0.6) - tt) / 1.2, 0, 1)
    for n in ch:
        for det in (-0.07, 0.0, 0.07):
            f = midi(n - 12) * 2 ** (det / 12)
            ph = 2 * np.pi * f * tt + rng.uniform(0, 6.28)
            pad[seg] += env * (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph))
pad = lowpass(pad, 1400) * 0.035

# Plucked arpeggio (8th notes), enters after the hook
arp = np.zeros_like(t)
step = beat / 2
k = 0
while k * step < DUR:
    st = k * step
    ch = chords[int(st // bar) % 4]
    n = ch[[0, 2, 1, 3, 2, 1, 3, 2][k % 8]] + 12
    m = (t >= st) & (t < st + 1.2)
    tt = t[m] - st
    f = midi(n)
    tone = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 9)
    arp[m] += tone * np.exp(-tt * 4.2) * (1 - np.exp(-tt * 300))
    k += 1
arp_gain = np.interp(
    t,
    [0, S["outlook"] - 0.5, S["outlook"] + 0.5, S["answer"], S["end"], S["end"] + 0.4, DUR],
    [0, 0, 0.5, 0.8, 1.0, 0.25, 0.0],
)
arp *= 0.06 * arp_gain

# Sub pulse on beats from the engine scene to the end card
pulse = np.zeros_like(t)
k = 0
while k * beat < DUR:
    st = k * beat
    if S["twin"] - 0.1 <= st < S["end"]:
        m = (t >= st) & (t < st + 0.5)
        tt = t[m] - st
        pulse[m] += np.sin(2 * np.pi * (55 + 30 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
    k += 1
pulse *= 0.10

# Whooshes on scene cuts: band-limited noise with a rising-then-falling envelope
whoosh = np.zeros_like(t)
for name in ("outlook", "draw", "twin", "answer", "sources", "end"):
    c = S[name]
    m = (t >= c - 0.45) & (t < c + 0.25)
    tt = t[m] - (c - 0.45)
    env = np.sin(np.pi * np.clip(tt / 0.7, 0, 1)) ** 2
    whoosh[m] += rng.normal(size=m.sum()) * env
whoosh = (lowpass(whoosh, 2500) - lowpass(whoosh, 300)) * 0.10

# Final chord bloom on the end card
bloom = np.zeros_like(t)
m = t >= S["end"]
tt = t[m] - S["end"]
for n in (57, 64, 69, 72, 76):
    bloom[m] += np.sin(2 * np.pi * midi(n) * tt) * np.exp(-tt * 0.9) * (1 - np.exp(-tt * 40))
bloom *= 0.035

mix = pad + arp + pulse + whoosh + bloom
master = np.interp(t, [0, 0.8, DUR - 1.2, DUR], [0, 1, 1, 0])
mix *= master
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.7
stereo = np.stack([mix, np.roll(mix, int(0.011 * SR))], axis=1)  # tiny Haas widening
sf.write(sys.argv[2], stereo, SR)
print("music", DUR, "s")
