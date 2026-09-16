# Analiza estructura DOM de una semana tuazar guardada en disco.
import io
import sys
from scrapling import Selector

ruta = sys.argv[1]
with io.open(ruta, encoding="utf-8") as f:
    html = f.read()

sel = Selector(html)
# tablas semanales
tablas = sel.css("table")
print("tablas:", len(tablas))
for i, t in enumerate(tablas[:6]):
    cab = t.css("thead th")
    print(f"--- tabla {i}: th en thead = {[c.get() for c in cab][:10]}")
    filas = t.css("tbody tr")
    print(f"    filas tbody: {len(filas)}")
    if filas:
        celdas = filas[0].css("th, td")
        print("    fila0 celdas:", len(celdas))
        for c in celdas[:4]:
            print("      celda:", repr(c.get())[:150])
# contenedores por loteria
juegos = sel.css(".lw-game")
print("lw-game count:", len(juegos))
nombres = {}
for g in juegos:
    n = (g.get() or "").strip()
    nombres[n] = nombres.get(n, 0) + 1
for k, v in sorted(nombres.items()):
    print(f"  {k}: {v} filas")
