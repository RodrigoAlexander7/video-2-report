// =============================================================================
// Plantilla "informe-teoria" (formato institucional UNSA / FIPS / EPIS)
// Disenada para Trabajos Parciales, Informes de Teoria e Investigacion Formativa
//
// Tipografia: Times New Roman / Liberation Serif / Tinos
// Caratula formal con escudo oficial UNSA y tabla de integrantes con roles.
// Encabezado sobrio con logo EPIS y pie de pagina con paginacion formal.
// Sin limite artificial de paginas; soporte para analisis exhaustivo y evidencias.
// =============================================================================

#let default-config = (
  course: "Calidad de Software",
  title: "Trabajo Parcial",
  subtitle: "Automatizacion de Pruebas de Software E2E",
  chapter: "Capitulo 6",
  instructor: "Docente del Curso",
  semester: "2026-B",
  year: "2026",
  city: "Arequipa",
  country: "Peru",
  members: (), // array de strings o dicts (name, role, cui)
  date: none,
  institution: (
    "UNIVERSIDAD NACIONAL DE SAN AGUSTIN DE AREQUIPA",
    "FACULTAD DE INGENIERIA DE PRODUCCION Y SERVICIOS",
    "ESCUELA PROFESIONAL DE INGENIERIA DE SISTEMAS",
  ),
  logo-cover: "unsa",
  logo-header: "epis",
  font: ("Times New Roman", "Liberation Serif", "Tinos"),
  mono-font: ("DejaVu Sans Mono", "Liberation Mono", "Courier New"),
  accent: "#7B1113", // Granate institucional UNSA
  secondary-accent: "#1A365D", // Azul oscuro formal
  toc: true,
  list-of-figures: true,
  list-of-tables: false,
  bibliography: none,
  bib-style: "ieee",
  cover-page: true,
)

// ---- Utilidades internas ----------------------------------------------------

#let _abs(p) = if p.starts-with("/") { p } else { "/" + p }

#let _label-fn = label
#let _as-label(l) = if type(l) == _label-fn { l } else { _label-fn(l) }
#let _with-label(el, l) = if l == none { el } else { [#el#_as-label(l)] }

#let _as-lines(x) = if type(x) == str { x.split("\n") } else { x }

#let _merge(base, extra) = {
  let out = base
  for (k, v) in extra {
    if v != none { out.insert(k, v) }
  }
  out
}

#let _load-config(config) = {
  let user = if config == auto or config == none {
    let src = sys.inputs.at("config", default: none)
    if src == none { (:) } else { json(_abs(src)) }
  } else if type(config) == str {
    json(_abs(config))
  } else {
    config
  }
  _merge(default-config, user)
}

#let _theme = state("informe-teoria-theme", (accent: rgb("#7B1113"), secondary: rgb("#1A365D")))
#let _accent() = _theme.get().accent
#let _secondary() = _theme.get().secondary

#let _logo(name, height: 1.5cm) = {
  if name == none { return none }
  if name.contains(".") {
    image(_abs(name), height: height)
  } else {
    image("assets/" + name + ".png", height: height)
  }
}

// ---- Helpers publicos -------------------------------------------------------

/// Caja de seccion formal con barra de titulo en color de acento
#let section-box(title, body, inset: (x: 1em, top: 0.6em, bottom: 0.8em)) = context {
  let accent = _accent()
  let edge = 0.6pt + luma(120)
  block(width: 100%, breakable: true, stroke: edge, radius: 2pt, {
    block(
      width: 100%,
      fill: accent,
      inset: (x: 0.8em, y: 0.55em),
      sticky: true,
      align(center, text(fill: white, weight: "bold", size: 10.5pt, title)),
    )
    block(width: 100%, inset: inset, breakable: true, body)
  })
}

/// Listado de codigo leido desde un archivo del proyecto
#let listing(
  path,
  lang: auto,
  caption: none,
  label: none,
  numbers: true,
  lines: none,
) = {
  let src = read(_abs(path)).replace("\r\n", "\n").trim("\n", at: end)
  if lines != none {
    let all = src.split("\n")
    src = all.slice(lines.at(0) - 1, calc.min(lines.at(1), all.len())).join("\n")
  }
  let language = if lang == auto {
    let ext = lower(path.split(".").last())
    if ext in ("py", "js", "ts", "json", "toml", "sh", "html", "css", "svelte", "typ") { ext } else { none }
  } else { lang }

  let code = raw(src, lang: language, block: true)
  let code = if numbers {
    {
      show raw.line: it => {
        box(width: 2.2em, align(right, text(fill: luma(140), size: 0.85em, str(it.number))))
        h(0.8em)
        it.body
      }
      code
    }
  } else { code }

  _with-label(
    figure(
      block(
        width: 100%,
        fill: rgb("#FAFAFA"),
        stroke: 0.5pt + rgb("#D1D5DB"),
        radius: 3pt,
        inset: (x: 0.8em, y: 0.6em),
        align(left, code),
      ),
      kind: raw,
      supplement: [Listado],
      caption: caption,
    ),
    label,
  )
}

