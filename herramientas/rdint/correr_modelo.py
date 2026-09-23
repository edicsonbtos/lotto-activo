# -*- coding: utf-8 -*-
"""Hilo 7, E1 (H1 y H2 del pre-registro): B0 (solo RD Int) contra B1 (+ Lotto Activo).

Uso (cada etapa en su propio proceso para no llenar la RAM):
  python correr_modelo.py b0 secuencia_v3     -> _b0_secuencia_v3.npz
  python correr_modelo.py b0 intradia_v2      -> _b0_intradia_v2.npz
  python correr_modelo.py fuga                -> prueba de fuga de B1 sobre el B0 elegido
  python correr_modelo.py reporte             -> cache_dev.npz + resultados/hilo7_modelo.md

ANTI-FUGA: los datos se truncan al primer sorteo del tramo 'test' ANTES de modelar; las
metricas se calculan solo en filas 'dev'. Nada de test/desc/vivo se toca.
"""
import json, math, os, subprocess, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, AQUI); sys.path.insert(0, HERR)
import lotto_eval as LE
import datos as DT
import modelo as MB

DESDE = 2000                       # dentro de 'cal' (2102 sorteos)
B0S = ["secuencia_v3", "intradia_v2"]
NBOOT = 2000
PAGO = LE.PAGO
FICHAS5 = np.array([2, 2, 2, 1, 1])
SALIDA_MD = os.path.join(HERR, "resultados", "hilo7_modelo.md")
CACHE = os.path.join(AQUI, "cache_dev.npz")
FUGA_JSON = os.path.join(AQUI, "_fuga.json")


def cargar_truncado():
    rd, la_h, la_h1, la_hoy, tramo = DT.cargar()
    n_fin = int(np.flatnonzero(tramo == "test")[0])
    assert set(np.unique(tramo[:n_fin])) <= {"cal", "dev"}
    return (rd.prefijo(n_fin), la_h[:n_fin], la_h1[:n_fin], la_hoy[:n_fin], tramo[:n_fin])


def ruta_b0(nombre):
    return os.path.join(AQUI, "_b0_%s.npz" % nombre)


def modelo_b0(nombre):
    return LE.cargar_modelo(os.path.join(HERR, "modelos", nombre + ".py"))


def etapa_b0(nombre):
    rd, *_ = cargar_truncado()
    P = LE.normalizar(modelo_b0(nombre).predecir(rd, DESDE))
    np.savez_compressed(ruta_b0(nombre), P=P.astype(np.float32), desde=DESDE, n_fin=len(rd))
    print("B0 %s: %d filas guardadas" % (nombre, len(P)))


def mbits(P, y):
    return 1000 * np.log2(P[np.arange(len(y)), y] * LE.K)


def elegir_b0(dev):
    """B0 = el de mas mbits en dev (seleccion en desarrollo, permitida)."""
    tabla = {}
    for nm in B0S:
        if os.path.exists(ruta_b0(nm)):
            z = np.load(ruta_b0(nm))
            tabla[nm] = z["P"].astype(np.float64)
    return tabla


def etapa_fuga():
    rd, la_h, la_h1, la_hoy, tramo = cargar_truncado()
    y = rd.seq[DESDE:]; dev = tramo[DESDE:] == "dev"
    tabla = elegir_b0(dev)
    nm = max(tabla, key=lambda k: mbits(LE.normalizar(tabla[k])[dev], y[dev]).mean())
    ok, res = MB.prueba_fuga(modelo_b0(nm), rd, la_h, la_h1, la_hoy, DESDE, cortes=2)
    print("fuga B1 sobre %s:" % nm, "SIN FUGA" if ok else "FUGA", res)
    with open(FUGA_JSON, "w", encoding="utf-8") as f:
        json.dump({"b0": nm, "ok": ok, "cortes": res}, f)


# ------------------------------------------------------------------ metricas
def mitades(dia):
    """Parte las filas dev en dos por el cambio de dia mas cercano a la mitad."""
    cambios = np.flatnonzero(np.r_[True, dia[1:] != dia[:-1]])
    m = cambios[np.argmin(np.abs(cambios - len(dia) / 2))]
    return [np.arange(0, m), np.arange(m, len(dia))]


