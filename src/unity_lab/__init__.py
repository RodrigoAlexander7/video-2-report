# -*- coding: utf-8 -*-
"""Reportes de laboratorio de Unity (docx sobre la plantilla EPIS) con figuras del video, código como imagen y revisión de estilo.

Uso: ``python main.py unity-lab new|plan|check|capture|build|review <carpeta-del-caso>``. Ver
`.agents/skills/unity-lab-report/SKILL.md` y `docs/cases/unity-lab.md`.
"""
from .build import build, default_dirs
from .checks import Report, check_lab, format_scorecard
from .figures import FigureError, capture_figures
from .model import ReportError, load_lab
from .scaffold import outline, scaffold

__all__ = ["build", "default_dirs", "check_lab", "format_scorecard", "Report", "capture_figures", "FigureError", "ReportError",
           "load_lab", "outline", "scaffold"]
