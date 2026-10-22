# -*- coding: utf-8 -*-
"""Modelo y validación del contenido de un deck (``content/slides.toml``).

Cada diapositiva declara un ``layout`` cerrado y sus campos. Los presupuestos de contenido
(palabras, viñetas, líneas) existen para que nada se desborde: se rechazan al cargar, antes de renderizar.
"""

from __future__ import annotations

import difflib
import re
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

LAYOUTS = ("title", "section", "bullets", "two-col", "figure", "table", "code", "quote", "stats", "closing")
DEFAULT_THEME = "academic-light"
DEFAULT_SLIDES_FILE = "content/slides.toml"

META_FALLBACK_TABLES = ("theory", "lab")   # [slides] hereda curso, docente, integrantes... de estas tablas


class DeckError(ValueError):
    """Contenido inválido. ``problems`` conserva cada hallazgo para mostrarlos todos de una vez."""

    def __init__(self, problems: List[str]):
        self.problems = list(problems)
        super().__init__("\n".join(f"  - {p}" for p in self.problems))


@dataclass
class Deck:
    meta: Dict[str, Any]
    slides: List[Dict[str, Any]] = field(default_factory=list)
    source: Optional[Path] = None


# --------------------------------------------------------------------------- utilidades
def _strip_markup(text: str) -> str:
    return re.sub(r"(\*\*|`)", "", text)


def chars(text: Any) -> int:
    """Caracteres visibles (sin **negrita** ni `código`): lo que de verdad ocupa ancho en la diapositiva."""
    return len(_strip_markup(str(text)).strip())


# Presupuestos de contenido, calibrados con el peor caso en Chrome a 1920x1080 (ver tests/test_slides.py).
LIMITS = {
    "cover_title": 90, "cover_subtitle": 170, "title": 85, "section_title": 60, "section_subtitle": 120,
    "lead": 150, "bullet": 110, "bullets_total": 520, "col_heading": 40, "col_item": 60,
    "caption": 170, "point": 80, "cell": 40, "row_total": 90, "quote": 240, "quote_author": 70,
    "stat_label": 50, "closing_title": 50, "closing_subtitle": 150, "closing_item": 90, "notes": 1200,
    "code_lines": 12, "code_width": 80,
}


class _Checker:
    """Acumula errores de UNA diapositiva con el prefijo ``diapositiva N (layout)``."""

    def __init__(self, index: int, slide: Mapping[str, Any], errors: List[str]):
        self.s, self.errors = slide, errors
        self.prefix = f"diapositiva {index} ({slide.get('layout', '?')})"

    def err(self, msg: str) -> None:
        self.errors.append(f"{self.prefix}: {msg}")

    def text(self, container: Mapping[str, Any], key: str, max_chars: int, *, required: bool = False,
             label: Optional[str] = None) -> Optional[str]:
        label = label or key
        value = container.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                self.err(f"falta '{label}'")
            return None
        if not isinstance(value, str):
            self.err(f"'{label}' debe ser texto")
            return None
        n = chars(value)
        if n > max_chars:
            self.err(f"'{label}' tiene {n} caracteres (máximo {max_chars}); resume o divídelo")
        return value

    def items(self, container: Mapping[str, Any], key: str, lo: int, hi: int, max_chars: int, *,
              label: Optional[str] = None) -> List[str]:
        label = label or key
        value = container.get(key)
        if not isinstance(value, list) or not all(isinstance(i, str) and i.strip() for i in value):
            self.err(f"'{label}' debe ser una lista de textos no vacíos")
            return []
        if not lo <= len(value) <= hi:
            self.err(f"'{label}' tiene {len(value)} elementos (permitido {lo}-{hi})")
        for i, it in enumerate(value, 1):
            n = chars(it)
            if n > max_chars:
                self.err(f"'{label}'[{i}] tiene {n} caracteres (máximo {max_chars})")
        return value


# --------------------------------------------------------------------------- reglas por layout
def _title(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["cover_title"], required=True)
    c.text(c.s, "subtitle", LIMITS["cover_subtitle"])


def _section(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["section_title"], required=True)
    c.text(c.s, "subtitle", LIMITS["section_subtitle"])
    c.text(c.s, "number", 3)


def _bullets(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["title"], required=True)
    c.text(c.s, "lead", LIMITS["lead"])
    items = c.items(c.s, "items", 1, 6, LIMITS["bullet"])
    total = sum(chars(i) for i in items) + (chars(c.s["lead"]) if isinstance(c.s.get("lead"), str) else 0)
    if total > LIMITS["bullets_total"]:
        c.err(f"el texto suma {total} caracteres (máximo {LIMITS['bullets_total']}); usa menos texto o separa en dos diapositivas")


