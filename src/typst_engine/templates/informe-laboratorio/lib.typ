// =============================================================================
// Plantilla "informe-laboratorio" (formato institucional UNSA / FIPS / EPIS)
//
// Uso minimo:
//
//   #import "template/lib.typ": *
//   #show: template.with(config: json("config.json"))
//   #section-box("SOLUCION Y RESULTADOS")[ ...contenido... ]
//
// Convenciones
//  * La configuracion llega como diccionario (`config:`), como ruta a un JSON
//    (`config: "config.json"`) o, si se omite, desde `--input config=<ruta>`.
//  * Los assets propios de la plantilla (logos) se resuelven relativos a ESTE
//    archivo; las rutas que reciben los helpers (`listing`, `figure-img`,
//    `evidence-figure`, bibliografia) son relativas a la RAIZ del proyecto
//    (--root), con o sin "/" inicial.
//  * Fecha y hora son opcionales: `--input fecha=AAAA-MM-DD` y
//    `--input hora=HH:MM` tienen prioridad sobre `config.date` / `config.time`;
//    sin ninguna de las dos, la fecha es la de hoy (y la hora se muestra "-").
// =============================================================================

// ---- Configuracion por defecto ----------------------------------------------

#let default-config = (
  // Datos del laboratorio
  course: "",
  title: "",
  number: "",
  instructor: "",
  semester: "",
  year: none,
  members: (),
  date: none,
  time: none,
  // Encabezado institucional
  institution: (
    "UNIVERSIDAD NACIONAL DE SAN AGUSTÍN",
    "FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS",
    "ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS",
  ),
  doc-title: "INFORME DE LABORATORIO",
  doc-format: "Guía de Práctica de Laboratorio / Talleres / Centros de Simulación",
  doc-approval: "2022/03/01",
  doc-code: "GUIA-PRLE-001",
  logo-left: "epis",
  logo-right: "abet",
  note-placeholder: "Nota colocada por el docente",
  // Tipografia (listas: se usa la primera familia disponible por glifo)
  font: ("Lato", "Liberation Sans", "DejaVu Sans"),
  mono-font: ("DejaVu Sans Mono", "Liberation Mono"),
  accent: "#C8310E",
  // Estructura
  results-title: "SOLUCIÓN Y RESULTADOS",
  toc: false,
  list-of-figures: false,
  feedback: true,
  bibliography: "references.bib", // none/false para omitir
  bib-style: "ieee",
  max-unbreakable-lines: 36, // listados mas cortos nunca se parten entre paginas
  code-keep-lines: 6, // en listados largos, lineas que se mantienen juntas al inicio y al final
)

// ---- Utilidades internas ----------------------------------------------------

// Ruta relativa a la raiz del proyecto. `read("x")` dentro de este archivo
// resolveria contra la carpeta de la plantilla, asi que se ancla a la raiz.
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

// Estado con el tema vigente para que los helpers (que se invocan fuera de la
// plantilla) conozcan el color de acento configurado.
#let _theme = state("informe-laboratorio-theme", (accent: rgb("#C8310E")))
#let _accent() = _theme.get().accent

// ---- Helpers publicos -------------------------------------------------------

/// Caja con barra de titulo en color de acento y cuerpo con borde. Se puede
/// partir entre paginas; la barra de titulo nunca queda sola al final de una.
#let section-box(title, body, inset: (x: 1em, top: 0.3em, bottom: 1em)) = context {
  let accent = _accent()
  let edge = 0.5pt + luma(70)
  block(width: 100%, breakable: true, stroke: edge, {
    block(
      width: 100%,
      fill: accent,
      inset: (x: 0.8em, y: 0.55em),
      sticky: true,
      align(center, text(fill: white, weight: "bold", size: 11pt, title)),
    )
    block(width: 100%, inset: inset, breakable: true, body)
  })
}

