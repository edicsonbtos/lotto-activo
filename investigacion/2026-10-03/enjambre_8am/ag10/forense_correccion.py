# ag10 — A: ¿la corrección de fechas 2026-09-29 o los faltantes 2026-10-03 crean/borran repeticiones primero-ayer?
import os, json, collections
from datetime import date, timedelta
from scipy.stats import poisson
AQUI = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.dirname(AQUI)
H = "/home/user/lotto-activo/herramientas/"
corr = json.load(open(H + "correccion_historial_2026-09-29.json"))["cambios"]
falt = json.load(open(H + "faltantes_historial_2026-10-03.json"))["agregar"]
lineas = [l.strip() for l in open(os.path.join(BASE, "hist_la.txt"), encoding="utf-8") if l.strip()]
inv = {c["despues"]: c["antes"] for c in corr}
assert all(c["despues"] in set(lineas) for c in corr), "hist_la no tiene la corrección aplicada"
print("cambios", len(corr), "todos presentes en hist_la (corregido):", True)
antes = [inv.get(l, l) for l in lineas if l not in falt]
dd = collections.Counter((l.split()[0], l.split()[1]) for l in antes)
print("pre-corrección: slots duplicados", sum(v > 1 for v in dd.values()))
fechas_tocadas = sorted({c["antes"].split()[0] for c in corr} | {c["despues"].split()[0] for c in corr})
print("fechas tocadas:", len(fechas_tocadas), fechas_tocadas[0], "..", fechas_tocadas[-1])
# hora de los cambios: ¿se tocaron primeros sorteos?
print("cambios por hora:", sorted(collections.Counter(int(c["antes"].split()[1]) for c in corr).items()))
# cambia el código? (solo deberían cambiar fechas)
print("cambios que tocan hora o código:", sum(c["antes"].split()[1:] != c["despues"].split()[1:] for c in corr))

def pares(ls):
    d = {}
    for l in ls:
        f, h, c = l.split(); d[(f, int(h))] = c
    pr = {}
    for (f, h), c in sorted(d.items()):
        pr.setdefault(f, (h, c))
    out = {}
    for f, (h, c) in pr.items():
        for k in (1, 3):
            y = (date.fromisoformat(f) - timedelta(days=k)).isoformat()
            if y in pr and pr[y][0] == h:
                out[(f, k)] = (c == pr[y][1], h)
    return out
pa, pd = pares(antes), pares(lineas)
for k in (1, 3):
    for era, hh in (("9:00", 1), ("8:00", 0)):
        A = [v for (f, kk), v in pa.items() if kk == k and v[1] == hh]
        D = [v for (f, kk), v in pd.items() if kk == k and v[1] == hh]
        print(f"k={k} era {era}: ANTES de corregir {sum(x[0] for x in A)}/{len(A)}  DESPUÉS {sum(x[0] for x in D)}/{len(D)}  (azar {len(D)/38:.1f})")
cambio = [(key, pa.get(key), pd.get(key)) for key in set(pa) | set(pd) if (pa.get(key) or (None,))[0] != (pd.get(key) or (None,))[0]]
print("pares cuyo resultado (repite/no) cambió con la corrección:", sorted(cambio))
print("días con repetición k=1 en el historial final:", sorted(f for (f, k), v in pd.items() if k == 1 and v[0]))
