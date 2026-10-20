# Pop2Piano needs essentia, which has no Windows build, so it runs in Linux.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
RUN pip install --no-cache-dir "essentia==2.1b6.dev1389" librosa pretty_midi scipy transformers soundfile resampy
COPY run.py /app/run.py
ENTRYPOINT ["python", "/app/run.py"]