/// Imagen dentro de figura numerada formal
#let figure-img(path, caption: none, label: none, width: 92%) = _with-label(
  figure(
    block(
      stroke: 0.4pt + luma(200),
      radius: 2pt,
      inset: 2pt,
      image(_abs(path), width: width),
    ),
    caption: caption,
  ),
  label,
)

/// Figura de evidencia de ejecucion con comando
#let evidence-figure(
  path,
  ..rest,
  caption: none,
  cmd: none,
  label: none,
  width: 95%,
) = {
  let cap = if caption != none { caption } else if rest.pos().len() > 0 { rest.pos().first() } else { none }
  let command = if cmd == none { none } else if type(cmd) == array { cmd.join("\n") } else { cmd }
  _with-label(
    figure(
      block(
        stroke: 0.5pt + luma(180),
        radius: 3pt,
        inset: 4pt,
        {
          image(_abs(path), width: width)
          if command != none {
            v(0.3em)
            block(
              width: width,
              inset: (x: 0.6em, y: 0.35em),
              fill: rgb("#F3F4F6"),
              stroke: 0.4pt + rgb("#D1D5DB"),
              radius: 2pt,
              align(left, {
                set text(size: 7.5pt, fill: rgb("#374151"))
                text(weight: "bold")[Comando de ejecucion: ]
                raw(command, block: false)
              }),
            )
          }
        },
      ),
      caption: cap,
    ),
    label,
  )
}

/// Tabla de resultados con cabecera sobria y alternancia de filas
#let result-table(
  headers,
  rows,
  caption: none,
  label: none,
  columns: auto,
  align: auto,
) = {
  let n = headers.len()
  let cols = if columns == auto { (1fr,) * n } else { columns }
  let table-el = context {
    let accent = _accent()
    table(
      columns: cols,
      align: if align == auto { start + horizon } else { align },
      stroke: 0.4pt + luma(180),
      fill: (col, row) => if row == 0 {
        accent
      } else if calc.odd(row) {
        rgb("#F9FAFB")
      } else {
        white
      },
      inset: (x: 0.65em, y: 0.5em),
      ..headers.map(h => text(fill: white, weight: "bold", size: 8.5pt, h)),
      ..rows.flatten().map(c => text(size: 8.5pt, c)),
    )
  }
  _with-label(
    figure(table-el, kind: table, supplement: [Tabla], caption: caption),
    label,
  )
}

/// Bloque de nota o dictamen formal académico (sobrio, sin colores artificiales tipo IA)
#let callout(kind: none, title: none, body) = {
  block(
    width: 100%,
    stroke: (left: 2.2pt + luma(100)),
    inset: (left: 1.0em, y: 0.45em),
    above: 0.8em,
    below: 0.8em,
    {
      if title != none {
        text(weight: "bold", size: 10pt, title + ": ")
      }
      text(size: 10pt, fill: luma(30), body)
    },
  )
}

// ---- Portada Institucional Formal -------------------------------------------

