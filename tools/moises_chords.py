"""Export the chord track of a Moises Studio project as block chords in a MIDI file (real-time seconds of the song).

Moises keeps each open project as a Loro document under %APPDATA%/Moises/File System/000/t/01/ (one file, renamed on
every save). Chords sit on its tick grid (960 per quarter) under the project's tempo map, and the audio clips say
which second of the song plays at which tick, so the chords come out aligned to the original audio.
Then: retime.py with the piano draft as phase_ref, and leadsheet.py with the result as its chords file.
Needs: pip install loro

Usage: python tools/moises_chords.py project_file out.mid
"""
import sys

import pretty_midi
from loro import LoroDoc

if len(sys.argv) != 3:
    sys.exit(__doc__)
PPQ = 960
QUALITIES = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11),
             "sus4": (0, 5, 7), "dim": (0, 3, 6)}
ROOTS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

doc = LoroDoc()
with open(sys.argv[1], "rb") as f:
    doc.import_(f.read())
project = doc.get_deep_value()

tempo = sorted((t["time"], t["value"]) for t in project["tempo"])
assert all(t["interpolation"] == "hold" for t in project["tempo"]), "only step tempo changes are handled"


def seconds(tick):
    """Project time of a tick under the stepwise tempo map."""
    total = 0.0
    for i, (start, bpm) in enumerate(tempo):
        end = tempo[i + 1][0] if i + 1 < len(tempo) else float("inf")
        total += (min(tick, end) - start) / PPQ * 60 / bpm if tick > start else 0
    return total


# Clips (position in ticks) place a slice of the song, from cueIn seconds, on the timeline.
track = project["timeline"][0]["id"]
clips = sorted((seconds(c["position"]), c["cueIn"], c["cueOut"]) for c in project["clips"] if c["trackId"] == track)


def song_time(tick):
    at = seconds(tick)
    start, cue_in, _ = max((c for c in clips if c[0] <= at), default=clips[0])
    return cue_in + at - start


pm = pretty_midi.PrettyMIDI()
pad = pretty_midi.Instrument(0, name="moises chords")
for c in sorted(project["chord"], key=lambda c: c["start"]):
    name = c["value"]
    root = (ROOTS[name[0]] + {"#": 1, "b": -1}.get(name[1:2], 0)) % 12
    quality = name[1 + (name[1:2] in ("#", "b")):]
    assert quality in QUALITIES, f"unknown chord quality in {name!r}: add it to QUALITIES"
    a, b = song_time(c["start"]), song_time(c["end"])
    pad.notes.append(pretty_midi.Note(80, 36 + root, a, b))  # root in the bass
    pad.notes += [pretty_midi.Note(80, 60 + root + i, a, b) for i in QUALITIES[quality]]
pm.instruments.append(pad)
pm.write(sys.argv[2])
print(f"{sys.argv[2]}: {len(project['chord'])} chords, key {project['project'].get('rootKey')}")
