# -*- coding: utf-8 -*-
"""Esqueleto de un caso `unity-lab` y esquema (outline) de los pasos a partir de la transcripción del video."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_TOML = '''pipeline = "unity-lab"

[unity]
template = "input-template.docx"          # plantilla EPIS (tabla INFORMACIÓN BÁSICA ... REFERENCIAS)
video = "video.mp4"
title = "Título de la práctica"
number = "00"
date = "01/01/2026"
members = ["Nombres Apellidos"]
# course, term = "2026 - B", level = "Octavo VIII", time = "12:00:00", instructor, video_link
# theme = "dark"                         # imágenes de código: "dark" (por defecto) o "light"
# ocr_langs = "eng"                      # idioma de la interfaz de Unity ("eng", "spa" o "eng+spa")
'''

REPORT_TOML = '''# Un [[block]] por paso. Cada paso: 1-2 frases en primera persona del plural y su imagen.
# Tiempos del video: 125, "2:05" o "1:02:05". El código sale del archivo real: file + lines (no se copia a mano).

[[block]]
kind = "heading"
text = "Configurar el Rigidbody"

[[block]]
kind = "step"
text = "Agregamos un Rigidbody al GameObject raíz del personaje."
[block.figure]
id = "rigidbody"
t = "2:05"
expect = ["Rigidbody"]
caption = "Componente Rigidbody en el Inspector."
[block.figure.crop]
panel = "inspector"
desde = "Rigidbody"
hasta = "Capsule Collider"

[[block]]
kind = "step"
text = "Escribimos la lectura de teclas en el método Update."
[block.code]
id = "update"
file = "code/Controller.cs"
lines = "10-24"

[[question]]
q = "¿Qué función cumple el componente Rigidbody?"
a = "Permite que el motor de física controle el objeto: masa, gravedad y respuesta a fuerzas."

[[conclusion]]
text = "Conclusión basada en lo observado en la práctica."

[[reference]]
text = "Unity Technologies, \\"Rigidbody,\\" Unity Scripting API, 2026. [En línea]. Disponible en: https://docs.unity3d.com/ScriptReference/Rigidbody.html"
'''


def scaffold(project_dir) -> Path:
    project_dir = Path(project_dir)
    if (project_dir / "project.toml").exists():
        raise FileExistsError(f"{project_dir / 'project.toml'} ya existe")
    (project_dir / "content").mkdir(parents=True, exist_ok=True)
    (project_dir / "code").mkdir(exist_ok=True)
    (project_dir / "project.toml").write_text(PROJECT_TOML, encoding="utf-8")
    (project_dir / "content" / "report.toml").write_text(REPORT_TOML, encoding="utf-8")
    return project_dir


_START = re.compile(r"^\W*(ahora|luego|despu[eé]s|siguiente|vamos a|primero|segundo|tercero|entonces|listo|bien|pasamos|empezamos)\b", re.I)


def find_transcript(project_dir: Path, meta: Dict[str, Any]) -> Optional[Path]:
    from ..core.registry import REPO_ROOT, resolve_slug
    names = [meta["transcript"]] if meta.get("transcript") else []
    candidates = [project_dir / n for n in names] + [project_dir / "transcription.json",
                                                    REPO_ROOT / "output" / resolve_slug(project_dir) / "cache" / "transcription.json"]
    return next((c for c in candidates if c.is_file()), None)


def outline(project_dir, gap: float = 3.0, min_len: float = 12.0) -> List[Dict[str, Any]]:
    """Agrupa los segmentos de la transcripción en pasos candidatos: ``[{t, end, text}]`` (solo orienta; no escribe el reporte)."""
    from .model import load_meta
    from ..video_engine.frames import format_time
    project_dir = Path(project_dir).resolve()
    meta = load_meta(project_dir)
    path = find_transcript(project_dir, meta)
    if path is None:
        raise FileNotFoundError("no hay transcripción: genera una con `python main.py transcribe <video>` "
                                "y guarda el .json como transcription.json en la carpeta del caso (o define [unity] transcript)")
    segments = json.loads(path.read_text(encoding="utf-8"))
    groups: List[Dict[str, Any]] = []
    for seg in segments:
        text = seg["text"].strip()
        new = not groups or seg["start"] - groups[-1]["end"] >= gap or (_START.match(text) and seg["start"] - groups[-1]["t"] >= min_len)
        if new:
            groups.append({"t": seg["start"], "end": seg["end"], "text": text})
        else:
            groups[-1]["end"] = seg["end"]
            groups[-1]["text"] += " " + text
    for g in groups:
        g["when"] = format_time(g["t"])
    return groups
