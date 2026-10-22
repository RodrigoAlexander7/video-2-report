---
name: unity-lab-report
description: Genera el reporte .docx de un laboratorio de Unity (IDSE, plantilla EPIS) a partir del video de la práctica, el código del proyecto y un report.toml, con figuras recortadas y verificadas por OCR, código como imagen de editor, texto directo y revisión visual. Usar al armar o mejorar cualquier reporte de laboratorio de Unity o de videojuegos.
---

# Reporte de laboratorio de Unity

Pipeline `unity-lab`: `inputs/<caso>/` -> `output/<caso>/Reporte_Practica_<NN>_Unity.docx` (+ `figures/`, `evidence/`, `review/`).
El profesor califica sobre todo lo **visual**: el reporte de nota 18 tenía ~40 palabras por imagen y una imagen por paso. Este flujo apunta a eso.

## Flujo

```bash
python main.py unity-lab new inputs/IDSE/lab08          # project.toml + content/report.toml de ejemplo
python main.py unity-lab plan inputs/IDSE/lab08         # pasos candidatos con su tiempo, desde la transcripción
# escribir content/report.toml; copiar el código a code/
python main.py unity-lab check inputs/IDSE/lab08        # tono, ortografía, citas, código, balance visual (sin video)
python main.py unity-lab capture inputs/IDSE/lab08      # figuras del video; hojas de revisión en output/<caso>/figures/_review/
python main.py unity-lab build inputs/IDSE/lab08 --review   # .docx + PDF + hojas de páginas en output/<caso>/review/
```

Corregir hasta que `check` no dé errores **ni avisos**. Mirar `figures/_review/<id>.png` (candidatos y recorte final) y `review/hoja-N.png` (páginas del .docx) antes de entregar.

## project.toml

```toml
pipeline = "unity-lab"
[unity]
template = "../IDSE-Lab05/input-template.docx"   # tabla EPIS: INFORMACIÓN BÁSICA ... REFERENCIAS
video = "video.mp4"
title = "Trabajo con Audio Source y Sonidos"
number = "07"
date = "16/10/2026"
members = ["Nombres Apellidos"]
# course, term = "2026 - B", level = "Octavo VIII", time, instructor, video_link
# theme = "dark" (código: "dark" por defecto o "light"), ocr_langs = "eng" (idioma de la interfaz de Unity)
```

## report.toml (bloques cerrados)

- `[[block]] kind = "heading"` (`level` 1 o 2): se numera solo (1., 1.1).
- `kind = "step"`: `text` (1-2 frases, ≤ 45 palabras) + `[block.figure]` y/o `[block.code]`.
- `kind = "figure"` / `kind = "code"`: solo imagen.
- `[[question]] q/a` (respuesta ≤ 90 palabras), `[[conclusion]] text` (≤ 4, ≤ 55 palabras), `[[reference]] text` (IEEE; se cita como `[1]`).
- En el texto: `{fig:id}` -> «Figura N», `**negrita**`, `` `código` ``. Nunca escribir números de figura a mano.

### Figura del video

```toml
[block.figure]
id = "rigidbody"            # nombre del archivo y de {fig:id}
t = "2:05"                  # segundo aproximado: la herramienta elige el fotograma más nítido y quieto de ±3 s
expect = ["Rigidbody"]      # textos que deben verse; si no aparecen, el build falla y deja la hoja de revisión
caption = "Componente Rigidbody en el Inspector."     # qué muestra, sin interpretar (≤ 28 palabras)
[block.figure.crop]
panel = "inspector"         # inspector | hierarchy | project | console | scene | game (por el título de su pestaña)
desde = "Rigidbody"         # texto donde empieza el recorte dentro del panel
hasta = "Capsule Collider"  # texto donde termina (o height = 330 px desde el borde superior)
[block.figure.annotate]     # opcional: UNA anotación, contorno fino sin relleno ni etiqueta
target = "Freeze Rotation"  # texto de la interfaz (se ubica por OCR); extend = [0, 0, 60, 0] para incluir el valor
```

Otras formas de recorte: `around = "texto"` + `margin = [px, px]`, o `rect = [x0, y0, x1, y1]` en fracciones del fotograma (útil para la vista Game). `legible = false` para escenas del juego sin texto que leer. `kind = "pair"` (dos `[[block.figure.frames]]`, antes/después lado a lado), `kind = "strip"` (`t_start`, `t_end`, `count` 2-4 fotogramas) reemplazan al GIF; `kind = "gif"` solo si el movimiento es imprescindible (no se anima al imprimir ni al exportar a PDF).

### Código