def _two_col(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["title"], required=True)
    for side in ("left", "right"):
        box = c.s.get(side)
        if not isinstance(box, dict):
            c.err(f"falta la tabla '{side}' (heading, items)")
            continue
        unknown = set(box) - {"heading", "items"}
        if unknown:
            c.err(f"'{side}' tiene campos desconocidos: {', '.join(sorted(unknown))}")
        c.text(box, "heading", LIMITS["col_heading"], required=True, label=f"{side}.heading")
        c.items(box, "items", 1, 4, LIMITS["col_item"], label=f"{side}.items")


def _figure(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["title"], required=True)
    has_image, has_ev = bool(c.s.get("image")), bool(c.s.get("evidence_id"))
    if has_image == has_ev:
        c.err("indica exactamente uno de 'image' o 'evidence_id'")
    c.text(c.s, "caption", LIMITS["caption"], required=True)
    if "points" in c.s:
        c.items(c.s, "points", 1, 3, LIMITS["point"])


def _table(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["title"], required=True)
    header, rows = c.s.get("header"), c.s.get("rows")
    if not isinstance(header, list) or not 2 <= len(header) <= 5 or not all(isinstance(h, str) for h in header):
        c.err("'header' debe ser una lista de 2 a 5 textos")
        return
    if not isinstance(rows, list) or not 1 <= len(rows) <= 6:
        c.err(f"'rows' debe tener de 1 a 6 filas (tiene {len(rows) if isinstance(rows, list) else 0})")
        return
    for r, row in enumerate(rows, 1):
        if not isinstance(row, list) or len(row) != len(header):
            c.err(f"fila {r}: debe tener {len(header)} celdas")
            continue
        total = sum(chars(cell) for cell in row)
        if total > LIMITS["row_total"] or any(chars(cell) > LIMITS["cell"] for cell in row):
            c.err(f"fila {r}: {total} caracteres (máximo {LIMITS['row_total']} por fila y {LIMITS['cell']} por celda)")
    c.text(c.s, "caption", LIMITS["caption"])


def _code(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["title"], required=True)
    has_code, has_file = isinstance(c.s.get("code"), str), bool(c.s.get("file"))
    if has_code == has_file:
        c.err("indica exactamente uno de 'code' o 'file'")
    if has_code:
        lines = c.s["code"].strip("\n").splitlines()
        check_code_block(c, lines)
    if "lines" in c.s and not re.fullmatch(r"\d+(-\d+)?", str(c.s["lines"])):
        c.err("'lines' debe ser 'N' o 'N-M' (p. ej. \"10-24\")")
    c.text(c.s, "caption", LIMITS["caption"])
    c.text(c.s, "language", 12)


def check_code_block(c: _Checker, lines: List[str]) -> None:
    if len(lines) > LIMITS["code_lines"]:
        c.err(f"el código tiene {len(lines)} líneas (máximo {LIMITS['code_lines']}); recorta con 'lines' o muestra solo lo esencial")
    too_wide = [i for i, ln in enumerate(lines, 1) if len(ln.expandtabs(4)) > LIMITS["code_width"]]
    if too_wide:
        c.err(f"líneas de código de más de {LIMITS['code_width']} caracteres: {', '.join(map(str, too_wide[:5]))}")


def _quote(c: _Checker) -> None:
    c.text(c.s, "text", LIMITS["quote"], required=True)
    c.text(c.s, "author", LIMITS["quote_author"])


def _stats(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["title"], required=True)
    items = c.s.get("items")
    if not isinstance(items, list) or not 2 <= len(items) <= 4:
        c.err("'items' debe tener de 2 a 4 indicadores {value, label}")
        return
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict) or set(it) - {"value", "label"}:
            c.err(f"items[{i}] debe ser una tabla con 'value' y 'label'")
            continue
        value = str(it.get("value", "")).strip()
        if not value or len(value) > 6:
            c.err(f"items[{i}].value debe tener de 1 a 6 caracteres")
        c.text(it, "label", LIMITS["stat_label"], required=True, label=f"items[{i}].label")


def _closing(c: _Checker) -> None:
    c.text(c.s, "title", LIMITS["closing_title"], required=True)
    c.text(c.s, "subtitle", LIMITS["closing_subtitle"])
    if "items" in c.s:
        c.items(c.s, "items", 1, 4, LIMITS["closing_item"])


