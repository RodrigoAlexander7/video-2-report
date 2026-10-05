---
name: epis-ne-report-builder
description: Genera informes académicos exhaustivos y profesionales para el curso de Negocios Electrónicos (EPIS - UNSA), cumpliendo estrictamente con la estructura del template institucional (GenericTemplate.docx), rúbricas de evaluación, estilo visual sobrio sin exceso de color y análisis SCM/ERP en Odoo.
---

# EPIS Negocios Electrónicos Report Builder Skill

Esta skill define el estándar pedagógico, metodológico y técnico para redactar y compilar informes académicos formales de la **Escuela Profesional de Ingeniería de Sistemas (EPIS) - Universidad Nacional de San Agustín de Arequipa (UNSA)**, específicamente para la cátedra de **Negocios Electrónicos**.

---

## 🎯 Arquitectura Modular del Código

Todo el motor de generación para este tipo de informes reside de manera aislada y reutilizable dentro de `src/`:

```text
video-report/
├── src/
│   ├── docx_engine/
│   │   ├── helpers.py           # Funciones de estilo sobrio: add_heading, add_p, add_bullet, add_table_custom, add_callout, add_screenshot_placeholder
│   │   └── __init__.py
│   └── reports/
│       └── epis_ne/
│           ├── builder.py       # Orquestador del informe (16 secciones)
│           ├── sections_part1.py # Portada, Índice, Planificación, Organización, Problema, Marco Teórico
│           └── sections_part2.py # Comparativas, Trabajo en equipo, Alternativas, Selección, Prototipo Odoo, Conclusiones, etc.
└── output/
    └── NE/Lab05/
        └── Informe_Lab05_Distribuidora_Inca_SCM.docx
```

---

## 🚀 Ejecución desde la CLI Unificada

Para compilar o regenerar el informe:

```bash
uv run python main.py epis-ne \
  --template inputs/NE/Lab05/GenericTemplate.docx \
  --output output/NE/Lab05/Informe_Lab05_Distribuidora_Inca_SCM.docx
```

---

## 📋 Estructura Obligatoria del Informe (16 Secciones)

1. **Portada Oficial EPIS:**
   - Cabecera oficial UNSA, Escuela Profesional de Ingeniería de Sistemas.
   - Logo/Escudo institucional intacto en alta resolución.
   - Datos del Curso: Negocios Electrónicos.
   - Título del Proyecto: Alineado al caso de estudio empresarial.
   - Integrantes del equipo en orden alfabético con código CUI.
   - Semestre, Docente y Fecha.

2. **Índice General:**
   - Tabla de contenidos estructurada con numeración jerárquica y paginación referencial.

3. **Planificar el tratamiento del problema:**
   - Objetivo General (alineado al caso de estudio).
   - Objetivos Específicos (mínimo 4 a 6, operacionales y verificables).
   - Alcances (delimitación funcional, técnica y organizacional).
   - Condiciones Actuales (entorno operativo, infraestructura y restricciones).

4. **Organizar el trabajo del equipo/grupo:**
   - Organización del equipo (4 roles fundamentales: Coordinador, Portavoz, Secretario, Miembro).
   - Asignación de roles y funciones operativas detalladas por integrante.

5. **Problema:**
   - Descripción del contexto (entorno empresarial, comercial y logístico).
   - Identificar el problema.
   - Enunciar el problema (redacción concisa y precisa).
   - Causas y efectos del problema (árbol de problemas, causas raíz, efectos cuantitativos y cualitativos).

6. **Marco Teórico:**
   - Búsqueda de nueva información (fuentes primarias, IEEE, Scopus, Google Scholar, normas ISO/PMI).
   - Organización de la información recopilada.
   - Conceptos nuevos (mínimo 10 conceptos técnicos rigurosos con autor y año).
   - Ventajas y desventajas de SCM/ERP (mínimo 2 autores citados).
   - Factores críticos de éxito (mínimo 2 autores citados).
   - Arquitectura de TI para distribución y logística.
   - Modelos, metodologías, métodos y técnicas (mínimo 2 autores citados por aspecto).
   - Herramientas relacionadas al problema y habilidades del equipo.
   - Casos de éxito reales documentados en consumo masivo.
   - Antecedentes Investigativos:
     * 4 Tesis de pregrado/posgrado: Título, Autor(es), Año, Problema, Objetivos, Resultados.
     * 4 Artículos científicos indexados con la misma ficha técnica completa.
   - Configuración e instalación de herramientas (Odoo Community en Ubuntu/Docker).
   - Mecanismos para compartir información trabajada.

