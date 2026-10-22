# -*- coding: utf-8 -*-
"""Captura de evidencia: ejecuta comandos reales y registra log, figura y manifiesto.

Los comandos se ejecutan SIN shell (se parten con shlex), por lo que no hay `eval`
ni expansión inesperada. Si se necesita una tubería, envolverla con `sh -c '...'`.
"""

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import manifest as mf
from .desktop import render_desktop
from .render import render_terminal
from .toolbox import render_toolbox


_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    """Quita secuencias de color/estilo (p. ej. las negritas de `mvn -version`): en la figura salían como cajas."""
    return _ANSI.sub("", text)


WINDOW_USER = os.environ.get("EVIDENCE_WINDOW_USER", "totora@rod")


def window_title(out_dir: str, user: Optional[str] = None) -> str:
    """Título decorativo de la ventana: ``usuario@equipo: ~/documents/<curso>/<práctica>``.

    Curso y práctica salen de la ruta ``output/<curso>/<práctica>/...`` del caso (no hay ruta fija);
    si ``out_dir`` no cuelga de ``output/`` se usa solo ``Terminal``. El título se guarda en el manifiesto
    (``window_title``): es presentación, no un dato de la ejecución.
    """
    parts = Path(out_dir).resolve().parts
    if "output" not in parts:
        return "Terminal"
    rest = [p for p in parts[len(parts) - parts[::-1].index("output"):] if p not in ("evidence", "figures", "build")]
    slug = [re.sub(r"[^\w.\-]+", "-", p.lower()).strip("-") for p in rest[:2]]
    return f"{user or WINDOW_USER}: ~/documents/" + "/".join(s for s in slug if s) if slug else "Terminal"


def _finish(out_dir: str, name: str, transcript: str, title: str, meta: Dict, screen: Optional[str] = None,
            window: Optional[str] = None) -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    log = os.path.join(out_dir, f"{name}.log")
    png = os.path.join(out_dir, f"{name}.png")
    with open(log, "w", encoding="utf-8") as f:
        f.write(transcript + "\n")
    if screen and window == "toolbox":
        render_toolbox(transcript, title, png, files=meta.get("spec_files", []), theme=screen)
        meta = {**meta, "render": "toolbox-frame", "theme": screen}  # composición: texto real de VDMJ, marco del Toolbox
    elif screen:
        render_desktop(transcript, title, png, theme=screen)
        meta = {**meta, "render": "desktop-frame", "theme": screen}  # composición: el texto es real, el marco no
    else:
        render_terminal(transcript, title, png)
    item = {
        "source": "terminal",
        "captured_at": mf.now_iso(),
        "log": mf.rel(out_dir, log),
        "log_sha256": mf.sha256_file(log),
        "image": mf.rel(out_dir, png),
        "image_sha256": mf.sha256_file(png),
        **meta,
    }
    return mf.upsert(out_dir, name, item)


def capture_commands(name: str, commands: Sequence[str], out_dir: str, cwd: Optional[str] = None,
                     timeout: float = 60.0) -> Dict:
    """Ejecuta cada comando, y guarda `<name>.log`, `<name>.png` y el item del manifiesto."""
    lines: List[str] = []
    codes: List[int] = []
    for cmd in commands:
        argv = shlex.split(cmd)
        lines.append(f"$ {cmd}")
        try:
            res = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                                 stdin=subprocess.DEVNULL)
            output, code = (res.stdout + res.stderr).rstrip("\n"), res.returncode
        except FileNotFoundError:
            output, code = f"{argv[0]}: comando no encontrado", 127
        except subprocess.TimeoutExpired:
            output, code = f"(tiempo agotado tras {timeout}s)", 124
        if output:
            lines.extend(output.split("\n"))
        codes.append(code)
    transcript = strip_ansi("\n".join(lines))
    # La imagen no se rotula como "real": la procedencia (comando, fecha, hashes) vive en el manifiesto.
    title = window_title(out_dir)
    return _finish(out_dir, name, transcript, title,
                   {"tool": "shell", "commands": list(commands), "returncodes": codes, "window_title": title})


def capture_vdmj(name: str, spec_files: List[str], commands: List[str], out_dir: str,
                 dialect: str = "vdmpp", release: str = "classic", cwd: Optional[str] = None,
                 screen: Optional[str] = None, window: Optional[str] = None) -> Dict:
    """Sesión interactiva real de VDMJ: el intérprete recibe los comandos y se registra su respuesta."""
    from .vdmj import run_session

    session = run_session(spec_files, commands, dialect=dialect, release=release, cwd=cwd)
    title = f"$ {session.command_line}   ({session.version})"
    return _finish(out_dir, name, session.transcript, title,
                   {"tool": session.version, "commands": list(commands), "spec_files": [os.path.basename(s) for s in spec_files],
                    "returncodes": [session.returncode]}, screen=screen, window=window)


def register_image(item_id: str, image_path: str, out_dir: str, source: str = "manual",
                   base: Optional[str] = None, note: str = "") -> Dict:
    """Registra una imagen que no generó el motor: una captura real tomada a mano ('manual')
    o una versión anotada ('annotated') de otro item, que debe indicar `base`."""
    if source not in ("manual", "annotated"):
        raise ValueError("source debe ser 'manual' o 'annotated'")
    if source == "annotated" and not base:
        raise ValueError("una imagen 'annotated' debe indicar su item base (--base)")
    if not os.path.isfile(image_path):
        raise FileNotFoundError(image_path)
    item = {
        "source": source,
        "captured_at": mf.now_iso(),
        "image": mf.rel(out_dir, image_path),
        "image_sha256": mf.sha256_file(image_path),
        "note": note,
    }
    if base:
        item["base"] = base
    return mf.upsert(out_dir, item_id, item)
