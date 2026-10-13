#!/usr/bin/env python3
"""Compatibilidad: transcribe un WAV con transcriber.transcribe_audio.

Uso: python -m src.video_engine.transcribe_fast <audio.wav> [prefijo_salida]
"""
import sys

from .transcriber import transcribe_audio


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        sys.exit("Uso: transcribe_fast <audio.wav> [prefijo_salida]")
    audio = argv[0]
    prefix = argv[1] if len(argv) > 1 else audio.rsplit(".", 1)[0]
    transcribe_audio(audio, prefix)


if __name__ == "__main__":
    main()
