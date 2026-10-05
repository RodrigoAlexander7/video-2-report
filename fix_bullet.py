with open("generate_report.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace add_bullet_point implementation
old_func = """def add_bullet_point(cell, bold_text, desc_text):
    p = cell.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    r_b = p.add_run(bold_text)
    r_b.bold = True
    r_b.font.name = "Arial"
    r_b.font.size = Pt(10)
    r_d = p.add_run(desc_text)
    r_d.font.name = "Arial"
    r_d.font.size = Pt(10)
    return p"""

new_func = """def add_bullet_point(cell, bold_text, desc_text):
    p = cell.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    r_sym = p.add_run("▪  ")
    r_sym.font.name = "Arial"
    r_sym.font.size = Pt(10)
    r_sym.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    r_b = p.add_run(bold_text)
    r_b.bold = True
    r_b.font.name = "Arial"
    r_b.font.size = Pt(10)
    r_d = p.add_run(desc_text)
    r_d.font.name = "Arial"
    r_d.font.size = Pt(10)
    return p"""

content = content.replace(old_func, new_func)
with open("generate_report.py", "w", encoding="utf-8") as f:
    f.write(content)

print("generate_report.py patched!")
