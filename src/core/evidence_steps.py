# -*- coding: utf-8 -*-
"""Captura de evidencia declarada en project.toml y verificación previa al build.

    [evidence]
    tool = "vdmj"        # dialect / release opcionales
    [[evidence.sessions]]
    name = "ej1"; specs = ["specs/A.vpp"]; script = "scripts/ej1.script"

Cada sesión se ejecuta de verdad; después se verifica el manifiesto y las directivas
`evidence:` del texto. Si algo no cuadra se aborta antes de compilar.
"""

from pathlib import Path
from typing import List

from .project import load_project


class EvidenceError(RuntimeError):
    pass


def capture_declared(project_dir: Path, evidence_dir: Path) -> List[str]:
    """Ejecuta las sesiones declaradas. Devuelve los nombres capturados (vacío si no hay sección)."""
    cfg = load_project(project_dir).get("evidence")
    if not cfg:
        return []
    from src import evidence_engine as ev
    from src.evidence_engine.vdmj import read_script

    if cfg.get("tool", "vdmj") != "vdmj":
        raise EvidenceError(f"[evidence].tool no soportado: {cfg.get('tool')!r} (disponible: vdmj)")
    names = []
    for s in cfg.get("sessions", []):
        specs = list(s["specs"])  # relativas al proyecto: los logs no exponen rutas del sistema
        script = read_script(str((project_dir / s["script"]).resolve()))
        ev.capture_vdmj(s["name"], specs, script, str(evidence_dir),
                        dialect=cfg.get("dialect", "vdmpp"), release=cfg.get("release", "classic"),
                        cwd=str(project_dir), screen=cfg.get("screen"))
        names.append(s["name"])
        print(f"  evidencia: {s['name']}")
    return names


def verify_project(project_dir: Path, evidence_dir: Path) -> None:
    """Verifica el manifiesto y las afirmaciones de content/*.typ y content/*.md; lanza EvidenceError si hay errores."""
    from src import evidence_engine as ev

    texts = sorted(p for pat in ("*.typ", "*.md") for p in (project_dir / "content").rglob(pat))
    issues = ev.verify_manifest(str(evidence_dir)) + ev.verify_claims(str(evidence_dir), [str(t) for t in texts])
    for issue in issues:
        print(f"  {issue}")
    errors = [i for i in issues if i.level == "error"]
    if errors:
        raise EvidenceError(f"La verificación de evidencia falló con {len(errors)} error(es); no se compila.")
