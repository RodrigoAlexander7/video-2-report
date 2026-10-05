---
name: figure-enhancer
description: Optimiza, recorta de forma inteligente y anota figuras técnicas (flechas, badges, recuadros de enfoque) para reportes de laboratorio e ingeniería.
---

# Figure Enhancer Skill

Esta skill proporciona herramientas y convenciones deterministas para mejorar capturas de pantalla de software, simuladores o IDEs antes de insertarlas en reportes técnicos y académicos.

## ¿Por qué usarla?
Al insertar capturas de pantalla completa (ej. 1920x1080) en un documento Word/PDF:
1. El texto de la interfaz queda minúsculo e ilegible.
2. El lector no sabe a qué botón, parámetro o línea prestar atención.
3. El documento luce descuidado con imágenes saturadas de paneles irrelevantes.

## Capacidades

1. **Recorte de Zona de Interés (`crop`):**
   Aísla el panel relevante (Inspector, Terminal, Ventana Game, código fuente).
2. **Cajas de Enfoque con Badge (`draw_focus_box`):**
   Destaca parámetros específicos con un marco nítido y fondo traslúcido.
3. **Flechas Vectoriales Estilizadas (`draw_arrow`):**
   Apunta con exactitud a casillas de verificación, menús desplegables o botones clave.
4. **Borde Técnico Sutil (`add_technical_frame`):**
   Enmarca la figura para evitar que bordes blancos se fundan con el papel del reporte.

## Uso en Código Python

```python
from PIL import Image, ImageDraw
from enhance_image import crop_image, draw_focus_box, draw_arrow, add_technical_frame

img = Image.open("screenshot.png")

# 1. Recortar panel deseado (Inspector en Unity)
panel = crop_image(img, (1420, 40, 1920, 1040))

# 2. Resaltar parámetro (ej: Freeze Rotation)
highlighted = draw_focus_box(panel, (15, 475, 485, 545), label="Freeze Rotation")

# 3. Dibujar flecha indicativa
draw = ImageDraw.Draw(highlighted)
draw_arrow(draw, start=(430, 420), end=(360, 490), color=(230, 57, 70, 255), width=4)

# 4. Guardar
highlighted.save("figura_optimizada.png")
```

## Formato de Prompt Recomendado para Solicitar Mejoras
Para pedirle al agente que mejore una figura, utiliza la siguiente plantilla:

```markdown
Por favor mejora la figura de [Nombre de Componente / Ventana]:
- Recorta solo la sección de [Inspector / Vista Game / Consola / Código].
- Agrega un recuadro de enfoque en [nombre del parámetro o valor].
- Agrega una flecha señalando [el botón o casilla clave].
- Mantén la estética sobria y fondo legible.
```
