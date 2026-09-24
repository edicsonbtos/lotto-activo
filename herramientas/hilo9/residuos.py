# -*- coding: utf-8 -*-
"""Hilo 9, paso 1 (PREREGISTRO_hilo9_subir.md): batería de residuos contra los modelos en uso, SOLO desarrollo.

Uso: python herramientas/hilo9/residuos.py   -> herramientas/resultados/hilo9_residuos.md
Reproducible: sólo lee historial.txt, datos_multiloteria/rdint_hist.csv y las caches walk-forward
(herramientas/exploracion/calor_cache.npz, herramientas/rdint/cache_todo.npz, _b0_intradia_v2.npz).
"""
import os, sys
from collections import defaultdict
from datetime import date, timedelta
from math import erfc, sqrt
import numpy as np

HERR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(HERR)
sys.path.insert(0, HERR); sys.path.insert(0, os.path.join(HERR, "rdint"))
import lotto_eval as LE
import datos as DT

SALIDA = os.path.join(HERR, "resultados", "hilo9_residuos.md")
ALFA = 0.05 / 9
LA_FIN = "2025-12-15"          # se excluyen las fechas corridas del historial (ver hilo 8)
# Verificación independiente: HILO9_DATOS=verificacion/hilo9/datos lee la copia congelada.
DATOS = os.environ.get("HILO9_DATOS")


def ruta(*partes):
    """Ruta de un dato: la copia congelada si HILO9_DATOS está puesto, si no la del proyecto."""
    return os.path.join(DATOS, partes[-1]) if DATOS else os.path.join(*partes)


def dia_menos(f, k):
    return (date.fromisoformat(f) - timedelta(days=k)).isoformat()


def prueba(nombre, P, y, hora, marcas):
    """marcas: lista de arrays/sets de animales marcados por fila (puede ser vacío)."""
    O = E = V = 0.0; n = 0
    por_h = defaultdict(lambda: [0.0, 0.0])
    for t, S in enumerate(marcas):
        if not S:
            continue
        S = list(S); e = float(P[t, S].sum()); o = float(y[t] in S)
        O += o; E += e; V += e * (1 - e); n += 1
        por_h[int(hora[t])][0] += o; por_h[int(hora[t])][1] += e
    z = (O - E) / sqrt(V) if V else 0.0
    p = erfc(abs(z) / sqrt(2))
    horas = " ".join("%d:%.2f" % (h, o / e) for h, (o, e) in sorted(por_h.items()) if e > 0)
    return "| %s | %d | %d | %.1f | %.3f | %+.2f | %.2g | %s | %s |" % (
        nombre, n, O, E, O / E if E else 0, z, p, "**SÍ**" if p < ALFA else "no", horas)


