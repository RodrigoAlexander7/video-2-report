# -*- coding: utf-8 -*-
"""Pipeline html-slides: ``project.toml`` + ``content/slides.toml`` -> HTML autocontenido + PDF (tema claro, sin animaciones)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Optional

from ...slides_engine import (DeckError, check_layout, check_theme, export_pdf, layout_problems, lint_html,
                              load_deck, render_deck, theme_css)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _safe_name(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "-", name, flags=re.UNICODE).strip("-.") or "deck"


def load_project(project_dir) -> dict:
    pdir = Path(project_dir).resolve()
    toml_path = pdir / "project.toml"
    if not toml_path.is_file():
        raise FileNotFoundError(f"No existe {toml_path}.")
    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)
    if "slides" not in data:
        raise ValueError(f"{toml_path}: falta la tabla [slides] (título, tema, archivo de contenido)")
    build = data.get("build") or {}
    base = _safe_name(str(build.get("name") or pdir.name))
    return {"dir": pdir, "data": data, "build": build, "name": base if base.endswith("-slides") else base + "-slides"}


def _defaults(project_dir: Path) -> tuple[Path, Path]:
    from ...core.registry import resolve_slug
    out = REPO_ROOT / "output" / resolve_slug(project_dir)
    return out / "build", out / "evidence"


def check(project_dir, evidence_dir=None) -> str:
    """Validación estática (contenido, tema, lints). Devuelve el HTML renderizado; no necesita Chrome."""
    project = load_project(project_dir)
    deck = load_deck(project["dir"], project["data"], project["name"])
    if evidence_dir is None:
        evidence_dir = _defaults(project["dir"])[1]
    html = render_deck(deck, project["dir"], Path(evidence_dir))
    problems = check_theme(theme_css(deck.meta["theme"]), deck.meta["theme"]) + lint_html(html)
    if problems:
        raise DeckError(problems)
    return html


def build(project_dir, out_dir=None, evidence_dir=None, pdf: Optional[bool] = None, layout: Optional[bool] = None) -> Path:
    """Genera ``<out_dir>/<nombre>.html`` y, salvo ``pdf = false``, ``<nombre>.pdf``. Devuelve el PDF (o el HTML)."""
    project = load_project(project_dir)
    default_out, default_evidence = _defaults(project["dir"])
    out_dir = Path(out_dir) if out_dir else default_out
    html = check(project_dir, evidence_dir if evidence_dir is not None else default_evidence)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / f"{project['name']}.html"
    html_path.write_text(html, encoding="utf-8")

    n_slides = html.count('<section class="slide ')
    want_pdf = project["build"].get("pdf", True) if pdf is None else pdf
    want_layout = project["build"].get("check", True) if layout is None else layout
    if want_layout:
        problems = layout_problems(check_layout(html))
        if problems:
            raise DeckError(problems + [f"(HTML conservado para depurar: {html_path})"])
    if not want_pdf:
        return html_path
    return export_pdf(html_path, out_dir / f"{project['name']}.pdf", n_slides)


def run(project_dir) -> Path:
    return build(project_dir)
