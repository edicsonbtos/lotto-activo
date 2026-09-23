# -*- coding: utf-8 -*-
"""H4b (PREREGISTRO_h4b_reciproca.md): ¿Lotto Activo gana al saber lo que salió en RD Int?

Base  : ensamble_v2 walk-forward sobre todo LA hasta FIN (desde LE.W).
Sonda : la de H4 (sonda_inversa.features + modelo.cruzado R=250, minimo=500, lam=1).
Ventana principal: LA 2025-12-17 .. FIN (nunca puntuada con RD). Control: 2025-07-01 .. 2025-12-16.

Uso: python herramientas/rdint/reciproca_la.py   -> resultados/hilo7_h4b_reciproca.md
"""
import os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, HERR); sys.path.insert(0, AQUI)
import lotto_eval as LE
import datos as DT
import modelo as MB
import correr_modelo as CM
import sonda_inversa as SI

FIN = "2026-09-22"
CACHE = os.path.join(AQUI, "_la_ensamble_todo.npz")
SALIDA_MD = os.path.join(HERR, "resultados", "hilo7_h4b_reciproca.md")
HIST = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or os.path.dirname(HERR), "historial.txt")
VENTANAS = [("PRINCIPAL", "2025-12-17", "2026-09-23"),
            ("  sub: tramo test de RD", "2025-12-17", "2026-04-13"),
            ("  sub: réplica", "2026-04-13", "2026-09-23"),
            ("control (prueba ciega vieja)", "2025-07-01", "2025-12-17"),
            ("desarrollo (ya visto)", "2024-03-01", "2025-07-01")]
rng = np.random.default_rng(20260924)
L = []


def di(s=""):
    print(s, flush=True); L.append(s)


def ensamble(la):
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        if int(z["n"]) == len(la):
            return z["P"].astype(np.float64)
    t0 = time.time()
    P = LE.normalizar(LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py")).predecir(la, LE.W))
    np.savez_compressed(CACHE, P=P.astype(np.float32), n=len(la))
    print("ensamble: %d filas en %.0f s" % (len(P), time.time() - t0), flush=True)
    return P


def main():
    la = LE.cargar(HIST)
    n = int(np.searchsorted(np.array(la.fecha), FIN, side="right"))
    la = la.prefijo(n)
    P = ensamble(la)
    y = np.asarray(la.seq)[LE.W:]; fechas = np.array(la.fecha[LE.W:])
    hora = np.asarray(la.hora)[LE.W:]; dia = np.asarray(la.dia)[LE.W:]

    # la caché vieja (calor_cache) debe coincidir en las filas comunes: mismo modelo, mismo walk-forward
    vieja = os.path.join(HERR, "exploracion", "calor_cache.npz")
    if os.path.exists(vieja):
        Pv = np.load(vieja)["P"]; m = min(len(Pv), len(P))
        print("control caché vieja: max |ΔP| en %d filas = %.2e" % (m, np.abs(LE.normalizar(Pv[:m]) - P[:m]).max()))

    rd, *_ = DT.cargar()
    rdd = {}
    for f, h, s in zip(rd.fecha, rd.hora, rd.seq):
        if f <= FIN:
            rdd.setdefault(f, {})[int(h)] = int(s)
    X, tiene = SI.features(list(fechas), hora, rdd)
    ok_fuga, mueve = SI.prueba_fuga(list(fechas), hora, rdd, X)
    P1, hist = MB.cruzado(P, X, y)

    di("# H4b — ¿Lotto Activo gana al saber lo que salió en RD Int? (%s)\n" % time.strftime("%Y-%m-%d %H:%M"))
    di("Pre-registro: `herramientas/exploracion/PREREGISTRO_h4b_reciproca.md` (contaminación declarada ahí).")
    di("LA %s .. %s (%d filas evaluables); con RD ese día: %.1f %%."
       % (fechas[0], fechas[-1], len(y), 100 * tiene.mean()))
    di("Prueba de fuga (cambiar RD desde h:30 no mueve la fila de LA h:00): **%s**; control movido: %d."
       % ("SIN FUGA" if ok_fuga else "FUGA", mueve))
    di("Coeficientes al final: %s  (exp: %s)\n"
       % (np.round(hist[-1][1], 3).tolist(), np.round(np.exp(hist[-1][1]), 2).tolist()))
    di("| ventana | n | Δ mbits [IC95] | Top-3 ens → +RD | Top-3 plano ens → +RD | Top-5 escal. ens → +RD [IC95] |")
    di("|---|---|---|---|---|---|")
    veredicto = None
    for nom, a, b in VENTANAS:
        s = (fechas >= a) & (fechas < b)
        if not s.any():
            continue
        d = CM.mbits(P1[s], y[s]) - CM.mbits(P[s], y[s])
        m, lo, hi = CM.boot_media(d, dia[s], rng)
        t0, r30, r50 = CM.apuestas(P[s], y[s]); t1, r31, r51 = CM.apuestas(P1[s], y[s])
        _, l5, h5 = CM.boot_media(100 * r51, dia[s], rng)
        di("| %s (%s..%s) | %d | %+.1f [%+.1f, %+.1f] | %.2f → %.2f %% | %+.1f → %+.1f %% | %+.1f → %+.1f [%+.1f, %+.1f] %% |"
           % (nom, a, b, s.sum(), m, lo, hi, 100 * t0.mean(), 100 * t1.mean(), 100 * r30.mean(),
              100 * r31.mean(), 100 * r50.mean(), 100 * r51.mean(), l5, h5))
        if nom == "PRINCIPAL":
            veredicto = (m >= 5 and lo > 0, r51.mean() > r50.mean())

    di("\nRepetición cruda LA h:00 == RD (h−1):30 (contra 1/38), ventana principal, por hora:")
    s = fechas >= "2025-12-17"
    rep = X[np.arange(len(y)), y, 0] > 0
    marc = X[:, :, 0].sum(1) > 0
    di("  total %d de %d (esperado %.1f)" % (rep[s].sum(), (s & marc).sum(), (s & marc).sum() / LE.K))
    pasa, dinero = veredicto
    di("\n**VEREDICTO H4b: %s** (Δ ≥ +5 mbits e IC95 > 0 en la ventana principal)" % ("PASA" if pasa else "FALLA"))
    di("**Dinero (Top-5 escalonado con RD > sin RD): %s**" % ("SÍ" if dinero else "NO"))
    with open(SALIDA_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
