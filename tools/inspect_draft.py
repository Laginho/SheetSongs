"""Quick stats for piano-cover drafts: length, density, range, tempo and estimated key.

Usage: python tools/inspect_draft.py draft1.mid [draft2.mid ...]
"""
import sys

from music21 import converter

if len(sys.argv) < 2:
    sys.exit(__doc__)
for path in sys.argv[1:]:
    score = converter.parse(path, quantizePost=False)  # keep raw timing; the models' grids differ
    notes = list(score.flatten().notes)
    pitches = [p for n in notes for p in n.pitches]
    assert pitches, f"{path}: no notes"
    marks = score.metronomeMarkBoundaries()  # [(start, end, mark)], defaults to 120 bpm if none
    secs = sum((end - start) * 60 / mm.number for start, end, mm in marks)
    bpms = sorted({round(mm.number) for _, _, mm in marks})
    key = score.analyze("key")
    print(f"{path}\n  notes {len(pitches)} | ~{len(pitches) / secs:.1f}/s | range {min(pitches).nameWithOctave}-{max(pitches).nameWithOctave}"
          f" | tempo {bpms[:5]}{'...' if len(bpms) > 5 else ''} | key {key} (confidence {key.correlationCoefficient:.2f})")
