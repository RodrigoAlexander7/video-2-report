"""Esqueleto de un proyecto html-slides (``project.toml`` + ``content/slides.toml``)."""

from __future__ import annotations

from pathlib import Path

PROJECT_TOML = """\
# Proyecto html-slides: diapositivas HTML (tema claro, sin animaciones) + PDF.
# Se construye con:  python main.py run <esta carpeta> --pipeline html-slides

pipeline = "html-slides"

[slides]
title = "Título de la presentación"
course = "Nombre de la asignatura"
instructor = "Grado. Nombres y apellidos del docente"
semester = "2026-B"
authors = [
  "Apellidos, Nombres",
]
# Opcionales (los valores por defecto se muestran):
# subtitle = "Subtítulo"
# theme = "academic-light"     # temas en src/slides_engine/assets/themes/
# institutional = true         # logos UNSA/EPIS en portada y pie
# footer = "Curso · Tema"      # texto del pie (por defecto, el curso)
# lang = "es"                  # "es" | "en" (etiquetas Figura/Tabla/...)
# date = "2026-01-31"          # por defecto, hoy
# file = "content/slides.toml"

# Si esta carpeta ya tiene [theory] o [lab], course/instructor/semester/members se heredan de ahí.

[build]
# name = "mi-deck"             # nombre de los archivos (se le agrega "-slides")
# pdf = true                   # false: solo HTML
# check = true                 # medir desbordes en Chrome antes de exportar
"""

SLIDES_TOML = """\
# Una tabla [[slide]] por diapositiva. Layouts: title, section, bullets, two-col, figure, table, code, quote, stats, closing.
# La primera debe ser 'title'. Texto en línea: **negrita** y `código`. Ver .agents/skills/academic-slides-builder.

[[slide]]
layout = "title"
title = "Título de la presentación"
subtitle = "TODO(autor): subtítulo o contexto"

[[slide]]
layout = "bullets"
title = "Objetivos"
items = [
  "TODO(autor): primer objetivo, en una frase",
  "TODO(autor): segundo objetivo",
]
notes = "TODO(autor): notas del expositor (no aparecen en el PDF)."

[[slide]]
layout = "closing"
title = "Gracias"
subtitle = "Preguntas"
"""


def scaffold(project_dir) -> Path:
    """Crea el esqueleto sin pisar archivos existentes. Devuelve la carpeta del proyecto."""
    pdir = Path(project_dir).resolve()
    (pdir / "content").mkdir(parents=True, exist_ok=True)
    for rel, text in (("project.toml", PROJECT_TOML), ("content/slides.toml", SLIDES_TOML)):
        target = pdir / rel
        if target.exists():
            raise FileExistsError(f"{target} ya existe; no se sobrescribe.")
        target.write_text(text, encoding="utf-8")
    return pdir
