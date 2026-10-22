#!/usr/bin/env python3
"""Compatibilidad: transcribe varios WAV reutilizando un único modelo cargado.

Uso: python -m src.video_engine.transcribe_batch <audio.wav> <prefijo> [<audio2.wav> <prefijo2> ...]
Sin argumentos procesa los dos audios por defecto de output/.cache/.
"""
import sys
import time

from .transcriber import load_model, transcribe_audio

DEFAULTS = [
    ("output/.cache/audio_bloques.wav", "output/.cache/transcription_bloques"),
    ("output/.cache/audio_version1.wav", "output/.cache/transcription_version1"),
]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and len(argv) % 2:
        sys.exit("Uso: transcribe_batch <audio> <prefijo> [<audio> <prefijo> ...]")
    pairs = list(zip(argv[::2], argv[1::2])) if argv else DEFAULTS
    t0 = time.time()
    model = load_model()
    for audio, prefix in pairs:
        transcribe_audio(audio, prefix, model)
    print(f"\nTiempo total: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
