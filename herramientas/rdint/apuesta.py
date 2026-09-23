# -*- coding: utf-8 -*-
"""Hilo 7, H3 (E2 apuesta por valor) y E3 (mesa doble LA h:00 / RD h:30). SOLO desarrollo.

Entradas (ya calculadas, walk-forward):
  rdint/cache_dev.npz          P1 (B1) y P0 (B0) de RD Int, solo filas 'dev'.
  exploracion/calor_cache.npz  P de ensamble_v2 para Lotto Activo, filas 2000..9356 de lotto_eval.cargar();
                               se usan SOLO las filas con fecha dentro de los dias dev de RD Int.

E2 (pre-registro): se juegan solo animales con 30p >= 1,10. v = (30p-1)/29; fichas proporcionales a v,
escaladas para que el mayor v del sorteo lleve 3, redondeadas y acotadas a 1..3. 0 animales = no se juega.

E3: en cada (dia, hora) con ambas loterias se juega el Top-5 escalonado en la que tenga mayor
EV5 = sum(max(0, 30p-1)) sobre su Top-5. La decision se toma ANTES de las h:00 (hay que apostar LA
antes de que salga), asi que para RD se usa P0 (no conoce LA h:00); si gana RD, el boleto RD se arma
con P1 a las h:00+. Variante 'ambas' = Top-5 escalonado en las dos.

Salida: resultados/hilo7_apuesta.md
"""
import os, sys
from datetime import date, timedelta
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, HERR)
import lotto_eval as LE

PAGO = LE.PAGO
NBOOT = 2000
UMBRAL = 1.10
FICHAS5 = np.array([2, 2, 2, 1, 1])
D0_RD = date(2023, 9, 4)               # primer dia de rdint_hist.csv (datos.py: dia = dias desde aqui)
DEV = ("2024-03-01", "2025-06-30")
CORTE_MITAD = "2024-10-29"             # ultimo dia de la 1a mitad (el mismo de hilo7_modelo.md)
SALIDA_MD = os.path.join(HERR, "resultados", "hilo7_apuesta.md")


# ------------------------------------------------------------------ datos
def cargar_rd():
    z = np.load(os.path.join(AQUI, "cache_dev.npz"))
    fecha = np.array([(D0_RD + timedelta(days=int(d))).isoformat() for d in z["dia"]])
    assert min(fecha) >= DEV[0] and max(fecha) <= DEV[1]
    return dict(P1=LE.normalizar(z["P1"].astype(np.float64)), P0=LE.normalizar(z["P0"].astype(np.float64)),
                y=z["y"], hora=z["hora"], fecha=fecha)


def cargar_la(dias_rd):
    la = LE.cargar()
    z = np.load(os.path.join(HERR, "exploracion", "calor_cache.npz"))
    ix = np.arange(2000, 2000 + len(z["y"]))
    fecha = np.array(la.fecha)[ix]
    assert (z["y"] == la.seq[ix]).all()
    m = np.isin(fecha, list(dias_rd))              # solo dias dev de RD Int: nada de test/desc/vivo
    assert max(fecha[m]) <= DEV[1]
    return dict(P=LE.normalizar(z["P"][m]), y=z["y"][m], hora=la.hora[ix][m], fecha=fecha[m])


# ------------------------------------------------------------------ boletos
def boleto_top(P, fichas):
    """Matriz de fichas (n, 38) para un Top-k con fichas dadas por puesto."""
    orden = LE.rankings(P)
    F = np.zeros(P.shape)
    for k, f in enumerate(fichas):
        F[np.arange(len(P)), orden[:, k]] = f
    return F


def boleto_e2(P):
    v = (PAGO * P - 1) / (PAGO - 1)
    ok = PAGO * P >= UMBRAL
    vmax = np.where(ok, v, 0).max(1, keepdims=True)
    F = np.where(ok, np.clip(np.rint(3 * v / np.where(vmax > 0, vmax, 1)), 1, 3), 0)
    return F


def boleto_e2_plano(P):
    return (PAGO * P >= UMBRAL).astype(float)


def liquidar(F, y):
    """(apostado, cobrado) por sorteo."""
    return F.sum(1), PAGO * F[np.arange(len(y)), y]