/// Listado de codigo leido desde un archivo del proyecto, dentro de una figura
/// "Listado N". `lines: (desde, hasta)` (1-based, inclusivo) recorta el archivo.
#let listing(
  path,
  lang: auto,
  caption: none,
  label: none,
  numbers: false,
  lines: none,
) = {
  let src = read(_abs(path)).replace("\r\n", "\n").trim("\n", at: end)
  if lines != none {
    let all = src.split("\n")
    src = all.slice(lines.at(0) - 1, calc.min(lines.at(1), all.len())).join("\n")
  }
  let language = if lang == auto {
    let ext = lower(path.split(".").last())
    if ext in ("py", "rs", "js", "ts", "c", "cpp", "h", "java", "sh", "json", "toml", "xml", "sql", "typ", "cs", "go") {
      ext
    } else { none }
  } else { lang }
  let code = raw(src, lang: language, block: true)
  let code = if numbers {
    {
      show raw.line: it => {
        box(width: 1.8em, align(right, text(fill: luma(150), size: 0.9em, str(it.number))))
        h(0.8em)
        it.body
      }
      code
    }
  } else { code }
  _with-label(
    figure(code, kind: raw, supplement: [Listado], caption: caption),
    label,
  )
}

/// Imagen del proyecto dentro de una figura numerada.
#let figure-img(path, caption: none, label: none, width: 95%) = _with-label(
  figure(image(_abs(path), width: width), caption: caption),
  label,
)

/// Figura de evidencia: la imagen y, en pequeno, el comando que la genero.
/// `cmd` admite un string o un array de strings (una linea por elemento).
/// Se puede llamar `evidence-figure(path, [caption], cmd: "...")`.
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
      {
        image(_abs(path), width: width)
        if command != none {
          v(0.35em)
          block(
            width: width,
            inset: (x: 0.6em, y: 0.4em),
            fill: luma(246),
            stroke: 0.4pt + luma(215),
            radius: 2pt,
            align(left, {
              set text(size: 7pt, fill: luma(80))
              set par(justify: false, leading: 0.5em)
              text(weight: "bold")[Comando: ]
              raw(command, block: false)
            }),
          )
        }
      },
      caption: cap,
    ),
    label,
  )
}

/// Tabla de resultados con cabecera en color de acento y filas alternas.
/// `headers`: array de encabezados; `rows`: array de filas (arrays de celdas).
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
      inset: (x: 0.6em, y: 0.5em),
      stroke: (x, y) => if y == 0 { 0.4pt + accent } else { 0.4pt + luma(205) },
      fill: (x, y) => if y == 0 { accent } else if calc.even(y) { luma(246) } else { white },
      table.header(..headers.map(h => text(fill: white, weight: "bold", h))),
      ..rows.flatten(),
    )
  }
  _with-label(
    figure(
      table-el,
      kind: table,
      supplement: [Tabla],
      caption: if caption == none { none } else { figure.caption(position: top, caption) },
    ),
    label,
  )
}

/// Pildora para un comando o nombre de archivo inline.
#let cmd(body) = box(
  fill: luma(240),
  stroke: 0.4pt + luma(210),
  inset: (x: 3.5pt, y: 0pt),
  outset: (y: 2.5pt),
  radius: 2pt,
  text(size: 0.88em, fill: luma(40), raw(body)),
)

/// Nota destacada (kind: "info" | "tip" | "warning" | "danger").
#let callout(body, title: none, kind: "info") = {
  let (color, tint) = (
    info: (rgb("#2B6CB0"), rgb("#F0F9FF")),
    tip: (rgb("#16A34A"), rgb("#F0FDF4")),
    warning: (rgb("#D97706"), rgb("#FFFBEB")),
    danger: (rgb("#DC2626"), rgb("#FEF2F2")),
  ).at(kind)
  block(
    width: 100%,
    fill: tint,
    stroke: (left: 3pt + color, rest: 0.4pt + luma(215)),
    inset: (x: 0.9em, y: 0.7em),
    radius: (right: 3pt),
    breakable: false,
    {
      if title != none { text(fill: color, weight: "bold", size: 0.95em, title); linebreak() }
      body
    },
  )
}

