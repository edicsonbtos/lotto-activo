# -*- coding: utf-8 -*-
"""Ciega 2 de H1 (adenda): réplica en otros juegos de 38 casillas, línea base = uniforme sobre los no salidos hoy."""
import sys, os, csv, numpy as np
from collections import defaultdict
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lotto_eval as LE
from rasgos import mascaras, IDX, POS
rng = np.random.default_rng(20261022)
NOMBRE_A_COD = {}
def medir(dias_seq, etiqueta):
    """dias_seq: {fecha: [idx en orden]} -> O/E de vecinos de rueda del anterior, base uniforme sin repetidos del día."""
    reg = []
    for f in sorted(dias_seq):
        s = dias_seq[f]
        for j in range(1, len(s)):
            vistos = set(s[:j]); libres = [c for c in range(38) if c not in vistos]
            mk = mascaras(s[j - 1], 1, 0)["H1_rueda"]
            e = sum(mk[c] for c in libres) / len(libres)
            reg.append((f, float(mk[s[j]]), e))
    o = sum(r[1] for r in reg); e = sum(r[2] for r in reg)
    por = defaultdict(lambda: [0.0, 0.0])
    for r in reg: por[r[0]][0] += r[1]; por[r[0]][1] += r[2]
    a = np.array(list(por.values())); B = []
    for _ in range(5000):
        x = a[rng.integers(0, len(a), len(a))].sum(0); B.append(x[0] / x[1])
    B = np.array(B)
    print(f"{etiqueta:44s} n={len(reg):5d} obs {o:5.0f} esp {e:6.1f} O/E {o/e:.3f} IC95 [{np.percentile(B,2.5):.2f};{np.percentile(B,97.5):.2f}] p(O/E≥1) {(B>=1).mean():.4f}")
# LA desarrollo (para comparar escala con la línea base simple)
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
la = defaultdict(list)
for t in range(2000, 9357): pass
for f, s in zip(D.fecha[:9357], D.seq[:9357]): la[f].append(int(s))
la = {f: v for f, v in la.items() if f >= D.fecha[2000]}
medir(la, "LA desarrollo (base simple)")
# LARD tramo ciego
lard = defaultdict(list); fil = []
for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/oficial_multi.csv"))):
    if r["juego"] == "3" and "2026-02-01" <= r["fecha"] <= "2026-09-22" and r["codigo"] in IDX:
        fil.append((r["fecha"], r["hora"], IDX[r["codigo"]]))
for f, h, c in sorted(fil): lard[f].append(c)
medir(lard, "LARD ciega 2026-02-01..09-22  (DECIDE)")
# RD desarrollo de RD (descriptivo): rdint_hist.csv con nombres
sys.path.insert(0, RAIZ)
import ast, re, unicodedata
src = open(os.path.join(RAIZ, "rdint_vivo.py"), encoding="utf-8").read()
NOMBRE = ast.literal_eval(re.search(r"^NOMBRE = (\{.*?\})", src, re.S | re.M).group(1))
norm = lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower().strip()
inv = {norm(v): k for k, v in NOMBRE.items()}
rd = defaultdict(list); malos = 0
for r in sorted(csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/rdint_hist.csv"), encoding="utf-8")), key=lambda r: (r["fecha"], r["hora"])):
    if "2024-03-01" <= r["fecha"] <= "2025-06-30":
        c = inv.get(norm(r["animal"]))
        if c is None: malos += 1; continue
        rd[r["fecha"]].append(IDX[c])
print("RD nombres sin mapear:", malos)
medir(rd, "RD desarrollo 2024-03..2025-06 (descriptivo)")
