# -*- coding: utf-8 -*-
"""Correcciones de LA (primer sorteo + exposición fecha/hora) sobre el motor de RD Internacional.

Uso (cada etapa en su propio proceso; ver PREREGISTRO.md):
  python analizar.py dev    -> ajusta los 6 factores SOLO con dev RD (2024-03-01..2025-06-30) -> factores.json
  python analizar.py conf   -> confirmación UNA vez en desc (2026-04-13..2026-09-13) con factores congelados
  python analizar.py vivo   -> reconstruye el motor RD en vivo (2026-09-14..último dato de oficial_multi.csv)
                               y mide lo mismo (descriptivo); además aplica la corrección al congelado de /api/rdint
                               si se pasa la ruta de un JSON descargado:  python analizar.py vivo api_rdint.json
Salidas: factores.json, resultados_<etapa>.json (y lo que imprime).
"""
import csv, io, json, os, sys
from datetime import date, timedelta
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
HERR = os.path.join(RAIZ, "herramientas")
sys.path.insert(0, HERR); sys.path.insert(0, os.path.join(HERR, "rdint"))
import lotto_eval as LE          # noqa: E402
import modelo as MB              # noqa: E402  (herramientas/rdint/modelo.py: ajustar, features)

K = LE.K
CACHE = os.path.join(HERR, "rdint", "cache_todo.npz")
FACT = os.path.join(AQUI, "factores.json")
NOMBRES = ["primer_ayer", "primer_hace3", "dia-1", "dia", "dia+1", "hora12"]
GRUPO_A, GRUPO_B = [0, 1], [2, 3, 4, 5]
SEMILLA, NBOOT = 20261015, 4000


# ------------------------------------------------------------------ rasgos
def rasgos(fecha, hora, y):
    """X (n, 38, 6) float32. Solo usa el pasado: primeros sorteos de días anteriores y el calendario."""
    n = len(y); X = np.zeros((n, K, 6), np.float32)
    primero = {}
    for f, h, s in zip(fecha, hora, y):
        primero.setdefault(f, (int(h), int(s)))
    vista = set()
    for t in range(n):
        f, h = fecha[t], int(hora[t])
        if f not in vista:                              # primer sorteo de este día
            vista.add(f)
            f0 = date.fromisoformat(f)
            for j, k in ((0, 1), (1, 3)):
                x = primero.get((f0 - timedelta(days=k)).isoformat())
                if x is not None and x[0] == h:
                    X[t, x[1], j] = 1
        d = int(f[8:10]); h12 = (h + 8 - 1) % 12 + 1
        for j, num in ((2, d - 1), (3, d), (4, d + 1), (5, h12)):
            if 1 <= num <= 36:
                X[t, LE.IDX[str(num)], j] = 1
    return X


def aplicar(P, X, b, cols=None):
    bb = np.zeros(X.shape[2]); cols = range(len(b)) if cols is None else cols
    for c in cols:
        bb[c] = b[c]
    z = np.log(np.clip(P, 1e-12, None)) + (X @ bb.astype(np.float32)).astype(np.float64)
    z -= z.max(1, keepdims=True); q = np.exp(z)
    return q / q.sum(1, keepdims=True)


# ------------------------------------------------------------------ métricas
def dmbits(Pa, Pb, y):
    r = np.arange(len(y))
    return 1000 * (np.log2(Pa[r, y]) - np.log2(Pb[r, y]))


def puesto(P, y):
    orden = LE.rankings(P)
    return np.argmax(orden == y[:, None], axis=1)


def estrat(d, hora):
    hs = [h for h in range(12) if (hora == h).any()]
    return float(np.mean([d[hora == h].mean() for h in hs]))