# ------------------------------------------------------------------ estadistica
def boot_ratio(num, den, dia, rng, nboot=NBOOT):
    """sum(num)/sum(den) con IC95 por bootstrap de jornadas (dias)."""
    _, g = np.unique(dia, return_inverse=True)
    N = np.bincount(g, weights=num); D = np.bincount(g, weights=den); nd = len(N)
    idx = rng.integers(0, nd, size=(nboot, nd))
    b = N[idx].sum(1) / np.maximum(D[idx].sum(1), 1e-12)
    return num.sum() / max(den.sum(), 1e-12), np.percentile(b, 2.5), np.percentile(b, 97.5)


def boot_dif(a1, c1, a2, c2, dia, rng, nboot=NBOOT):
    """Diferencia pareada de retorno por ficha (estrategia 1 - estrategia 2), bootstrap por dia."""
    _, g = np.unique(dia, return_inverse=True)
    A1, C1, A2, C2 = (np.bincount(g, weights=x) for x in (a1, c1, a2, c2)); nd = len(A1)
    idx = rng.integers(0, nd, size=(nboot, nd))
    r = lambda A, C, i: (C[i].sum(1) - A[i].sum(1)) / np.maximum(A[i].sum(1), 1e-12)
    b = r(A1, C1, idx) - r(A2, C2, idx)
    pt = (c1.sum() - a1.sum()) / a1.sum() - (c2.sum() - a2.sum()) / a2.sum()
    return pt, np.percentile(b, 2.5), np.percentile(b, 97.5)


def partes(fecha):
    p1 = fecha <= CORTE_MITAD
    return [("dev", np.ones(len(fecha), bool)), ("1ª mitad", p1), ("2ª mitad", ~p1)]


def fila_ret(nombre, apost, cobr, fecha, rng, extra=""):
    out = []
    for nom, m in partes(fecha):
        r, lo, hi = boot_ratio(cobr[m] - apost[m], apost[m], fecha[m], rng)
        out.append((nom, r, lo, hi, apost[m].sum(), cobr[m].sum() - apost[m].sum()))
    celdas = " | ".join("%+.1f %% [%+.1f, %+.1f] · %d f · neto %+d" % (100 * r, 100 * lo, 100 * hi, a, n)
                        for _, r, lo, hi, a, n in out)
    return "| %s | %s |%s" % (nombre, celdas, extra), {nom: r for nom, r, *_ in out}


def calibracion(P, y, titulo):
    n = len(y); Yi = np.zeros(P.shape, bool); Yi[np.arange(n), y] = True
    p = P.ravel(); o = Yi.ravel()
    cortes = np.quantile(p, np.linspace(0, 1, 11))
    L = ["\n### Calibración de %s por deciles de p (%d sorteos × 38 animales)\n" % (titulo, n),
         "| decil | rango de p | p media (dice) | frecuencia (sale) | casos | sale/dice |", "|---|---|---|---|---|---|"]
    g = np.clip(np.searchsorted(cortes, p, side="right") - 1, 0, 9)
    for k in range(10):
        s = g == k
        L.append("| %d | %.4f–%.4f | %.4f | %.4f | %d | %.2f |" % (
            k + 1, p[s].min(), p[s].max(), p[s].mean(), o[s].mean(), s.sum(), o[s].mean() / p[s].mean()))
    for lo, hi in [(UMBRAL / PAGO, 0.045), (0.045, 0.06), (0.06, 1.0)]:
        s = (p >= lo) & (p < hi)
        if s.any():
            L.append("| p∈[%.4f, %.4f) | — | %.4f | %.4f | %d | %.2f |" % (
                lo, hi, p[s].mean(), o[s].mean(), s.sum(), o[s].mean() / p[s].mean()))
    return L


