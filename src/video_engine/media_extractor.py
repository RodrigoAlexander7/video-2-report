import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Union

from PIL import Image, ImageDraw

# Agregar scripts de la skill y la raíz del repo (para importar config)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
for _p in (project_root, os.path.join(project_root, ".agents/skills/figure-enhancer/scripts")):
    if _p not in sys.path:
        sys.path.append(_p)
from enhance_image import crop_image, draw_focus_box, draw_arrow, add_technical_frame
from config import ReportConfig, DEFAULT_CONFIG

# Especificación declarativa de figuras. Estos valores reproducen el comportamiento original
# (práctica Unity 02); se pueden sustituir con un JSON de la misma forma (ver load_stages).
# Coordenadas negativas en un rect se interpretan desde el borde opuesto (-12 = ancho - 12).
DEFAULT_STAGES: Dict[str, Any] = {
    "frames": [
        {
            "name": "unity_inspector_rigidbody.png",
            "t": 855,
            "crop": [1430, 40, 1918, 970],
            "boxes": [{"rect": [12, 475, -12, 535], "label": "Freeze Rotation X, Y, Z"}],
            "arrows": [{"start": [350, 420], "end": [420, 485]}],
        }
    ],
    "gifs": [
        {"name": "animacion_movimiento_rotacion_error.gif", "t": 818, "duration": 5, "crop": "crop=1240:610:195:40"},
        {"name": "animacion_movimiento_exitoso.gif", "t": 942, "duration": 5, "crop": "crop=1240:610:195:40"},
        {"name": "animacion_salto_gato.gif", "t": 1340, "duration": 5, "crop": "crop=1240:610:195:40"},
    ],
}
ACCENT = (230, 57, 70, 255)


def load_stages(stages: Union[None, str, Dict[str, Any]]) -> Dict[str, Any]:
    """Acepta None (valores por defecto), una ruta a JSON o un dict ya cargado."""
    if stages is None:
        return DEFAULT_STAGES
    if isinstance(stages, dict):
        return stages
    with open(stages, encoding="utf-8") as f:
        return json.load(f)


def _run_ffmpeg(args: List[str]) -> None:
    res = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg falló ({' '.join(args[:6])} ...):\n{res.stderr[-600:]}")


def extract_frame(video_path: str, t: float, out_path: str) -> str:
    """Extrae un único frame del video en el segundo t."""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    _run_ffmpeg(["-ss", str(t), "-i", video_path, "-vframes", "1", out_path])
    return out_path

def generate_gif(video_path: str, start: float, duration: float, output_path: str, crop_filter: str = "", cfg: ReportConfig = DEFAULT_CONFIG):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fps = cfg.gif_fps
    width = cfg.gif_scale_width
    colors = cfg.gif_max_colors
    lossy = cfg.gifsicle_lossy

    # Si hay filtro de recorte (ej. enfocar solo la ventana Game o el personaje)
    crop_str = f"{crop_filter}," if crop_filter else ""

    palette_filter = (
        f"{crop_str}fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];"
        f"[s0]palettegen=max_colors={colors}:stats_mode=diff[p];"
        f"[s1][p]paletteuse=dither=bayer:bayer_scale=2:diff_mode=rectangle"
    )

    _run_ffmpeg(["-ss", str(start), "-t", str(duration), "-i", video_path, "-vf", palette_filter, output_path])

    gifsicle_bin = shutil.which("gifsicle")
    if gifsicle_bin:
        temp_opt = output_path + ".opt.gif"
        cmd_gifsicle = [
            gifsicle_bin,
            "-O3",
            f"--lossy={lossy}",
            "-o", temp_opt,
            output_path
        ]
        res = subprocess.run(cmd_gifsicle, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(temp_opt):
            os.replace(temp_opt, output_path)

def _abs(v: int, size: int) -> int:
    return size + v if v < 0 else v


def _annotated_frame(video: str, spec: Dict[str, Any], media_dir: str) -> str:
    raw = os.path.join(media_dir, "raw_" + os.path.splitext(spec["name"])[0] + ".png")
    extract_frame(video, spec["t"], raw)
    img = Image.open(raw)
    if spec.get("crop"):
        img = crop_image(img, tuple(spec["crop"]))
    w, h = img.size
    for box in spec.get("boxes", []):
        x0, y0, x1, y1 = box["rect"]
        img = draw_focus_box(img, (_abs(x0, w), _abs(y0, h), _abs(x1, w), _abs(y1, h)),
                             label=box.get("label", ""), color=ACCENT, border_width=3)
    draw = ImageDraw.Draw(img)
    for arrow in spec.get("arrows", []):
        draw_arrow(draw, start=tuple(arrow["start"]), end=tuple(arrow["end"]),
                   color=ACCENT, width=4, arrowhead_len=18)
    final = add_technical_frame(img)
    out = os.path.join(media_dir, spec["name"])
    final.save(out)
    return out


def generate_and_enhance_figures(cfg: ReportConfig = DEFAULT_CONFIG,
                                 stages: Union[None, str, Dict[str, Any]] = None) -> List[str]:
    """Genera figuras anotadas y GIFs del video según `stages` (por defecto, la práctica Unity 02)."""
    spec = load_stages(stages)
    media_dir = cfg.media_dir
    os.makedirs(media_dir, exist_ok=True)
    video = cfg.video_path
    produced: List[str] = []

    for n, frame in enumerate(spec.get("frames", []), 1):
        out = _annotated_frame(video, frame, media_dir)
        produced.append(out)
        print(f"✓ Figura {n} mejorada guardada en {out}")

    for n, gif in enumerate(spec.get("gifs", []), 1):
        out = os.path.join(media_dir, gif["name"])
        generate_gif(video, gif["t"], gif.get("duration", 5), out, crop_filter=gif.get("crop", ""), cfg=cfg)
        produced.append(out)
        print(f"✓ GIF {n} guardado en {out}")
    return produced


def frames_from_manifest(video_path: str, manifest_path: str, out_dir: str, offset: float = 0.0) -> List[Dict[str, Any]]:
    """Extrae un frame por cada hito del manifiesto de timeline_analyzer (start + offset).

    Devuelve el manifiesto enriquecido con la ruta de cada frame; así los timestamps salen
    de lo que se dice en el video y no están escritos a mano en el código.
    """
    with open(manifest_path, encoding="utf-8") as f:
        matches = json.load(f)
    os.makedirs(out_dir, exist_ok=True)
    result = []
    for n, m in enumerate(matches, 1):
        t = max(0.0, float(m["start"]) + offset)
        slug = re.sub(r"[^a-z0-9]+", "_", m.get("keyword", "hito").lower()).strip("_")
        out = os.path.join(out_dir, f"{n:02d}_{slug}_{int(t)}s.png")
        extract_frame(video_path, t, out)
        result.append({**m, "t": t, "frame": out})
    return result


if __name__ == "__main__":
    generate_and_enhance_figures(DEFAULT_CONFIG)
