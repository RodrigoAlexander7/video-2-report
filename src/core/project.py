# -*- coding: utf-8 -*-
"""Carga de project.toml: opciones por proyecto sin tocar el código."""

import tomllib
from pathlib import Path
from typing import Any, Dict

PROJECT_FILE = "project.toml"


def load_project(project_dir: Path) -> Dict[str, Any]:
    path = Path(project_dir) / PROJECT_FILE
    if not path.is_file():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)