def boot(d, hora, fecha, nb=NBOOT, semilla=SEMILLA):
    """IC90 de la media estratificada por hora, remuestreando jornadas completas."""
    dias = np.unique(fecha); idx = {f: np.flatnonzero(fecha == f) for f in dias}
    rng = np.random.default_rng(semilla); out = np.empty(nb)
    for b in range(nb):
        sel = np.concatenate([idx[f] for f in rng.choice(dias, len(dias))])
        out[b] = estrat(d[sel], hora[sel])
    return [float(np.percentile(out, 5)), float(np.percentile(out, 95))], float((out <= 0).mean())


def informe(P1, X, y, hora, fecha, b, etiqueta):
    res = {"tramo": etiqueta, "n": int(len(y)), "dias": int(len(np.unique(fecha))),
           "desde": str(fecha[0]), "hasta": str(fecha[-1])}
    p0 = puesto(P1, y)
    for nombre, cols in (("conjunto", None), ("a_primer", GRUPO_A), ("b_exposicion", GRUPO_B)):
        Pa = aplicar(P1, X, b, cols); d = dmbits(Pa, P1, y); pa = puesto(Pa, y)
        ic, pneg = boot(d, hora, fecha)
        r = {"mbits_estrat": estrat(d, hora), "mbits_crudo": float(d.mean()), "ic90": ic, "p_boot_le0": pneg,
             "top3": [float((p0 < 3).mean() * 100), float((pa < 3).mean() * 100)],
             "top5": [float((p0 < 5).mean() * 100), float((pa < 5).mean() * 100)],
             "top15": [float((p0 < 15).mean() * 100), float((pa < 15).mean() * 100)],
             "por_hora": [round(float(d[hora == h].mean()), 2) if (hora == h).any() else None for h in range(12)]}
        es1 = np.r_[True, fecha[1:] != fecha[:-1]]
        r["mbits_primer_sorteo"] = float(d[es1].mean()); r["n_primer"] = int(es1.sum())
        res[nombre] = r
    # conteos O/E de cada rasgo contra el motor (descriptivo)
    oe = {}
    for j, nm in enumerate(NOMBRES):
        m = X[:, :, j] > 0
        O = int(m[np.arange(len(y)), y].sum()); E = float((P1 * m).sum())
        oe[nm] = {"O": O, "E": round(E, 1), "OE": round(O / E, 3) if E > 0 else None}
    res["OE_contra_motor"] = oe
    res["criterio"] = {"ic90_inf_mayor_0": res["conjunto"]["ic90"][0] > 0,
                       "top5_no_empeora_0.5pp": res["conjunto"]["top5"][1] - res["conjunto"]["top5"][0] >= -0.5}
    res["PASA"] = all(res["criterio"].values())
    return res


def imprimir(res):
    print("== %s: n=%d (%d días) %s..%s" % (res["tramo"], res["n"], res["dias"], res["desde"], res["hasta"]))
    for nm in ("conjunto", "a_primer", "b_exposicion"):
        r = res[nm]
        print("  %-13s %+7.2f mbits [IC90 %+.2f; %+.2f] p<=0 %.3f | Top-3 %.2f->%.2f Top-5 %.2f->%.2f Top-15 %.2f->%.2f"
              " | primer sorteo %+.1f (n=%d)" % (nm, r["mbits_estrat"], r["ic90"][0], r["ic90"][1], r["p_boot_le0"],
                                                 *r["top3"], *r["top5"], *r["top15"], r["mbits_primer_sorteo"], r["n_primer"]))
    print("  por hora (conjunto):", res["conjunto"]["por_hora"])
    print("  O/E contra motor:", {k: (v["O"], v["E"], v["OE"]) for k, v in res["OE_contra_motor"].items()})
    print("  criterio:", res["criterio"], "-> PASA" if res["PASA"] else "-> NO PASA")


def cache(tramo):
    z = np.load(CACHE)
    t = z["tramo"]; f = z["fecha"]; h = z["hora"]; y = z["y"]
    X = rasgos(list(f), h, y)                        # primeros de días previos (incluye cal/dev anteriores)
    m = t == tramo
    return z["P1"][m].astype(np.float64), X[m], y[m], h[m], f[m]


