# Caso `html-slides`: diapositivas HTML en tema claro y PDF

**Input** (`inputs/<caso>/`)

```text
project.toml          # [slides] titulo, curso, autores, tema; [build] opciones
content/slides.toml   # una tabla [[slide]] por diapositiva (layout cerrado)
figures/ code/        # imagenes y fuentes que las diapositivas referencian
```

**Output** (`output/<caso>/build/`): `<caso>-slides.html` (un solo archivo, sin JavaScript) y `<caso>-slides.pdf` (una diapositiva por pagina, 1920x1080, vectorial). Las figuras con `evidence_id` se leen de `output/<caso>/evidence/manifest.json`.

```bash
python main.py slides new inputs/mi-deck       # esqueleto
python main.py slides check inputs/mi-deck     # contenido, tema y reglas (sin Chrome)
python main.py run inputs/mi-deck              # o: slides build; HTML + PDF
```

Requiere Chrome o Chromium (`CHROME_BIN=/ruta` si no esta en el PATH). Si la carpeta tambien es un informe (`[theory]`/`[lab]`), elegir: `--pipeline html-slides`.

## Garantias (verificadas en cada build)

| Regla | Como se comprueba |
|---|---|
| Siempre tema claro | `check_theme`: fondos con luminancia alta y contraste WCAG >= 4.5:1; sin `prefers-color-scheme: dark` |
| Sin animaciones ni JS | `lint_html`: sin `animation`, `transition`, `@keyframes`, `scroll-behavior: smooth`, `<script>` ni recursos externos |
| Nada se desborda | presupuestos por caracteres (`LIMITS`) + medicion en Chrome a 1920x1080 por diapositiva |
| Texto legible | fuente minima 24 px medida en Chrome |
| PDF completo | el numero de paginas del PDF debe igualar el de diapositivas |

## project.toml

```toml
pipeline = "html-slides"

[slides]
title = "Automatizacion de Pruebas E2E"      # obligatorio
course = "Calidad de Software"
instructor = "Mg. ..."
semester = "2026-B"
authors = ["Apellidos, Nombres"]
# subtitle, theme = "academic-light", institutional = true, footer, lang = "es", date, file, ratio = "16:9"

[build]
# name = "deck", pdf = true, check = true
```

`course`, `instructor`, `semester` y los integrantes se heredan de `[theory]`/`[lab]` si existen. Los layouts, sus campos y limites estan en `.agents/skills/academic-slides-builder/SKILL.md`.

## Codigo

`src/slides_engine/` (modelo, renderer Jinja2, reglas, Chrome) y `src/reports/html_slides/` (pipeline y esqueleto). Pruebas: `python -m unittest tests.test_slides` (incluye el peor caso de cada layout medido en Chrome).
