# -*- coding: utf-8 -*-
"""Registro de pipelines. Cada caso declara su contrato de entrada/salida.

El pipeline se elige por `pipeline = "<nombre>"` en project.toml o, si falta, por los
archivos que contiene el directorio de inputs. Si hay más de un candidato no se adivina:
se pide indicarlo explícitamente.
"""

import fnmatch
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .project import load_project

REPO_ROOT = Path(__file__).resolve().parents[2]
Plan = Dict[str, Any]


def resolve_slug(project_dir: Path) -> str:
    """inputs/NE/Lab05 -> 'NE/Lab05' (mismo árbol bajo output/); fuera de inputs/ usa el nombre del directorio."""
    project_dir = Path(project_dir).resolve()
    try:
        return project_dir.relative_to(REPO_ROOT / "inputs").as_posix()
    except ValueError:
        return project_dir.name


def _path(project_dir: Path, value: Any) -> str:
    """Las rutas de project.toml son relativas al proyecto (las absolutas se respetan)."""
    p = Path(str(value))
    return str(p if p.is_absolute() else (project_dir / p).resolve())


def _required(project_dir: Path, options: Dict[str, Any], key: str, pattern: str) -> str:
    """Valor de `key` en project.toml o primer archivo que cumpla `pattern`; si no hay, error claro."""
    if key in options:
        return _path(project_dir, options[key])
    found = _first(project_dir, pattern)
    if found is None:
        raise FileNotFoundError(
            f"Falta '{key}': no hay '{pattern}' en {project_dir}. Colócalo ahí o indícalo en project.toml "
            f"([{project_dir.name}] {key} = \"ruta\").")
    return str(found)


def _first(project_dir: Path, pattern: str) -> Optional[Path]:
    found = sorted(p for p in project_dir.iterdir() if p.is_file() and fnmatch.fnmatch(p.name.lower(), pattern.lower()))
    return found[0] if found else None


def _opt(options: Dict[str, Any], key: str, default: Any) -> Any:
    return options.get(key, default)


@dataclass(frozen=True)
class Pipeline:
    name: str
    summary: str
    requires: Tuple[str, ...]           # patrones que DEBEN existir en el directorio de inputs
    accepts: Tuple[str, ...]            # patrones opcionales que se usan si existen
    produces: str
    template: str
    example: str
    plan: Callable[[Path, Dict[str, Any], str], Plan]
    run: Callable[[Plan], List[str]]
    deprecated: bool = False
    auto: bool = True                                   # False: solo se usa si se pide explícitamente
    predicate: Optional[Callable[[Path], bool]] = None  # condición extra para la detección automática

    def matches(self, project_dir: Path) -> bool:
        """Cumple los archivos requeridos (contrato mínimo)."""
        files = [p.name for p in Path(project_dir).iterdir() if p.is_file()]
        return all(any(fnmatch.fnmatch(f.lower(), pat.lower()) for f in files) for pat in self.requires)

    def auto_matches(self, project_dir: Path) -> bool:
        return self.auto and not self.deprecated and self.matches(project_dir) and (
            self.predicate is None or self.predicate(Path(project_dir)))


# ---------------------------------------------------------------- planes y ejecución
def _out_dir(slug: str) -> Path:
    return REPO_ROOT / "output" / slug


def _plan_video_report(d: Path, o: Dict[str, Any], slug: str) -> Plan:
    out = _out_dir(slug)
    return {"video": _required(d, o, "video", "*.mp4"), "template": _required(d, o, "template", "*.docx"),
            "output": _path(d, o["output"]) if "output" in o else str(out / f"Reporte_{d.name}.docx"),
            "media_dir": _path(d, o["media_dir"]) if "media_dir" in o else str(out / "figures"),
            "stages": _path(d, o["stages"]) if "stages" in o else None,
            "low_quality": bool(o.get("low_quality", False)), "skip_media": bool(o.get("skip_media", False))}


def _run_video_report(p: Plan) -> List[str]:
    from config import ReportConfig
    from src.video_engine.media_extractor import generate_and_enhance_figures
    from src.reports.unity_practice.generate_report import build_report
    cfg = ReportConfig(high_quality_gifs=not p["low_quality"], video_path=p["video"], template_path=p["template"],
                       output_path=p["output"], media_dir=p["media_dir"])
    if not p["skip_media"]:
        generate_and_enhance_figures(cfg, p["stages"])
    build_report(cfg)
    return [p["output"]]


