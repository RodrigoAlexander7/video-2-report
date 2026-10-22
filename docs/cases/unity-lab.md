# Caso `unity-lab`: reporte .docx de un laboratorio de Unity

**Input** (`inputs/<caso>/`)

```text
project.toml          # [unity] plantilla EPIS, video, título, número, fecha, integrantes
content/report.toml   # bloques: heading, step (texto + figura/código), figure, code; question, conclusion, reference
content/glossary.txt  # (opcional) palabras que la revisión ortográfica no debe marcar
code/*.cs             # código real del proyecto; las imágenes de código salen de aquí
video.mp4             # video de la práctica (ruta en [unity] video)
```

**Output** (`output/<caso>/`): `Reporte_Practica_<NN>_Unity.docx`, `figures/` (PNG finales, `captures.json`, `_review/` con los candidatos de cada captura), `evidence/` (manifiesto verificable e imágenes de código) y `review/` (PDF y hojas de páginas del .docx).

```bash
python main.py unity-lab new inputs/IDSE/lab08
python main.py unity-lab plan inputs/IDSE/lab08          # pasos candidatos con tiempos
python main.py unity-lab check inputs/IDSE/lab08         # sin video: tono, ortografía, citas, código, balance visual
python main.py unity-lab capture inputs/IDSE/lab08       # solo las figuras (caché por especificación y video)
python main.py unity-lab build inputs/IDSE/lab08 --review
python main.py run inputs/IDSE/lab08                     # equivale a build
```

Formato de `report.toml`, opciones de recorte y reglas de estilo: `.agents/skills/unity-lab-report/SKILL.md`.

## Qué mejora respecto a los scripts por laboratorio

| Problema visto | Cómo se evita |
|---|---|
| Capturas del video mal tomadas (movidas, cortadas, a mitad de transición) | Se extraen candidatos en ±3 s alrededor del tiempo, se puntúan por nitidez y estabilidad y el OCR confirma que se vea lo esperado (`expect`). Si no, el build falla con una hoja de revisión |
| Recortes escritos en píxeles que cortan texto | Recorte por panel (pestaña + franjas oscuras de Unity), por `desde/hasta` o por fracciones; nunca corta una línea de texto |
| Flechas que no señalan nada y recuadros con relleno | La anotación se ancla al texto de la interfaz hallado por OCR; contorno fino, sin relleno ni etiqueta, ≤ 25 % del área, ≤ 1 por figura; sin objetivo, no hay anotación |
| Imágenes enormes (hasta 10 in de alto) | Alto máximo 4,6 in; ancho según la forma; si el texto de la interfaz quedaría < 8 pt el build pide recortar |
| Pocas imágenes | Un paso, una imagen; aviso por pasos sin imagen o > 60 palabras por imagen |
| Código pegado como texto | Imagen de editor desde el archivo real, dividida en ≤ 20 líneas con numeración real |
| Texto redundante y genérico | Presupuestos de palabras y revisión de estilo (superlativos, etiquetas, voseo, muletillas, afirmaciones técnicas dudosas) |
| Erratas y referencias sueltas | Ortografía con hunspell es_ES; cada `[n]` existe y cada referencia se cita |
| Páginas con huecos y pies de figura separados de su imagen | Imagen y pie en un párrafo; una fila «no partir» por bloque; `--review` renderiza el .docx y avisa de páginas casi vacías |

## Garantías verificadas por las pruebas

`tests/test_video_figures.py` (OCR, puntuación de fotogramas, recortes, anotaciones) y `tests/test_unity_lab.py` (modelo, estilo, tamaños, división de código, plantilla, caché y un flujo completo con un video sintético y Chrome real).

## Límites conocidos

- La vista previa depende del conversor disponible. Con el `x2t` de ONLYOFFICE se ve lo mismo que en su editor: ignora `cantSplit` y los saltos de página dentro de celdas, así que un texto puede quedar en una página y su figura en la siguiente (el pie siempre queda con su imagen).
- El OCR usa el idioma indicado en `ocr_langs` (por defecto `eng`, la interfaz de Unity en inglés).
- Las anotaciones por `target` exigen que el texto esté visible en el fotograma elegido.
