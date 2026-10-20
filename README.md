# SheetSongs

Piano arrangements built with an LLM as collaborator and teacher: MusicXML scores, music21 checks, and a personal style doc.

## Cover drafts

Three piano-cover models turn an audio file into a rough MIDI draft to start an arrangement from:

```powershell
python tools/cover.py amtapc  sources/song.wav sources/out/song_amtapc.mid level2
python tools/cover.py etude   sources/song.wav sources/out/song_etude.mid 111
python tools/cover.py pop2piano sources/song.wav sources/out/song_pop2piano.mid composer1
```

Run `python tools/cover.py` with no arguments for the style options. Pop2Piano runs in Docker (Docker Desktop must be running). The model code, weights and `sources/` are gitignored; see `.gitignore`.

Setup notes (Windows, RTX 50-series): AMT-APC uses torch 2.11 cu128; Etude uses torch 2.8 cu128 with the Demucs backend (`tools/etude-windows.yaml`); Pop2Piano runs in the `sheetsongs-pop2piano` image built from `tools/pop2piano/`.
