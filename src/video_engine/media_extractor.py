import os
import subprocess
from PIL import Image, ImageDraw
import sys

# Agregar scripts de la skill
sys.path.append(os.path.join(os.path.dirname(__file__), ".agents/skills/figure-enhancer/scripts"))
from enhance_image import crop_image, draw_focus_box, draw_arrow, add_technical_frame
from config import ReportConfig, DEFAULT_CONFIG

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

    cmd_ffmpeg = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", video_path,
        "-vf", palette_filter,
        output_path
    ]
    subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    gifsicle_bin = subprocess.run(["which", "gifsicle"], capture_output=True, text=True).stdout.strip()
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

def generate_and_enhance_figures(cfg: ReportConfig = DEFAULT_CONFIG):
    media_dir = cfg.media_dir
    os.makedirs(media_dir, exist_ok=True)
    video = cfg.video_path

    # --- FIGURA 1: Inspector con Rigidbody & Constraints enfocados ---
    raw_inspector = os.path.join(media_dir, "raw_unity_inspector.png")
    subprocess.run([
        "ffmpeg", "-y", "-ss", "855", "-i", video, "-vframes", "1", raw_inspector
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    img_insp = Image.open(raw_inspector)
    # Recorte del panel lateral derecho (Inspector de Unity: x 1430 a 1920)
    panel_insp = crop_image(img_insp, (1430, 40, 1918, 970))
    
    # Coordenadas relativas en el panel recortado para 'Constraints -> Freeze Rotation'
    # Constraints está aproximadamente en y: 470 a 535
    w_p, h_p = panel_insp.size
    panel_focused = draw_focus_box(
        panel_insp, 
        (12, 475, w_p - 12, 535), 
        label="Freeze Rotation X, Y, Z",
        color=(230, 57, 70, 255),
        border_width=3
    )

    # Flecha estilizada que señala hacia las casillas activas
    draw = ImageDraw.Draw(panel_focused)
    draw_arrow(
        draw,
        start=(350, 420),
        end=(420, 485),
        color=(230, 57, 70, 255),
        width=4,
        arrowhead_len=18
    )

    panel_final = add_technical_frame(panel_focused)
    final_fig1 = os.path.join(media_dir, "unity_inspector_rigidbody.png")
    panel_final.save(final_fig1)
    print(f"✓ Figura 1 mejorada guardada en {final_fig1}")

    # --- FIGURAS GIF: Recorte enfocado en la vista de juego (Game View) ---
    # En Unity, la vista Game ocupa x: 195 a 1435, y: 40 a 650 aprox.
    # Recortar solo la ventana de simulación elimina paneles inertes y maximiza la acción
    game_crop = "crop=1240:610:195:40"

    g1 = os.path.join(media_dir, "animacion_movimiento_rotacion_error.gif")
    generate_gif(video, 818, 5, g1, crop_filter=game_crop, cfg=cfg)
    print(f"✓ GIF 1 (Enfocado) guardado en {g1}")

    g2 = os.path.join(media_dir, "animacion_movimiento_exitoso.gif")
    generate_gif(video, 942, 5, g2, crop_filter=game_crop, cfg=cfg)
    print(f"✓ GIF 2 (Enfocado) guardado en {g2}")

    g3 = os.path.join(media_dir, "animacion_salto_gato.gif")
    generate_gif(video, 1340, 5, g3, crop_filter=game_crop, cfg=cfg)
    print(f"✓ GIF 3 (Enfocado) guardado en {g3}")

if __name__ == "__main__":
    generate_and_enhance_figures(DEFAULT_CONFIG)
