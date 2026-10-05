#!/usr/bin/env python3
"""
Módulo determinista para optimización, recorte y anotación visual de figuras técnicas.
Permite:
- Recortar regiones de interés (Crop inteligente).
- Resaltar componentes con cajas delimitadoras redondeadas / badges.
- Dibujar flechas vectoriales estilizadas apuntando a controles específicos.
- Aplicar bordes técnicos sutiles.
"""

import math
from typing import Tuple, List, Optional
from PIL import Image, ImageDraw, ImageFont

COLOR_ACCENT_RED = (230, 57, 70, 255)       # #E63946
COLOR_ACCENT_BLUE = (27, 54, 93, 255)      # #1B365D
COLOR_ACCENT_AMBER = (244, 162, 97, 255)    # #F4A261
COLOR_BOX_BG = (230, 57, 70, 45)           # Fondo semitransparente

def crop_image(img: Image.Image, box: Tuple[int, int, int, int]) -> Image.Image:
    """Recorta la imagen a la tupla (left, upper, right, lower)."""
    return img.crop(box)

def draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: Tuple[int, int],
    end: Tuple[int, int],
    color: Tuple[int, int, int, int] = COLOR_ACCENT_RED,
    width: int = 5,
    arrowhead_len: int = 22,
    arrowhead_angle_deg: float = 30.0
):
    """Dibuja una flecha limpia con punta poligonal orientada desde start hasta end."""
    x0, y0 = start
    x1, y1 = end
    
    # Línea principal
    draw.line([(x0, y0), (x1, y1)], fill=color, width=width)
    
    # Ángulo del vector
    angle = math.atan2(y1 - y0, x1 - x0)
    angle_rad = math.radians(arrowhead_angle_deg)
    
    # Puntos de la cabeza triangular
    left_x = x1 - arrowhead_len * math.cos(angle - angle_rad)
    left_y = y1 - arrowhead_len * math.sin(angle - angle_rad)
    right_x = x1 - arrowhead_len * math.cos(angle + angle_rad)
    right_y = y1 - arrowhead_len * math.sin(angle + angle_rad)
    
    draw.polygon([(x1, y1), (left_x, left_y), (right_x, right_y)], fill=color)

def draw_focus_box(
    img: Image.Image,
    box: Tuple[int, int, int, int],
    label: Optional[str] = None,
    color: Tuple[int, int, int, int] = COLOR_ACCENT_RED,
    border_width: int = 4,
    fill_alpha: int = 35
) -> Image.Image:
    """Dibuja un marco de enfoque con relleno semitransparente y etiqueta opcional."""
    # Convertir a RGBA para soportar transparencias
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    x0, y0, x1, y1 = box
    fill_color = (color[0], color[1], color[2], fill_alpha)
    
    # Relleno tenue
    draw_overlay.rectangle([x0, y0, x1, y1], fill=fill_color, outline=color, width=border_width)
    
    # Badge de etiqueta si se proporciona
    if label:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except Exception:
            font = ImageFont.load_default()
        
        # Medir tamaño del texto
        bbox = draw_overlay.textbbox((x0, y0 - 24), label, font=font)
        badge_rect = [bbox[0] - 6, bbox[1] - 3, bbox[2] + 6, bbox[3] + 3]
        draw_overlay.rectangle(badge_rect, fill=color)
        draw_overlay.text((x0, y0 - 24), label, fill=(255, 255, 255, 255), font=font)
        
    result = Image.alpha_composite(base, overlay)
    return result.convert("RGB")

def add_technical_frame(img: Image.Image, border_color=(203, 213, 225), border_width=1) -> Image.Image:
    """Añade un borde sutil alrededor de la imagen para integrarla con elegancia en el documento."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for i in range(border_width):
        draw.rectangle([i, i, w - 1 - i, h - 1 - i], outline=border_color)
    return img
