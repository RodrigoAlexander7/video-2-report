# Generador de reportes por casos

Cada caso es un **pipeline** con entrada y salida delimitadas: se coloca el material en `inputs/<caso>/`, se ejecuta `main.py run` y el resultado queda en `output/<caso>/`. El pipeline se elige por `pipeline = "..."` en el `project.toml` del directorio o, si falta, por los archivos que contiene. Si hay más de un candidato no se adivina: se pide indicarlo.

```bash
python main.py list                       # pipelines disponibles
python main.py describe typst-lab         # contrato: entradas, salida, plantilla
python main.py run inputs/NE/Lab05        # ejecuta el que corresponde
python main.py run inputs/NE/Lab05 --dry-run   # muestra qué usaría, sin ejecutar
```

## Casos

| Pipeline | Input | Output | Doc |
|---|---|---|---|
| `video-report` | video `.mp4` + plantilla `.docx` | `.docx` con figuras anotadas y GIFs | [docs/cases/video-report.md](docs/cases/video-report.md) |
| `unity-lab06` | plantilla `.docx` + figuras (explícito) | `.docx` en 5 etapas | [docs/cases/video-report.md](docs/cases/video-report.md) |
| `epis-ne` | `StudyCase.md` + plantilla EPIS `.docx` | informe de 16 secciones | [docs/cases/epis-ne.md](docs/cases/epis-ne.md) |
| `epis-ne-short` | `input-template.docx` (explícito) | informe corto de la guía | [docs/cases/epis-ne.md](docs/cases/epis-ne.md) |
| `typst-lab` | `project.toml` con `[lab]`, `content/*.typ`, specs y scripts | PDF con evidencia real | [docs/cases/typst-lab.md](docs/cases/typst-lab.md) |
| `html-slides` | `project.toml` con `[slides]` y `content/slides.toml` | HTML + PDF de diapositivas, tema claro y sin animaciones | [docs/cases/html-slides.md](docs/cases/html-slides.md) |
| `unity-lab` | `project.toml` con `[unity]`, `content/report.toml`, `code/` y el video | `.docx` EPIS de laboratorio de Unity: figuras verificadas por OCR, código como imagen, revisión de estilo y vista previa | [docs/cases/unity-lab.md](docs/cases/unity-lab.md) |

Función transversal `code-image`: `snippets.toml` -> imágenes de fragmentos de código con aspecto de editor (tema oscuro por defecto), registradas en el manifiesto y reutilizables en docx, Typst y diapositivas ([docs/cases/code-snippet-images.md](docs/cases/code-snippet-images.md)).

`inputs/templates/user-manual.typ` y `output/autocad-addin-manual/` corresponden al generador de manuales de AutoCAD, función **deprecada**: se conserva, pero ya no recibe mantenimiento ni está registrada como pipeline.

## Estructura

```text
main.py            CLI (list, describe, run, evidence, transcribe, ...)
config.py          Configuración de reportes de video (rutas derivadas de la raíz del repo)
src/
  core/            Registro de pipelines, detección por inputs, project.toml
  docx_engine/     Helpers python-docx (documento y celda) e inspector de .docx
  typst_engine/    Compilador Typst y plantilla informe-laboratorio
  editor_engine/   Imágenes de fragmentos de código con aspecto de editor (Pygments + Chrome)
  slides_engine/   Diapositivas HTML: modelo, render Jinja2, reglas (tema claro, sin animaciones) y Chrome
  video_engine/    Transcripción (faster-whisper), fotogramas por calidad, OCR, recortes por panel y anotaciones ancladas
  unity_lab/       Reporte de laboratorio de Unity (docx): modelo, revisión de estilo, figuras, código, build
  evidence_engine/ Evidencia real: comandos/VDMJ -> log + figura + manifiesto verificable
  reports/         Un paquete por caso (epis_ne, unity_practice, typst_lab, html_slides)
tests/             Pruebas automáticas (unittest)
docs/cases/        Documentación de cada caso
inputs/<caso>/     Material de entrada (no versionado)
output/<caso>/     Resultados: figures/, evidence/, build/ (no versionado)
.agents/           Reglas y skills para agentes
```

## Evidencia real

Las figuras de resultados salen de ejecuciones reales y quedan registradas en `output/<caso>/evidence/manifest.json` (comando, fecha, hashes). `main.py evidence verify` comprueba que nada se editó después de capturarse y que lo que afirma el texto aparece en los logs. Ver `.agents/skills/terminal-evidence/SKILL.md`.

## Instalación

```bash
sudo apt install -y ffmpeg gifsicle poppler-utils tesseract-ocr tesseract-ocr-spa hunspell-es   # y Typst (https://typst.app) para typst-lab; Chrome/Chromium para html-slides y code-image; LibreOffice u ONLYOFFICE para la vista previa de unity-lab
uv sync
```

VDMJ (para evidencia VDM) se toma de la extensión VDM de VS Code o de `VDMJ_JAR=/ruta/vdmj.jar`; requiere Java.

## Pruebas

```bash
python -m unittest discover -s tests -t .
```

## Para agentes

1. No escribas scripts ni salidas en la raíz; todo entregable va en `output/<caso>/`.
2. Reutiliza `src/docx_engine`, `src/typst_engine`, `src/video_engine` y `src/evidence_engine` en lugar de duplicar helpers.
3. Nunca dibujes ni edites capturas de resultados: usa `main.py evidence`.
4. Estilo académico y sobrio, sin colores llamativos. Reglas de redacción en `.agents/skills/lab-report-writing`.
5. Diapositivas: siempre en tema claro y sin animaciones (`.agents/skills/academic-slides-builder`).
6. Fragmentos de código (no el código completo) en un reporte: imagen de editor con `main.py code-image` (`.agents/skills/code-snippet-images`), nunca texto pegado ni captura editada.
7. Reportes de laboratorio de Unity: `main.py unity-lab` (`.agents/skills/unity-lab-report`). Un paso, una imagen; texto directo, sin superlativos ni juicios; `check` sin errores ni avisos y revisar `figures/_review` y `review/` antes de entregar.
8. Los paquetes de Python se instalan en el entorno del proyecto (`uv add`), nunca en el sistema.