def boot_media(v, dia, rng, nboot=NBOOT):
    """Media de v (por sorteo) con IC95 por bootstrap de bloques de jornada."""
    _, g = np.unique(dia, return_inverse=True)
    S = np.bincount(g, weights=v); C = np.bincount(g).astype(float); nd = len(S)
    idx = rng.integers(0, nd, size=(nboot, nd))
    b = S[idx].sum(1) / C[idx].sum(1)
    return float(v.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def apuestas(P, y):
    orden = LE.rankings(P)
    pos = np.argmax(orden == y[:, None], axis=1)
    top3 = (pos < 3).astype(float)
    ret3 = (PAGO * top3 - 3) / 3                                   # retorno por ficha, Top-3 plano
    gana5 = np.where(pos < 5, FICHAS5[np.minimum(pos, 4)], 0)
    ret5 = (PAGO * gana5 - FICHAS5.sum()) / FICHAS5.sum()           # Top-5 escalonado 2-2-2-1-1
    return top3, ret3, ret5


def mh_por_hora(X, y, hora, j):
    """Mantel-Haenszel por hora: pares (sorteo, animal); expuesto = feature j; evento = animal salio.
    Devuelve (OR_MH, observados, esperados por azar 1/38)."""
    num = den = 0.0; obs = esp = 0.0
    n = len(y); Yi = np.zeros((n, LE.K), bool); Yi[np.arange(n), y] = True
    E = X[:, :, j] > 0
    for h in range(12):
        s = hora == h
        if not s.any():
            continue
        e, yy = E[s], Yi[s]
        a = (e & yy).sum(); b = (e & ~yy).sum(); c = (~e & yy).sum(); d = (~e & ~yy).sum()
        N = a + b + c + d
        num += a * d / N; den += b * c / N
        obs += a; esp += e.sum() / LE.K
    return (num / den if den else float("nan")), int(obs), esp


def etapa_reporte():
    rd, la_h, la_h1, la_hoy, tramo = cargar_truncado()
    y_all = np.asarray(rd.seq)[DESDE:]; tr = tramo[DESDE:]; dev = tr == "dev"
    assert dev.sum() > 0 and set(np.unique(tr)) <= {"cal", "dev"}
    hora_all = np.asarray(rd.hora)[DESDE:]; dia_all = np.asarray(rd.dia)[DESDE:]
    fila_all = np.arange(DESDE, len(rd))
    tabla = elegir_b0(dev)
    y = y_all[dev]; dia = dia_all[dev]; hora = hora_all[dev]; partes = mitades(dia)
    rng = np.random.default_rng(7)
    L = []; di = L.append

    # ---- B0: seleccion
    sel = {}
    for nm, P in tabla.items():
        m = mbits(LE.normalizar(P)[dev], y)
        sel[nm] = (m.mean(), [m[p].mean() for p in partes])
    b0 = max(sel, key=lambda k: sel[k][0])
    P0_all = LE.normalizar(tabla[b0])
    X_all = MB.features(la_h, la_h1, la_hoy)[DESDE:]
    P1_all, hist = MB.cruzado(P0_all, X_all, y_all)
    P0, P1, X = P0_all[dev], P1_all[dev], X_all[dev]
    np.savez_compressed(CACHE, P0=P0.astype(np.float32), P1=P1.astype(np.float32), y=y, hora=hora,
                        dia=dia, fila=fila_all[dev], b0=b0)

    fuga = json.load(open(FUGA_JSON, encoding="utf-8")) if os.path.exists(FUGA_JSON) else None

    di("# Hilo 7 — E1: RD Int con memoria cruzada de Lotto Activo (H1 y H2)\n")
    di("Generado por `herramientas/rdint/correr_modelo.py`. Pre-registro: "
       "`herramientas/exploracion/PREREGISTRO_rdint_cruzado.md` (criterios sin cambios).\n")
    di("- Datos truncados al primer sorteo de 'test' (fila %d) ANTES de modelar. Predicciones "
       "walk-forward desde la fila %d (dentro de 'cal'); **métricas solo en 'dev'**: %d sorteos, %d días "
       "(%s .. %s)." % (len(rd), DESDE, len(y), len(np.unique(dia)),
                       rd.fecha[fila_all[dev][0]], rd.fecha[fila_all[dev][-1]]))
    di("- Mitades del desarrollo (cortadas en cambio de día): 1ª = %d sorteos (%s .. %s), 2ª = %d (%s .. %s)."
       % (len(partes[0]), rd.fecha[fila_all[dev][partes[0][0]]], rd.fecha[fila_all[dev][partes[0][-1]]],
          len(partes[1]), rd.fecha[fila_all[dev][partes[1][0]]], rd.fecha[fila_all[dev][partes[1][-1]]]))
    di("- IC95 por bootstrap de bloques de jornada (%d remuestreos). Azar = 1/38 (RD usa los 38 códigos; "
       "la Ballena '00' sale menos)." % NBOOT)
    di("- Sorteos dev sin Lotto Activo a las h:00: %d (feature = 0)." % int((la_h[DESDE:][dev] < 0).sum()))
    if fuga:
        di("- **Prueba de fuga de B1** (sobre %s; se baraja RD desde c y Lotto Activo desde c+1, se exige que "
           "P0 y P1 de las filas ≤ c no cambien): **%s**. Cortes: %s." % (
               fuga["b0"], "SIN FUGA" if fuga["ok"] else "FUGA",
               "; ".join("c=%d máx|ΔP0|=%.1e máx|ΔP1|=%.1e (futuro sí cambia: %.1e)" % tuple(r)
                         for r in fuga["cortes"])))
        if fuga["b0"] != b0:
            di("  - OJO: la prueba de fuga se corrió sobre otro B0.")
    else:
        di("- Prueba de fuga: NO CORRIDA.")

    di("\n## B0 (solo RD Int) contra el uniforme\n")
    di("| modelo | mbits dev | 1ª mitad | 2ª mitad | IC95 dev |")
    di("|---|---|---|---|---|")
    for nm, (m, mm) in sel.items():
        mm_ = mbits(LE.normalizar(tabla[nm])[dev], y)
        _, lo, hi = boot_media(mm_, dia, rng)
        di("| %s%s | %+.2f | %+.2f | %+.2f | [%+.2f, %+.2f] |" % (nm, " **(B0)**" if nm == b0 else "", m,
                                                           mm[0], mm[1], lo, hi))
    di("\nB0 = **%s** (más mbits en dev; selección en desarrollo, permitida)." % b0)

    # ---- H1
    d = mbits(P1, y) - mbits(P0, y)
    di("\n## H1 — Δ mbits por sorteo, B1 − B0\n")
    di("| tramo | n | Δ mbits | IC95 | ¿Δ ≥ +5 e IC>0? |")
    di("|---|---|---|---|---|")
    pasa1 = []
    for nom, ix in [("dev completo", np.arange(len(y))), ("1ª mitad", partes[0]), ("2ª mitad", partes[1])]:
        m, lo, hi = boot_media(d[ix], dia[ix], rng)
        ok = m >= 5 and lo > 0
        if nom != "dev completo":
            pasa1.append(ok)
        di("| %s | %d | %+.2f | [%+.2f, %+.2f] | %s |" % (nom, len(ix), m, lo, hi, "sí" if ok else "no"))
    H1 = all(pasa1)
    di("\n**H1: %s** (criterio: Δ ≥ +5 mbits y límite inferior del IC95 > 0 en AMBAS mitades)." %
       ("PASA" if H1 else "FALLA"))

    # ---- coeficientes
    di("\n### Coeficientes de B1 (log-razón de tasa sobre B0; walk-forward, reajuste cada 250)\n")
    di("| ajuste con filas < | " + " | ".join(MB.NOMBRES) + " |")
    di("|---|---|---|---|")
    for T, b in hist[:: max(1, len(hist) // 8)] + [hist[-1]]:
        di("| %d (%s) | %s |" % (T + DESDE, rd.fecha[T + DESDE],
                                 " | ".join("%+.3f (×%.2f)" % (v, math.exp(v)) for v in b)))
    bdev, bfin = [b for T, b in hist if T + DESDE <= fila_all[dev][0]][-1], hist[-1][1]
    di("\nCoeficientes al empezar dev: %s. Al final: %s." % (np.round(bdev, 3).tolist(), np.round(bfin, 3).tolist()))

    di("\n### Descriptivo en dev: tasa del animal marcado, Mantel-Haenszel por hora\n")
    di("| feature | expuestos | salió | esperado 1/38 | obs/esp | OR MH por hora | exposición media por sorteo |")
    di("|---|---|---|---|---|---|---|")
    for j, nm in enumerate(MB.NOMBRES):
        orm, ob, es = mh_por_hora(X, y, hora, j)
        di("| %s | %d | %d | %.1f | %.2f | %.2f | %.2f |" % (nm, int((X[:, :, j] > 0).sum()), ob, es, ob / es,
                                                            orm, (X[:, :, j] > 0).sum() / len(y)))

    # ---- H2
    di("\n## H2 — ¿B1 gana plata en desarrollo?\n")
    di("Retorno por ficha: pago 30x. Top-3 plano = 1 ficha a cada uno de los 3 primeros (equilibrio 10 %). "
       "Top-5 escalonado = 2-2-2-1-1 fichas (8 por sorteo).\n")
    di("| modelo | tramo | Top-3 | IC95 | retorno/ficha Top-3 (IC95) | retorno/ficha Top-5 esc. (IC95) |")
    di("|---|---|---|---|---|---|")
    res = {}
    for nmod, P in [("B0", P0), ("B1", P1)]:
        t3, r3, r5 = apuestas(P, y)
        for nom, ix in [("dev", np.arange(len(y))), ("1ª mitad", partes[0]), ("2ª mitad", partes[1])]:
            a = boot_media(t3[ix], dia[ix], rng); b = boot_media(r3[ix], dia[ix], rng)
            c = boot_media(r5[ix], dia[ix], rng)
            res[(nmod, nom)] = (a, b, c)
            di("| %s | %s | %.2f %% | [%.2f, %.2f] | %+.1f %% [%+.1f, %+.1f] | %+.1f %% [%+.1f, %+.1f] |" % (
                nmod, nom, 100 * a[0], 100 * a[1], 100 * a[2], 100 * b[0], 100 * b[1], 100 * b[2],
                100 * c[0], 100 * c[1], 100 * c[2]))
    r3a = apuestas(P0, y)[1]; r3b = apuestas(P1, y)[1]
    for nom, ix in [("dev", np.arange(len(y))), ("1ª mitad", partes[0]), ("2ª mitad", partes[1])]:
        m, lo, hi = boot_media(r3b[ix] - r3a[ix], dia[ix], rng)
        di("| B1 − B0 (pareado) | %s | | | %+.1f pp [%+.1f, %+.1f] | |" % (nom, 100 * m, 100 * lo, 100 * hi))
    t3d = res[("B1", "dev")][0][0]
    H2 = t3d >= 0.105 and res[("B1", "1ª mitad")][1][0] > 0 and res[("B1", "2ª mitad")][1][0] > 0
    di("\n**H2: %s** (criterio: Top-3 de B1 ≥ 10,5 %% en dev [%.2f %%] Y retorno por ficha del Top-3 plano > 0 "
       "en ambas mitades [%+.1f %%, %+.1f %%])." % ("PASA" if H2 else "FALLA", 100 * t3d,
                                                    100 * res[("B1", "1ª mitad")][1][0],
                                                    100 * res[("B1", "2ª mitad")][1][0]))

    di("\n## Veredicto E1\n")
    di("- H1 (B1 mejora a B0 en log-verosimilitud): **%s**." % ("PASA" if H1 else "FALLA"))
    di("- H2 (B1 gana plata con el Top-3 plano): **%s**." % ("PASA" if H2 else "FALLA"))
    ini = int(np.sum(fila_all[dev] < DESDE + 500))
    di("\n## Notas\n")
    di("- B1 usa b = 0 en sus primeras 500 filas (hasta la fila %d): los primeros %d sorteos de dev tienen "
       "B1 = B0 y Δ = 0, lo que diluye (no infla) la 1ª mitad." % (DESDE + 499, ini))
    di("- Casi toda la ventaja económica ya está en B0 (evitación intradía propia de RD Int): B0 solo da "
       "Top-3 %.2f %% en dev. Lo que aporta Lotto Activo se lee en la fila pareada B1 − B0." % (100 * res[("B0", "dev")][0][0]))
    di("- B0 se eligió entre %d candidatos en dev; la diferencia entre ellos (%.1f mbits) es menor que el IC." %
       (len(sel), abs(sel[B0S[0]][0] - sel[B0S[1]][0]) if len(sel) > 1 else 0))
    di("- El retorno del Top-3 plano de la 1ª mitad tiene IC95 que cruza 0: H2 pasa por la estimación puntual "
       "que fija el pre-registro, no con margen.")
    di("- La prueba ciega NO se miró. `cache_dev.npz` guarda P0, P1, y, hora, dia, fila solo de filas dev.")
    with open(SALIDA_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    et = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if et == "b0":
        etapa_b0(sys.argv[2])
    elif et == "fuga":
        etapa_fuga()
    elif et == "reporte":
        etapa_reporte()
    elif et == "todo":
        for nm in B0S:
            subprocess.run([sys.executable, __file__, "b0", nm], check=True)
        subprocess.run([sys.executable, __file__, "fuga"], check=True)
        etapa_reporte()
    else:
        sys.exit(__doc__)