#let _cover-page(cfg) = {
  set text(font: _as-lines(cfg.font), lang: "es")
  align(center, {
    v(0.5cm)
    // Encabezado institucional
    for line in _as-lines(cfg.institution) {
      text(size: 11pt, weight: "bold", tracking: 0.05em, upper(line))
      linebreak()
      v(0.15em)
    }

    v(0.4cm)
    // Escudo oficial de la UNSA (tamano sobrio y proporcionado)
    _logo(cfg.logo-cover, height: 3.6cm)

    v(0.6cm)
    // Nombre del curso y capitulo
    text(size: 14pt, weight: "bold", fill: rgb(cfg.accent), upper(cfg.course))
    v(0.2cm)
    text(size: 12pt, weight: "bold", fill: rgb(cfg.secondary-accent), upper(cfg.chapter))

    v(0.6cm)
    // Titulo del trabajo
    line(length: 60%, stroke: 1.2pt + rgb(cfg.accent))
    v(0.3cm)
    text(size: 16pt, weight: "bold", cfg.title)
    if cfg.subtitle != "" and cfg.subtitle != none {
      v(0.2cm)
      text(size: 12pt, style: "italic", cfg.subtitle)
    }
    v(0.3cm)
    line(length: 60%, stroke: 1.2pt + rgb(cfg.accent))

    v(1.2cm)
    // Tabla formal de integrantes y docente
    align(left, {
      block(width: 100%, inset: (x: 1.5cm), {
        grid(
          columns: (auto, 1fr),
          row-gutter: 0.6em,
          column-gutter: 1.2em,
          text(weight: "bold", size: 10pt)[Docente:], text(size: 10pt, cfg.instructor),
          text(weight: "bold", size: 10pt)[Semestre:], text(size: 10pt, [#cfg.semester (#cfg.year)]),
          text(weight: "bold", size: 10pt)[Integrantes:], {
            let mems = cfg.members
            if mems.len() > 0 {
              set list(marker: [•], spacing: 0.45em)
              list(..mems.map(m => {
                if type(m) == str {
                  text(size: 9.5pt, m)
                } else if type(m) == dictionary {
                  let mname = m.at("name", default: "")
                  let mrole = m.at("role", default: "")
                  let mcui = m.at("cui", default: "")
                  text(size: 9.5pt)[*#mname* #if mrole != "" [— #emph(mrole)] #if mcui != "" [(CUI: #mcui)]]
                } else {
                  str(m)
                }
              }))
            }
          },
        )
      })
    })

    v(1fr)
    // Pie de caratula
    text(size: 10pt, weight: "bold", upper(cfg.city + " — " + cfg.country))
    linebreak()
    text(size: 9.5pt, cfg.year)
    v(0.5cm)
  })
}

// ---- Plantilla Principal ----------------------------------------------------

#let template(config: auto, body) = {
  let cfg = _load-config(config)
  let accent = rgb(cfg.accent)
  let secondary = rgb(cfg.secondary-accent)

  let text-fonts = _as-lines(cfg.font)
  let mono-fonts = _as-lines(cfg.mono-font)

  // Document metadata
  set document(
    title: cfg.title + " — " + cfg.course,
    author: if type(cfg.members) == array and cfg.members.len() > 0 {
      cfg.members.map(m => if type(m) == dictionary { m.at("name", default: "") } else { str(m) })
    } else { () },
  )

  // Typography
  set text(font: text-fonts, lang: "es", size: 10.5pt)
  set par(justify: true, leading: 0.7em)
  show raw: set text(font: mono-fonts, size: 8.5pt)

  // Numeracion de encabezados
  set heading(numbering: (..n) => {
    let nums = n.pos()
    if nums.len() == 1 {
      str(nums.at(0)) + "."
    } else {
      nums.map(str).join(".")
    }
  })

  // Estilos de encabezados
  show heading.where(level: 1): it => block(width: 100%, below: 1.0em, above: 1.6em, {
    set text(fill: accent, weight: "bold", size: 13pt)
    it
    v(0.2em)
    line(length: 100%, stroke: 0.8pt + accent)
  })

  show heading.where(level: 2): it => block(width: 100%, below: 0.8em, above: 1.2em, {
    set text(fill: secondary, weight: "bold", size: 11.5pt)
    it
  })

  show heading.where(level: 3): it => block(width: 100%, below: 0.6em, above: 1.0em, {
    set text(fill: rgb("#2D3748"), weight: "bold", size: 10.5pt)
    it
  })

  // Theme state
  _theme.update((accent: accent, secondary: secondary))

  // Render Cover Page
  if cfg.cover-page {
    set page(
      paper: "a4",
      margin: (top: 2.2cm, bottom: 2.2cm, x: 2.5cm),
      header: none,
      footer: none,
    )
    _cover-page(cfg)
    pagebreak()
  }

  // Running pages format
  set page(
    paper: "a4",
    margin: (top: 2.8cm, bottom: 2.5cm, x: 2.5cm),
    header-ascent: 0.6cm,
    footer-descent: 0.6cm,
    header: context {
      let page-num = counter(page).get().first()
      if cfg.cover-page and page-num <= 1 { return none }
      grid(
        columns: (auto, 1fr),
        align: (left + horizon, right + horizon),
        _logo(cfg.logo-header, height: 0.9cm),
        align(right, {
          set text(size: 8pt, fill: rgb("#4B5563"))
          text(weight: "bold", upper(cfg.course))
          [ — ]
          text(cfg.chapter + ": " + cfg.title)
        }),
      )
      v(0.2em)
      line(length: 100%, stroke: 0.4pt + luma(180))
    },
    footer: context {
      let page-num = counter(page).get().first()
      if cfg.cover-page and page-num <= 1 { return none }
      line(length: 100%, stroke: 0.4pt + luma(180))
      v(0.3em)
      grid(
        columns: (1fr, auto),
        align: (left, right),
        text(size: 8pt, fill: luma(110))[Universidad Nacional de San Agustin de Arequipa — EPIS],
        text(size: 8pt, fill: luma(90))[Pagina #counter(page).display() de #counter(page).final().first()],
      )
    },
  )

  // Indice general opcional
  if cfg.toc {
    v(0.5cm)
    outline(
      title: [Indice de Contenidos],
      depth: 3,
      indent: 1.2em,
    )
    v(0.8cm)
    if cfg.list-of-figures {
      outline(
        title: [Indice de Figuras],
        target: figure.where(kind: image),
      )
      v(0.5cm)
    }
    pagebreak()
  }

  // Contenido
  body

  // Bibliografia
  if cfg.bibliography != none and cfg.bibliography != false {
    pagebreak()
    bibliography(_abs(cfg.bibliography), title: [Referencias Bibliográficas y Normativas], style: cfg.bib-style, full: true)
  }
}
