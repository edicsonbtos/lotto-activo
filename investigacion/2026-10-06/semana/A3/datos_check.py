from comun import *
import csv
from collections import Counter
print("Repeticiones del día: hueco G (sorteos desde la salida anterior hoy)")
for era, me in (("dev", DEV), ("2026", A26)):
    for g, gm in (("MVF", MVF), ("SM", ~MVF)):
        m = me & gm & HOYB[rows, y]; c = Counter(np.minimum(G[rows, y][m], 8))
        print(f"  {era:4} {g:3} n={m.sum():4d}  G=1:{c[1]:3d} 2:{c[2]:3d} 3:{c[3]:3d} 4:{c[4]:3d} 5:{c[5]:3d} 6:{c[6]:3d} 7:{c[7]:3d} 8+:{c[8]:3d}")
# concordancia con API oficial (juego 1 = LA) y lottoactivo.csv
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
hist = {(D.fecha[T], int(HORA[T])): POS[SEQ[T]] for T in range(n)}
def norm(c):
    c = c.strip(); return c if c in ("0", "00") else str(int(c))
def comp(path, fj, fh, fc, filt=None, hconv=None):
    ok = Counter(); bad = Counter(); miss = Counter(); ejemplos = []
    with open(path) as fh_:
        r = csv.DictReader(fh_)
        for row in r:
            if filt and not filt(row): continue
            fe = row[fj]; ho = hconv(row[fh])
            if ho is None or fe < "2026-01-01": continue
            k = (fe, ho); dw = date.fromisoformat(fe).weekday()
            if k not in hist: miss[dw] += 1; continue
            if norm(row[fc]) == hist[k]: ok[dw] += 1
            else: bad[dw] += 1; ejemplos.append((fe, ho, row[fc], hist[k]))
    print(f"\n{path.split('/')[-1]}: por día (lun..dom) coinciden / difieren / faltan en historial")
    for k in range(7): print(f"   {['lun','mar','mié','jue','vie','sáb','dom'][k]}: {ok[k]:4d} / {bad[k]:3d} / {miss[k]:3d}")
    print("   ejemplos de diferencias:", ejemplos[:8])
import sys
def hc(s):
    hh = int(s.split(":")[0]); return hh - 8 if 8 <= hh <= 19 else None
comp("/home/user/lotto-activo/datos_multiloteria/oficial_multi.csv", "fecha", "hora", "codigo", filt=lambda r: r["juego"] == "1", hconv=hc)
comp("/home/user/lotto-activo/datos_multiloteria/lottoactivo.csv", "fecha", "hora", "numero", hconv=hc)