# ------------------------------------------------------------------ main
def main():
    rng = np.random.default_rng(11)
    rd = cargar_rd()
    la = cargar_la(set(rd["fecha"].tolist()))
    L = []; di = L.append
    di("# Hilo 7 — H3 (E2, apuesta por valor) y E3 (mesa doble)\n")
    di("Generado por `herramientas/rdint/apuesta.py`. Pre-registro: "
       "`herramientas/exploracion/PREREGISTRO_rdint_cruzado.md` (criterios sin cambios). **Solo desarrollo; "
       "la prueba ciega no se miró.**\n")
    di("- RD Int: `rdint/cache_dev.npz` (P1 = B1, P0 = B0 = %s), %d sorteos, %s .. %s." % (
        "secuencia_v3", len(rd["y"]), min(rd["fecha"]), max(rd["fecha"])))
    di("- Lotto Activo: `exploracion/calor_cache.npz` (ensamble_v2 walk-forward), solo filas con fecha en los "
       "días dev de RD: %d sorteos, %s .. %s (la caché empieza el 2024-03-07)." % (
           len(la["y"]), min(la["fecha"]), max(la["fecha"])))
    di("- Mitades por fecha (la misma que `hilo7_modelo.md`): 1ª ≤ %s < 2ª. Retorno por ficha = neto / fichas "
       "apostadas; IC95 por bootstrap de jornadas (%d). Pago 30x." % (CORTE_MITAD, NBOOT))
    di("- E2: v = (30p−1)/29 en los animales con 30p ≥ %.2f; fichas = redondeo(3·v/v_máx del sorteo) acotado "
       "a 1..3 (lectura de «proporcionales, redondeadas a 1-3»: el mejor lleva 3). Se muestra también la "
       "variante de 1 ficha plana por animal como sensibilidad, no decide." % UMBRAL)

    # ---- a) y b) estrategias por loteria
    res = {}
    cab = "| estrategia | dev | 1ª mitad | 2ª mitad |\n|---|---|---|---|"
    for lot, P, y, fecha in [("RD Int (P1)", rd["P1"], rd["y"], rd["fecha"]),
                             ("RD Int (P0, referencia)", rd["P0"], rd["y"], rd["fecha"]),
                             ("Lotto Activo", la["P"], la["y"], la["fecha"])]:
        di("\n## %s\n" % lot)
        di(cab)
        for nom, F in [("Top-3 plano", boleto_top(P, [1, 1, 1])),
                       ("Top-5 escalonado 2-2-2-1-1", boleto_top(P, FICHAS5)),
                       ("E2 valor (1..3 fichas)", boleto_e2(P)),
                       ("E2 valor, 1 ficha plana", boleto_e2_plano(P))]:
            a, c = liquidar(F, y)
            txt, r = fila_ret(nom, a, c, fecha, rng)
            di(txt); res[(lot, nom)] = (r, a, c)
        F = boleto_e2(P); nanim = (F > 0).sum(1)
        for nom, m in partes(fecha):
            jug = nanim[m] > 0
            di("\n- E2 %s: sorteos sin jugar %d de %d (%.1f %%); animales por sorteo jugado: media %.2f, "
               "mediana %d, máx %d; fichas por sorteo jugado: media %.2f." % (
                   nom, (~jug).sum(), m.sum(), 100 * (~jug).mean(), nanim[m][jug].mean(),
                   int(np.median(nanim[m][jug])), nanim[m].max(), F[m][jug].sum(1).mean()))
        hist = np.bincount(np.minimum(nanim, 8), minlength=9)
        di("- Distribución de animales por sorteo (0,1,..,7,8+): %s." % ", ".join(map(str, hist)))
        a1, c1 = res[(lot, "E2 valor (1..3 fichas)")][1:]
        a2, c2 = res[(lot, "Top-5 escalonado 2-2-2-1-1")][1:]
        di("- Diferencia pareada E2 − Top-5 escalonado (pp de retorno por ficha): " + "; ".join(
            "%s %+.1f [%+.1f, %+.1f]" % ((nom,) + tuple(100 * x for x in boot_dif(a1[m], c1[m], a2[m], c2[m], fecha[m], rng)))
            for nom, m in partes(fecha)) + ".")

    # ---- H3
    di("\n## Veredicto H3\n")
    di("Criterio: retorno por ficha de E2 > el del Top-5 escalonado en AMBAS mitades, en RD Int (con B1) "
       "y/o en Lotto Activo, por separado (estimación puntual).\n")
    h3 = {}
    for lot in ["RD Int (P1)", "Lotto Activo"]:
        e2 = res[(lot, "E2 valor (1..3 fichas)")][0]; t5 = res[(lot, "Top-5 escalonado 2-2-2-1-1")][0]
        ok = all(e2[m] > t5[m] for m in ["1ª mitad", "2ª mitad"])
        h3[lot] = ok
        di("- %s: E2 %+.1f %% / %+.1f %% contra Top-5 %+.1f %% / %+.1f %% (1ª / 2ª mitad) → **%s**." % (
            lot, 100 * e2["1ª mitad"], 100 * e2["2ª mitad"], 100 * t5["1ª mitad"], 100 * t5["2ª mitad"],
            "PASA" if ok else "FALLA"))
    di("\n**H3: %s** (%s)." % ("PASA" if any(h3.values()) else "FALLA",
                              ", ".join("%s %s" % (k, "pasa" if v else "falla") for k, v in h3.items())))

    # ---- c) E3 mesa doble
    kla = {(f, int(h)): i for i, (f, h) in enumerate(zip(la["fecha"], la["hora"]))}
    par = [(i, kla[(f, int(h))]) for i, (f, h) in enumerate(zip(rd["fecha"], rd["hora"])) if (f, int(h)) in kla]
    ir = np.array([p[0] for p in par]); il = np.array([p[1] for p in par])
    fecha = rd["fecha"][ir]
    F_rd = boleto_top(rd["P1"][ir], FICHAS5); F_la = boleto_top(la["P"][il], FICHAS5)
    a_rd, c_rd = liquidar(F_rd, rd["y"][ir]); a_la, c_la = liquidar(F_la, la["y"][il])

    def ev5(P):
        s = -np.sort(-P, axis=1)[:, :5]
        return np.maximum(0, PAGO * s - 1).sum(1)
    elige_rd = ev5(rd["P0"][ir]) > ev5(la["P"][il])        # decision antes de h:00: RD con P0
    elige_rd_p1 = ev5(rd["P1"][ir]) > ev5(la["P"][il])     # solo diagnostico: usa LA h:00 para decidir
    di("\n## E3 — mesa doble (Top-5 escalonado)\n")
    di("Horas con ambas loterías en dev: %d (%d días). La decisión se toma antes de las h:00 con "
       "EV5 = Σ máx(0, 30p−1) del Top-5: LA con su caché, RD con **P0** (no puede conocer LA h:00 al decidir "
       "si apostar LA h:00). Si gana RD, el boleto RD se arma con P1 después de las h:00." % (
           len(ir), len(np.unique(fecha))))
    di("Se elige RD en %.1f %% de las horas (1ª mitad %.1f %%, 2ª %.1f %%).\n" % (
        100 * elige_rd.mean(), 100 * elige_rd[fecha <= CORTE_MITAD].mean(), 100 * elige_rd[fecha > CORTE_MITAD].mean()))
    di(cab)
    a_m = np.where(elige_rd, a_rd, a_la); c_m = np.where(elige_rd, c_rd, c_la)
    filas = [("Solo LA", a_la, c_la), ("Solo RD (P1)", a_rd, c_rd),
             ("Mesa doble: mayor EV5", a_m, c_m), ("Ambas", a_la + a_rd, c_la + c_rd)]
    for nom, a, c in filas:
        di(fila_ret(nom, a, c, fecha, rng)[0])
    for nom, a, c in filas[1:]:
        di("\n- %s − Solo LA (pp): " % nom + "; ".join(
            "%s %+.1f [%+.1f, %+.1f]" % ((pn,) + tuple(100 * x for x in boot_dif(a[m], c[m], a_la[m], c_la[m], fecha[m], rng)))
            for pn, m in partes(fecha)) + ".")
    a_x = np.where(elige_rd_p1, a_rd, a_la); c_x = np.where(elige_rd_p1, c_rd, c_la)
    di("\nDiagnóstico, NO válido para jugar (decide con P1, que ya conoce LA h:00):\n")
    di(cab)
    di(fila_ret("Mesa doble decidida con P1", a_x, c_x, fecha, rng)[0])

    # ---- calibracion
    di("\n## Calibración\n")
    L.extend(calibracion(rd["P1"], rd["y"], "P1 (RD Int)"))
    L.extend(calibracion(la["P"], la["y"], "la caché de Lotto Activo"))
    di("\nLas tres últimas filas de cada tabla miran la zona donde apuesta E2 (30p ≥ %.2f)." % UMBRAL)

    di("\n## Notas\n")
    di("- La caché de Lotto Activo NO es fuera de muestra aquí: es el tramo de desarrollo del proyecto LA "
       "(filas 2000..%d, hasta %s), donde se eligieron los modelos y los pesos de ensamble_v2. Sus retornos "
       "(+20 %% o más) son optimistas. Los de RD Int (B1 fijado en el pre-registro, coeficientes walk-forward) "
       "no tienen ese problema, aunque B0 se eligió entre 2 candidatos en este dev." % (
           LE.CORTE_FIJO - 1, LE.cargar().fecha[LE.CORTE_FIJO - 1]))
    di("- H3 se decide por estimación puntual, como fija el pre-registro. Las diferencias pareadas E2 − Top-5 "
       "tienen IC95 que cruzan 0 en todas las mitades, en RD y en LA.")
    di("- La escala de «fichas proporcionales» (el mayor v del sorteo lleva 3) es una lectura mía: el "
       "pre-registro no la fija. La variante de 1 ficha plana se muestra solo como sensibilidad.")
    with open(SALIDA_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
