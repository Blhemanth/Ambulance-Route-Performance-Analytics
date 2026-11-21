import docx
import os

doc = docx.Document("AMBULANCE_ROUTE_OPTIMIZATION_FINAL_REPORT.docx")
print("File size:", os.path.getsize("AMBULANCE_ROUTE_OPTIMIZATION_FINAL_REPORT.docx"), "bytes")
print("Paragraphs count:", len(doc.paragraphs))
print("Tables count:", len(doc.tables))

page_breaks = 0
for p in doc.paragraphs:
    for r in p.runs:
        if 'w:type="page"' in r._r.xml:
            page_breaks += 1
print("Explicit page breaks count:", page_breaks)

inline_shapes = 0
for p in doc.paragraphs:
    for r in p.runs:
        if "drawing" in r._r.xml:
            inline_shapes += 1
print("Drawings / Inline shapes found:", inline_shapes)