RULES: Dict[str, Callable[[_Checker], None]] = {
    "title": _title, "section": _section, "bullets": _bullets, "two-col": _two_col, "figure": _figure,
    "table": _table, "code": _code, "quote": _quote, "stats": _stats, "closing": _closing,
}
ALLOWED: Dict[str, set] = {
    "title": {"title", "subtitle"},
    "section": {"title", "subtitle", "number"},
    "bullets": {"title", "lead", "items"},
    "two-col": {"title", "left", "right"},
    "figure": {"title", "image", "evidence_id", "caption", "points"},
    "table": {"title", "header", "rows", "caption"},
    "code": {"title", "code", "file", "lines", "language", "caption"},
    "quote": {"text", "author"},
    "stats": {"title", "items"},
    "closing": {"title", "subtitle", "items"},
}
COMMON_KEYS = {"layout", "notes"}


def validate_slides(slides: List[Dict[str, Any]]) -> List[str]:
    """Todos los problemas de contenido de la lista de diapositivas (vacía = correcto)."""
    errors: List[str] = []
    if not slides:
        return ["no hay diapositivas: agrega al menos un [[slide]] en el archivo de contenido"]
    for i, slide in enumerate(slides, 1):
        layout = slide.get("layout")
        if layout not in LAYOUTS:
            hint = difflib.get_close_matches(str(layout), LAYOUTS, n=1)
            errors.append(f"diapositiva {i}: layout '{layout}' desconocido"
                          + (f" (¿'{hint[0]}'?)" if hint else f"; disponibles: {', '.join(LAYOUTS)}"))
            continue
        c = _Checker(i, slide, errors)
        for key in sorted(set(slide) - ALLOWED[layout] - COMMON_KEYS):
            hint = difflib.get_close_matches(key, ALLOWED[layout], n=1)
            c.err(f"campo desconocido '{key}'" + (f" (¿'{hint[0]}'?)" if hint else ""))
        if "notes" in slide:
            c.text(slide, "notes", LIMITS["notes"])
        RULES[layout](c)
    if slides[0].get("layout") != "title":
        errors.append("la primera diapositiva debe usar el layout 'title'")
    return errors


# --------------------------------------------------------------------------- carga desde project.toml
def _authors(raw: Any) -> List[str]:
    out = []
    for m in raw or []:
        out.append(m.get("name", "") if isinstance(m, dict) else str(m))
    return [a for a in out if a]


def build_meta(project: Mapping[str, Any], name_fallback: str) -> Dict[str, Any]:
    """Metadatos del deck: [slides] manda; el resto se hereda de [theory]/[lab] cuando existen."""
    slides = dict(project.get("slides") or {})
    inherited: Dict[str, Any] = {}
    for table in META_FALLBACK_TABLES:
        for k, v in (project.get(table) or {}).items():
            inherited.setdefault(k, v)
    pick = lambda key, default=None: slides.get(key, inherited.get(key, default))  # noqa: E731

    meta = {
        "title": pick("title"), "subtitle": slides.get("subtitle"), "course": pick("course", ""),
        "instructor": pick("instructor", ""), "semester": pick("semester", ""),
        "authors": _authors(slides.get("authors", pick("members", []))),
        "date": str(slides.get("date") or date.today().isoformat()),
        "theme": slides.get("theme", DEFAULT_THEME), "institutional": bool(slides.get("institutional", True)),
        "footer": slides.get("footer"), "lang": slides.get("lang", "es"), "ratio": str(slides.get("ratio", "16:9")),
        "file": slides.get("file", DEFAULT_SLIDES_FILE), "name": name_fallback,
    }
    meta["footer"] = meta["footer"] or meta["course"] or str(meta["title"] or "")
    return meta


def load_deck(project_dir: Path, project: Mapping[str, Any], name: str) -> Deck:
    """Lee ``[slides]`` de project.toml y el archivo de contenido; valida todo antes de devolver."""
    project_dir = Path(project_dir).resolve()
    meta = build_meta(project, name)
    errors: List[str] = []
    if not meta["title"]:
        errors.append("project.toml: falta 'title' en [slides]")
    if meta["ratio"] != "16:9":
        errors.append(f"project.toml: ratio '{meta['ratio']}' no soportado (solo 16:9)")

    source = project_dir / meta["file"]
    slides: List[Dict[str, Any]] = []
    if not source.is_file():
        errors.append(f"no existe el contenido: {source} (crea el esqueleto con `main.py slides new <carpeta>`)")
    else:
        with source.open("rb") as fh:
            try:
                data = tomllib.load(fh)
            except tomllib.TOMLDecodeError as exc:
                raise DeckError([f"{source}: TOML inválido: {exc}"]) from exc
        slides = [dict(s) for s in data.get("slide", [])]
        errors.extend(validate_slides(slides))
    if errors:
        raise DeckError(errors)
    return Deck(meta=meta, slides=slides, source=source)
