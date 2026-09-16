import sys
from pypdf import PdfReader

r = PdfReader(sys.argv[1])
for i, p in enumerate(r.pages):
    t = p.extract_text() or ""
    print(f"--- pagina {i} ({len(t)} chars) ---")
    print(t[:1500])
    print()
