---
name: theory-report-builder
description: Reglas y flujo de trabajo para construir informes academicos formales de Teoria, Trabajos Parciales e Investigacion Formativa (EPIS - UNSA) en Typst, con tipografia Times New Roman, caratula institucional con escudo UNSA, header con logo EPIS, rigor normativo ISO/IEC/IEEE 29119 y evidencias reproducibles.
---

# Theory Report Builder (EPIS - UNSA)

Esta skill define el estandar de diseno, redaccion tecnica y arquitectura para informes academicos formales de cursos de Teoria (como **Calidad de Software**, **Ingenieria de Software**, **Arquitectura de Software**) en la **Escuela Profesional de Ingenieria de Sistemas (EPIS) - Universidad Nacional de San Agustin de Arequipa (UNSA)**.

---

## 🏛️ Caracteristicas de Diseno y Estilo

1. **Tipografia Formal:**
   - Fuente principal: **Times New Roman** (con fallbacks en Linux: *Liberation Serif*, *Tinos*).
   - Monospace: **DejaVu Sans Mono** / *Liberation Mono*.
   - Tamano base: 10.5pt, justificado completo, espaciado de parrafo equilibrado.

2. **Identidad Visual Institucional:**
   - **Caratula Oficial:** Encabezado centrado (UNSA / FIPS / EPIS), escudo oficial de la universidad (`assets/unsa.png`), titulo del trabajo, capitulo tematico, curso, docente, tabla de integrantes con sus roles y pie de pagina con ciudad y anio.
   - **Encabezado en paginas de contenido:** Logo EPIS (`assets/epis.png`) a la izquierda, nombre del curso y tema a la derecha, con linea de division sutil.
   - **Pie de pagina:** Nombre de la universidad y paginacion formal (`Pagina X de Y`).
   - **Colores sobrios:** Granate institucional UNSA (`#7B1113`) y azul marino formal (`#1A365D`) exclusivamente para títulos principales y encabezados de tablas institucionales.
   - **Prohibición estricta de marcadores y cajas de colores tipo IA:** Prohibido el uso de bloques, callouts o resaltadores con fondos de colores llamativos o pasteles (verde, azul claro, amarillo, badges estilo GitHub o prompts de IA). Rompen el estilo profesional institucional. Cualquier nota formal, principio o dictamen debe utilizar tipografía académica sobria, texto oscuro y un filete vertical neutro en escala de grises (`stroke: (left: 2.2pt + luma(100))`), sin fondos coloreados.
   - **Dimensionamiento equilibrado del escudo:** El escudo institucional en la carátula debe mantener un tamaño sobrio (ancho de 3.6cm) para integrarse armónicamente con la jerarquía tipográfica sin saturar la portada.
   - **Tablas con anchos explícitos:** Todas las tablas de trazabilidad, resultados o métricas que contengan nombres de archivos técnicos o firmas de métodos deben definir anchos de columna explícitos (e.g., `columns: (1.1cm, 1.1cm, 4.5cm, 5.5cm, 3.8cm)`) para garantizar cero solapamiento o desborde de texto.

3. **Extensión del informe y especificaciones de la guía:**
   - La plantilla no impone un límite artificial arbitrario en el motor tipográfico; sin embargo, se debe verificar siempre la sección de entregables de la guía de la práctica o trabajo. Si la guía prescribe un rango de páginas (por ejemplo, "4–6 páginas"), se debe informar explícitamente y permitir generar tanto la versión exhaustiva integral como la versión sintetizada conforme a la rúbrica del docente.

---

## 📋 Estructura Obligatoria para Trabajos de Automatizacion (ISO 29119)

1. **Caratula Institucional y Tabla de Contenidos (Indice)**.
2. **Introduccion, Proposito y Resultados de Aprendizaje:**
   - Justificacion de que y por que automatizar.
   - Objetivos medibles y delimitacion del alcance.
3. **Marco Normativo y Estandares de Referencia:**
   - Familia **ISO/IEC/IEEE 29119** (Partes 1 a 5: conceptos, procesos, documentacion, tecnicas y pruebas modular/keyword-driven).
   - Modelo de calidad **ISO/IEC 25010:2023** y calidad del codigo fuente **ISO/IEC 5055:2021**.
   - Estandares web: **W3C WebDriver** y protocolos de automatizacion (Playwright CDP).
4. **Contexto del Caso de Estudio:**
   - Descripcion de la aplicacion evaluada (ej. SIVIRA Web: Vigilancia y Despacho de Suministros Epidemiologicos de Salud Publica).
   - Definicion de los 6 requisitos academicos (R1 a R6).
5. **Plan de Pruebas y Gestion de Riesgos (ISO 29119-2/3):**
   - Criterios de entrada y salida, mitigacion de riesgos, oraculos independientes de prueba.
6. **Diseno de Casos de Prueba (ISO 29119-4):**
   - Especificacion de los 12 casos (T01 a T12) usando particiones de equivalencia, analisis de valores limite y transiciones.
7. **Matriz de Trazabilidad Completa:**
   - Requisito $\leftrightarrow$ Caso $\leftrightarrow$ Script Playwright (Page Object) $\leftrightarrow$ Oraculo $\leftrightarrow$ Evidencia.
8. **Arquitectura de la Suite de Automatizacion (ISO 29119-5):**
   - Separacion estricta entre acciones reutilizables (`pages/`) y datos de prueba (`data/*.json`).
   - Configuracion reproducible (`playwright.config.js`: Chromium, 1 worker, 0 retries).
9. **Resultados de las Tres Pasadas de Ejecucion:**
   - Tablas comparativas por pasada, tiempos, estado de aprobacion (100%), tasa de inestabilidad (*flakiness* = 0%).
10. **Analisis Metrico de Calidad y Retorno de Inversion (ROI):**
    - Cobertura de requisitos, tasa de automatizacion, comparacion tiempo manual vs. automatizado, punto de equilibrio.
11. **Clasificacion de Incidentes y Analisis de Fallos:**
    - Taxonomia de errores: Defectos del producto vs. fallos del script vs. inconsistencias de datos o infraestructura.
12. **Conclusiones y Decision Sustentada de Aceptacion/Rechazo del Alcance**.
13. **Registro de Aportes Individuales y Revision Cruzada:**
    - Cuadro con los 5 roles asignados, responsabilidades y evidencia de revision cruzada entre integrantes.
14. **Referencias Bibliograficas (formato IEEE)**.

---

## 🛠️ Reglas de Redaccion y Evidencias

- **Prosa directa y tecnica:** Evitar introducciones vacias, frases de relleno y adjetivaciones innecesarias.
- **Evidencias reales:** Toda metrica, tiempo y captura debe proceder de ejecuciones reales de la suite Playwright o de la aplicacion.
- **Figuras anotadas:** Las capturas de pantalla de la UI deben mostrar claramente el estado evaluado (ordenamiento, carrito, validaciones, calculo de impuestos).
- **Referencias cruzadas nativas:** Usar `@fig:nombre`, `@lst:nombre`, `@tbl:nombre` en Typst.
