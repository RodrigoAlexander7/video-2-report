# -*- coding: utf-8 -*-
"""Búsqueda de Chrome/Chromium, compartida por los motores que lo usan (diapositivas, imágenes de código)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

CANDIDATES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")


class BrowserError(RuntimeError):
    """Chrome no está disponible o terminó con error."""


def find_chrome() -> str:
    env = os.environ.get("CHROME_BIN")
    if env:
        if not (Path(env).is_file() and os.access(env, os.X_OK)):
            raise BrowserError(f"CHROME_BIN apunta a un ejecutable inexistente: {env}")
        return env
    for name in CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    raise BrowserError("No se encontró Chrome/Chromium (probé: " + ", ".join(CANDIDATES) + "). "
                       "Instálalo o define CHROME_BIN=/ruta/al/ejecutable.")