# ------------------------------------------------------------------ etapas
def etapa_dev():
    P1, X, y, h, f = cache("dev")
    assert f[0] >= "2024-03-01" and f[-1] <= "2025-06-30"
    b = MB.ajustar(np.log(np.clip(P1, 1e-12, None)), X, y, lam=1.0)
    fac = {"b": [float(v) for v in b], "mult": {nm: round(float(np.exp(v)), 4) for nm, v in zip(NOMBRES, b)},
           "ajuste": "modelo.ajustar(lam=1) sobre P1 de cache_todo.npz, solo filas dev 2024-03-01..2025-06-30",
           "congelado": "2026-10-14"}
    with open(FACT, "w", encoding="utf-8") as fh:
        json.dump(fac, fh, indent=1, ensure_ascii=False)
    print("factores congelados:", fac["mult"])
    res = informe(P1, X, y, h, f, b, "dev (dentro de muestra)"); imprimir(res)
    json.dump(res, open(os.path.join(AQUI, "resultados_dev.json"), "w"), indent=1)


def _b():
    with open(FACT, encoding="utf-8") as fh:
        return np.array(json.load(fh)["b"])


def etapa_conf():
    b = _b()
    P1, X, y, h, f = cache("desc")
    res = informe(P1, X, y, h, f, b, "confirmación desc"); imprimir(res)
    json.dump(res, open(os.path.join(AQUI, "resultados_conf.json"), "w"), indent=1)


