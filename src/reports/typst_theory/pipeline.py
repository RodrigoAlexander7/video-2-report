# -*- coding: utf-8 -*-
"""Pipeline typst-theory: ``project.toml`` + ``content/*.typ`` -> PDF formal de Teoria en Typst."""

from __future__ import annotations

import datetime as _dt
import json
import logging
import re
import shutil
import tomllib
from pathlib import Path
from typing import Mapping, Optional

try:
    from src.typst_engine import TEMPLATES_DIR, compile_typst_detailed, typst_fonts
except ImportError:
    from typst_engine import TEMPLATES_DIR, compile_typst_detailed, typst_fonts

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_NAME = "informe-teoria"
DEFAULT_COPY = ("content", "figures", "evidence", "code", "assets")

SERIF_FAMILIES = ["Times New Roman", "Liberation Serif", "Tinos", "Libertinus Serif"]
MONO_FALLBACKS = ["DejaVu Sans Mono", "Liberation Mono", "Cascadia Mono"]

THEORY_KEYS = (
    "course", "title", "subtitle", "chapter", "instructor", "semester", "year",
    "city", "country", "members", "institution", "logo-cover", "logo-header",
    "accent", "secondary-accent", "toc", "list-of-figures", "list-of-tables",
    "bib-style", "cover-page",
)
REQUIRED_THEORY = ("course", "title", "instructor", "members")

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".DS_Store", "node_modules")
IMPORT_LINE = '#import "/template/lib.typ": *\n'


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^\w.\-]+", "-", name, flags=re.UNICODE).strip("-.")
    return cleaned or "informe-teoria"


def _jsonable(value):
    if isinstance(value, _dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, _dt.date):
        return value.isoformat()
    if isinstance(value, _dt.time):
        return value.strftime("%H:%M")
    if isinstance(value, Mapping):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _font_stack(requested, fallbacks, available: set[str]) -> list[str]:
    if isinstance(requested, str):
        requested = [requested]
    candidates: list[str] = []
    for fam in [*(requested or []), *fallbacks]:
        if fam.lower() not in {c.lower() for c in candidates}:
            candidates.append(fam)
    if not available:
        return candidates
    known = {a.lower() for a in available}
    stack = [c for c in candidates if c.lower() in known]
    return stack or candidates[:1]


def load_project(project_dir) -> dict:
    pdir = Path(project_dir).resolve()
    toml_path = pdir / "project.toml"
    if not toml_path.is_file():
        raise FileNotFoundError(f"No existe {toml_path}.")
    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)
    theory = data.get("theory") or data.get("lab") or {}
    build = data.get("build") or {}
    missing = [k for k in REQUIRED_THEORY if k not in theory or theory[k] in ("", [], None)]
    if missing:
        raise ValueError(f"{toml_path}: faltan claves obligatorias en [theory]: {', '.join(missing)}")
    name = _safe_name(str(build.get("name") or pdir.name))
    return {"dir": pdir, "theory": theory, "build": build, "name": name}


def _resolve_sections(project: dict) -> list[str]:
    pdir: Path = project["dir"]
    raw = project["build"].get("sections")
    if raw is None:
        # Busca automaticamente en content/*.typ
        content_dir = pdir / "content"
        if content_dir.is_dir():
            raw = sorted(str(p.relative_to(pdir)) for p in content_dir.glob("*.typ"))
        else:
            raw = []
    if not raw:
        raise ValueError(f"{pdir / 'project.toml'}: no hay secciones definidas ni archivos en content/*.typ")
    sections: list[str] = []
    for item in raw:
        rel = str(item)
        if "/" not in rel and not rel.endswith(".typ"):
            rel = f"content/{rel}.typ"
        if not (pdir / rel).is_file():
            raise FileNotFoundError(f"Seccion no encontrada: {pdir / rel}")
        sections.append(Path(rel).as_posix())
    return sections


def _typst_str(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def _render_main(sections: list[str]) -> str:
    includes = "\n  #parbreak()\n".join(f"  #include {_typst_str(s)}" for s in sections)
    return (
        "// Generado automaticamente por src/reports/typst_theory (no editar).\n"
        '#import "template/lib.typ": *\n'
        '#let cfg = json("config.json")\n'
        "#show: template.with(config: cfg)\n\n"
        f"{includes}\n"
    )


def _copy_into(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, ignore=_IGNORE, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _inject_template_import(stage: Path, sections: list[str]) -> None:
    targets = {stage / s for s in sections}
    if (stage / "content").is_dir():
        targets.update((stage / "content").rglob("*.typ"))
    for typ in targets:
        if typ.is_file():
            text = typ.read_text(encoding="utf-8")
            # Limpiar imports previos si los hubiera
            text = re.sub(r'#import\s+["\']/?template/lib\.typ["\']:\s*\*\s*\n?', '', text)
            typ.write_text(IMPORT_LINE + text, encoding="utf-8")


def build(project_dir, out_dir=None, inputs: Optional[Mapping[str, object]] = None, evidence_dir=None) -> Path:
    project = load_project(project_dir)
    pdir: Path = project["dir"]
    theory, bld = project["theory"], project["build"]
    out = Path(out_dir).resolve() if out_dir else (pdir / "build")
    sections = _resolve_sections(project)

    font_paths = [(pdir / p).resolve() for p in bld.get("font-paths", [])]
    available = typst_fonts(font_paths)

    config: dict = {k: theory[k] for k in THEORY_KEYS if k in theory}
    config.update({k: bld[k] for k in THEORY_KEYS if k in bld})

    # Font stack: Times New Roman con fallbacks metricos
    config["font"] = _font_stack(bld.get("font") or theory.get("font"), SERIF_FAMILIES, available)
    config["mono-font"] = _font_stack(bld.get("mono-font") or theory.get("mono-font"), MONO_FALLBACKS, available)

    bib = bld.get("bibliography", "references.bib")
    config["bibliography"] = bib if bib and (pdir / bib).is_file() else None

    # Directorio de trabajo stage
    stage = out / "_stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    _copy_into(TEMPLATES_DIR / TEMPLATE_NAME, stage / "template")

    to_copy = [*DEFAULT_COPY, *map(str, bld.get("copy", [])), *sections]
    if config["bibliography"]:
        to_copy.append(str(bib))
    for rel in to_copy:
        src = pdir / rel
        if src.exists():
            _copy_into(src, stage / rel)

    if evidence_dir:
        ev = Path(evidence_dir).resolve()
        if ev.is_dir():
            _copy_into(ev, stage / "evidence")

    _inject_template_import(stage, sections)
    (stage / "main.typ").write_text(_render_main(sections), encoding="utf-8")

    clean_cfg = _jsonable(config)
    (stage / "config.json").write_text(json.dumps(clean_cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    pdf_out = out / f"{project['name']}.pdf"
    res = compile_typst_detailed(
        stage / "main.typ",
        pdf_out,
        root=stage,
        inputs=inputs or {},
        font_paths=font_paths,
    )
    for w in res.warnings:
        logging.warning("Typst: %s", w)
    return pdf_out


def run(project_dir, out_dir=None, inputs=None) -> Path:
    return build(project_dir, out_dir=out_dir, inputs=inputs)
