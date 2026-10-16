# -*- coding: utf-8 -*-
"""Construye la plantilla visual del Toolbox a partir de una captura real.

La plantilla (assets/toolbox_template.png) es la ventana del Toolbox recortada de una
captura real (lab04), con las zonas dinámicas en blanco (árbol del Manager y texto del
intérprete) y reparados los bordes tapados por una anotación roja de la captura original.
Solo se ejecuta para regenerar el asset; el render usa el PNG ya construido.
"""

from PIL import Image

# Rectángulo de la ventana dentro de la captura original (1918x1078)
WINDOW = (82, 32, 1887, 1046)
# Zona ocupada por la anotación roja de la captura original (no tocar la barra de herramientas)
ANNOTATION = (388, 118, 982, 384)
# Zonas dinámicas, en coordenadas de la captura original
ANNOTATION = (388, 118, 982, 384)  # recuadro rojo de la captura original: no tocar la barra de herramientas
INTERP_TEXT = (407, 148, 1879, 538)
MANAGER_LIST = (92, 199, 394, 1009)
PROMPT = (408, 547, 440, 567)
WHITE = (255, 255, 255)


def _is_red(p):
    r, g, b = p
    return r > 150 and g < 110 and b < 110 and r - max(g, b) > 80


def build(source_png: str, out_png: str) -> str:
    im = Image.open(source_png).convert("RGB")
    px = im.load()
    w, h = im.size
    # máscara de píxeles de la anotación (con 1 px de margen por el antialias)
    red = [[_is_red(px[x, y]) for x in range(w)] for y in range(h)]
    mask = set()
    ax0, ay0, ax1, ay1 = ANNOTATION
    for y in range(ay0, ay1):
        for x in range(ax0, ax1):
            if red[y][x]:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        mask.add((x + dx, y + dy))
    src = im.copy()
    sp = src.load()
    for (x, y) in mask:
        if not (0 <= x < w and 0 <= y < h):
            continue
        if x < 407 and y >= 147:          # borde izquierdo: copiar de filas limpias más abajo
            px[x, y] = sp[x, 400]
        elif x < 400:                      # cabecera: copiar del píxel limpio a la izquierda
            px[x, y] = sp[391, y]
        else:                              # bordes superior y derecho: copiar de la derecha
            px[x, y] = sp[981, y]
    # zonas dinámicas en blanco
    for (x0, y0, x1, y1) in (INTERP_TEXT, MANAGER_LIST, PROMPT):
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[x, y] = WHITE
    im.crop(WINDOW).save(out_png)
    return out_png


if __name__ == "__main__":
    import sys
    build(sys.argv[1], sys.argv[2])
