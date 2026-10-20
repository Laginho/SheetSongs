# Runs AMT-APC's infer with torchaudio.load swapped for soundfile:
# torchaudio >= 2.9 needs torchcodec + shared FFmpeg DLLs, which have no clean Windows/CUDA install.
# Usage: tools/amt-apc/.venv/Scripts/python -X utf8 tools/run_amtapc.py input.wav -o out.mid [-s level1|level2|level3]
import os, runpy, sys
from pathlib import Path
import soundfile as sf, torch, torchaudio

def _load(path, *args, **kwargs):
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return torch.from_numpy(x.T.copy()), sr

torchaudio.load = _load
# AMT-APC uses paths relative to its own folder, so make the user's paths absolute, then cd there.
args = sys.argv[1:]
for i, a in enumerate(args):
    if i == 0 or args[i - 1] in ("-o", "--output"):
        args[i] = str(Path(a).resolve())
repo = Path(__file__).resolve().parent / "amt-apc"
os.chdir(repo)
infer = repo / "infer"
sys.argv = [str(infer)] + args
runpy.run_path(str(infer), run_name="__main__")
