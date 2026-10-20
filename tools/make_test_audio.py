# Synthetic 16-bar C-G-Am-F loop with a melody, for smoke-testing cover models.
import sys
import numpy as np, soundfile as sf
sr, bpm = 44100, 100
beat = 60 / bpm
def tone(midi, dur, amp):
    t = np.arange(int(sr * dur)) / sr
    f = 440 * 2 ** ((midi - 69) / 12)
    env = np.exp(-3 * t)
    return amp * env * sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 6))
chords = [[48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48]]  # C G Am F
melody = [[64, 62, 60, 62], [62, 59, 55, 59], [60, 64, 69, 67], [65, 64, 62, 60]]
out = np.zeros(int(sr * beat * 4 * 16) + sr)
for bar in range(16):
    c, m = chords[bar % 4], melody[bar % 4]
    start = int(sr * beat * 4 * bar)
    for n in c:
        x = tone(n, beat * 4, 0.12); out[start:start + len(x)] += x
    for i, n in enumerate(m):
        x = tone(n, beat, 0.25); s = start + int(sr * beat * i); out[s:s + len(x)] += x
sf.write(sys.argv[1], out / np.abs(out).max() * 0.8, sr)
