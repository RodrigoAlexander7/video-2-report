import os
import subprocess
from config import ReportConfig, DEFAULT_CONFIG

def generate_gif(video_path: str, start: float, duration: float, output_path: str, cfg: ReportConfig = DEFAULT_CONFIG):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fps = cfg.gif_fps
    width = cfg.gif_scale_width
    colors = cfg.gif_max_colors
    lossy = cfg.gifsicle_lossy

    print(f"Generando GIF: {os.path.basename(output_path)} (HQ={cfg.high_quality_gifs}, {width}px, {fps}fps, {colors} cols)...")

    # ffmpeg con palettegen y paletteuse optimizado
    palette_filter = (
        f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];"
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

    # Optimización adicional con gifsicle si está disponible
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

    print(f"✓ GIF listo: {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")

def generate_all_media(cfg: ReportConfig = DEFAULT_CONFIG):
    media_dir = cfg.media_dir
    os.makedirs(media_dir, exist_ok=True)
    video = cfg.video_path

    # Captura Inspector
    cap1 = os.path.join(media_dir, "unity_inspector_rigidbody.png")
    subprocess.run([
        "ffmpeg", "-y", "-ss", "145", "-i", video, "-vframes", "1", cap1
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # GIF 1: Torque / Desbalance (818s, 5s)
    g1 = os.path.join(media_dir, "animacion_movimiento_rotacion_error.gif")
    generate_gif(video, 818, 5, g1, cfg)

    # GIF 2: Movimiento corregido (942s, 5s)
    g2 = os.path.join(media_dir, "animacion_movimiento_exitoso.gif")
    generate_gif(video, 942, 5, g2, cfg)

    # GIF 3: Salto continuo (1340s, 5s)
    g3 = os.path.join(media_dir, "animacion_salto_gato.gif")
    generate_gif(video, 1340, 5, g3, cfg)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extractor de media y GIFs para el reporte")
    parser.add_argument("--low-quality", action="store_true", help="Desactiva HQ para generar GIFs más livianos")
    args = parser.parse_args()

    cfg = ReportConfig(high_quality_gifs=not args.low_quality)
    generate_all_media(cfg)
