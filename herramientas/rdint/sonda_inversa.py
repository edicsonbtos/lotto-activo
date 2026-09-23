# -*- coding: utf-8 -*-
"""Hilo 7, H4 del pre-registro (sonda inversa): gana Lotto Activo al saber lo que salio en RD Int?

Base  : P de ensamble_v2 CONGELADO (herramientas/exploracion/calor_cache.npz), filas 2000..9356
        de lotto_eval.cargar(). Solo se usan las de fecha < 2025-07-01 (todas caen en 'dev').
Sonda : logit condicional con offset log P
            P1[t, i] ~ P[t, i] * exp(b . x_i(t))
        x_i(t) = [ RD Int (h-1):30 == i , salio hoy en RD Int antes de h:00 y no es el de (h-1):30 ]
        Para LA de h:00 solo vale RD de (h-1):30 y anteriores del MISMO dia. RD de h:30 es posterior.
Ajuste: solo b (2 coeficientes). Principal: fuera de muestra por cuartos (ajusta en 3, evalua en
        el 4o). Secundario: walk-forward (reajuste cada 250 filas con las anteriores).

ANTI-FUGA: RD se trunca al primer sorteo 'test' antes de construir nada; las filas LA con fecha
>= 2025-07-01 se descartan antes de ajustar o medir.

Uso: python sonda_inversa.py   -> resultados/hilo7_sonda_inversa.md
"""
import os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, AQUI); sys.path.insert(0, HERR)
import lotto_eval as LE
import datos as DT
import modelo as MB

CACHE_LA = os.path.join(HERR, "exploracion", "calor_cache.npz")
SALIDA_MD = os.path.join(HERR, "resultados", "hilo7_sonda_inversa.md")
DESDE_LA = 2000
TOPE = "2025-07-01"
NBOOT = 2000
K = LE.K
NOMBRES = ["RD (h-1):30", "RD antes hoy"]


def mbits(P, y):
    return 1000 * np.log2(P[np.arange(len(y)), y] * K)


def mitades(dia):
    cambios = np.flatnonzero(np.r_[True, dia[1:] != dia[:-1]])
    m = cambios[np.argmin(np.abs(cambios - len(dia) / 2))]
    return [np.arange(0, m), np.arange(m, len(dia))]


def cuartos(dia):
    """4 bloques contiguos cortados en cambio de dia; los dos primeros = 1a mitad."""
    out = []
    for ix in mitades(dia):
        a, b = mitades(dia[ix])
        out += [ix[a], ix[b]]
    return out


