# -*- coding: utf-8 -*-
"""Prueba preregistrada (PREREGISTRO.md): ¿salen menos los animales que publican los pronosticadores?
Uso: python analizar.py  -> resultados.json, salida.txt (misma carpeta). Ligero (<100 MB)."""
import io, json, math, os, sys
from collections import defaultdict
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402

SEMILLA, B = 20261014, 4000
W, MITAD, CORTE = 2000, 5688, 9357
FIN_C1 = "2025-12-14"
SAL, RES = [], {}


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)


# ------------------------------------------------------------------ datos publicados
PUB = defaultdict(dict)   # (juego, fecha) -> {fuente: set(idx)}
nerr = 0
for ln in open(os.path.join(AQUI, "datos", "publicados.jsonl"), encoding="utf-8"):
    r = json.loads(ln)
    if "error" in r["datos"]:
        nerr += 1; continue
    for juego, v in r["datos"].items():
        if v.get("fecha_pagina") and v["fecha_pagina"] != r["fecha"]:
            continue                                   # la web devolvió otro día: no vale
        s = {LE.IDX[n] for n in v["nums"] if n in LE.IDX}
        if s:
            PUB[("RD" if "RD" in juego else "LA", r["fecha"])][r["fuente"]] = s


def piramide(fecha):
    a, m, d = fecha.split("-")
    filas = [[int(c) for c in d + m + a]]
    while len(filas[-1]) > 1:
        f = filas[-1]; filas.append([(f[i] + f[i + 1]) % 10 for i in range(len(f) - 1)])
    return {LE.IDX[str(sum(f))] for f in filas if sum(f) <= 36}


assert piramide("2026-10-14") == {LE.IDX[str(n)] for n in (16, 25, 17, 34, 18, 9, 10, 0)}


def conjunto(juego, fecha, fuente):
    p = PUB.get((juego, fecha), {})
    if fuente == "S1":
        return p.get("lotoven")
    if fuente == "S2":
        return p.get("loteriadehoy")
    if fuente == "U":
        if not p:
            return None
        return set().union(*p.values())
    if fuente == "S3":
        return piramide(fecha)


def confusores(fecha, h):
    d = int(fecha[8:10]); r12 = (h + 8 - 1) % 12 + 1
    return {LE.IDX[str(x)] for x in (d, d + 1, r12) if x <= 36}


def medir(P, Y, H, F, DIA, fuente, juego, quitar=False, mult=None):
    o, e, dd, hh, gan, sz = [], [], [], [], [], []
    for t in range(len(Y)):
        A = conjunto(juego, F[t], fuente)
        if A is None:
            continue
        if quitar:
            A = A - confusores(F[t], H[t])
        if not A:
            continue
        a = np.fromiter(A, int)
        sz.append(len(A)); o.append(float(Y[t] in A)); e.append(float(P[t, a].sum())); dd.append(DIA[t]); hh.append(H[t])
        if mult is not None:
            q = P[t].copy(); q[a] *= mult; q /= q.sum()
            gan.append(1000 * math.log2(q[Y[t]] / P[t, Y[t]]))
    o, e, dd, hh = map(np.array, (o, e, dd, hh))
    if len(o) == 0:
        return None
    u, g = np.unique(dd, return_inverse=True)
    so, se = np.bincount(g, o), np.bincount(g, e)
    rng = np.random.default_rng(SEMILLA); idx = rng.integers(0, len(u), (B, len(u)))
    bs = so[idx].sum(1) / se[idx].sum(1)
    out = dict(sorteos=int(len(o)), dias=int(len(u)), obs=int(o.sum()), esp=round(float(e.sum()), 1),
               oe=round(float(o.sum() / e.sum()), 3),
               ic95=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
               tam_medio=round(float(np.mean(sz)), 2),
               por_hora={int(h) + 8: [int(o[hh == h].sum()), round(float(e[hh == h].sum()), 1)] for h in np.unique(hh)})
    # Mantel-Haenszel con E del motor = suma por estratos; z bajo Poisson
    out["z"] = round(float((o.sum() - e.sum()) / math.sqrt(e.sum())), 2)
    if mult is not None:
        gan = np.array(gan); sg = np.bincount(g, gan); n = np.bincount(g)
        bg = sg[idx].sum(1) / n[idx].sum(1)
        out["mbits"] = round(float(gan.mean()), 2)
        out["mbits_ic95"] = [round(float(np.percentile(bg, 2.5)), 2), round(float(np.percentile(bg, 97.5)), 2)]
    return out


def linea(nom, r):
    if r is None:
        log(f"  {nom}: sin datos"); return
    s = (f"  {nom}: días {r['dias']} sorteos {r['sorteos']} obs {r['obs']} esp {r['esp']} "
         f"O/E {r['oe']:.3f} [IC95 {r['ic95'][0]:.2f}; {r['ic95'][1]:.2f}] z {r['z']:+.2f}")
    if "mbits" in r:
        s += f"  ganancia {r['mbits']:+.2f} mbits [{r['mbits_ic95'][0]:+.2f}; {r['mbits_ic95'][1]:+.2f}]"
    log(s)


