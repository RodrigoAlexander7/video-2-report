---
name: progressive-tutorial-builder
description: Redacta el desarrollo de un laboratorio como pasos cortos en orden cronológico, cada uno con su imagen o su código, a partir de la transcripción del video y del código fuente. Úsala antes de escribir el report.toml de un laboratorio de Unity (ver unity-lab-report).
---

# Pasos de un laboratorio, directos y visuales

El desarrollo del reporte es una secuencia de pasos, no un tutorial con secciones fijas. El reporte de nota 18 se leía así: una acción, su captura, la siguiente acción. Los reportes anteriores generados por agente bajaron a 14 por lo contrario: párrafos largos, pocas imágenes, el mismo contenido repetido en etapas, cuestionario y conclusiones, y un tono genérico.

## Principios

1. **Un paso, una acción, una imagen.** 1-2 frases (≤ 45 palabras) y su captura o su fragmento de código inmediatamente después. Si un paso necesita más texto, son dos pasos.
2. **Orden del video.** Los tiempos salen de la transcripción (`python main.py unity-lab plan`), no de memoria.
3. **Solo lo que se hizo.** Sin «Objetivo de la etapa», sin introducciones («En esta etapa se…»), sin resumen al cierre de cada etapa. El encabezado ya dice de qué trata.
4. **Voz del reporte de 18**: primera persona del plural y verbos de acción: «Creamos el script», «Marcamos Freeze Rotation». Sin voseo.
5. **Sin adjetivos de valor** (clave, crítico, fundamental, robusto, riguroso, óptimo…) ni apreciaciones personales. Se describe lo que ocurrió y lo que se observó.
6. **Errores y correcciones**: si el video muestra un fallo, un paso para el fallo (con su captura) y otro para la corrección. La causa va en una frase.
7. **Código**: nunca se transcribe. Se referencia `file` + `lines` del código real; el motor lo dibuja como imagen de editor y lo divide si es largo.
8. **Cuestionario y conclusiones**: responden lo que pide la guía en 2-3 frases; las conclusiones salen de lo observado (valores, resultados, el fallo y su arreglo), no de lecciones generales.

## Ejemplo

Malo (genérico y largo):

> **Advertencia Técnica Clave (Ámbito de Clases):** Durante la sesión se cometió el error inicial de anidar `OnCollisionStay` dentro del método `ProcessInput()`. Debido a que Unity invoca estos eventos mágicos por reflexión…

Bueno:

> Habíamos escrito `OnCollisionStay` dentro de `ProcessInput()` y el salto no funcionaba. Lo movimos al nivel de la clase, junto a `Update()`.

## Integración

- `faster-whisper` (`main.py transcribe`): transcripción con tiempos.
- `unity-lab-report`: formato de `report.toml`, figuras por OCR, código como imagen, `check`/`build`/`review`.
- `code-snippet-images`: el motor de imágenes de código.