def main():
    L = ["# Hilo 9 — paso 1: residuos contra los modelos en uso (sólo desarrollo)\n",
         "Pre-registro: `herramientas/exploracion/PREREGISTRO_hilo9_subir.md`. O = veces que salió un animal marcado; "
         "E = lo que ya le daba el modelo (suma de P). O/E > 1: el modelo se queda corto; < 1: se pasa. "
         "Pasa si p < 0,05/9 = 0,0056 (dos colas). Última columna: O/E por hora (0 = 8:xx).\n",
         "| hipótesis | sorteos marcados | O | E | O/E | z | p | pasa | O/E por hora |",
         "|---|---|---|---|---|---|---|---|---|"]
    # ---- datos
    la = LE.cargar(ruta(RAIZ, "historial.txt"))
    la_d = defaultdict(dict)
    for f, h, s in zip(la.fecha, la.hora, la.seq):
        la_d[f][int(h)] = int(s)
    rd, *_ = DT.cargar()
    rd_d = defaultdict(dict)
    for f, h, s in zip(rd.fecha, rd.hora, rd.seq):
        rd_d[f][int(h)] = int(s)

    # ---- RD (P1 = B1) tramo dev
    T = np.load(ruta(HERR, "rdint", "cache_todo.npz"))
    s = T["tramo"] == "dev"
    P1 = T["P1"][s].astype(float); y = T["y"][s]; hr = T["hora"][s]; fe = T["fecha"][s]
    P1 = P1 / P1.sum(1, keepdims=True)
    ayer = [set(la_d.get(dia_menos(f, 1), {}).values()) for f in fe]
    anteayer = [set(la_d.get(dia_menos(f, 2), {}).values()) for f in fe]
    dos_hoy = []
    rd_hoy = []
    for f, h in zip(fe, hr):
        c = defaultdict(int)
        for hh, a in la_d.get(f, {}).items():
            if hh <= h:
                c[a] += 1
        dos_hoy.append({a for a, k in c.items() if k >= 2})
        rd_hoy.append({a for hh, a in rd_d.get(f, {}).items() if hh < h})
    L.append(prueba("R1 RD ← LA ayer", P1, y, hr, ayer))
    L.append(prueba("R2 RD ← LA anteayer", P1, y, hr, anteayer))
    L.append(prueba("R3 RD ← LA hoy 2+ veces", P1, y, hr, dos_hoy))
    L.append(prueba("R4 RD ← RD hoy (auto-evitación)", P1, y, hr, rd_hoy))

    # ---- LA (ensamble_v2) filas 2000..9357, fecha < LA_FIN
    C = np.load(ruta(HERR, "exploracion", "calor_cache.npz"))
    PL = C["P"]; yl = C["y"]
    fl = np.array(la.fecha[LE.W:LE.W + len(yl)]); hl = np.asarray(la.hora)[LE.W:LE.W + len(yl)]
    m = fl < LA_FIN
    PL, yl, fl, hl = PL[m], yl[m], fl[m], hl[m]
    tiene_rd = np.array([f in rd_d for f in fl])
    PL, yl, fl, hl = PL[tiene_rd], yl[tiene_rd], fl[tiene_rd], hl[tiene_rd]
    L.append(prueba("L1 LA ← RD ayer", PL, yl, hl, [set(rd_d.get(dia_menos(f, 1), {}).values()) for f in fl]))
    L.append(prueba("L2 LA ← RD anteayer", PL, yl, hl, [set(rd_d.get(dia_menos(f, 2), {}).values()) for f in fl]))
    L.append(prueba("L3 LA ← RD (h−2):30", PL, yl, hl,
                    [{rd_d[f][h - 2]} if h >= 2 and (h - 2) in rd_d.get(f, {}) else set() for f, h in zip(fl, hl)]))
    L.append("\nFilas: RD dev %d (%s..%s); LA dev con RD %d (%s..%s)." % (
        len(y), fe[0], fe[-1], len(yl), fl[0], fl[-1]))

    # ---- E1: mezcla log-lineal de B1 con intradia_v2 de RD, peso walk-forward (bloques de 250)
    I = np.load(ruta(HERR, "rdint", "_b0_intradia_v2.npz"))
    D = np.load(ruta(HERR, "rdint", "cache_dev.npz"))
    fila = D["fila"]; Pi_all = I["P"].astype(float); desde = int(I["desde"])
    Pi = Pi_all[fila - desde]; Pi = Pi / Pi.sum(1, keepdims=True)
    Pb = D["P1"].astype(float); Pb = Pb / Pb.sum(1, keepdims=True); yd = D["y"]; dd = D["dia"]
    assert (D["y"] == y).all(), "cache_dev y cache_todo(dev) no alinean"
    lb, li = np.log(np.clip(Pb, 1e-9, 1)), np.log(np.clip(Pi, 1e-9, 1))
    grid = [(a, b) for a in np.arange(0.5, 1.51, 0.05) for b in np.arange(-0.5, 1.01, 0.05)]

    def ll(a, b, idx):
        z = a * lb[idx] + b * li[idx]; z -= z.max(1, keepdims=True)
        lp = z - np.log(np.exp(z).sum(1, keepdims=True))
        return lp[np.arange(len(idx)), yd[idx]]
    Pn_ly = np.zeros(len(yd)); pesos = []
    R = 250
    for k0 in range(0, len(yd), R):
        idx = np.arange(k0, min(k0 + R, len(yd)))
        if k0 == 0:
            a, b = 1.0, 0.0
        else:
            past = np.arange(0, k0)
            a, b = max(grid, key=lambda g: ll(g[0], g[1], past).sum())
        pesos.append((k0, a, b)); Pn_ly[idx] = ll(a, b, idx)
    base_ly = np.log(Pb[np.arange(len(yd)), yd])
    d = (Pn_ly - base_ly) / np.log(2) * 1000
    rng = np.random.default_rng(20260923)
    u, g = np.unique(dd, return_inverse=True)
    mitad = len(u) // 2

    def ic(sel):
        du = np.unique(g[sel]); S = np.bincount(g[sel], d[sel], len(u)); N = np.bincount(g[sel], None, len(u))
        bs = [S[k].sum() / N[k].sum() for k in (rng.choice(du, len(du)) for _ in range(2000))]
        return d[sel].mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    L.append("\n## E1 — RD: B1 mezclado con intradia_v2 (walk-forward)\n")
    L.append("| tramo | n | Δ mbits | IC95 | pasa (≥ +5 e IC > 0) |")
    L.append("|---|---|---|---|---|")
    pasa = []
    for nom, sel in (("dev completo", np.ones(len(d), bool)), ("1ª mitad", g < mitad), ("2ª mitad", g >= mitad)):
        mu, lo, hi = ic(sel); ok = mu >= 5 and lo > 0; pasa.append(ok)
        L.append("| %s | %d | %+.2f | [%+.2f, %+.2f] | %s |" % (nom, sel.sum(), mu, lo, hi, "sí" if ok else "no"))
    L.append("\nPesos (a sobre B1, b sobre intradia_v2) al inicio de cada bloque: " +
             ", ".join("%d:(%.2f,%.2f)" % p for p in pesos[::4]) + ". **E1: %s**" % ("PASA" if all(pasa[1:]) else "NO PASA"))
    txt = "\n".join(L)
    print(txt, flush=True)
    with open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