# ------------------------------------------------------------------ LA: motor walk-forward (hilo 9)
D = LE.cargar(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "calor_cache.npz"))
P = LE.normalizar(c["P"]); Y = c["y"].astype(int)
assert (D.seq[W:CORTE] == Y).all()
H = D.hora[W:CORTE]; F = np.array(D.fecha[W:CORTE]); DIA = D.dia[W:CORTE]; FILA = np.arange(W, CORTE)
SEL = {"desarrollo": FILA < MITAD, "confirmacion1": (FILA >= MITAD) & (F <= FIN_C1)}

# cobertura
for juego in ("LA", "RD"):
    for fu in ("lotoven", "loteriadehoy"):
        k = [len(v[fu]) for (j, f), v in PUB.items() if j == juego and fu in v]
        log(f"cobertura {juego} {fu}: {len(k)} días, {np.mean(k) if k else 0:.2f} animales/día")
log(f"descargas con error: {nerr}")

# diagnóstico de fuga: ¿los datos son los ganadores de ayer o de hoy? (fracción de A_d que salió)
gan_dia = defaultdict(set)
for f_, y_ in zip(D.fecha, D.seq):
    gan_dia[f_].add(int(y_))
from datetime import date as _d, timedelta as _td
for fu in ("lotoven", "loteriadehoy"):
    hoy = ayer = n = 0
    for (j, f_), v in PUB.items():
        if j != "LA" or fu not in v or f_ > FIN_C1 or f_ not in gan_dia:
            continue
        fa = (_d.fromisoformat(f_) - _td(days=1)).isoformat()
        for a in v[fu]:
            n += 1; hoy += a in gan_dia[f_]; ayer += a in gan_dia.get(fa, set())
    if n:
        log(f"fuga? {fu}: de {n} datos, salieron ese día {hoy / n:.3f}, salieron la víspera {ayer / n:.3f} "
            f"(azar con ~11 distintos por día ≈ 0,29)")

for tramo, s in SEL.items():
    log(f"\n== LA {tramo} ({F[s][0]} .. {F[s][-1]})")
    for fu in ("U", "S1", "S2", "S3"):
        RES[f"LA_{tramo}_{fu}"] = r = medir(P[s], Y[s], H[s], F[s], DIA[s], fu, "LA"); linea(fu, r)
    RES[f"LA_{tramo}_U_sin_confusores"] = r = medir(P[s], Y[s], H[s], F[s], DIA[s], "U", "LA", quitar=True)
    linea("U sin día/día+1/hora12", r)

# explotabilidad: x del desarrollo aplicado en confirmación 1
x = RES["LA_desarrollo_U"]["oe"]
s = SEL["confirmacion1"]
RES["LA_confirmacion1_U_explotar"] = r = medir(P[s], Y[s], H[s], F[s], DIA[s], "U", "LA", mult=x)
log(f"\n== Explotar: p×{x:.3f} sobre U (x del desarrollo) en confirmación 1"); linea("U×x", r)

# ------------------------------------------------------------------ RD: réplica (motor P1 del hilo 9, dev)
c = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "cache_todo.npz"))
s = c["tramo"] == "dev"
P1 = c["P1"][s].astype(float); P1 /= P1.sum(1, keepdims=True)
log(f"\n== RD réplica dev ({c['fecha'][s][0]} .. {c['fecha'][s][-1]})")
for fu in ("U", "S1", "S2", "S3"):
    RES[f"RD_dev_{fu}"] = r = medir(P1, c["y"][s], c["hora"][s], c["fecha"][s], c["dia"][s], fu, "RD"); linea(fu, r)

# ------------------------------------------------------------------ Confirmación 2: vivo (/api/mesa)
ruta = os.path.join(AQUI, "datos", "mesa.jsonl")
if os.path.exists(ruta):
    filas = [json.loads(l) for l in open(ruta, encoding="utf-8")]
    filas = [f for f in filas if f["winner_num"] in LE.IDX and f["fecha"] >= "2026-09-15"
             and all(v is not None for v in f["prob"].values())]
    filas.sort(key=lambda f: (f["fecha"], f["hora"]))
    PM = np.array([[f["prob"][n] for n in LE.POS] for f in filas]); PM /= PM.sum(1, keepdims=True)
    YM = np.array([LE.IDX[f["winner_num"]] for f in filas]); HM = np.array([f["hora"] for f in filas])
    FM = np.array([f["fecha"] for f in filas]); DM = np.unique(FM, return_inverse=True)[1]
    log(f"\n== LA confirmación 2, vivo ({FM[0]} .. {FM[-1]}, {len(YM)} sorteos)")
    for fu in ("U", "S1", "S2", "S3"):
        RES[f"LA_vivo_{fu}"] = r = medir(PM, YM, HM, FM, DM, fu, "LA"); linea(fu, r)
    RES["LA_vivo_U_explotar"] = r = medir(PM, YM, HM, FM, DM, "U", "LA", mult=x); linea("U×x", r)

# ------------------------------------------------------------------ veredicto
d, c1 = RES["LA_desarrollo_U"], RES["LA_confirmacion1_U"]
rd = RES["RD_dev_U"]
pasa = c1["oe"] < 1 and c1["ic95"][1] < 1 and (d["oe"] < 1) and rd["oe"] <= 1
RES["veredicto"] = "PASA" if pasa else "NO PASA"
log(f"\nVEREDICTO (U en LA, confirmación 1 + réplica RD): {RES['veredicto']}")
with io.open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as fh:
    json.dump(RES, fh, ensure_ascii=False, indent=1)
with io.open(os.path.join(AQUI, "salida.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(SAL) + "\n")
