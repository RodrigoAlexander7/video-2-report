"""Núcleo del generador: registro de pipelines, detección por inputs y rutas de proyecto."""
from .registry import PIPELINES, Pipeline, detect, plan_for, resolve_slug

__all__ = ["PIPELINES", "Pipeline", "detect", "plan_for", "resolve_slug"]
