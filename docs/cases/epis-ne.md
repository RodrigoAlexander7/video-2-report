# Casos EPIS Negocios Electrónicos

## `epis-ne`
Informe institucional de 16 secciones (Lab 05, Distribuidora Inca, SCM con Odoo).

- **Input:** `StudyCase.md` y la plantilla `*.docx` de EPIS-UNSA en `inputs/NE/Lab05/`.
- **Output:** `output/NE/Lab05/Informe_Lab05_Distribuidora_Inca_SCM.docx`.
- **Código:** `src/reports/epis_ne/` (`builder.py` orquesta; `sections_part1.py` y `sections_part2.py` construyen las secciones). Las capturas de prototipos aún no liberados se dejan como placeholders formales.
- **Skill:** `.agents/skills/epis-ne-report-builder/SKILL.md`.

## `epis-ne-short`
Informe corto para la guía de prácticas (una tabla por apartado). Solo explícito:

```toml
# inputs/NE/Lab05-short-report/project.toml
pipeline = "epis-ne-short"
```

- **Input:** `input-template.docx`. **Output:** `output/NE/Lab05-short-report/Informe_Corto_Lab05_Distribuidora_Inca_SCM.docx` (con copia en `output/NE/Lab05/`).

```bash
python main.py run inputs/NE/Lab05
python main.py run inputs/NE/Lab05-short-report
python main.py inspect output/NE/Lab05/Informe_Lab05_Distribuidora_Inca_SCM.docx   # código 1 si hay anomalías
```
