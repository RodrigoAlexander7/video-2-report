#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Inspección y Dry-Run para Documentos Generados (.docx)
Permite verificar la integridad estructural, tablas, párrafos y figuras sin recompilar.

`inspect_docx(path) -> bool` devuelve True solo si NO se detectan anomalías reales:

  - archivo inexistente, vacío o ilegible (no es un .docx válido);
  - texto de relleno: lorem ipsum, TODO, XXX, 'Apellido Apellido';
  - encabezados (Heading/Título/Title o con nivel de esquema) sin texto;
  - tablas totalmente vacías (sin texto ni imágenes);
  - imágenes referenciadas en el XML cuyo archivo no existe en el paquete
    (word/media) o cuya relación no está declarada.

Los placeholders formales de captura ("EVIDENCIA DE PROTOTIPO - FIGURA n",
"PEGAR AQUÍ LA CAPTURA...") que usan a propósito los informes EPIS NO son una
anomalía: se listan como información.
"""

import os
import posixpath
import re
import sys
import zipfile

import docx
from lxml import etree

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
    "o": "urn:schemas-microsoft-com:office:office",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
W = "{%s}" % NS["w"]
R = "{%s}" % NS["r"]
O = "{%s}" % NS["o"]

_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)

# Texto de relleno. TODO es sensible a mayúsculas y exige forma de marcador
# ("TODO:", "TODO(", "[TODO]" o línea solo con TODO) para no confundirlo con la
# palabra española "todo".
FILLER_PATTERNS = [
    ("lorem ipsum", re.compile(r"lorem\s+ipsum|dolor\s+sit\s+amet", re.IGNORECASE)),
    ("TODO", re.compile(r"\[\s*TODO\s*\]|\bTODO\s*[:(]|^\s*TODO\s*$")),
    ("XXX", re.compile(r"(?<![A-Za-z0-9])X{3,}(?![A-Za-z0-9])")),
    ("Apellido Apellido", re.compile(r"Apellido\s+Apellido", re.IGNORECASE)),
]

HEADING_STYLE = re.compile(r"^(heading|título|titulo|title)\b", re.IGNORECASE)

# Placeholders formales de captura (informativos)
PLACEHOLDER_BADGE = re.compile(r"EVIDENCIA DE PROTOTIPO\s*-\s*FIGURA\s+([^\s:]+)")
PLACEHOLDER_BOX = re.compile(r"PEGAR\s+AQU[ÍI]", re.IGNORECASE)

# Elementos que cuentan como contenido aunque no haya texto
_CONTENT_TAGS = ("drawing", "pict", "object", "fldChar", "fldSimple", "sym")

MAX_LISTED = 8


def _load_xml(zf, name):
    return etree.fromstring(zf.read(name), _PARSER)


def _par_text(p):
    """Texto de un párrafo (w:t y tabulaciones; ignora texto eliminado)."""
    parts = []
    for el in p.iter(W + "t", W + "tab"):
        parts.append("\t" if el.tag == W + "tab" else (el.text or ""))
    return "".join(parts)


def _has_content_element(el):
    return any(next(el.iter(W + tag), None) is not None for tag in _CONTENT_TAGS)


def _style_map(zf):
    """styleId -> (nombre, nivel de esquema o None) desde word/styles.xml."""
    styles = {}
    if "word/styles.xml" not in zf.namelist():
        return styles
    root = _load_xml(zf, "word/styles.xml")
    for st in root.iterfind("w:style", NS):
        sid = st.get(W + "styleId")
        name_el = st.find("w:name", NS)
        name = name_el.get(W + "val") if name_el is not None else ""
        lvl_el = st.find("w:pPr/w:outlineLvl", NS)
        lvl = int(lvl_el.get(W + "val")) if lvl_el is not None and lvl_el.get(W + "val", "").isdigit() else None
        styles[sid] = (name, lvl)
    return styles


def _is_heading(p, styles):
    ppr = p.find("w:pPr", NS)
    if ppr is None:
        return False
    lvl_el = ppr.find("w:outlineLvl", NS)
    if lvl_el is not None and lvl_el.get(W + "val", "").isdigit():
        return int(lvl_el.get(W + "val")) < 9
    ps = ppr.find("w:pStyle", NS)
    if ps is None:
        return False
    name, style_lvl = styles.get(ps.get(W + "val"), ("", None))
    if HEADING_STYLE.match(name or ""):
        return True
    return style_lvl is not None and style_lvl < 9


def _text_parts(zf):
    """Partes de texto del cuerpo: document.xml, headers y footers."""
    names = zf.namelist()
    body = ["word/document.xml"] if "word/document.xml" in names else []
    heads = sorted(n for n in names if re.fullmatch(r"word/header\d*\.xml", n))
    foots = sorted(n for n in names if re.fullmatch(r"word/footer\d*\.xml", n))
    return body, heads, foots


def _read_rels(zf, part):
    rels_name = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
    if rels_name not in zf.namelist():
        return {}
    root = _load_xml(zf, rels_name)
    rels = {}
    for rel in root.iterfind("rel:Relationship", NS):
        rels[rel.get("Id")] = (rel.get("Target", ""), rel.get("TargetMode") == "External")
    return rels


def _resolve_target(part, target):
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def _short(text, width=70):
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 3] + "..."


def _print_limited(items, prefix="    - "):
    for it in items[:MAX_LISTED]:
        print(f"{prefix}{it}")
    if len(items) > MAX_LISTED:
        print(f"{prefix}... y {len(items) - MAX_LISTED} más")


def inspect_docx(file_path: str) -> bool:
    """Inspecciona un .docx. Devuelve True solo si no hay anomalías reales."""
    try:
        return _inspect_docx(file_path)
    except Exception as exc:  # paquete tan dañado que el análisis no puede continuar
        print(f"✗ Error: inspección interrumpida ({type(exc).__name__}: {exc})")
        return False


def _inspect_docx(file_path: str) -> bool:
    anomalies = []   # (categoría, detalle)
    info = []        # líneas informativas

    if not os.path.isfile(file_path):
        print(f"✗ Error: el archivo no existe en {file_path}")
        return False

    size = os.path.getsize(file_path)
    print("=" * 80)
    print(f"INSPECCIÓN ESTRUCTURAL DE DOCUMENTO (DRY-RUN): {os.path.basename(file_path)}")
    print(f"Ruta completa: {file_path}")
    print(f"Tamaño: {size / (1024 * 1024):.2f} MB")
    print("=" * 80)

    if size == 0:
        print("✗ Error: el archivo está vacío (0 bytes).")
        return False

    try:
        zf = zipfile.ZipFile(file_path)
    except Exception as exc:  # no es un zip / corrupto
        print(f"✗ Error: no se pudo leer el documento ({type(exc).__name__}: {exc})")
        return False

    # python-docx es la prueba de "se puede abrir"; el resto del análisis es XML directo
    # para poder diagnosticar también paquetes rotos (p. ej. imagen ausente en word/media).
    try:
        docx.Document(file_path)
    except Exception as exc:
        anomalies.append(("lectura", f"python-docx no puede abrir el documento ({type(exc).__name__}: {exc})"))

    with zf:
        body_parts, head_parts, foot_parts = _text_parts(zf)
        names = set(zf.namelist())
        styles = {}
        try:
            styles = _style_map(zf)
        except etree.XMLSyntaxError as exc:
            anomalies.append(("XML", f"word/styles.xml malformado: {exc}"))

        # ---- Recorrido XML de cada parte de texto ---------------------------------
        drawings = {"document": 0, "headers": 0, "footers": 0}
        total_tables = 0
        filler = {}          # (categoría, fragmento) -> None (dedupe, conserva orden)
        empty_headings = []
        empty_tables = []
        placeholder_figs = []
        placeholder_boxes = 0
        parsed = {}

        for kind, parts in (("document", body_parts), ("headers", head_parts), ("footers", foot_parts)):
            for part in parts:
                try:
                    root = parsed[part] = _load_xml(zf, part)
                except etree.XMLSyntaxError as exc:
                    anomalies.append(("XML", f"{part} malformado: {exc}"))
                    continue

                drawings[kind] += sum(1 for _ in root.iter(W + "drawing"))

                for p in root.iter(W + "p"):
                    text = _par_text(p)
                    stripped = text.strip().replace(" ", "").replace("​", "")

                    if stripped:
                        for label, pat in FILLER_PATTERNS:
                            if pat.search(text):
                                filler[(label, f"{part}: «{_short(text)}»")] = None
                        mb = PLACEHOLDER_BADGE.search(text)
                        if mb:
                            placeholder_figs.append(mb.group(1))
                        if PLACEHOLDER_BOX.search(text):
                            placeholder_boxes += 1
                    elif _is_heading(p, styles) and not _has_content_element(p):
                        prev = p.getprevious()
                        ctx = _short(_par_text(prev)) if prev is not None and prev.tag == W + "p" else ""
                        empty_headings.append(f"{part}: encabezado vacío" + (f" (tras «{ctx}»)" if ctx else ""))

                for idx, tbl in enumerate(root.iter(W + "tbl"), start=1):
                    if kind == "document":
                        total_tables += 1
                    has_text = any((t.text or "").strip() for t in tbl.iter(W + "t"))
                    if not has_text and not _has_content_element(tbl):
                        rows = tbl.findall("w:tr", NS)
                        cols = len(rows[0].findall("w:tc", NS)) if rows else 0
                        empty_tables.append(f"{part}: tabla #{idx} totalmente vacía ({len(rows)}x{cols})")

        # ---- Integridad de imágenes referenciadas ---------------------------------
        referenced = set()
        external_imgs = []
        media_files = sorted(n for n in names if n.startswith("word/media/"))
        for part in sorted(n for n in names if re.fullmatch(r"word/[^/]+\.xml", n)):
            root = parsed.get(part)
            if root is None:
                try:
                    root = _load_xml(zf, part)
                except etree.XMLSyntaxError:
                    continue
            rids = [el.get(R + "embed") or el.get(R + "link") for el in root.iter("{%s}blip" % NS["a"])]
            rids += [el.get(R + "id") or el.get(O + "relid") for el in root.iter("{%s}imagedata" % NS["v"])]
            rids = [rid for rid in rids if rid]
            if not rids:
                continue
            rels = _read_rels(zf, part)
            for rid in rids:
                if rid not in rels:
                    anomalies.append(("imagen", f"{part}: la imagen usa la relación '{rid}' que no está declarada"))
                    continue
                target, external = rels[rid]
                if external:
                    external_imgs.append(f"{part}: imagen vinculada externamente → {target}")
                    continue
                path = _resolve_target(part, target)
                referenced.add(path)
                if path not in names:
                    anomalies.append(("imagen", f"{part}: referencia a '{path}' pero el archivo no existe en el paquete"))
                elif zf.getinfo(path).file_size == 0:
                    anomalies.append(("imagen", f"{path}: archivo de imagen vacío (0 bytes)"))
        orphan_media = [m for m in media_files if m not in referenced]

    for label, frag in filler:
        anomalies.append(("relleno", f"texto de relleno ({label}) en {frag}"))
    anomalies += [("encabezado", e) for e in empty_headings]
    anomalies += [("tabla", e) for e in empty_tables]

    # ---- Reporte --------------------------------------------------------------
    doc_root = parsed.get("word/document.xml")
    body = doc_root.find("w:body", NS) if doc_root is not None else None
    top_paragraphs = body.findall("w:p", NS) if body is not None else []
    total_p = len(top_paragraphs)
    total_t = len(body.findall("w:tbl", NS)) if body is not None else 0
    total_drawings = sum(drawings.values())

    print("\n[Métricas Generales]")
    print(f"  - Total de Párrafos: {total_p}")
    print(f"  - Total de Tablas:   {total_t}" + (f" (+{total_tables - total_t} anidadas)" if total_tables > total_t else ""))
    print(f"  - Figuras / GIFs:    {total_drawings} "
          f"(cuerpo: {drawings['document']}, encabezados: {drawings['headers']}, pies: {drawings['footers']})")
    print(f"  - Archivos en word/media: {len(media_files)}")

    print("\n[Estructura de Secciones Detectadas]")
    headings_found = []
    for i, p in enumerate(top_paragraphs):
        txt = _par_text(p).strip()
        if txt and any(txt.startswith(f"{n}. ") for n in range(1, 25)) and not txt.endswith("..."):
            headings_found.append((i, txt))

    if headings_found:
        for idx, (p_num, h_text) in enumerate(headings_found[:20]):
            print(f"  {idx+1:02d}. [P{p_num:03d}] {h_text[:75]}")
        if len(headings_found) > 20:
            print(f"  ... y {len(headings_found) - 20} subsecciones adicionales.")
    else:
        # Fallback a títulos de tabla o primeros párrafos
        print("  (Estructura tabular / compacta)")

    if placeholder_figs or placeholder_boxes:
        figs = ", ".join(dict.fromkeys(placeholder_figs))
        info.append(
            f"{max(len(placeholder_figs), placeholder_boxes)} placeholder(s) formal(es) de captura pendiente(s)"
            + (f" (figuras: {figs})" if figs else "")
            + " - uso intencional, no es anomalía"
        )
    if orphan_media:
        info.append(f"{len(orphan_media)} archivo(s) en word/media sin referencia desde el XML "
                    f"(posible residuo de la plantilla): {', '.join(os.path.basename(m) for m in orphan_media[:6])}"
                    + ("..." if len(orphan_media) > 6 else ""))
    info += external_imgs

    if info:
        print("\n[Informativo]")
        _print_limited(info, prefix="  · ")

    print()
    anomalies = list(dict.fromkeys(anomalies))  # mc:AlternateContent duplica referencias
    if anomalies:
        print(f"✗ Inspección finalizada: {len(anomalies)} anomalía(s) detectada(s):")
        _print_limited([f"[{cat}] {det}" for cat, det in anomalies], prefix="  - ")
        print("=" * 80)
        return False

    print("✓ Inspección finalizada: sin anomalías (lectura OpenXML, texto, tablas, encabezados e imágenes).")
    print("=" * 80)
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        results = [inspect_docx(path) for path in sys.argv[1:]]
        sys.exit(0 if all(results) else 1)
    print("Uso: python inspector.py <ruta_al_archivo.docx> [otro.docx ...]")
    sys.exit(2)
