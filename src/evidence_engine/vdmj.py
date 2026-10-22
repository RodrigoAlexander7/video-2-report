# -*- coding: utf-8 -*-
"""Adaptador VDMJ: ejecuta una sesión interactiva real y devuelve la transcripción.

El texto que luego se renderiza como figura sale siempre de aquí: los comandos
se envían al intérprete y la salida se captura tal cual, sin editarla.
"""

import glob
import os
import select
import subprocess
from dataclasses import dataclass
from typing import List, Optional

PROMPT = b"> "


@dataclass
class Session:
    command_line: str
    version: str
    transcript: str
    returncode: Optional[int]


def find_vdmj_jar() -> str:
    """Resuelve el jar de VDMJ: $VDMJ_JAR o el que trae la extensión VDM de VS Code."""
    env = os.environ.get("VDMJ_JAR")
    if env and os.path.isfile(env):
        return env
    pattern = os.path.expanduser(
        "~/.vscode/extensions/overturetool.vdm-vscode-*/resources/jars/vdmj/vdmj-*.jar"
    )
    jars = sorted(j for j in glob.glob(pattern) if "lsp" not in os.path.basename(j))
    if not jars:
        raise FileNotFoundError("No se encontró VDMJ. Define VDMJ_JAR=/ruta/vdmj.jar")
    return jars[-1]


def read_script(path: str) -> List[str]:
    """Lee un script de comandos, ignorando líneas vacías y comentarios '--'."""
    with open(path, encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f if l.strip() and not l.lstrip().startswith("--")]


def _read_until_prompt(fd: int, timeout: float) -> str:
    buf = b""
    while not buf.endswith(PROMPT):
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            raise TimeoutError(f"VDMJ no respondió en {timeout}s. Salida parcial:\n{buf.decode(errors='replace')}")
        chunk = os.read(fd, 4096)
        if not chunk:
            break
        buf += chunk
    return buf.decode("utf-8", errors="replace")


def run_session(spec_files: List[str], commands: List[str], dialect: str = "vdmpp",
                release: str = "classic", timeout: float = 30.0,
                jar: Optional[str] = None, cwd: Optional[str] = None) -> Session:
    """Abre VDMJ en modo interactivo, envía cada comando y arma la transcripción.

    La transcripción reproduce lo que vería el usuario en el terminal:
    cabecera de carga/chequeo, y por cada comando la línea '> cmd' seguida de
    la respuesta literal del intérprete.
    """
    jar = jar or find_vdmj_jar()
    argv = ["java", "-cp", jar, "VDMJ", f"-{dialect}", "-r", release, "-i", *spec_files]
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, cwd=cwd)
    out_fd = proc.stdout.fileno()
    lines: List[str] = []
    try:
        header = _read_until_prompt(out_fd, timeout)
        lines.extend(header[: -len(PROMPT.decode())].rstrip("\n").split("\n"))
        for cmd in commands:
            proc.stdin.write((cmd + "\n").encode("utf-8"))
            proc.stdin.flush()
            reply = _read_until_prompt(out_fd, timeout)
            body = reply[: -len(PROMPT.decode())].rstrip("\n")
            lines.append(f"> {cmd}")
            if body:
                lines.extend(body.split("\n"))
        proc.stdin.write(b"quit\n")
        proc.stdin.flush()
        proc.stdin.close()
        proc.wait(timeout=timeout)
    finally:
        if proc.poll() is None:
            proc.kill()
    version = os.path.basename(jar)
    return Session(" ".join(argv[:1] + ["-cp", os.path.basename(jar), "VDMJ"] + [a if a.startswith("-") else os.path.basename(a) for a in argv[4:]]),
                   version, "\n".join(lines), proc.returncode)
