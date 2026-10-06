# ¿El historial usado coincide con la API oficial (juego 1) por día de la semana? Uso: python datos_check.py <SP>
import sys, csv
from datetime import date
from collections import Counter
SP = sys.argv[1]
H = {}
for ln in open(SP + "/hist_0605.txt"):
    p = ln.split()
    if len(p) == 3: H[(p[0], int(p[1]))] = p[2]
O = {}
for r in csv.DictReader(open("/home/user/lotto-activo/datos_multiloteria/oficial_multi.csv")):
    if r["juego"] == "1": O[(r["fecha"], int(r["hora"][:2]) - 8)] = r["codigo"]
tot, dif, falta = Counter(), Counter(), Counter()
for k, v in O.items():
    if k[0] < "2025-07-01": continue
    dw = date.fromisoformat(k[0]).weekday(); era = "2026" if k[0] >= "2026-01-01" else "2025-S2"
    tot[(era, dw)] += 1
    if k not in H: falta[(era, dw)] += 1
    elif H[k] != v: dif[(era, dw)] += 1
nm = "lun mar mié jue vie sáb dom".split()
for era in ("2025-S2", "2026"):
    print(era, "  ".join(f"{nm[d]} {tot[(era,d)]} dif {dif[(era,d)]} falta {falta[(era,d)]}" for d in range(7)))
print("fechas de la API:", min(O)[0], "..", max(O)[0])