/// Diagrama de clases sencillo: las clases se disponen en una fila y entre clases
/// contiguas se dibuja la relacion `relations.at(i)` (entre la clase i y la i+1),
/// con `label` y una flecha en la direccion de `dir` ("right" | "left" | "none").
/// Cada clase es (name:, attrs: (...), ops: (...)).
#let uml-diagram(..classes, relations: (), caption: none, label: none) = {
  let cls(c) = block(stroke: 0.7pt + luma(60), width: 100%, breakable: false, {
    block(width: 100%, fill: luma(240), inset: 0.45em, align(center, strong(c.name)))
    line(length: 100%, stroke: 0.5pt + luma(60))
    block(width: 100%, inset: 0.45em, align(left, text(size: 7.5pt, c.at("attrs", default: ()).join(linebreak()))))
    if c.at("ops", default: ()).len() > 0 {
      line(length: 100%, stroke: 0.5pt + luma(60))
      block(width: 100%, inset: 0.45em, align(left, text(size: 7.5pt, c.at("ops", default: ()).join(linebreak()))))
    }
  })
  let rel(r) = align(center + horizon, {
    let tip-l = if r.at("dir", default: "right") == "left" { "◀" } else { "" }
    let tip-r = if r.at("dir", default: "right") == "right" { "▶" } else { "" }
    text(size: 7pt, r.at("label", default: ""))
    linebreak()
    text(size: 8pt, tip-l + "───" + tip-r)
  })
  let items = classes.pos()
  let cells = ()
  for (i, c) in items.enumerate() {
    cells.push(cls(c))
    if i < items.len() - 1 {
      cells.push(if i < relations.len() { rel(relations.at(i)) } else { [] })
    }
  }
  let cols = ()
  for i in range(items.len()) {
    cols.push(1fr)
    if i < items.len() - 1 { cols.push(2.2cm) }
  }
  _with-label(
    figure(grid(columns: cols, column-gutter: 0.3em, align: top, ..cells), caption: caption),
    label,
  )
}

// ---- Piezas de la plantilla ---------------------------------------------------

#let _logo(name, height) = {
  if name == none { return none }
  if name.contains(".") {
    image(_abs(name), height: height)
  } else {
    // Relativo a este archivo: assets/epis.png, assets/abet.png, assets/unsa.png
    image("assets/" + name + ".png", height: height)
  }
}

