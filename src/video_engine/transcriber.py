#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transcripción local y offline con faster-whisper.

Producto: <prefijo>.txt (con timestamps) y <prefijo>.json (segmentos start/end/text),
que consume timeline_analyzer. Los imports pesados son perezosos para que importar
este módulo no cargue el modelo ni ejecute nada.
"""

import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional


def extract_audio(video_path: str, wav_path: str, sample_rate: int = 16000) -> str:
    """Extrae el audio de un video a WAV mono con ffmpeg."""
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"No se encontró el video: {video_path}")
    os.makedirs(os.path.dirname(os.path.abspath(wav_path)), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", str(sample_rate), wav_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg falló extrayendo audio:\n{res.stderr[-800:]}")
    return wav_path


def load_model(model_size: str = "small", threads: int = 8):
    from faster_whisper import WhisperModel
    return WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=threads)


def transcribe_audio(audio_path: str, out_prefix: str, model: Optional[Any] = None,
                     language: str = "es", beam_size: int = 3, verbose: bool = True) -> List[Dict[str, Any]]:
    """Transcribe un WAV y escribe <out_prefix>.txt y <out_prefix>.json. Devuelve los segmentos."""
    import soundfile as sf

    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"No se encontró el audio: {audio_path}")
    model = model or load_model()
    audio, sr = sf.read(audio_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if verbose:
        print(f"--- Transcribiendo {audio_path} ({len(audio) / sr:.1f}s a {sr}Hz) ---")

    t0 = time.time()
    segments, info = model.transcribe(audio, language=language, beam_size=beam_size)
    if verbose:
        print(f"Idioma detectado: {info.language} ({info.language_probability:.2f})")

    os.makedirs(os.path.dirname(os.path.abspath(out_prefix)), exist_ok=True)
    result: List[Dict[str, Any]] = []
    with open(f"{out_prefix}.txt", "w", encoding="utf-8") as f_txt:
        for s in segments:
            seg = {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            result.append(seg)
            line = f"[{seg['start']:06.2f} -> {seg['end']:06.2f}] {seg['text']}\n"
            f_txt.write(line)
            f_txt.flush()
            if verbose:
                print(line, end="")
    with open(f"{out_prefix}.json", "w", encoding="utf-8") as f_json:
        json.dump(result, f_json, ensure_ascii=False, indent=2)
    if verbose:
        print(f"Guardado {out_prefix}.txt/.json en {time.time() - t0:.1f}s")
    return result


def transcribe_video(video_path: str, out_prefix: str, model_size: str = "small", threads: int = 8) -> List[Dict[str, Any]]:
    """Atajo: video -> WAV temporal (junto al prefijo) -> transcripción."""
    wav = f"{out_prefix}.wav"
    extract_audio(video_path, wav)
    return transcribe_audio(wav, out_prefix, load_model(model_size, threads))
