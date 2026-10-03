# Exploración SOLO en dev (y conteo crudo en cal). No toca prueba ni vivo.
import numpy as np, json
from comun import *
dev = [t for t in FIRST if TR[t] == "dev"]
dev9 = [t for t in dev if H[t] == 1]; dev8 = [t for t in dev if H[t] == 0]
cal = [t for t in FIRST if TR[t] == "cal"]
print("dev", len(dev), "9:00", len(dev9), "8:00", len(dev8), "cal", len(cal))
rows = []
for (tipo, k, j) in rasgos():
    O, E, n = oe(dev, k, j); O9, E9, _ = oe(dev9, k, j); O8, E8, _ = oe(dev8, k, j)
    # cal: crudo contra 1/38
    Oc = 0; nc = 0
    for t in cal:
        a = objetivo(t, k, j)
        if a is None: continue
        nc += 1; Oc += int(S[t] == a)
    rows.append(dict(tipo=tipo, k=k, j=j, n=n, O=O, E=E, oe=O/E if E else np.nan, p=poisson_p2(O, E),
                     O9=O9, E9=E9, O8=O8, E8=E8, Oc=Oc, Ec=nc/38))
q = bh([r["p"] for r in rows])
for r, qq in zip(rows, q): r["q"] = qq
def mismo_signo(r): return (r["O9"] - r["E9"]) * (r["O8"] - r["E8"]) > 0
print("nº rasgos en la familia:", len(rows))
print("\n== Controles (ya en P_aj) ==")
for r in rows:
    if r["tipo"] == "A" and r["j"] == 0 and r["k"] in (1, 3):
        print(f"k={r['k']} j=0  O={r['O']} E={r['E']:.1f} O/E={r['oe']:.2f} IC={ic(r['O'])[0]/r['E']:.2f}-{ic(r['O'])[1]/r['E']:.2f} p={r['p']:.3f}  9:00 {r['O9']}/{r['E9']:.1f}  8:00 {r['O8']}/{r['E8']:.1f}")
print("\n== Top 25 por p (dev, dos eras) ==")
for r in sorted(rows, key=lambda r: r["p"])[:25]:
    print(f"{r['tipo']} k={r['k']:2d} j={str(r['j']):>3}  n={r['n']} O={r['O']:2d} E={r['E']:5.1f} O/E={r['oe']:.2f} p={r['p']:.4f} q={r['q']:.2f}  "
          f"9:00 {r['O9']}/{r['E9']:.1f}={r['O9']/max(r['E9'],1e-9):.2f}  8:00 {r['O8']}/{r['E8']:.1f}={r['O8']/max(r['E8'],1e-9):.2f}  "
          f"signo={'=' if mismo_signo(r) else 'X'}  cal {r['Oc']}/{r['Ec']:.1f}")
print("\nBH q<0.10:", sum(r["q"] < 0.10 for r in rows), " q<0.10 y mismo signo:", sum((r["q"] < 0.10) and mismo_signo(r) for r in rows))
# Mapa k x j (O/E)
print("\n== Mapa O/E dev (filas k=1..14, columnas j=0..11) ==")
M = {(r["k"], r["j"]): r for r in rows if r["tipo"] == "A"}
print("k\\j " + " ".join(f"{j:5d}" for j in range(12)))
for k in range(1, 15):
    print(f"{k:3d} " + " ".join(f"{M[(k,j)]['oe']:5.2f}" for j in range(12)))
print("\n== Primero de hace k (j=0) y último de hace k, k=1..30 ==")
for k in range(1, 31):
    a = M.get((k, 0)) or next(r for r in rows if r["tipo"]=="A" and r["k"]==k and r["j"]==0)
    # último
    if k <= 14:
        Ou, Eu, _ = oe(dev, k, "ult"); pu = poisson_p2(Ou, Eu)
    else:
        u = next(r for r in rows if r["tipo"]=="U" and r["k"]==k); Ou, Eu, pu = u["O"], u["E"], u["p"]
    print(f"k={k:2d} primero O={a['O']:2d} E={a['E']:5.1f} O/E={a['oe']:.2f} p={a['p']:.3f} (9:{a['O9']}/{a['E9']:.1f} 8:{a['O8']}/{a['E8']:.1f}) | último O={Ou:2d} E={Eu:5.1f} O/E={Ou/Eu:.2f} p={pu:.3f}")
