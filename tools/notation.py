"""Score helpers shared by tidy.py and leadsheet.py."""
from music21 import clef, key, meter, pitch, stream, tempo


def speller(k):
    """Spell MIDI-parsed pitches as key k does: its diatonic names, plus the raised 7th in minor."""
    names = {p.pitchClass: p.name for p in k.pitches}
    if k.mode == "minor":
        leading = k.pitchFromDegree(7).transpose("A1")
        names[leading.pitchClass] = leading.name

    def spell(p):
        q = pitch.Pitch(names.get(p.pitchClass, p.name), octave=4)
        q.octave += (p.midi - q.midi) // 12  # e.g. B4 spelled C-flat lives in octave 5
        assert q.midi == p.midi, (p, q)
        return q

    return spell


def staff(name, k, bass=False, bpm=None):
    """An empty 4/4 part with a fixed clef and key signature (and the tempo mark on the top staff)."""
    part = stream.Part(id=name)
    part.insert(0, clef.BassClef() if bass else clef.TrebleClef())
    part.insert(0, key.KeySignature(k.sharps))
    part.insert(0, meter.TimeSignature("4/4"))
    if bpm:
        part.insert(0, tempo.MetronomeMark(number=float(bpm)))
    return part
