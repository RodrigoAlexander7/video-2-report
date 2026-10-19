# -*- coding: utf-8 -*-
"""Pipeline de diapositivas HTML (tema claro, sin animaciones) con exportación a PDF."""
from .pipeline import build, check, run
from .scaffold import scaffold

__all__ = ["build", "check", "run", "scaffold"]