# Estructura
print("\n== Estructura (agregados, excluyendo los controles k=1,3 j=0) ==")
def agg(sel, filas=dev):
    O = E = 0
    for (tipo, k, j) in sel:
        o, e, _ = oe(filas, k, j); O += o; E += e
    return O, E
celdas = [("A", k, j) for k in range(1, 15) for j in range(12) if not (j == 0 and k in (1, 3))]
for nombre, sel in [("k par (A, todas j)", [c for c in celdas if c[1] % 2 == 0]),
                    ("k impar (A, todas j)", [c for c in celdas if c[1] % 2 == 1])]:
    for fn, fl in (("dev", dev), ("9:00", dev9), ("8:00", dev8)):
        O, E = agg(sel, fl); print(f"{nombre:28s} {fn:5s} O={O} E={E:.1f} O/E={O/E:.3f} p={poisson_p2(O,E):.3f}")
prim = [("A", k, 0) for k in range(1, 31) if k not in (1, 3)]
for nombre, sel in [("primero k par (2..30, sin 1,3)", [c for c in prim if c[1] % 2 == 0]),
                    ("primero k impar (5..29)", [c for c in prim if c[1] % 2 == 1]),
                    ("primero k=7,14,21,28", [c for c in prim if c[1] % 7 == 0]),
                    ("primero resto k (sin 1,3,7x)", [c for c in prim if c[1] % 7 != 0])]:
    for fn, fl in (("dev", dev), ("9:00", dev9), ("8:00", dev8)):
        O, E = agg(sel, fl); print(f"{nombre:32s} {fn:5s} O={O} E={E:.1f} O/E={O/E:.3f} p={poisson_p2(O,E):.3f}")
# misma semana, todas las posiciones j k=7,14
for nombre, sel in [("A k=7,14 todas j", [c for c in celdas if c[1] in (7, 14)])]:
    for fn, fl in (("dev", dev), ("9:00", dev9), ("8:00", dev8)):
        O, E = agg(sel, fl); print(f"{nombre:32s} {fn:5s} O={O} E={E:.1f} O/E={O/E:.3f} p={poisson_p2(O,E):.3f}")
# por posición j agregando k=1..14 (salvo controles)
print("\n== Por posición j (k=1..14 juntos, sin controles) ==")
for j in range(12):
    sel = [c for c in celdas if c[2] == j]
    O, E = agg(sel); O9, E9 = agg(sel, dev9); O8, E8 = agg(sel, dev8)
    print(f"j={j:2d} O={O} E={E:.1f} O/E={O/E:.3f} p={poisson_p2(O,E):.3f}  9:00 {O9/max(E9,1e-9):.2f}  8:00 {O8/max(E8,1e-9):.2f}")
print("\n== Por k (todas j, sin controles) ==")
for k in range(1, 15):
    sel = [c for c in celdas if c[1] == k]
    O, E = agg(sel); O9, E9 = agg(sel, dev9); O8, E8 = agg(sel, dev8)
    print(f"k={k:2d} O={O} E={E:.1f} O/E={O/E:.3f} p={poisson_p2(O,E):.3f}  9:00 {O9/max(E9,1e-9):.2f}  8:00 {O8/max(E8,1e-9):.2f}")
json.dump([{kk: (v if not isinstance(v, (np.floating, np.integer)) else v.item()) for kk, v in r.items()} for r in rows],
          open(os.path.join(AQUI, "dev_rasgos.json"), "w"), indent=0, default=str)
# conteo crudo en cal por posición j (k=1..14) contra 1/38
print("\n== cal (crudo vs 1/38) por posición j, k=1..14 ==")
for j in range(12):
    Oc = sum(r["Oc"] for r in rows if r["tipo"]=="A" and r["j"]==j and r["k"]<=14)
    Ec = sum(r["Ec"] for r in rows if r["tipo"]=="A" and r["j"]==j and r["k"]<=14)
    if Ec: print(f"j={j:2d} O={Oc} E={Ec:.1f} O/E={Oc/Ec:.2f}")
