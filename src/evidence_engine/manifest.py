# -*- coding: utf-8 -*-
"""Manifiesto de evidencias: qué figura salió de qué comando, cuándo y con qué hash."""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

MANIFEST_NAME = "manifest.json"
SOURCES = ("terminal", "manual", "annotated", "code", "video")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def manifest_path(out_dir: str) -> str:
    return os.path.join(out_dir, MANIFEST_NAME)


def load_manifest(path: str) -> Dict[str, Any]:
    if os.path.isdir(path):
        path = manifest_path(path)
    if not os.path.isfile(path):
        return {"version": 1, "items": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def upsert(out_dir: str, item_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta o reemplaza un item. Las rutas se guardan relativas al directorio del manifiesto."""
    data = load_manifest(out_dir)
    data["items"][item_id] = item
    os.makedirs(out_dir, exist_ok=True)
    with open(manifest_path(out_dir), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    return item


def rel(out_dir: str, path: Optional[str]) -> Optional[str]:
    return None if path is None else os.path.relpath(path, out_dir)
