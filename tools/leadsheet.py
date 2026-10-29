"""Lead sheet: the sung melody on top, chord symbols guessed from the piano draft, chord roots on a bass staff.

Chords are matched every half bar against triad/seventh templates (duration-weighted pitch classes, with the
lowest notes deciding the bass), so a passing note can tip one; the Roman numeral under each bass note is the
chord's function in the key. Both inputs must sit on the same grid: retime the melody with the draft as phase_ref.
Bars line up with tidy.py's score of the same draft.

Usage: python tools/leadsheet.py draft_146.mid melody_146.mid out.musicxml key bpm [chords_146.mid]
  chords: take the harmony from this file instead of the draft (e.g. moises_chords.py output, retimed)
"""
import sys

from pathlib import Path

import numpy as np
import pretty_midi
from music21 import chord, harmony, key, layout, metadata, note, pitch, roman, stream

from notation import speller, staff

if len(sys.argv) not in (6, 7):
    sys.exit(__doc__)
draft_path, melody_path, dst, key_name, bpm = sys.argv[1:6]
chords_path = sys.argv[6] if len(sys.argv) == 7 else draft_path
k = key.Key(key_name)
spell = speller(k)
q_per_sec = float(bpm) / 60
WINDOW = 1 if chords_path != draft_path else 2  # quarters: given chords are clean, so follow them beat by beat

# kind (music21 / MusicXML name) -> intervals above the root; simpler chords win ties.
KINDS = {
    "major": (0, 4, 7), "minor": (0, 3, 7), "diminished": (0, 3, 6), "suspended-fourth": (0, 5, 7),
    "dominant-seventh": (0, 4, 7, 10), "minor-seventh": (0, 3, 7, 10), "major-seventh": (0, 4, 7, 11),
}
EXTRA_TONE_COST = 0.08  # a 4th chord tone must carry 8% of the weight to earn a seventh chord
SUS_COST = 0.06  # sus4 only when the third is (nearly) missing, not for every melodic 4-3 suspension
STICKINESS = 0.05  # keep the previous chord unless the new one fits clearly better: fewer mid-bar flickers


def fit(w, root, kind, bass_pc):
    """How well a chord template covers normalized pitch-class weights w."""
    ivs = KINDS[kind]
    return (sum(w[(root + i) % 12] for i in ivs) - EXTRA_TONE_COST * len(ivs) - SUS_COST * (kind == "suspended-fourth")
            + 0.05 * (root == bass_pc) + 0.05 * w[root])


draft = [(n.start * q_per_sec, n.end * q_per_sec, n.pitch) for i in pretty_midi.PrettyMIDI(draft_path).instruments for n in i.notes]
harmony_src = [(n.start * q_per_sec, n.end * q_per_sec, n.pitch) for i in pretty_midi.PrettyMIDI(chords_path).instruments for n in i.notes]
melody = sorted((n.start * q_per_sec, n.end * q_per_sec, n.pitch) for i in pretty_midi.PrettyMIDI(melody_path).instruments for n in i.notes)
lead = round(min(s for s, _, _ in draft) * 4) / 4 // 4 * 4  # same leading-silence trim as tidy.py

# One chord per window, then merge repeats into segments [start, end, root, kind, bass].
end = max(e for _, e, _ in harmony_src)
segments = []
for t in np.arange(lead, end, WINDOW):
    weights, bass = np.zeros(12), np.zeros(12)
    sounding = [(min(e, t + WINDOW) - max(s, t), p) for s, e, p in harmony_src if s < t + WINDOW and e > t]
    if not sounding:
        continue
    low = min(p for _, p in sounding)
    for dur, p in sounding:
        weights[p % 12] += dur
        if p < max(48, low + 5):  # below C3, or the lowest notes when the left hand sits higher
            bass[p % 12] += dur
    w, bass_pc = weights / weights.sum(), int(bass.argmax())
    score, root, kind = max((fit(w, r, kd, bass_pc), r, kd) for r in range(12) for kd in KINDS)
    if segments and segments[-1][1] == t - lead and score - fit(w, *segments[-1][2:4], bass_pc) < STICKINESS:
        root, kind = segments[-1][2:4]
    chord_id = (root, kind, bass_pc)
    if segments and segments[-1][1] == t - lead and tuple(segments[-1][2:]) == chord_id:
        segments[-1][1] += WINDOW
    else:
        segments.append([t - lead, t - lead + WINDOW, *chord_id])

on_three = sum(1 for s in segments if s[0] % 4 == 2)
print(f"{len(segments)} chord changes, {on_three} land on beat 3 (many more than on beat 1 would mean the barlines are half a bar off)")

top = staff("melody", k, bpm=bpm)
bottom = staff("chords", k, bass=True)
symbols = []  # added after barring: in an unbarred part, makeNotation turns them into a phantom second voice
for start, stop, root, kind, bass_pc in segments:
    r = spell(pitch.Pitch(midi=60 + root))
    b = spell(pitch.Pitch(midi=40 + (bass_pc - 4) % 12))  # E2..E-flat3
    symbol = harmony.ChordSymbol(root=r.name, kind=kind, bass=b.name if bass_pc != root else None)
    symbols.append((start, symbol))
    # Numeral from the root-position triad (sus4 read as its major triad); the slash in the symbol shows the bass.
    triad = (0, 4, 7) if kind == "suspended-fourth" else KINDS[kind][:3]
    numeral = roman.romanNumeralFromChord(chord.Chord([spell(pitch.Pitch(midi=60 + root + i)) for i in triad]), k).romanNumeral
    n = note.Note(b, quarterLength=stop - start)
    n.addLyric(numeral + "o" * (kind == "diminished") + {"dominant-seventh": "7", "minor-seventh": "7", "major-seventh": "maj7"}.get(kind, "") + "sus4" * (kind == "suspended-fourth"))
    bottom.insert(start, n)

# Melody: snap to 16ths, one note at a time (each cut at the next onset), nothing before the trimmed lead.
snapped = [(round(s * 4) / 4 - lead, round(e * 4) / 4 - lead, p) for s, e, p in melody]
snapped = [(s, e, p) for s, e, p in snapped if e > s and s >= 0]
for i, (s, e, p) in enumerate(snapped):
    if i + 1 < len(snapped):
        e = min(e, snapped[i + 1][0])
    if e > s:
        top.insert(s, note.Note(spell(pitch.Pitch(midi=p)), quarterLength=e - s))
if top.highestTime < segments[-1][1]:  # the song can end on accompaniment: give the chords bars to sit in
    top.insert(top.highestTime, note.Rest(quarterLength=segments[-1][1] - top.highestTime))

score = stream.Score()
score.insert(0, metadata.Metadata(title=Path(dst).stem, composer=""))
score.insert(0, top)
score.insert(0, bottom)
score.insert(0, layout.StaffGroup([top, bottom], symbol="brace"))
score.makeNotation(inPlace=True)
bars = list(top.getElementsByClass("Measure"))
for start, symbol in symbols:
    bars[int(start // 4)].insert(start % 4, symbol)
score.write("musicxml", fp=dst)
print("wrote", dst)
