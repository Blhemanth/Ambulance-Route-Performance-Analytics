import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import os

doc = docx.Document()
section = doc.sections[0]
footer = section.footer
p = footer.paragraphs[0]
p.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.RIGHT
p.add_run("Page ")
p._p.append(parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w')))
p.add_run(" of ")
p._p.append(parse_xml(r'<w:fldSimple %s w:instr="NUMPAGES"/>' % nsdecls('w')))
doc.save("test_footer.docx")
print("Footer test passed successfully!")
if os.path.exists("test_footer.docx"):
    os.remove("test_footer.docx")
