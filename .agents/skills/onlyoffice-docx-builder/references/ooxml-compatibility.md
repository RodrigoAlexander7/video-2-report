# OpenXML (OOXML) Compatibility & Troubleshooting Reference

This document provides a deep technical reference for generating Microsoft Word compatible `.docx` files using ONLYOFFICE Document Builder, resolving common rendering anomalies, and ensuring strict ECMA-376 / ISO-29500 schema compliance.

---

## 1. The "Unreadable Content" (`Contenido no legible`) Error in Word

When Microsoft Word encounters an OpenXML validation error during document parsing, it displays the following prompt:

> *"Word found unreadable content in 'filename.docx'. Do you want to recover the contents of this document? If you trust the source of this document, click Yes."*

If clicking "Yes" recovers the file with all contents intact, the document was not corrupted; rather, it suffered from **strict XML schema sequence violations** or **unbound namespace prefixes**.

### Root Cause A: Unbound Prefixes in `mc:Ignorable` (Namespace MCE Violation)

- **Standard Reference:** ISO/IEC 29500-3 (Markup Compatibility and Extensibility), Section 10.2:
  > *"The attribute value is a whitespace-delimited list of namespace prefixes. Each prefix SHALL be bound to a namespace name in scope."*
- **Mechanism:** ONLYOFFICE root elements (`<w:document>`, `<w:hdr>`) contain:
  ```xml
  mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh wp14"
  ```
- **The Pitfall:** When using Python's standard `xml.etree.ElementTree` to parse and serialize OpenXML parts, the serializer drops any `xmlns:prefix` declarations for prefixes that are not explicitly used in tag or attribute names within the DOM.
- **The Consequence:** The output XML retains `mc:Ignorable="... w15 ..."` but lacks `xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml"`. Microsoft Word's XML parser flags this as an unresolvable namespace prefix and aborts with the unreadable content prompt.
- **The Solution:** Use `lxml.etree` which preserves the complete prefix namespace mapping (`nsmap`) from the original document during parsing and serialization. Always serialize with:
  ```python
  ET.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
  ```

---

### Root Cause B: Strict Sequence Order in `<w:tcPr>` and `<w:tblPr>`

OpenXML schemas define element groups using `<xsd:sequence>`. Child elements **must appear in the exact order** declared by the XSD. Word will fail validation if tags are inverted.

#### 1. Cell Properties (`CT_TcPr`) Schema Order:
```
1.  w:cnfStyle
2.  w:tcW           <-- Cell width (dxa)
3.  w:gridSpan      <-- Column span count
4.  w:hMerge
5.  w:vMerge
6.  w:tcBorders     <-- Cell borders
7.  w:shd           <-- Cell background shading
8.  w:noWrap
9.  w:tcMar
10. w:textDirection
11. w:tcFitText
12. w:vAlign
13. w:hideMark
14. w:headers
15. w:cellIns
16. w:cellDel
17. w:cellMerge
18. w:tcPrChange
```

> **Critical Trap:** When setting cell background shading in ONLYOFFICE (`cell.SetShd(...)`), ONLYOFFICE inserts `<w:shd>` directly. If `<w:tcBorders>` is also present, `<w:shd>` is frequently placed **before** `<w:tcBorders>`. In ECMA-376, `w:tcBorders` MUST precede `w:shd`. Post-processing must sort `tcPr` children to restore valid order.

#### 2. Table Properties (`CT_TblPr`) Schema Order:
```
1.  w:tblStyle
2.  w:tblpPr
3.  w:tblOverlap
4.  w:bidiVisual
5.  w:tblStyleRowBandSize
6.  w:tblStyleColBandSize
7.  w:tblW           <-- Total table width
8.  w:jc             <-- Alignment (left, center, right)
9.  w:tblCellSpacing
10. w:tblInd
11. w:tblBorders     <-- Table borders
12. w:shd           <-- Table shading
13. w:tblLayout      <-- Layout algorithm (fixed/autofit)
14. w:tblCellMar
15. w:tblLook
16. w:tblCaption
17. w:tblDescription
18. w:tblPrChange
```

---

## 2. The "Crushed Table" (`Tabla aplastada`) Error in Word

### The Rendering Discrepancy
- **ONLYOFFICE Engine:** When a table has `<w:tblW w:type="pct" w:w="5000"/>` (100% width), ONLYOFFICE dynamically calculates column widths based on available page width, even if the underlying `<w:tblGrid>` contains dummy or default values.
- **Microsoft Word Engine:** Word prioritizes `<w:tblGrid>` and `<w:tcW>` over percentage hints.
- When `Api.CreateTable(rows, cols)` is called, ONLYOFFICE creates a `<w:tblGrid>` with default dummy columns of **20 mm** (1134 twips) each:
  ```xml
  <w:tblGrid>
    <w:gridCol w:w="1134"/>
  </w:tblGrid>
  ```
- **Result in Word:** A 1-column section container table is rendered at exactly **1134 dxa (2 cm / 0.8 inches)** wide. The entire document body is crushed into an unusable 2 cm vertical strip.

### The Fix: Explicit Twip Geometry

1. **Calculate Printable Width:**
   - Standard A4 page: $210\text{ mm} \times 297\text{ mm} = 11906 \times 16838\text{ twips}$ (where $1\text{ mm} \approx 56.693\text{ twips}$, $1\text{ pt} = 20\text{ twips}$).
   - Left Margin: $19\text{ mm} = 1077\text{ twips}$
   - Right Margin: $19\text{ mm} = 1077\text{ twips}$
   - **Net Printable Width:** $11906 - 2 \times 1077 = 9752\text{ twips}$ ($17.2\text{ cm}$).

2. **Enforce Fixed Table Layout:**
   - Set table width in dxa/twips:
     ```xml
     <w:tblW w:w="9752" w:type="dxa"/>
     <w:tblLayout w:type="fixed"/>
     ```

3. **Reconstruct `<w:tblGrid>`:**
   - Define exact `w:gridCol` widths whose sum equals the total table width:
     ```xml
     <w:tblGrid>
       <w:gridCol w:w="2200"/>
       <w:gridCol w:w="1510"/>
       <w:gridCol w:w="1510"/>
       <w:gridCol w:w="1510"/>
       <w:gridCol w:w="1510"/>
       <w:gridCol w:w="1512"/>
     </w:tblGrid>
     ```

4. **Calculate Spanned Cell Widths (`gridSpan`):**
   - For every `<w:tc>` in each row:
     $$\text{cell\_width} = \sum_{k=\text{col\_idx}}^{\text{col\_idx} + \text{span} - 1} \text{col\_widths}[k]$$
   - Write explicit `<w:tcW w:w="{cell_width}" w:type="dxa"/>` on every cell.

---

## 3. Clean Watermark Removal

Community editions of ONLYOFFICE Document Builder inject an evaluation watermark into the header:
```xml
<w:p ...>
  ...
  <mc:AlternateContent>
    ... Unregistered Version ...
  </mc:AlternateContent>
</w:p>
```

### Why String Regex Is Dangerous
- Using naïve regex (`re.sub(...)`) to remove `<mc:AlternateContent>` leaves an empty `<w:p>` preceding the header table.
- This creates unwanted top spacing in the header and risks corrupting surrounding XML tags if namespaces or child nodes vary.

### Recommended DOM-Level Removal
Iterate over top-level children of `<w:hdr>` and remove the exact element:
```python
for child in list(root):
    if "Unregistered Version" in "".join(child.itertext()):
        root.remove(child)
```
This guarantees complete watermark eradication without leaving empty paragraphs or corrupting document markup.
