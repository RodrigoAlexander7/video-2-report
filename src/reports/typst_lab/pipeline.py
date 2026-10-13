"""Pipeline typst-lab: ``project.toml`` + ``content/*.typ`` -> PDF con la plantilla institucional.

Diseño
------
``build`` prepara un directorio de trabajo autocontenido (``<out_dir>/_stage``) que sirve
como raiz de Typst::

    _stage/
      main.typ        generado: importa la plantilla e #include-a las secciones, en orden
      config.json     configuracion (dict) que recibe ``template.with(config: ...)``
      template/       copia de src/typst_engine/templates/informe-laboratorio
      content/ figures/ evidence/ code/ ...   copias de lo que el proyecto aporta
      references.bib

y compila ``_stage/main.typ`` a ``<out_dir>/<nombre>.pdf``. El directorio ``_stage`` se
conserva para depurar (``typst watch --root _stage _stage/main.typ``).
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
import tomllib
from pathlib import Path
from typing import Mapping, Optional

try:  # uso normal: ``from src.reports.typst_lab import run`` con la raiz del repo en sys.path
    from src.typst_engine import TEMPLATES_DIR, compile_typst_detailed, typst_fonts
except ImportError:  # ``src`` en sys.path (como hace main.py)
    from typst_engine import TEMPLATES_DIR, compile_typst_detailed, typst_fonts

from .scaffold import IMPORT_LINE, scaffold

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_NAME = "informe-laboratorio"
DEFAULT_SECTIONS = (
    "content/ejercicios.typ",
    "content/cuestionario.typ",
    "content/conclusiones.typ",
)
# Carpetas del proyecto que se copian al directorio de trabajo si existen.
DEFAULT_COPY = ("content", "figures", "evidence", "code", "assets")
FONT_FALLBACKS = ["Lato", "Liberation Sans", "DejaVu Sans", "Libertinus Serif"]
MONO_FALLBACKS = ["DejaVu Sans Mono", "Liberation Mono", "Cascadia Mono"]

# Claves de [lab] y [build] que pasan tal cual a config.json (la plantilla define los defaults).
LAB_KEYS = (
    "course", "title", "number", "instructor", "semester", "year", "members", "date", "time",
    "institution", "doc-title", "doc-format", "doc-approval", "doc-code", "logo-left",
    "logo-right", "note-placeholder",
)
BUILD_KEYS = (
    "toc", "list-of-figures", "feedback", "results-title", "bib-style", "accent",
    "max-unbreakable-lines", "code-keep-lines",
)
REQUIRED_LAB = ("course", "title", "number", "instructor", "members")

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".DS_Store")


def load_project(project_dir) -> dict:
    """Lee y valida ``project.toml``. Devuelve ``{"dir", "lab", "build", "name"}``."""
    pdir = Path(project_dir).resolve()
    toml_path = pdir / "project.toml"
    if not toml_path.is_file():
        raise FileNotFoundError(
            f"No existe {toml_path}. Crea el esqueleto con run({str(project_dir)!r}, scaffold_only=True)."
        )
    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)
    lab = data.get("lab") or {}
    build = data.get("build") or {}
    missing = [k for k in REQUIRED_LAB if k not in lab or lab[k] in ("", [], None)]
    if missing:
        raise ValueError(f"{toml_path}: faltan claves obligatorias en [lab]: {', '.join(missing)}")
    if not isinstance(lab["members"], list) or not all(isinstance(m, str) for m in lab["members"]):
        raise ValueError(f"{toml_path}: [lab].members debe ser una lista de strings")
    name = _safe_name(str(build.get("name") or pdir.name))
    return {"dir": pdir, "lab": lab, "build": build, "name": name}


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^\w.\-]+", "-", name, flags=re.UNICODE).strip("-.")
    return cleaned or "informe"


def _jsonable(value):
    """TOML -> JSON: fechas y horas de TOML se convierten a texto (HH:MM sin segundos)."""
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
    """Familias candidatas sin repetir y solo las que Typst conoce (evita sus warnings)."""
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
    return stack or candidates[-1:]


def _resolve_sections(project: dict) -> list[str]:
    pdir: Path = project["dir"]
    raw = project["build"].get("sections")
    if raw is None:
        raw = [s for s in DEFAULT_SECTIONS if (pdir / s).is_file()]
    if not raw:
        raise ValueError(f"{pdir / 'project.toml'}: [build].sections esta vacio y no hay content/*.typ por defecto")
    sections: list[str] = []
    for item in raw:
        rel = str(item)
        if "/" not in rel and not rel.endswith(".typ"):  # "ejercicios" -> content/ejercicios.typ
            rel = f"content/{rel}.typ"
        if not (pdir / rel).is_file():
            raise FileNotFoundError(f"Seccion no encontrada: {pdir / rel} (listada en [build].sections)")
        sections.append(Path(rel).as_posix())
    return sections


def _typst_str(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def _render_main(sections: list[str]) -> str:
    includes = "\n  #parbreak()\n".join(f"  #include {_typst_str(s)}" for s in sections)
    return (
        "// Generado por src/reports/typst_lab (se regenera en cada build; no editar).\n"
        '#import "template/lib.typ": *\n'
        '#let cfg = json("config.json")\n'
        "#show: template.with(config: cfg)\n\n"
        "#section-box(cfg.results-title)[\n"
        f"{includes}\n"
        "]\n"
    )


def _copy_into(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, ignore=_IGNORE, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _inject_template_import(stage: Path, sections: list[str]) -> None:
    """Antepone el import de la plantilla a las secciones y a content/**/*.typ que no lo traen.

    Un ``#include`` evalua el archivo en un ambito nuevo: sin este import, los helpers
    (``listing``, ``figure-img``...) no existirian dentro de las secciones. Si el import
    se inyecta, los numeros de linea de los errores en ese archivo se corren en +1.
    """
    targets = {stage / s for s in sections}
    targets.update((stage / "content").rglob("*.typ"))
    for typ in targets:
        text = typ.read_text(encoding="utf-8")
        if "template/lib.typ" not in text:
            typ.write_text(IMPORT_LINE + text, encoding="utf-8")


def _default_out_dir(project: dict) -> Path:
    pdir: Path = project["dir"]
    output_root = (REPO_ROOT / "output").resolve()
    if output_root in pdir.parents:  # el proyecto vive en output/...: el build queda a su lado
        return pdir / "build"
    return output_root / project["name"] / "build"


def build(project_dir, out_dir=None, inputs: Optional[Mapping[str, object]] = None,
          evidence_dir=None) -> Path:
    """Compila el proyecto y devuelve la ruta del PDF.

    ``evidence_dir`` (opcional) es una carpeta con la evidencia capturada (``output/<caso>/evidence``);
    se copia a ``evidence/`` del directorio de trabajo y reemplaza a la del proyecto.
    ``out_dir`` por defecto es ``output/<nombre>/build`` (o ``<proyecto>/build`` si el
    proyecto ya esta dentro de ``output/``). ``inputs`` se pasa como ``--input k=v``;
    por ejemplo ``{"fecha": "2026-01-31", "hora": "20:00"}`` fija la fecha y la hora.
    """
    project = load_project(project_dir)
    pdir: Path = project["dir"]
    lab, bld = project["lab"], project["build"]
    out = Path(out_dir).resolve() if out_dir else _default_out_dir(project)
    sections = _resolve_sections(project)

    font_paths = [(pdir / p).resolve() for p in bld.get("font-paths", [])]
    available = typst_fonts(font_paths)

    # ---- config.json ----
    config: dict = {k: lab[k] for k in LAB_KEYS if k in lab}
    config.update({k: bld[k] for k in BUILD_KEYS if k in bld})
    config["font"] = _font_stack(bld.get("font"), FONT_FALLBACKS, available)
    config["mono-font"] = _font_stack(bld.get("mono-font"), MONO_FALLBACKS, available)
    config.setdefault("results-title", "SOLUCIÓN Y RESULTADOS")
    bib = bld.get("bibliography", "references.bib")
    config["bibliography"] = bib if bib and (pdir / bib).is_file() else False

    # ---- directorio de trabajo ----
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
        if not src.exists():
            continue
        if not src.resolve().is_relative_to(pdir):
            raise ValueError(f"[build].copy apunta fuera del proyecto: {rel}")
        _copy_into(src, stage / rel)
    if evidence_dir is not None and Path(evidence_dir).is_dir():
        _copy_into(Path(evidence_dir), stage / "evidence")
    _inject_template_import(stage, sections)

    (stage / "config.json").write_text(
        json.dumps(_jsonable(config), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (stage / "main.typ").write_text(_render_main(sections), encoding="utf-8")

    # ---- compilacion ----
    pdf = out / f"{project['name']}.pdf"
    result = compile_typst_detailed(
        stage / "main.typ", pdf, root=stage, inputs=dict(inputs or {}), font_paths=font_paths
    )
    return result.pdf


def run(project_dir: str, scaffold_only: bool = False, out_dir=None) -> Path:
    """Punto de entrada del CLI ``typst-lab``.

    - ``scaffold_only=True``: crea el esqueleto (sin sobrescribir) y devuelve ``project.toml``.
    - si no, compila el proyecto y devuelve la ruta del PDF.
    """
    if scaffold_only:
        toml_path = scaffold(project_dir)
        print(f"[typst-lab] Esqueleto listo en {toml_path.parent} (edita project.toml y content/*.typ)")
        return toml_path
    pdf = build(project_dir, out_dir=out_dir)
    print(f"[typst-lab] PDF generado: {pdf}")
    return pdf
