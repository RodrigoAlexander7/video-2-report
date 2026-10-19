# -*- coding: utf-8 -*-
"""Decks de prueba para html-slides: contenido mínimo válido y peor caso permitido por los presupuestos."""

from __future__ import annotations

from pathlib import Path
from typing import List

from src.slides_engine.model import LIMITS

_PHRASE = ("la verificación institucional de requisitos funcionales garantiza trazabilidad completa entre "
           "estándares, casos de prueba, evidencias reproducibles y decisiones de aceptación del alcance ")


def fill(n: int) -> str:
    """Texto realista (palabras de ~7 letras) de ``n`` caracteres como máximo, cortado en límite de palabra."""
    text = (_PHRASE * (n // len(_PHRASE) + 2)).strip()
    if len(text) <= n:
        return text
    cut = text[:n]
    return cut if text[n] == " " else cut[:cut.rfind(" ")]


def _arr(xs: List[str]) -> str:
    return "[" + ", ".join('"%s"' % x for x in xs) + "]"


def worst_case_toml(image: Path, code_file: str = "code/big.txt") -> str:
    """Una diapositiva por layout, cada una con el máximo de contenido que el modelo acepta."""
    L = LIMITS
    items = fill(L["bullet"])
    per_item = L["bullets_total"] // 6
    return f'''
[[slide]]
layout = "title"
title = "{fill(L['cover_title'])}"
subtitle = "{fill(L['cover_subtitle'])}"

[[slide]]
layout = "section"
number = "99"
title = "{fill(L['section_title'])}"
subtitle = "{fill(L['section_subtitle'])}"

[[slide]]
layout = "bullets"
title = "{fill(L['title'])}"
lead = "{fill(40)}"
items = {_arr([fill(min(per_item, L['bullet']))] * 6)}

[[slide]]
layout = "bullets"
title = "{fill(L['title'])}"
items = {_arr([items] * 4)}

[[slide]]
layout = "two-col"
title = "{fill(L['title'])}"
[slide.left]
heading = "{fill(L['col_heading'])}"
items = {_arr([fill(L['col_item'])] * 4)}
[slide.right]
heading = "{fill(L['col_heading'])}"
items = {_arr([fill(L['col_item'])] * 4)}

[[slide]]
layout = "figure"
title = "{fill(L['title'])}"
image = "{image.as_posix()}"
caption = "{fill(L['caption'])}"
points = {_arr([fill(L['point'])] * 3)}

[[slide]]
layout = "table"
title = "{fill(L['title'])}"
header = {_arr([fill(L['row_total'] // 5)] * 5)}
rows = [{", ".join(_arr([fill(L['row_total'] // 5)] * 5) for _ in range(6))}]
caption = "{fill(L['caption'])}"

[[slide]]
layout = "code"
title = "{fill(L['title'])}"
file = "{code_file}"
language = "python"
caption = "{fill(L['caption'])}"

[[slide]]
layout = "quote"
text = "{fill(L['quote'])}"
author = "{fill(L['quote_author'])}"

[[slide]]
layout = "stats"
title = "{fill(L['title'])}"
items = [{", ".join('{value = "123456", label = "%s"}' % fill(L['stat_label']) for _ in range(4))}]

[[slide]]
layout = "closing"
title = "{fill(L['closing_title'])}"
subtitle = "{fill(L['closing_subtitle'])}"
items = {_arr([fill(L['closing_item'])] * 4)}
'''


def write_project(root: Path, slides_toml: str, *, institutional: bool = True) -> Path:
    """Crea project.toml + content/slides.toml (+ code/big.txt para el peor caso) y devuelve la carpeta."""
    (root / "content").mkdir(parents=True, exist_ok=True)
    (root / "code").mkdir(exist_ok=True)
    (root / "code" / "big.txt").write_text("\n".join("m" * LIMITS["code_width"] for _ in range(LIMITS["code_lines"])), encoding="utf-8")
    (root / "project.toml").write_text(
        'pipeline = "html-slides"\n[slides]\ntitle = "Deck de prueba"\ncourse = "Curso de prueba"\n'
        'instructor = "Docente de prueba"\nsemester = "2026-B"\nauthors = ["Autor Uno", "Autor Dos"]\n'
        f'institutional = {"true" if institutional else "false"}\n', encoding="utf-8")
    (root / "content" / "slides.toml").write_text(slides_toml, encoding="utf-8")
    return root