def boot_media(v, dia, rng, nboot=NBOOT):
    _, g = np.unique(dia, return_inverse=True)
    S = np.bincount(g, weights=v); C = np.bincount(g).astype(float); nd = len(S)
    idx = rng.integers(0, nd, size=(nboot, nd))
    b = S[idx].sum(1) / C[idx].sum(1)
    return float(v.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def rd_por_fecha():
    """{fecha: {hora_rd: idx}} SOLO con RD de tramos cal/dev (truncado antes del primer 'test')."""
    rd, _, _, _, tramo = DT.cargar()
    n_fin = int(np.flatnonzero(tramo == "test")[0])
    assert set(np.unique(tramo[:n_fin])) <= {"cal", "dev"}
    rd = rd.prefijo(n_fin)
    d = {}
    for f, h, s in zip(rd.fecha, rd.hora, rd.seq):
        d.setdefault(f, {})[int(h)] = int(s)
    return d, rd.fecha[-1]


def features(fechas, horas, rdd):
    """(n, 38, 2). LA de h:00 ve RD de horas 0..h-1 (8:30..(h-1):30) del mismo dia."""
    n = len(fechas); X = np.zeros((n, K, 2), np.float32); tiene = np.zeros(n, bool)
    for t, (f, h) in enumerate(zip(fechas, horas)):
        dia = rdd.get(f)
        if not dia:
            continue
        tiene[t] = True
        prev = dia.get(h - 1, -1) if h > 0 else -1
        if prev >= 0:
            X[t, prev, 0] = 1
        for hh, s in dia.items():
            if hh <= h - 1 and s != prev:
                X[t, s, 1] = 1
    return X, tiene


def prueba_fuga(fechas, horas, rdd, X, semilla=0):
    """Cambia al azar todo RD de h:30 en adelante en cada dia: las features de LA h:00 no deben
    moverse. Control: cambiar RD de (h-1):30 SI debe moverlas."""
    rng = np.random.default_rng(semilla)
    ok = True; mueve = 0
    for t in rng.choice(len(fechas), size=300, replace=False):
        f, h = fechas[t], int(horas[t])
        if f not in rdd:
            continue
        d2 = {f: {hh: (int(rng.integers(0, K)) if hh >= h else s) for hh, s in rdd[f].items()}}
        x2, _ = features([f], [h], d2)
        ok &= bool(np.array_equal(x2[0], X[t]))
        if h > 0 and (h - 1) in rdd[f]:
            d3 = {f: dict(rdd[f])}; d3[f][h - 1] = (rdd[f][h - 1] + 1) % K
            x3, _ = features([f], [h], d3)
            mueve += int(not np.array_equal(x3[0], X[t]))
    return ok, mueve


def aplicar(L0, X, b):
    z = L0 + (X @ b.astype(np.float32)).astype(np.float64)
    z -= z.max(1, keepdims=True); p = np.exp(z)
    return p / p.sum(1, keepdims=True)


def mh_repeticion(y, X, P, hora, col):
    """O/E estratificado por hora: veces que LA repite el animal marcado en X[:,:,col]
    contra lo esperado por el ensamble (E = suma de P sobre esos animales)."""
    marc = X[:, :, col] > 0
    O = marc[np.arange(len(y)), y].astype(float)
    E = (P * marc).sum(1); V = (P * marc * (1 - P)).sum(1)   # aprox. varianza de Bernoulli
    fil = []
    for h in range(12):
        s = hora == h
        fil.append((h, O[s].sum(), E[s].sum()))
    z = (O.sum() - E.sum()) / np.sqrt(V.sum()) if V.sum() > 0 else float("nan")
    return O.sum(), E.sum(), z, fil


def desfases(fechas, hora, y, rdd):
    """Diagnostico de alineacion (NO entra al modelo): repeticiones LA h:00 == RD (h+k):30 contra
    1/38, para k = -3..+2, solo filas dev. Si la hora de RD estuviera corrida, el hueco no quedaria
    centrado entre k=-1 y k=0 (los dos RD a 30 min de LA h:00)."""
    out = []
    for k in range(-3, 3):
        O = N = 0
        for f, h, s in zip(fechas, hora, y):
            r = rdd.get(f, {}).get(int(h) + k)
            if r is not None:
                N += 1; O += int(r == s)
        E = N / K
        out.append((k, N, O, E, (O - E) / np.sqrt(E * (1 - 1 / K))))
    return out


def main():
    rng = np.random.default_rng(7)
    la = LE.cargar()
    z = np.load(CACHE_LA)
    P_all, y_all = z["P"], z["y"]
    fin = LE.CORTE_FIJO
    assert np.array_equal(y_all, la.seq[DESDE_LA:fin])
    fechas_all = np.array(la.fecha[DESDE_LA:fin])
    keep = fechas_all < TOPE                              # fuera test RD y test LA
    n = int(keep.sum()); assert keep[:n].all()
    P = LE.normalizar(P_all[:n]); y = y_all[:n]
    fechas = list(fechas_all[:n]); hora = la.hora[DESDE_LA:DESDE_LA + n]; dia = la.dia[DESDE_LA:DESDE_LA + n]
    del P_all
    assert min(fechas) >= "2024-03-01" and max(fechas) < TOPE   # todo 'dev'

    rdd, ult_rd = rd_por_fecha()
    assert ult_rd < TOPE
    X, tiene = features(fechas, hora, rdd)
    fuga_ok, mueve = prueba_fuga(fechas, hora, rdd, X)
    L0 = np.log(P); m0 = mbits(P, y)

    # principal: cuartos
    Q = cuartos(dia); P1 = np.empty_like(P); bq = []
    for k, ix in enumerate(Q):
        tr = np.concatenate([Q[j] for j in range(4) if j != k])
        b = MB.ajustar(L0[tr], X[tr], y[tr], lam=1.0)
        bq.append(b); P1[ix] = aplicar(L0[ix], X[ix], b)
    dq = mbits(P1, y) - m0
    # b en toda la muestra (solo descriptivo, NO es fuera de muestra)
    b_todo = MB.ajustar(L0, X, y, lam=1.0)

    # secundario: walk-forward
    Pw, hist = MB.cruzado(P, X, y, R=250, minimo=500, lam=1.0)
    dw = mbits(Pw, y) - m0

    partes = mitades(dia)
    lin = []; di = lin.append
    di("# Hilo 7 — H4, sonda inversa: ¿gana Lotto Activo al saber lo que salió en RD Int?\n")
    di("Generado por `herramientas/rdint/sonda_inversa.py`. Criterio fijado en "
       "`herramientas/exploracion/PREREGISTRO_rdint_cruzado.md` (H4): **PASA si Δ ≥ +5 mbits con IC95 > 0 "
       "en ambas mitades del desarrollo**. Se esperaba que FALLE.\n")
    di("## Datos y anti-fuga\n")
    di("- Lotto Activo: filas %d..%d de `lotto_eval.cargar()` con fecha < %s → **%d sorteos**, %s .. %s "
       "(todo en tramo desarrollo). Base = P de ensamble_v2 congelado (`calor_cache.npz`)." %
       (DESDE_LA, DESDE_LA + n - 1, TOPE, n, fechas[0], fechas[-1]))
    di("- RD Int truncado antes del primer sorteo del tramo 'test' (último RD usado: %s)." % ult_rd)
    di("- Para LA de h:00 se usa RD de (h−1):30 y anteriores del MISMO día; RD de h:30 (posterior) nunca. "
       "LA de 8:00 no tiene RD previo (features = 0).")
    di("- Sorteos LA con algún RD ese día: %d de %d (%.1f %%); con RD en (h−1):30 marcado: %d." %
       (tiene.sum(), n, 100 * tiene.mean(), int(X[:, :, 0].sum())))
    di("- Prueba de fuga (300 sorteos, se cambia al azar todo RD desde h:30): **%s**; control "
       "(cambiar RD de (h−1):30 sí mueve las features): %d casos movidos." %
       ("SIN FUGA" if fuga_ok else "FUGA", mueve))
    di("- Métrica: mbits por sorteo = 1000·log2(38·p(ganador)). IC95 por bootstrap de bloques de "
       "jornada (%d remuestreos). Mitades cortadas en cambio de día.\n" % NBOOT)

    di("## Descriptivo: ¿LA repite lo que acaba de sacar RD? (O/E contra el ensamble, por hora)\n")
    di("| indicador | observados | esperados (ensamble) | O/E | z |")
    di("|---|---|---|---|---|")
    for c, nm in enumerate(NOMBRES):
        O, E, zz, fil = mh_repeticion(y, X, P, hora, c)
        di("| %s | %d | %.1f | %.2f | %+.1f |" % (nm, O, E, O / E, zz))
    O, E, zz, fil = mh_repeticion(y, X, P, hora, 0)
    di("\nPor hora (RD (h−1):30 → LA h:00): " + ", ".join(
        "%d:00 %d/%.1f" % (h + 8, o, e) for h, o, e in fil if e > 0) + "\n")

    di("## Diagnóstico de alineación horaria (descriptivo, no entra al modelo)\n")
    di("Repeticiones LA h:00 == RD (h+k):30 en desarrollo, contra 1/38. k=0 es RD de h:30 (posterior a "
       "LA h:00): aquí solo se mira para ubicar el hueco, nunca se usa para predecir.\n")
    di("| k | RD | n | observados | esperados | z |")
    di("|---|---|---|---|---|---|")
    for k, N, O, E, zz in desfases(fechas, hora, y, rdd):
        di("| %+d | (h%+d):30 | %d | %d | %.1f | %+.1f |" % (k, k, N, O, E, zz))
    di("\nEl hueco se centra entre k=−1 y k=0 (los dos sorteos RD a 30 min de LA h:00) y decae hacia "
       "los lados: compatible con horas bien alineadas y con un operador que evita repetir lo reciente "
       "de la otra lotería en ambos sentidos. Ojo: en la ventana de descubrimiento (test B, 2026) la "
       "dirección RD → LA (lag −1) no apareció en el top 25 (|z| < 1,8): el efecto podría haberse "
       "debilitado; la prueba ciega lo dirá.\n")
    di("## Coeficientes\n")
    di("| ajuste | b[%s] | b[%s] |" % tuple(NOMBRES))
    di("|---|---|---|")
    for k, b in enumerate(bq):
        di("| sin cuarto %d | %+.3f | %+.3f |" % (k + 1, b[0], b[1]))
    di("| todo dev (descriptivo, dentro de muestra) | %+.3f | %+.3f |" % tuple(b_todo))
    di("\n(Referencia: exp(b) es el factor sobre la probabilidad del animal; b = −∞ sería 'nunca repite'.)\n")

    di("## H4 — Δ mbits por sorteo, sonda − ensamble (fuera de muestra)\n")
    di("| esquema | tramo | n | Δ mbits | IC95 | ¿Δ ≥ +5 e IC>0? |")
    di("|---|---|---|---|---|---|")
    res = {}
    for esq, d in [("cuartos (principal)", dq), ("walk-forward", dw)]:
        for nom, ix in [("dev completo", np.arange(n)), ("1ª mitad", partes[0]), ("2ª mitad", partes[1])]:
            m, lo, hi = boot_media(d[ix], dia[ix], rng)
            res[(esq, nom)] = (m, lo, hi)
            di("| %s | %s | %d | %+.2f | [%+.2f, %+.2f] | %s |" %
               (esq, nom, len(ix), m, lo, hi, "sí" if (m >= 5 and lo > 0) else "no"))
    di("\nPor cuarto (principal): " + ", ".join(
        "Q%d %+.2f" % (k + 1, dq[ix].mean()) for k, ix in enumerate(Q)))
    di("Walk-forward: las primeras 500 filas usan b = 0 (Δ = 0 por construcción).\n")
    pasa = all(res[("cuartos (principal)", s)][0] >= 5 and res[("cuartos (principal)", s)][1] > 0
               for s in ("1ª mitad", "2ª mitad"))
    di("**H4: %s** (criterio: Δ ≥ +5 mbits y límite inferior del IC95 > 0 en AMBAS mitades; "
       "esquema principal = cuartos)." % ("PASA" if pasa else "FALLA"))
    txt = "\n".join(lin) + "\n"
    with open(SALIDA_MD, "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
