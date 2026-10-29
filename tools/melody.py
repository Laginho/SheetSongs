"""Transcribe a separated vocal stem into a monophonic melody MIDI (real-time seconds, like the cover drafts).

pYIN pitch track -> median-smoothed semitones -> notes split at pitch changes and vocal onsets.
Short blips are dropped, so ornaments and fast runs come out simplified; fix those by ear.
Runs in the Etude venv (librosa, pretty_midi). Make the stem first:
  tools/etude/.venv/Scripts/python.exe -m demucs --two-stems vocals -n htdemucs -o sources/out/song/stems sources/song.mp3

Usage: python tools/melody.py vocals.wav out.mid
"""
import sys

import librosa
import numpy as np
import pretty_midi
from scipy.ndimage import median_filter

if len(sys.argv) != 3:
    sys.exit(__doc__)
src, dst = sys.argv[1:]
SR, HOP = 22050, 256
MIN_NOTE = 0.09  # seconds; shorter runs are glitches, slides or consonants

y, _ = librosa.load(src, sr=SR, mono=True)
f0, voiced, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C6"), sr=SR, hop_length=HOP)
# Stem bleed and breaths: ignore frames far below the vocal's typical loudness.
rms = librosa.feature.rms(y=y, hop_length=HOP)[0][: len(f0)]
voiced &= rms > 0.15 * np.median(rms[voiced])
semis = np.where(voiced, librosa.hz_to_midi(np.nan_to_num(f0, nan=1.0)), np.nan)
smooth = median_filter(np.nan_to_num(semis, nan=0.0), size=9)  # ~100 ms: flattens vibrato wobble across a semitone
pitch = np.where(voiced, np.round(smooth), 0).astype(int)
onsets = set(librosa.onset.onset_detect(y=y, sr=SR, hop_length=HOP, backtrack=True))

# Run-length notes: a new note starts where the pitch changes or a new syllable is sung.
notes, start = [], 0
for i in range(1, len(pitch) + 1):
    if i == len(pitch) or pitch[i] != pitch[i - 1] or i in onsets:
        if pitch[start] > 0:
            notes.append([pitch[start], start, i])
        start = i
frame = HOP / SR
notes = [n for n in notes if (n[2] - n[1]) * frame >= MIN_NOTE]
# pYIN sometimes lands an octave off: pull notes that leap far from their neighbours back toward them.
for i, n in enumerate(notes):
    around = np.median([m[0] for m in notes[max(0, i - 4) : i + 5]])
    while n[0] - around > 9:
        n[0] -= 12
    while around - n[0] > 9:
        n[0] += 12

pm = pretty_midi.PrettyMIDI()
voice = pretty_midi.Instrument(0, name="melody")
voice.notes = [pretty_midi.Note(90, p, a * frame, b * frame) for p, a, b in notes]
pm.instruments.append(voice)
pm.write(dst)
print(f"{dst}: {len(notes)} notes, voiced {voiced.mean():.0%} of frames")