def _plan_unity_lab06(d: Path, o: Dict[str, Any], slug: str) -> Plan:
    out = _out_dir(slug)
    return {"template": _required(d, o, "template", "*.docx"),
            "output": _path(d, o["output"]) if "output" in o else str(out / "Reporte_Practica_06_Unity.docx"),
            "media": _path(d, o["media"]) if "media" in o else str(out / "figures")}


def _run_unity_lab06(p: Plan) -> List[str]:
    script = REPO_ROOT / "src/reports/unity_practice/generate_lab06_report.py"
    subprocess.run([sys.executable, str(script), "--template", p["template"], "--output", p["output"],
                    "--media", p["media"]], cwd=REPO_ROOT, check=True)
    return [p["output"]]


def _plan_epis_ne(d: Path, o: Dict[str, Any], slug: str) -> Plan:
    return {"template": _required(d, o, "template", "*.docx"),
            "output": _path(d, o["output"]) if "output" in o else str(_out_dir(slug) / "Informe_Lab05_Distribuidora_Inca_SCM.docx")}


def _run_epis_ne(p: Plan) -> List[str]:
    from src.reports.epis_ne.builder import generate_epis_ne_report
    generate_epis_ne_report(template_path=p["template"], output_path=p["output"])
    return [p["output"]]


def _plan_epis_short(d: Path, o: Dict[str, Any], slug: str) -> Plan:
    return {"template": _required(d, o, "template", "input-template.docx"),
            "output": _path(d, o["output"]) if "output" in o else str(_out_dir(slug) / "Informe_Corto_Lab05_Distribuidora_Inca_SCM.docx")}


def _run_epis_short(p: Plan) -> List[str]:
    from src.reports.epis_ne.short_report_builder import generate_short_report
    generate_short_report(template_path=p["template"], output_path=p["output"])
    return [p["output"]]


def _plan_typst_lab(d: Path, o: Dict[str, Any], slug: str) -> Plan:
    return {"project_dir": str(d), "out_dir": _path(d, o["out_dir"]) if "out_dir" in o else str(_out_dir(slug) / "build"),
            "evidence_dir": _path(d, o["evidence_dir"]) if "evidence_dir" in o else str(_out_dir(slug) / "evidence")}


def _run_typst_lab(p: Plan) -> List[str]:
    from src.reports.typst_lab import build
    from .evidence_steps import capture_declared, verify_project
    project_dir, evidence_dir = Path(p["project_dir"]), Path(p["evidence_dir"])
    if capture_declared(project_dir, evidence_dir):
        verify_project(project_dir, evidence_dir)
    return [str(build(project_dir, p["out_dir"], evidence_dir=evidence_dir))]


def _has_lab_table(d: Path) -> bool:
    return "lab" in load_project(d)


def _plan_typst_theory(d: Path, o: Dict[str, Any], slug: str) -> Plan:
    return {"project_dir": str(d), "out_dir": _path(d, o["out_dir"]) if "out_dir" in o else str(_out_dir(slug) / "build"),
            "evidence_dir": _path(d, o["evidence_dir"]) if "evidence_dir" in o else str(_out_dir(slug) / "evidence")}


def _run_typst_theory(p: Plan) -> List[str]:
    from src.reports.typst_theory import build
    project_dir, evidence_dir = Path(p["project_dir"]), Path(p["evidence_dir"])
    return [str(build(project_dir, p["out_dir"], evidence_dir=evidence_dir))]


def _has_theory_table(d: Path) -> bool:
    proj = load_project(d)
    return "theory" in proj or proj.get("pipeline") == "typst-theory"


def _plan_html_slides(d: Path, o: Dict[str, Any], slug: str) -> Plan:
    return {"project_dir": str(d), "out_dir": _path(d, o["out_dir"]) if "out_dir" in o else str(_out_dir(slug) / "build"),
            "evidence_dir": _path(d, o["evidence_dir"]) if "evidence_dir" in o else str(_out_dir(slug) / "evidence")}


def _run_html_slides(p: Plan) -> List[str]:
    from src.reports.html_slides import build
    return [str(build(p["project_dir"], p["out_dir"], evidence_dir=p["evidence_dir"]))]


def _has_slides_table(d: Path) -> bool:
    proj = load_project(d)
    return "slides" in proj or proj.get("pipeline") == "html-slides"


