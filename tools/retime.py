"""Put a cover draft on the song's real beat grid so MuseScore shows sensible bars.

The models write notes at real-time seconds under a placeholder 120 bpm. This rewrites the file at the
song's tempo in 4/4, shifting every note so the given downbeat falls on a barline (a short rest may
open the piece). Sounding timing is unchanged.

Usage: python tools/retime.py in.mid out.mid bpm downbeat_seconds [phase_ref.mid]
  downbeat is rough and gets snapped to the nearest beat; phase_ref (e.g. the piano draft, when retiming the
  vocal melody) takes the beat phase from another file so both land on the same grid
"""
import sys

import numpy as np
import pretty_midi

if len(sys.argv) not in (5, 6):
    sys.exit(__doc__)
src, dst, bpm, downbeat = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
old = pretty_midi.PrettyMIDI(src)
ref = pretty_midi.PrettyMIDI(sys.argv[5]) if len(sys.argv) == 6 else old
beat, bar = 60 / bpm, 4 * 60 / bpm
# Snap the rough downbeat to this file's own beat phase (mean onset angle on the beat cycle):
# models disagree by tens of ms, so one shared downbeat would leave some drafts off the grid.
onsets = np.array([n.start for i in ref.instruments for n in i.notes])
phase = np.angle(np.exp(2j * np.pi * onsets / beat).mean()) / (2 * np.pi) * beat
downbeat = phase + round((downbeat - phase) / beat) * beat
shift = (bar - downbeat % bar) % bar
assert abs(((downbeat + shift) / bar) - round((downbeat + shift) / bar)) < 1e-9

new = pretty_midi.PrettyMIDI(initial_tempo=bpm)
new.time_signature_changes.append(pretty_midi.TimeSignature(4, 4, 0))
for inst in old.instruments:
    out = pretty_midi.Instrument(inst.program, inst.is_drum, inst.name)
    out.notes = [pretty_midi.Note(n.velocity, n.pitch, n.start + shift, n.end + shift) for n in inst.notes]
    out.control_changes = [pretty_midi.ControlChange(c.number, c.value, c.time + shift) for c in inst.control_changes]
    new.instruments.append(out)
new.write(dst)
print(f"{dst}: {bpm:g} bpm, shifted {shift:.3f}s, {sum(len(i.notes) for i in new.instruments)} notes")