#let _page-header(cfg) = {
  let small(body, weight: "regular") = text(size: 7pt, weight: weight, body)
  table(
    columns: (1fr, 2fr, 1fr),
    align: center + horizon,
    stroke: 0.5pt + rgb("#808080"),
    inset: (x: 0.5em, y: 0.3em),
    _logo(cfg.logo-left, 1.35cm),
    text(size: 7.5pt, weight: "bold", _as-lines(cfg.institution).join(linebreak())),
    _logo(cfg.logo-right, 1.35cm),
    table.cell(colspan: 3, align: left, {
      small(weight: "bold")[Formato: ]
      small(cfg.doc-format)
    }),
    small(weight: "bold")[Aprobación: #cfg.doc-approval],
    small(weight: "bold")[Código: #cfg.doc-code],
    table.cell(align: right, small(weight: "bold")[Página: #context counter(page).display()]),
  )
}

#let _page-footer(cfg) = context {
  set text(size: 8pt, fill: luma(90))
  line(length: 100%, stroke: 0.5pt + luma(190))
  v(0.3em)
  grid(
    columns: (1fr, auto),
    align: (left, right),
    [Laboratorio #cfg.number#if cfg.title != "" [ — #cfg.title]],
    [Página #counter(page).display() de #counter(page).final().first()],
  )
}

#let _front-matter(cfg, accent, fecha, hora, year) = {
  set text(size: 8.5pt, hyphenate: false)
  set par(justify: false)
  let label-cell(body) = table.cell(fill: luma(245), strong(body))
  table(
    columns: (1.5fr, 1fr, 1.4fr, 1fr, 1.1fr, 1fr),
    align: left + horizon,
    stroke: 0.5pt + black,
    inset: 0.5em,
    table.cell(
      colspan: 6,
      fill: accent,
      align(center, text(fill: white, weight: "bold", size: 11pt)[INFORMACIÓN BÁSICA]),
    ),
    label-cell[Asignatura:], table.cell(colspan: 5, cfg.course),
    label-cell[Título de la práctica:], table.cell(colspan: 5, cfg.title),
    label-cell[Número de la práctica:], [#cfg.number],
    label-cell[Año lectivo:], [#year],
    label-cell[Nro. semestre:], [#cfg.semester],
    label-cell[Fecha de presentación:], [#fecha],
    label-cell[Hora de presentación:], table.cell(colspan: 3, hora),
    table.cell(colspan: 4, {
      strong[Integrante(s):]
      v(0.15em)
      set list(marker: [–], indent: 0pt, body-indent: 0.5em, spacing: 0.35em)
      list(..cfg.members)
    }),
    label-cell[NOTA:], [#cfg.note-placeholder],
    table.cell(colspan: 6, {
      strong[Docente:]
      linebreak()
      cfg.instructor
    }),
  )
}

// ---- Plantilla principal ----------------------------------------------------

/// Plantilla del informe de laboratorio.
/// - config (dictionary | str | auto): claves en `default-config`.
#let template(config: auto, body) = {
  let cfg = _load-config(config)
  let accent = rgb(cfg.accent)

  // Fecha/hora: --input > config > hoy (fecha) / "-" (hora)
  let today = datetime.today()
  let fecha = sys.inputs.at("fecha", default: cfg.date)
  let fecha = if fecha == none { today.display("[year]-[month]-[day]") } else { str(fecha) }
  let hora = sys.inputs.at("hora", default: cfg.time)
  let hora = if hora == none or str(hora) == "" { "—" } else { str(hora) }
  let ymd = fecha.match(regex("^(\d{4})-(\d{2})-(\d{2})$"))
  let year = if cfg.year != none { str(cfg.year) } else if ymd != none { ymd.captures.at(0) } else { str(today.year()) }
  let doc-date = if ymd != none {
    let c = ymd.captures.map(int)
    datetime(year: c.at(0), month: c.at(1), day: c.at(2))
  } else { auto }

  let text-fonts = _as-lines(cfg.font)
  let mono-fonts = _as-lines(cfg.mono-font)
  let margin-x = 1.9cm
  let margin-top = 4cm
  let header-ascent = 0.45cm

  set document(
    title: cfg.doc-title + " " + str(cfg.number) + if cfg.title != "" { " — " + cfg.title } else { "" },
    author: cfg.members,
    date: doc-date,
  )
  set text(font: text-fonts, lang: "es", size: 10pt)
  set par(justify: true, leading: 0.65em)

  set page(
    paper: "a4",
    margin: (top: margin-top, bottom: 2.4cm, x: margin-x),
    header-ascent: header-ascent,
    header: context {
      // El encabezado se alinea al borde inferior del margen superior: si es mas
      // alto que el margen, se solaparia con el cuerpo. Se falla en voz alta.
      let h = measure(width: page.width - 2 * margin-x, _page-header(cfg)).height
      assert(
        h <= margin-top - header-ascent - 0.6cm,
        message: "El encabezado institucional mide " + repr(h) + " y no cabe en el margen superior (" + repr(margin-top - header-ascent - 0.6cm) + " utiles); acorta `institution` o reduce los logos.",
      )
      _page-header(cfg)
    },
    footer: _page-footer(cfg),
    footer-descent: 0.55cm,
  )

  // Tema compartido con los helpers
  _theme.update((accent: accent))

  // Encabezados
  // Numeracion jerarquica: 1.  /  1.1  /  1.1.1  /  a)  (cuarto nivel)
  set heading(numbering: (..n) => {
    let nums = n.pos()
    if nums.len() == 1 { numbering("1.", ..nums) }
    else if nums.len() <= 3 { nums.map(str).join(".") }
    else { numbering("a)", nums.last()) }
  })
  let indent = cfg.heading-indent * 1cm
  show heading: set text(font: text-fonts)
  show heading.where(level: 1): set text(size: 12pt, weight: "bold")
  show heading.where(level: 1): set block(above: 1.4em, below: 0.9em)
  show heading.where(level: 2): set text(size: 11pt, weight: "bold")
  show heading.where(level: 2): set block(above: 1.2em, below: 0.8em)
  show heading.where(level: 3): set text(size: 10pt, weight: "bold")
  show heading.where(level: 3): set block(above: 1em, below: 0.7em)
  show heading.where(level: 4): set text(size: 10pt, weight: "bold", style: "italic")
  show heading.where(level: 4): set block(above: 0.9em, below: 0.6em)
  // Sangria por nivel: el nivel 1 va al margen y cada nivel inferior se desplaza un paso mas
  show heading: it => if it.level > 1 { pad(left: indent * (it.level - 1), it) } else { it }

  // Codigo: fuente mono fija; bloques con inset 0.8em que no se parten mal
  show raw: set text(font: mono-fonts)
  show raw.where(block: false): set text(size: 0.9em)
  show raw.where(block: true): it => {
    set text(size: 8pt, fill: rgb("#24292E"))
    let n = it.lines.len()
    let frame(breakable, body) = block(
      width: 100%,
      fill: luma(247),
      stroke: 0.5pt + luma(214),
      radius: 3pt,
      inset: 0.8em,
      breakable: breakable,
      above: 0.9em,
      below: 0.9em,
      align(start, body),
    )
    if n <= cfg.max-unbreakable-lines {
      // Listado corto: salta entero a la pagina siguiente si no cabe.
      frame(false, it)
    } else {
      // Listado largo: puede partirse, pero siempre quedan al menos `keep`
      // lineas juntas al inicio y al final de cada trozo (sin fragmentos huerfanos).
      let keep = cfg.code-keep-lines
      let part(from, to, breakable) = block(
        breakable: breakable,
        spacing: 0.65em,
        // Una linea vacia al borde de un bloque se perderia: se rellena con un ZWSP.
        it.lines.slice(from, to).map(l => if l.text == "" { [\u{200B}] } else { l }).join(linebreak()),
      )
      frame(true, {
        part(0, keep, false)
        part(keep, n - keep, true)
        part(n - keep, n, false)
      })
    }
  }

  // Figuras, tablas y listados
  set figure(gap: 0.8em)
  show figure: set block(above: 1.3em, below: 1.3em)
  show figure.where(kind: raw): set block(breakable: true)
  show figure.where(kind: table): set block(breakable: true)
  show figure.caption: it => {
    set text(size: 9pt)
    context {
      text(weight: "bold")[#it.supplement #it.counter.display(it.numbering)#it.separator]
      it.body
    }
  }

  // Enlaces: sin cursiva ni subrayado forzados (tambien dentro de la bibliografia)
  show link: set text(fill: rgb("#1D4ED8"), style: "normal")

  set list(indent: 0.8em, body-indent: 0.6em)
  set enum(indent: 0.8em, body-indent: 0.6em)

  // ---- Documento ----
  align(center, text(size: 13pt, weight: "bold", cfg.doc-title))
  v(0.2em)
  _front-matter(cfg, accent, fecha, hora, year)
  v(0.9em)

  if cfg.toc {
    section-box("TABLA DE CONTENIDOS", outline(title: none, depth: 3, indent: auto))
    v(0.9em)
  }
  if cfg.list-of-figures {
    section-box("LISTA DE FIGURAS", outline(title: none, target: figure.where(kind: image)))
    v(0.9em)
  }
  if cfg.toc or cfg.list-of-figures { pagebreak(weak: true) }

  body

  if cfg.feedback {
    v(0.9em)
    section-box("RETROALIMENTACIÓN GENERAL", v(5em))
  }
  if cfg.bibliography not in (none, false) {
    v(0.9em)
    section-box("REFERENCIAS Y BIBLIOGRAFÍA", {
      set text(size: 9pt)
      set par(justify: false)
      bibliography(_abs(cfg.bibliography), title: none, style: cfg.bib-style)
    })
  }
}