PIPELINES: Dict[str, Pipeline] = {pl.name: pl for pl in [
    Pipeline("video-report", "Reporte Word por etapas a partir de un video (figuras anotadas y GIFs).",
             requires=("*.mp4",), accepts=("*.docx", "project.toml"), produces="<output>/<slug>/Reporte_<caso>.docx + figures/",
             template="plantilla .docx (la primera del directorio o inputs/input-template.docx)",
             example="main.py run inputs/video-unity-02", plan=_plan_video_report, run=_run_video_report),
    Pipeline("unity-lab06", "Reporte de la Práctica 06 de Unity (rotación y Time.deltaTime), 5 etapas.",
             requires=(), accepts=("*.docx", "*.mp4", "project.toml"), produces="output/<slug>/Reporte_Practica_06_Unity.docx",
             template="plantilla .docx del directorio; figuras ya generadas en output/<slug>/figures",
             example="main.py run inputs/IDSE/lab06 --pipeline unity-lab06", plan=_plan_unity_lab06, run=_run_unity_lab06,
             auto=False),
    Pipeline("epis-ne", "Informe institucional EPIS de Negocios Electrónicos (16 secciones obligatorias).",
             requires=("StudyCase.md",), accepts=("*.docx",), produces="output/<slug>/Informe_Lab05_Distribuidora_Inca_SCM.docx",
             template="GenericTemplate.docx (EPIS-UNSA) del directorio", example="main.py run inputs/NE/Lab05",
             plan=_plan_epis_ne, run=_run_epis_ne),
    Pipeline("epis-ne-short", "Informe corto EPIS para la guía de prácticas (una tabla por apartado).",
             requires=("input-template.docx",), accepts=("project.toml",),
             produces="output/<slug>/Informe_Corto_Lab05_Distribuidora_Inca_SCM.docx",
             template="input-template.docx del directorio", example="main.py run inputs/NE/Lab05-short-report",
             plan=_plan_epis_short, run=_run_epis_short, auto=False),
    Pipeline("typst-lab", "Informe de laboratorio en Typst/PDF con evidencia verificable.",
             requires=("project.toml",), accepts=("content/*.typ", "figures/", "evidence/"),
             produces="output/<slug>/build/<caso>.pdf", template="paquete informe-laboratorio (src/typst_engine)",
             example="main.py typst-lab new inputs/mi-lab && main.py run inputs/mi-lab",
             plan=_plan_typst_lab, run=_run_typst_lab, predicate=_has_lab_table),
    Pipeline("typst-theory", "Informe formal de teoría y trabajo parcial en Typst/PDF.",
             requires=("project.toml",), accepts=("content/*.typ", "figures/", "evidence/"),
             produces="output/<slug>/build/<caso>.pdf", template="paquete informe-teoria (src/typst_engine)",
             example="main.py run inputs/Calidad-Software/Actividad05 --pipeline typst-theory",
             plan=_plan_typst_theory, run=_run_typst_theory, predicate=_has_theory_table),
    Pipeline("html-slides", "Diapositivas HTML (siempre en tema claro, sin animaciones) y PDF.",
             requires=("project.toml",), accepts=("content/slides.toml", "figures/", "evidence/", "code/"),
             produces="output/<slug>/build/<caso>-slides.html + .pdf (una diapositiva por página, 1920x1080)",
             template="tema academic-light (src/slides_engine/assets/themes)",
             example="main.py slides new inputs/mi-deck && main.py run inputs/mi-deck",
             plan=_plan_html_slides, run=_run_html_slides, predicate=_has_slides_table),
]}


def detect(project_dir: Path, forced: Optional[str] = None) -> Pipeline:
    project_dir = Path(project_dir)
    if not project_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio de inputs: {project_dir}")
    name = forced or load_project(project_dir).get("pipeline")
    if name:
        if name not in PIPELINES:
            raise KeyError(f"Pipeline desconocido '{name}'. Disponibles: {', '.join(PIPELINES)}")
        pl = PIPELINES[name]
        if not pl.matches(project_dir):
            raise ValueError(f"'{name}' requiere {', '.join(pl.requires)} en {project_dir}")
        return pl
    candidates = [pl for pl in PIPELINES.values() if pl.auto_matches(project_dir)]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise ValueError(f"Ningún pipeline reconoce {project_dir}. Revisa `main.py list` (algunos casos exigen "
                         f"--pipeline <nombre> o pipeline = \"...\" en project.toml).")
    names = ", ".join(c.name for c in candidates)
    raise ValueError(f"Ambiguo: {project_dir} encaja con varios pipelines ({names}). "
                     f"Usa --pipeline <nombre> o agrega pipeline = \"...\" a project.toml.")


def plan_for(pipeline: Pipeline, project_dir: Path) -> Plan:
    project_dir = Path(project_dir).resolve()
    options = load_project(project_dir).get(pipeline.name, {})
    return pipeline.plan(project_dir, options, resolve_slug(project_dir))
