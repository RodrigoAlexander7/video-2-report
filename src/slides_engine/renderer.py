# -*- coding: utf-8 -*-
"""Renderer: ``Deck`` -> un único HTML autocontenido (CSS, imágenes y logos incrustados; sin JavaScript)."""

from __future__ import annotations

import base64
import copy
import io
import re
import textwrap
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape

from ..evidence_engine.manifest import load_manifest
from ..typst_engine import TEMPLATES_DIR as TYPST_TEMPLATES
from .model import Deck, DeckError, _Checker, check_code_block

PACKAGE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PACKAGE_DIR / "assets"
TEMPLATES_DIR = PACKAGE_DIR / "templates"
THEMES_DIR = ASSETS_DIR / "themes"
LOGO_DIR = TYPST_TEMPLATES / "informe-laboratorio" / "assets"

LABELS = {
    "es": {"slide": "Diapositiva", "figure": "Figura", "table": "Tabla", "authors": "Integrantes", "instructor": "Docente"},
    "en": {"slide": "Slide", "figure": "Figure", "table": "Table", "authors": "Authors", "instructor": "Instructor"},
}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
        ".webp": "image/webp", ".svg": "image/svg+xml"}

_DP = re.compile(r"(?<![\w.#])(-?\d+(?:\.\d+)?)dp\b")


def expand_dp(css: str) -> str:
    """``44dp`` -> ``calc(44 * var(--px))``: píxel de diseño a 1920 de ancho, escalable con la diapositiva."""
    return _DP.sub(lambda m: f"calc({m.group(1)} * var(--px))", css)


def available_themes() -> List[str]:
    return sorted(p.stem for p in THEMES_DIR.glob("*.css"))


def theme_css(name: str) -> str:
    path = THEMES_DIR / f"{name}.css"
    if not path.is_file():
        raise DeckError([f"tema '{name}' no existe; disponibles: {', '.join(available_themes())}"])
    return path.read_text(encoding="utf-8")


def inline(text: Any) -> Markup:
    """Escapa y admite solo **negrita** y `código` en línea."""
    out = str(escape(str(text)))
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    return Markup(out)


def _data_uri(path: Path) -> str:
    mime = MIME.get(path.suffix.lower())
    if mime is None:
        raise DeckError([f"formato de imagen no soportado: {path.name} (usa png, jpg, gif, webp o svg)"])
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


@lru_cache(maxsize=None)
def _logo_uri(name: str, height_px: int) -> str:
    """Logo institucional reducido a ``height_px`` de alto (2x del tamaño mostrado) para no inflar el HTML."""
    from PIL import Image
    with Image.open(LOGO_DIR / f"{name}.png") as im:
        im = im.convert("RGBA")
        width = round(im.width * height_px / im.height)
        im = im.resize((width, height_px), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _logos(meta: Dict[str, Any]) -> Optional[Dict[str, str]]:
    if not meta["institutional"]:
        return None
    return {"unsa": _logo_uri("unsa", 192), "epis": _logo_uri("epis", 168)}


def _resolve_image(slide: Dict[str, Any], project_dir: Path, evidence_dir: Optional[Path], manifest: Dict[str, Any],
                   errors: List[str], index: int) -> Optional[Path]:
    if slide.get("evidence_id"):
        item = manifest.get("items", {}).get(slide["evidence_id"])
        if item is None or not item.get("image"):
            errors.append(f"diapositiva {index} (figure): evidence_id '{slide['evidence_id']}' no está en el manifiesto "
                          f"de evidencia ({evidence_dir / 'manifest.json' if evidence_dir else 'sin directorio de evidencia'})")
            return None
        path = (evidence_dir / item["image"]).resolve()
    else:
        raw = Path(slide["image"])
        candidates = [raw] if raw.is_absolute() else [project_dir / raw] + ([evidence_dir / raw] if evidence_dir else [])
        path = next((c.resolve() for c in candidates if c.is_file()), candidates[0])
    if not path.is_file():
        errors.append(f"diapositiva {index} (figure): no existe la imagen {path}")
        return None
    return path


def _code_text(slide: Dict[str, Any], project_dir: Path, errors: List[str], index: int) -> str:
    c = _Checker(index, slide, errors)
    if slide.get("file"):
        path = (project_dir / slide["file"]).resolve()
        if not path.is_file():
            c.err(f"no existe el archivo de código {path}")
            return ""
        lines = path.read_text(encoding="utf-8").splitlines()
        if slide.get("lines"):
            lo, _, hi = str(slide["lines"]).partition("-")
            lines = lines[int(lo) - 1:int(hi or lo)]
        lines = textwrap.dedent("\n".join(lines)).splitlines()
        check_code_block(c, lines)
        return "\n".join(lines)
    return textwrap.dedent(slide["code"]).strip("\n")


def prepare_slides(deck: Deck, project_dir: Path, evidence_dir: Optional[Path]) -> List[Dict[str, Any]]:
    """Copia las diapositivas añadiendo lo resuelto en disco (imágenes, código, numeración). Errores acumulados."""
    project_dir = Path(project_dir).resolve()
    manifest = load_manifest(str(evidence_dir)) if evidence_dir else {"items": {}}
    errors: List[str] = []
    out: List[Dict[str, Any]] = []
    fig_no = tab_no = 0
    for i, original in enumerate(deck.slides, 1):
        s = copy.deepcopy(original)
        # `items` choca con dict.items() en Jinja: las plantillas leen `entries`.
        s["entries"] = s.get("items", [])
        for side in (s.get("left"), s.get("right")):
            if isinstance(side, dict):
                side["entries"] = side.get("items", [])
        if s["layout"] == "figure":
            path = _resolve_image(s, project_dir, evidence_dir, manifest, errors, i)
            fig_no += 1
            s["fig_no"] = fig_no
            s["image_uri"] = _data_uri(path) if path else ""
        elif s["layout"] == "table" and s.get("caption"):
            tab_no += 1
            s["tab_no"] = tab_no
        elif s["layout"] == "code":
            s["code_text"] = _code_text(s, project_dir, errors, i)
        out.append(s)
    if errors:
        raise DeckError(errors)
    return out


def _environment() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.filters["inline"] = inline
    return env


def render_deck(deck: Deck, project_dir: Path, evidence_dir: Optional[Path] = None) -> str:
    meta = deck.meta
    slides = prepare_slides(deck, project_dir, evidence_dir)
    css = expand_dp(theme_css(meta["theme"]) + "\n" + (ASSETS_DIR / "base.css").read_text(encoding="utf-8"))
    labels = LABELS.get(meta["lang"], LABELS["es"])
    template = _environment().get_template("deck.html.j2")
    return template.render(meta=meta, slides=slides, css=Markup(css), labels=labels, logos=_logos(meta), total=len(slides))