def _leer_series():
    """RD y LA (fecha, h, idx) desde rdint_hist.csv + historial.txt + oficial_multi.csv (juegos 2 y 1)."""
    sys.path.insert(0, os.path.join(HERR, "rdint")); import datos as DT
    rd = {}
    with io.open(DT.RD_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cod = DT.ANIMALES.get(DT.sin_acentos(r["animal"])); hh = int(r["hora"][:2]) - 8
            if cod is not None and r["hora"].endswith(":30") and 0 <= hh <= 11:
                rd[(r["fecha"], hh)] = LE.IDX[cod]
    la = {}
    lah = LE.cargar(os.path.join(RAIZ, "historial.txt"))
    for f, hh, s in zip(lah.fecha, lah.hora, lah.seq):
        la[(f, int(hh))] = int(s)
    choques = 0
    with io.open(os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            hh = int(r["hora"][:2]) - 8; cod = r["codigo"]
            if cod not in LE.IDX:
                continue
            dest = rd if r["juego"] == "2" else la if r["juego"] == "1" else None
            if dest is None or not 0 <= hh <= 11:
                continue
            k = (r["fecha"], hh)
            if k in dest and dest[k] != LE.IDX[cod]:
                choques += 1
            dest.setdefault(k, LE.IDX[cod])
    return rd, la, choques


def etapa_vivo(ruta_api=None):
    b = _b()
    rd, la, choques = _leer_series()
    claves = sorted(rd)
    fechas = [k[0] for k in claves]; horas = np.array([k[1] for k in claves]); seq = np.array([rd[k] for k in claves])
    d0 = date.fromisoformat(fechas[0])
    datos = LE.Datos(seq, horas, np.array([date.fromisoformat(x).weekday() for x in fechas]),
                     np.array([(date.fromisoformat(x) - d0).days for x in fechas]), fechas)
    n = len(seq); i0 = next(i for i, x in enumerate(fechas) if x >= "2026-09-14")
    DESDE, R = 2000, 250
    T0 = DESDE + ((i0 - DESDE) // R) * R
    print("RD filas %d; vivo desde fila %d (%s) hasta %s; frontera %d; choques fuente %d" % (n, i0, fechas[i0], fechas[-1], T0, choques))
    m0 = LE.cargar_modelo(os.path.join(HERR, "modelos", "secuencia_v3.py"))
    P0 = LE.normalizar(m0.predecir(datos, T0))[i0 - T0:]
    coef = json.load(open(os.path.join(HERR, "rdint", "coef_b1.json"), encoding="utf-8"))["b"]
    la_h = np.array([la.get((fechas[t], horas[t]), -1) for t in range(i0, n)])
    la_h1 = np.array([la.get((fechas[t], horas[t] - 1), -1) if horas[t] > 0 else -1 for t in range(i0, n)])
    la_hoy = np.zeros((n - i0, K), np.int8)
    for j, t in enumerate(range(i0, n)):
        for hh in range(horas[t] + 1):
            s = la.get((fechas[t], hh))
            if s is not None:
                la_hoy[j, s] += 1
    Xb = MB.features(la_h, la_h1, la_hoy)
    z = np.log(np.clip(P0, 1e-12, None)) + (Xb @ np.array(coef, np.float32)).astype(np.float64)
    z -= z.max(1, keepdims=True); P1 = np.exp(z); P1 /= P1.sum(1, keepdims=True)
    X = rasgos(fechas, horas, seq)[i0:]
    y = seq[i0:]; h = horas[i0:]; f = np.array(fechas[i0:])
    res = informe(P1, X, y, h, f, b, "vivo reconstruido"); res["sin_LA_h"] = int((la_h < 0).sum()); imprimir(res)
    print("  filas sin LA h:00:", res["sin_LA_h"])
    if ruta_api:
        api = json.load(open(ruta_api, encoding="utf-8")); pr = api["pronostico"]
        fe, hh = pr["fecha"], int(pr["hora"]); orden = pr["orden"]
        ult = {(a, int(bh)): LE.IDX[c] for a, bh, c in api["ultimos"]}
        allrd = dict(rd); allrd.update(ult)
        prim = {}
        for (a, bh) in sorted(allrd):
            prim.setdefault(a, (bh, allrd[(a, bh)]))
        x = np.zeros((1, K, 6), np.float32)
        es_primero = all(a != fe for a, _ in allrd)
        f0 = date.fromisoformat(fe)
        if es_primero:
            for j, k in ((0, 1), (1, 3)):
                q = prim.get((f0 - timedelta(days=k)).isoformat())
                if q is not None and q[0] == hh:
                    x[0, q[1], j] = 1
        d = int(fe[8:10]); h12 = (hh + 8 - 1) % 12 + 1
        for j, num in ((2, d - 1), (3, d), (4, d + 1), (5, h12)):
            if 1 <= num <= 36:
                x[0, LE.IDX[str(num)], j] = 1
        # el congelado solo trae prob del Top-15: el resto se reparte igual (aprox.; solo para el ejemplo)
        p = np.zeros(K); top = pr["prob"]; resto = (1 - sum(top.values())) / (K - len(top))
        for c in orden:
            p[LE.IDX[c]] = top.get(c, resto)
        q = aplicar(p[None], x, b)[0]
        nuevo = sorted(LE.POS, key=lambda c: (-q[LE.IDX[c]], LE.IDX[c]))
        tocados = {LE.POS[i]: [NOMBRES[j] for j in range(6) if x[0, i, j]] for i in range(K) if x[0, i].any()}
        print("  /api/rdint %s h=%d: tocados %s" % (fe, hh, tocados))
        print("    Top-15 actual :", orden[:15]); print("    Top-15 con corr:", nuevo[:15])
        res["ejemplo_api"] = {"fecha": fe, "hora": hh, "tocados": tocados, "top15_actual": orden[:15], "top15_corr": nuevo[:15]}
    json.dump(res, open(os.path.join(AQUI, "resultados_vivo.json"), "w"), indent=1)


if __name__ == "__main__":
    etapa = sys.argv[1] if len(sys.argv) > 1 else "dev"
    {"dev": etapa_dev, "conf": etapa_conf}.get(etapa, lambda: etapa_vivo(sys.argv[2] if len(sys.argv) > 2 else None))()