7. **Comparativa de la selección de aspectos:**
   - Cuadros comparativos exhaustivos con criterios técnicos y ponderación (Modelos, Metodologías, Métodos, Técnicas y Herramientas SCM).
   - Cuadro de habilidades requeridas vs habilidades del equipo.
   - Matriz de proponer y sustentar las TI recabadas.
   - Categorización de TI (Hardware, BD, Redes, SO, Lenguajes).

8. **Trabajar en grupo, colaborativamente:**
   - Cronograma de actividades, matriz de responsabilidades RACI.

9. **Generación de posibles soluciones (Alternativas):**
   - Mínimo 3 alternativas tecnológicas viables respetando el presupuesto límite de S/. 6,000.00:
     * a. Enunciado
     * b. Ventajas (mínimo 3)
     * c. Desventajas (mínimo 3)
     * d. Acciones a ejecutar (mínimo 3)
     * e. Innovación en la propuesta (mínimo 3)
     * f. Costos, plazos y viabilidad

10. **Selección de la mejor alternativa:**
    - Identificación unívoca de la alternativa elegida (Odoo Community Edition).
    - Justificación multicriterio (funcional, tecnológica, estratégica y operativa).
    - Desglose presupuestal detallado que cumpla estrictamente con la restricción de presupuesto.

11. **Presentación de la Solución:**
    - Estrategia de entrega (presentación ejecutiva, video institucional, estructura de pitch).

12. **Prototipo o Análisis Situacional:**
    - Requerimientos de TI detallados.
    - Procedimiento de configuración e instalación en Odoo paso a paso.
    - Pruebas de funcionamiento por flujos de negocio (Compras, Inventario multialmacén, Ventas omnicanal, Despacho y flota).
    - Bloques de reserva visual (*Placeholders* formales) para capturas de pantalla (`[CAPTURA XX: Título, Objetivo y Qué debe observarse]`).
    - Verificación del cumplimiento de requerimientos y cuantificación de beneficios.

13. **Lecciones Aprendidas:**
    - Categorización (Experiencia, Progreso, Entrenamiento, Habilidades, Conocimiento, Práctica, Destrezas).
    - Redacción en tiempo pasado con la estructura metodológica dual.

14. **Conclusiones:**
    - Al menos una conclusión por cada objetivo específico planteado más conclusiones de resultados (mínimo 8).

15. **Referencias:**
    - Mínimo 15 referencias académicas completas (formato IEEE o APA).

16. **Anexos:**
    - Anexo 1: Láminas de presentación de resultados.
    - Anexo 2: Infografía de arquitectura técnica y flujos integrados de la cadena de suministro.
    - Anexo 3: Datos de prueba y configuración inicial del sistema.
    - Autoevaluación cuantitativa del equipo (0-100 puntos).

---

## 🎨 Reglas de Estilo Visual Sobrio (Cero Estridencia)

- **Sin colores saturados:** Texto principal en negro (#000000 / #333333), títulos institucionales en azul marino formal (#1B365D / #2B4C7E).
- **Tablas limpias:** Encabezados en gris oscuro (#2B4C7E o #334155) con texto en blanco, bordes finos (#CBD5E1) y celdas alternadas en gris claro sutil (#F8FAFC).
- **Cajas de llamada y placeholders:** Fondo gris muy claro (#F8FAFC o #EFF6FF), borde tenue (#CBD5E1) y texto técnico riguroso.
- **Sin textos de plantilla docente:** Prohibido conservar instrucciones en rojo o ejemplos en cursiva del docente.
