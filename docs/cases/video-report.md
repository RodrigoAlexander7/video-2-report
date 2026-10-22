# Casos con video: `video-report` y `unity-lab06`

## `video-report`
Transforma un video de demostración en un reporte Word por etapas, con figuras anotadas y GIFs.

- **Input:** `*.mp4` y una plantilla `*.docx` en el directorio (o `video`/`template` en `project.toml`). Opcional `stages` con un JSON de hitos.
- **Output:** `output/<caso>/Reporte_<caso>.docx` y `output/<caso>/figures/`.
- **Hitos:** por defecto se usan los de la práctica Unity 02 (`DEFAULT_STAGES` en `src/video_engine/media_extractor.py`). Se reemplazan con un JSON de la misma forma: `frames` (tiempo, recorte, cajas, flechas) y `gifs` (tiempo, duración, recorte).
- **Desde lo que se dice en el video:** `main.py transcribe video.mp4 --out output/<caso>/.cache/t`, luego `timeline_analyzer.search_keywords_in_timeline` y `media_extractor.frames_from_manifest` extraen un frame por hito.

```bash
python main.py run inputs/<caso>
python main.py video-report --video v.mp4 --template p.docx --stages hitos.json
```

## `unity-lab06`
Reporte de la práctica 06 de Unity (rotación y `Time.deltaTime`) en cinco etapas. Se activa solo de forma explícita:

```toml
# inputs/IDSE/lab06/project.toml
pipeline = "unity-lab06"
[unity-lab06]
template = "../IDSE-Lab05/input-template.docx"   # relativa al proyecto
```

Las figuras deben existir en `output/<caso>/figures` (las genera `src/reports/unity_practice/generate_lab06_figures.py`).

Contrato pedagógico: `.agents/skills/progressive-tutorial-builder/SKILL.md`. Recortes y flechas: `.agents/skills/figure-enhancer/SKILL.md`.
