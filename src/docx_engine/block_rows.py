# -*- coding: utf-8 -*-
"""Un bloque de contenido por fila de la tabla institucional, con «no partir fila entre páginas».

La plantilla EPIS pone todo el contenido de una sección en una sola celda gigante; los visores la parten por donde cae
la página (un encabezado al pie y su figura en la hoja siguiente, o una figura cortada). Aquí cada bloque (encabezado +
paso + figura + pie) vive en su propia fila clonada de la original y marcada ``cantSplit``: si no cabe en lo que queda
de página, la fila entera pasa a la siguiente. Las filas intermedias no dibujan línea entre sí, así que visualmente
sigue siendo una sola caja.
"""

from __future__ import annotations

import copy
from typing import List

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import _Row


def _tc_borders(tc):
    tcPr = tc.get_or_add_tcPr()
    borders = tcPr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        # tcBorders va antes de shd/vAlign en el esquema
        anchor = next((c for c in tcPr if c.tag in (qn("w:shd"), qn("w:noWrap"), qn("w:tcMar"), qn("w:vAlign"))), None)
        if anchor is not None:
            anchor.addprevious(borders)
        else:
            tcPr.append(borders)
    return borders


def _set_border(tc, side: str, value: str) -> None:
    borders = _tc_borders(tc)
    el = borders.find(qn(f"w:{side}"))
    if el is None:
        el = OxmlElement(f"w:{side}")
        borders.append(el)
    for k, v in (("w:val", value), ("w:sz", "0" if value == "nil" else "4"), ("w:space", "0"), ("w:color", "000000")):
        el.set(qn(k), v)


def _cant_split(tr, on: bool = True) -> None:
    trPr = tr.get_or_add_trPr()
    el = trPr.find(qn("w:cantSplit"))
    if el is None:
        el = OxmlElement("w:cantSplit")
        trPr.insert(0, el)
    el.set(qn("w:val"), "1" if on else "0")


class BlockRows:
    """Reparte el contenido de una sección en filas: ``next_cell()`` devuelve la celda donde escribir el siguiente bloque."""

    def __init__(self, table, row: _Row, clear):
        self.table = table
        clear(row.cells[0])
        self._template = copy.deepcopy(row._tr)         # fila original ya vacía: molde de las siguientes
        self.rows: List[_Row] = []
        self._first = row

    def next_cell(self):
        if not self.rows:
            self.rows.append(self._first)
            return self._first.cells[0]
        tr = copy.deepcopy(self._template)
        self.rows[-1]._tr.addnext(tr)
        row = _Row(tr, self.table)
        self.rows.append(row)
        return row.cells[0]

    def finish(self) -> None:
        """Sin línea entre filas del bloque y cada fila indivisible."""
        last = len(self.rows) - 1
        for i, row in enumerate(self.rows):
            _cant_split(row._tr)
            for tc in row._tr.findall(qn("w:tc")):
                if i > 0:
                    _set_border(tc, "top", "nil")
                if i < last:
                    _set_border(tc, "bottom", "nil")
