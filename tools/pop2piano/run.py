# Usage: run.py input_audio output.mid [composer1..composer21]
import sys
import librosa, torch
from transformers import Pop2PianoForConditionalGeneration, Pop2PianoProcessor

src, dst = sys.argv[1], sys.argv[2]
composer = sys.argv[3] if len(sys.argv) > 3 else "composer1"
device = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", device)

model = Pop2PianoForConditionalGeneration.from_pretrained("sweetcocoa/pop2piano").to(device)
processor = Pop2PianoProcessor.from_pretrained("sweetcocoa/pop2piano")
audio, sr = librosa.load(src, sr=44100)
inputs = processor(audio=audio, sampling_rate=sr, return_tensors="pt")
out = model.generate(input_features=inputs["input_features"].to(device), composer=composer)
midi = processor.batch_decode(token_ids=out.cpu(), feature_extractor_output=inputs)["pretty_midi_objects"][0]
midi.write(dst)
print("wrote", dst)
