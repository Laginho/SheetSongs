"""Turn a retimed cover draft (MIDI) into a readable two-staff piano score (MusicXML).

Trims leading silence, snaps to a 16th grid (no triplets), splits hands by pitch, keeps one voice per hand,
fixes clefs to treble/bass and spells every note in the given key.

Usage: python tools/tidy.py in.mid out.musicxml key bpm [split_midi_pitch]
  key: music21 key name, e.g. e- (E-flat minor), G- (G-flat major); default split 60 (middle C goes right)
"""
import sys

from pathlib import Path

from music21 import chord, converter, key, layout, metadata, note, stream

from notation import speller, staff

if len(sys.argv) < 5:
    sys.exit(__doc__)
src, dst, key_name, bpm = sys.argv[1:5]
split = int(sys.argv[5]) if len(sys.argv) > 5 else 60
k = key.Key(key_name)
spell = speller(k)

draft = converter.parse(src, quantizePost=True, quarterLengthDivisors=(4,)).flatten()
events = [el for el in draft.notes if el.quarterLength > 0]  # zero-length = blips from quantizing
lead = events[0].offset // 4 * 4  # drop the empty bars before the first note
hands = {"rh": {}, "lh": {}}  # onset -> [(pitch, length)]
for el in events:
    for p in el.pitches:
        q = spell(p)
        hands["rh" if p.midi >= split else "lh"].setdefault(el.offset - lead, []).append((q, el.quarterLength))

score = stream.Score()
score.insert(0, metadata.Metadata(title=Path(dst).stem, composer=""))
for name in ("rh", "lh"):
    out = staff(name, k, bass=name == "lh", bpm=bpm if name == "rh" else None)
    # One voice per hand: each chord lasts until the hand's next onset (the pedal carries the rest).
    # shortcut: inner held notes (a melody over moving chords) get cut; restore voices by hand when arranging
    onsets = sorted(hands[name])
    for i, t in enumerate(onsets):
        notes = hands[name][t]
        length = max(d for _, d in notes)
        if i + 1 < len(onsets):
            length = min(length, onsets[i + 1] - t)
        pitches = sorted({q.nameWithOctave: q for q, _ in notes}.values(), key=lambda q: q.midi)
        out.insert(t, chord.Chord(pitches, quarterLength=length) if len(pitches) > 1 else note.Note(pitches[0], quarterLength=length))
    score.insert(0, out)
score.insert(0, layout.StaffGroup(list(score.parts), symbol="brace"))
score.makeNotation(inPlace=True)
score.write("musicxml", fp=dst)
print("wrote", dst)
