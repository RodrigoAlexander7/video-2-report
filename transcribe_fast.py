import sys
import time
import json
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel

audio_path = "/home/totora/Documents/PROFESIONAL/video-report/audio.wav"
print("Reading audio with soundfile...")
audio_data, sr = sf.read(audio_path, dtype="float32")
if audio_data.ndim > 1:
    audio_data = audio_data.mean(axis=1)

print(f"Audio loaded: {len(audio_data)/sr:.2f} seconds at {sr}Hz.")

print("Loading faster-whisper model (small, cpu, int8)...")
t0 = time.time()
model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=12)
print(f"Model loaded in {time.time() - t0:.2f}s. Transcribing audio numpy array...")

t1 = time.time()
segments, info = model.transcribe(audio_data, language="es", beam_size=3)
print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

with open("transcription.txt", "w", encoding="utf-8") as f_txt, open("transcription_segments.json", "w", encoding="utf-8") as f_json:
    all_segs = []
    for s in segments:
        seg_data = {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        all_segs.append(seg_data)
        line = f"[{seg_data['start']:06.2f} -> {seg_data['end']:06.2f}] {seg_data['text']}\n"
        f_txt.write(line)
        f_txt.flush()
        print(line, end="")
    json.dump(all_segs, f_json, ensure_ascii=False, indent=2)

print(f"\nDone transcription in {time.time() - t1:.2f}s!")
