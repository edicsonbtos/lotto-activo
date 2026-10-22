# -*- coding: utf-8 -*-
"""Pruebas del motor por otras vías (diagnóstico preregistrado, no decide nada) sobre pronósticos congelados en vivo."""
import sys, os, json, csv, numpy as np
from collections import defaultdict
from datetime import date
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lotto_eval as LE
from rasgos import IDX, NUM
AQ = os.path.dirname(os.path.abspath(__file__))
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
gan = {(f, int(h)): int(s) for f, h, s in zip(D.fecha, D.hora, D.seq)}
for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/oficial_multi.csv"))):
    if r["juego"] == "1": gan.setdefault((r["fecha"], int(r["hora"][:2]) - 8), IDX[r["codigo"]])
mesas = {m: [r for r in json.load(open(os.path.join(AQ, f"vivo/mesa_{m}_2026-10-22.json"))) if r and r["winner"] is not None and r["p"] and None not in r["p"]]
         for m in ("ensamble", "principal")}
for rows in mesas.values():
    for r in rows: gan.setdefault((r["fecha"], r["hora"]), r["winner"])
orden = sorted(gan); pos = {k: i for i, k in enumerate(orden)}; seq = [gan[k] for k in orden]
rng = np.random.default_rng(20261022)
def oe(lista):   # lista de (obs, esp)
    o = sum(a for a, b in lista); e = sum(b for a, b in lista)
    return f"{o:4.0f}/{e:6.1f} = {o/e if e else float('nan'):.2f} (z {(o-e)/np.sqrt(max(e*(1-e/len(lista)),1e-9)):+.1f})"
for m, rows in mesas.items():
    print(f"\n===== {m} (n={len(rows)})")
    # 1. calibración por puesto
    bandas = [(1, 5), (6, 10), (11, 15), (16, 25), (26, 38)]
    print("1) calibración por puesto: esperado vs salió")
    for a, b in bandas:
        L = []
        for r in rows:
            p = np.array(r["p"]) / sum(r["p"]); o = np.argsort(-p)
            L.append((float(a <= r["rank"] <= b), p[o[a - 1:b]].sum()))
        print(f"   puestos {a:2d}-{b:2d}: {oe(L)}")
    # 2. O/E por grupos
    grupos = defaultdict(list)
    for r in rows:
        p = np.array(r["p"]) / sum(r["p"]); w = r["winner"]; k = pos[(r["fecha"], r["hora"])]
        d = date.fromisoformat(r["fecha"])
        # hueco del ganador vs masa del modelo por tramo de hueco
        hue = np.full(38, 999)
        for j in range(k - 1, max(-1, k - 400), -1):
            c = seq[j]
            if hue[c] == 999: hue[c] = k - j
        for lbl, rg in (("1-12", (1, 12)), ("13-36", (13, 36)), ("37-84", (37, 84)), ("85+", (85, 9999))):
            mk = (hue >= rg[0]) & (hue <= rg[1]); grupos["hueco " + lbl].append((float(mk[w]), p[mk].sum()))
        hoy = {gan[(r["fecha"], h)] for h in range(r["hora"]) if (r["fecha"], h) in gan}
        mk = np.array([c in hoy for c in range(38)]); grupos["ya salió hoy"].append((float(mk[w]), p[mk].sum()))
        mk = np.array([NUM[c] == d.day for c in range(38)]); grupos["número = día del mes"].append((float(mk[w]), p[mk].sum()))
        h12 = [8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7][r["hora"]]
        mk = np.array([NUM[c] == h12 for c in range(38)]); grupos["número = hora (12 h)"].append((float(mk[w]), p[mk].sum()))
        grupos[f"hora {r['hora']:02d}"].append((float(r["rank"] <= 15), p[np.argsort(-p)[:15]].sum()))
        grupos[f"día sem {d.weekday()}"].append((float(r["rank"] <= 15), p[np.argsort(-p)[:15]].sum()))
    print("2) O/E (salió / el modelo esperaba). Hora y día: aciertos Top-15 vs esperado")
    for g in sorted(grupos): print(f"   {g:22s} {oe(grupos[g])}")
    # 3. permutación: barajar ganadores entre sorteos de la misma hora
    P = [np.array(r["p"]) / sum(r["p"]) for r in rows]; W = np.array([r["winner"] for r in rows]); H = np.array([r["hora"] for r in rows])
    real = np.mean([1000 * np.log2(P[i][W[i]] * 38) for i in range(len(rows))])
    nul = []
    for _ in range(1000):
        Wp = W.copy()
        for h in set(H):
            ix = np.where(H == h)[0]; Wp[ix] = Wp[rng.permutation(ix)]
        nul.append(np.mean([1000 * np.log2(P[i][Wp[i]] * 38) for i in range(len(rows))]))
    nul = np.array(nul)
    print(f"3) permutación: señal real {real:+.1f} mbits; barajado {nul.mean():+.1f} ± {nul.std():.1f}; p = {(nul >= real).mean():.3f}")
    # 4. rachas: P(≤3 aciertos Top-15 en 13 sorteos) según el propio modelo (Poisson-binomial) y frecuencia en vivo
    q15 = np.array([p[np.argsort(-p)[:15]].sum() for p in P]); hit = np.array([r["rank"] <= 15 for r in rows])
    sim = (rng.random((20000, 13)) < q15.mean()).sum(1)
    ventanas = [hit[i:i + 13].sum() for i in range(len(hit) - 12)]
    print(f"4) P(≤3 de 13 en Top-15) según el modelo: {(sim <= 3).mean()*100:.1f}% por ventana; "
          f"ventanas de 13 en vivo con ≤3: {sum(v <= 3 for v in ventanas)} de {len(ventanas)}")
