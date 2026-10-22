---
name: academic-slides-builder
description: Construye diapositivas HTML (y su PDF) para exposiciones academicas EPIS - UNSA, SIEMPRE en tema claro y SIN animaciones, desde un project.toml y un content/slides.toml con layouts cerrados y presupuestos de contenido verificados en Chrome. Usar cuando se pida una presentacion, diapositivas, slides o exposicion de un curso.
---

# Academic Slides Builder (EPIS - UNSA)

Pipeline `html-slides`: `inputs/<caso>/` -> `output/<caso>/build/<caso>-slides.{html,pdf}`.
El HTML es un solo archivo (CSS, imagenes y logos incrustados), **sin JavaScript** y **sin recursos externos**. El PDF es vectorial, una diapositiva por pagina a 1920x1080.

## Reglas no negociables

1. **Siempre tema claro.** No existe tema oscuro ni `prefers-color-scheme: dark`. `check_theme` rechaza fondos oscuros y contrastes < 4.5:1.
2. **Cero animaciones.** Prohibidos `animation`, `transition`, `@keyframes`, `scroll-behavior: smooth`, `<script>`. `lint_html` los rechaza.
3. **Un mensaje por diapositiva.** Si no cabe, se divide; nunca se reduce la fuente ni se desborda. El presupuesto de caracteres (`LIMITS` en `src/slides_engine/model.py`) esta calibrado con el peor caso medido en Chrome.
4. **Evidencia real.** Las figuras de resultados salen de `main.py evidence` (`evidence_id`), nunca dibujadas ni editadas. Ver `terminal-evidence`.
5. **Tono academico sobrio**, igual que `lab-report-writing` y `theory-report-builder`: prosa directa, sin relleno ni adjetivos vacios.

## Flujo

```bash
python main.py slides new inputs/<caso>      # esqueleto (project.toml + content/slides.toml)
# editar content/slides.toml
python main.py slides check inputs/<caso>    # contenido, tema y reglas; sin Chrome
python main.py slides build inputs/<caso>    # HTML + PDF; Chrome mide desbordes y fuente minima (24 px)
```

Si la carpeta ya tiene `[theory]`/`[lab]` (informe) y `[slides]` (deck), `run` pide elegir: `python main.py run inputs/<caso> --pipeline html-slides`. `course`, `instructor`, `semester` e integrantes se heredan de `[theory]`/`[lab]`.

## project.toml

```toml
pipeline = "html-slides"
[slides]
title = "..."            # obligatorio
course = "..."; instructor = "..."; semester = "2026-B"
authors = ["Apellidos, Nombres"]
# subtitle, theme = "academic-light", institutional = true (logos UNSA/EPIS),
# footer, lang = "es"|"en", date, file = "content/slides.toml", ratio = "16:9" (unico soportado)
[build]
# name, pdf = true, check = true
```

## Layouts (`content/slides.toml`, una tabla `[[slide]]` por diapositiva)

La primera diapositiva es `title`. Texto en linea: `**negrita**` y `` `codigo` ``. Cualquier layout acepta `notes` (notas del expositor; no salen en el PDF).

| layout | campos | limites |
|---|---|---|
| `title` | title, subtitle | 90 / 170 caracteres |
| `section` | title, subtitle?, number? | 60 / 120 |
| `bullets` | title, lead?, items | 1-6 items de <=110; texto total <=520 |
| `two-col` | title, left{heading, items}, right{...} | heading <=40; 1-4 items de <=60 |
| `figure` | title, image **o** evidence_id, caption, points? | caption <=170; 1-3 points de <=80 |
| `table` | title, header, rows, caption? | 2-5 columnas, 1-6 filas; <=90 caracteres por fila, <=40 por celda |
| `code` | title, code **o** file (+ lines "10-24"), language?, caption? | <=12 lineas de <=80 caracteres |
| `quote` | text, author? | 240 / 70 |
| `stats` | title, items [{value, label}] | 2-4 indicadores; value <=6 caracteres; label <=50 |
| `closing` | title, subtitle?, items? | 50 / 150; <=4 items de <=90 |

Titulos de contenido: <=85 caracteres. Los errores se reportan todos juntos con el numero de diapositiva y una sugerencia si hay un typo.

## Diseno (ui-ux-pro-max)

- Para elegir paleta o tipografia de un tema nuevo: `python .agents/skills/ui-ux-pro-max/scripts/search.py "<consulta>" --design-system -p "<nombre>"`. Usar solo estilo, colores y tipografia; ignorar el "pattern" de landing y los consejos de hover/animacion.
- `academic-light` sigue Swiss Modernism 2.0: azul marino `#1A365D`, granate UNSA `#7B1113`, titulares en serif (Times New Roman / Liberation Serif), cuerpo en Inter / Liberation Sans.
- Un tema nuevo es un CSS en `src/slides_engine/assets/themes/` con tokens en tres capas (primitivos -> `--color-*` semanticos en hex -> `--slide-*` de componente). Debe pasar `check_theme`.
- Tamanos en `dp` (pixel de diseno a 1920x1080; el renderer los convierte a `calc(N * var(--px))`). Minimos: cuerpo 38-44 dp, pie y etiquetas >= 24 dp.

## Anadir un layout

1. Regla y limites en `src/slides_engine/model.py` (`RULES`, `ALLOWED`, `LIMITS`).
2. Plantilla `src/slides_engine/templates/layouts/<layout>.html.j2` y estilos en `assets/base.css`.
3. Su peor caso en `tests/slides_fixtures.py::worst_case_toml`; `python -m unittest tests.test_slides` lo mide en Chrome. Si desborda, bajar el limite, no la fuente.

## Origen de las ideas

Se evaluaron `zarazhangrui/frontend-slides` y `bluedusk/html-slides` (MIT) y **no se usan como dependencia**: sus temas claros son capas sobre CSS oscuro, incluyen animaciones y recursos externos, y su PDF es raster. De ellos se tomo la idea de escenario 16:9 fijo, componentes cerrados con temas en CSS y exportacion a PDF por navegador sin cabeceras.
