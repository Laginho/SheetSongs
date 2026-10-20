"""Generate a piano-cover draft (MIDI) from an audio file with one of three models.

Usage: python tools/cover.py {amtapc,etude,pop2piano} input_audio output.mid [style]

style:
  amtapc     level1 | level2 | level3          (default level2; higher = denser)
  etude      three digits 0-2: polyphony, rhythm, sustain, e.g. 112 (default 111)
  pop2piano  composer1 ... composer21          (default composer1; arranger styles from its training set)
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

if len(sys.argv) < 4:
    sys.exit(__doc__)
model, src, dst = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
style = sys.argv[4] if len(sys.argv) > 4 else None
if not src.is_file():
    sys.exit(f"input not found: {src}")
dst.parent.mkdir(parents=True, exist_ok=True)
env = {**os.environ, "PYTHONUTF8": "1"}  # both repos read JSON with the platform default encoding

if model == "amtapc":
    cmd = [TOOLS / "amt-apc/.venv/Scripts/python", TOOLS / "run_amtapc.py", src, "-o", dst]
    subprocess.run(cmd + (["-s", style] if style else []), check=True, env=env)

elif model == "etude":
    p, r, s = style or "111"
    repo = TOOLS / "etude"
    subprocess.run(
        [repo / ".venv/Scripts/python", "infer.py", "--config", TOOLS / "etude-windows.yaml",
         "--input", src, "--output_name", "cover", "--polyphony", p, "--rhythm", r, "--sustain", s],
        check=True, cwd=repo, env=env,
    )
    shutil.copy(repo / "outputs/infer/cover.mid", dst)

elif model == "pop2piano":
    cache = TOOLS / "pop2piano/hf-cache"
    subprocess.run(
        ["docker", "run", "--rm", "--gpus", "all",
         "-v", f"{src.parent}:/in", "-v", f"{dst.parent}:/out", "-v", f"{cache}:/root/.cache/huggingface",
         "sheetsongs-pop2piano", f"/in/{src.name}", f"/out/{dst.name}"] + ([style] if style else []),
        check=True,
    )

else:
    sys.exit(__doc__)