```toml
[block.code]
id = "movimiento"
file = "code/CatControl.cs"   # archivo real; el LLM no copia código al reporte
lines = "13-30"               # o ["13-17", "24-27"] (⋯ entre tramos); max_lines = 20 por imagen
focus = [24, 25]              # líneas resaltadas
dedent = true                 # quita la sangría común si el fragmento está muy anidado
```

Un fragmento largo se divide solo en imágenes de ≤ 20 líneas, cortando en llaves o líneas en blanco y conservando la numeración real. Si el paso muestra un estado distinto del archivo final (p. ej. antes de corregir un error), guardar esa versión como `code/paso-3.cs`.

## Reglas de estilo (las hace cumplir `check`)

1. **Un paso, una imagen.** Más de ~60 palabras por imagen o un paso sin imagen: aviso.
2. **Frases directas en primera persona del plural**, como el reporte de 18: «Agregamos un Rigidbody al GameObject raíz de Mango.» Sin voseo, sin muletillas («En esta etapa se…», «Cabe destacar»), sin etiquetas en Mayúsculas Iniciales con dos puntos («Advertencia Técnica Clave (Ámbito de Clases):»).
3. **Sin superlativos ni juicios**: clave, crítico, fundamental, indispensable, riguroso, robusto, óptimo, sinergia, paradigma, trascendencia, mágico… Di el hecho. Sin apreciaciones personales («creemos que», «nos parece»).
4. **Sin redundancia**: el cuestionario responde lo que pregunta la guía en 2-3 frases; las conclusiones salen de lo observado y no repiten los pasos.
5. **Pies de figura que describen**, no que concluyen.
6. **Referencias**: cada `[n]` existe y cada referencia se cita; deben ser de lo que se usó en la práctica (nada de cámaras o luces en una práctica de física).
7. **Ortografía y afirmaciones técnicas**: diccionario hunspell es_ES + glosario de Unity + identificadores del código + textos de la interfaz declarados en las figuras. Términos nuevos: `content/glossary.txt` (una palabra por línea). `Update()` corre una vez por fotograma, no «cada milisegundo».
8. **Evidencia**: las capturas se registran en `output/<caso>/evidence/manifest.json` (`source = "video"`, segundo elegido, textos hallados). `main.py evidence verify` detecta cambios.

## Tamaño y legibilidad (build)

- Alto máximo 4,6 in por captura y 5 in por imagen de código; ancho según la forma.
- El texto de la interfaz debe medir ≥ 8 pt en el papel: si una captura es demasiado grande para mostrarse completa, el build falla y pide recortar (`crop.panel` con `desde/hasta` o `height`).
- Imágenes reducidas a 220 dpi; imagen y pie en un solo párrafo.
- Cada bloque va en su propia fila de la tabla marcada «no partir» (Word la respeta; ONLYOFFICE no siempre, y entonces el pie sigue pegado a su imagen pero el texto puede quedar en la página anterior).

## Anotaciones (reglas de `video_engine/annotate.py`)

Contorno fino del color institucional, sin relleno ni etiqueta dentro de la imagen; ≤ 25 % del área; ≤ 1 por figura; la flecha termina a 6 px del objetivo. Normalmente no hace falta anotar: el reporte de nota 18 no tenía ninguna. Anotar solo cuando el control es pequeño y el lector podría no encontrarlo.

## Grabar mejor desde el origen

- Pausar ~1 s después de cada acción: da fotogramas quietos y nítidos.
- Dejar fijo el diseño de ventanas de Unity y la interfaz en un solo idioma (`ocr_langs`).
- Nombrar cada paso en voz alta («ahora agregamos el Rigidbody»): `plan` los detecta en la transcripción.
- Grabar a 1080p o más; las pestañas Inspector/Hierarchy/Project visibles sirven para el recorte por panel.

## Dependencias

Solo herramientas ya instaladas: `ffmpeg`, `tesseract` (+ `tesseract-ocr-spa` si la interfaz está en español), Chrome (imágenes de código), `pdftoppm`, hunspell `es_ES` (`/usr/share/hunspell`). Para `--review`: LibreOffice (`soffice`) o ONLYOFFICE Desktop Editors (se usa su conversor `x2t`, nativo o flatpak). Paquetes de Python: solo los del entorno del proyecto (`uv sync`).

## Código

`src/unity_lab/` (modelo, estilo, figuras, código, build), `src/video_engine/{ocr,frames,crops,annotate}.py`, `src/editor_engine/` (imágenes de código), `src/docx_engine/block_rows.py`, `src/core/docx_render.py` (vista previa). Pruebas: `python -m unittest tests.test_unity_lab tests.test_video_figures`.
