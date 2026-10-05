from dataclasses import dataclass
from typing import Optional

@dataclass
class ReportConfig:
    # --- Calidad de GIFs ---
    # Si high_quality es True: 1080p escalado a 960px, 18 fps, paleta completa 256 colores, dithering difuso de alta fidelidad
    # Si high_quality es False: 640px, 12 fps, paleta 128 colores, optimización agresiva
    high_quality_gifs: bool = True
    
    # Parámetros según calidad
    @property
    def gif_fps(self) -> int:
        return 18 if self.high_quality_gifs else 12

    @property
    def gif_scale_width(self) -> int:
        return 960 if self.high_quality_gifs else 640

    @property
    def gif_max_colors(self) -> int:
        return 256 if self.high_quality_gifs else 128

    @property
    def gifsicle_lossy(self) -> int:
        return 30 if self.high_quality_gifs else 80

    # --- Tipografía y Estética de Documento ---
    font_family_body: str = "Times New Roman"
    font_family_code: str = "JetBrains Mono"  # Fallback a Consolas / Courier New si no está instalada
    font_size_body_pt: float = 12.0
    font_size_heading1_pt: float = 14.0
    font_size_heading2_pt: float = 13.0
    font_size_code_pt: float = 9.5
    font_size_caption_pt: float = 10.0

    # Sangría y espaciado
    body_line_spacing: float = 1.25
    paragraph_space_after_pt: float = 6.0
    bullet_indent_inches: float = 0.25
    bullet_sub_indent_inches: float = 0.50

    # Rutas por defecto
    video_path: str = "/home/totora/Documents/PROFESIONAL/video-report/inputs/video/2026-10-04 13-52-34.mp4"
    template_path: str = "/home/totora/Documents/PROFESIONAL/video-report/inputs/input-template.docx"
    output_path: str = "/home/totora/Documents/PROFESIONAL/video-report/Reporte_Practica_02_Unity.docx"
    media_dir: str = "/home/totora/Documents/PROFESIONAL/video-report/media"

# Instancia global por defecto
DEFAULT_CONFIG = ReportConfig(high_quality_gifs=True)
