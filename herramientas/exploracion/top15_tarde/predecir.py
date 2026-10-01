# -*- coding: utf-8 -*-
"""Predicciones walk-forward del MODELO ACTUAL (lo que la web juega) hasta 2026-09-29 -> cache/.

LA: ensamble_v2 (intradia_v2 + secuencia_v3 + haz_v1), predecir(D, 2000): submodelos desde la fila
    1000 y pesos reajustados en 2000 + k*250 con filas anteriores, igual que prediccion.py.
    Historial: enjambre_2026-09-30/reentreno/historial_la.txt (fechas corregidas el 2026-09-29 y API
    oficial hasta el 2026-09-29; se cotejaron 5.147 sorteos con la API sin diferencias).
RD: B1 = B0 (secuencia_v3 solo con RD, desde 2000) * exp(b.x), b walk-forward (modelo.cruzado,
    R=250, minimo=500), como cache_todo.npz. RD = rdint_hist.csv corregido y completado con la API
    oficial (juego 2) hasta el 2026-09-29 (oficial_multi.csv + oficial_extra.csv del enjambre).

Uso: python predecir.py         (2-4 min; no calcula ninguna métrica de la idea)
"""
import csv, io, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.abspath(os.path.join(AQUI, "..", ".."))
RAIZ = os.path.dirname(HERR)
sys.path.insert(0, HERR); sys.path.insert(0, os.path.join(HERR, "rdint")); sys.path.insert(0, RAIZ)
import lotto_eval as LE

ENJ = os.path.join(HERR, "exploracion", "enjambre_2026-09-30", "reentreno")
HIST_LA = os.path.join(ENJ, "historial_la.txt")
EXTRA = os.path.join(ENJ, "oficial_extra.csv")
CACHE = os.path.join(AQUI, "cache")
RD_CSV_EXT = os.path.join(CACHE, "rdint_hist_ext.csv")
DESDE = 2000


def rd_csv_extendido():
    """rdint_hist.csv corregido con la API oficial (juego 2): donde hay dato oficial manda el oficial
    (el CSV tiene 11 sorteos distintos, 2026-03-04..07 de 17:30 a 19:30), y se añaden los sorteos
    oficiales que faltan (2026-09-23..29 de oficial_extra.csv)."""
    import rdint_vivo as RV
    base = list(csv.DictReader(io.open(os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv"), encoding="utf-8")))
    of = {}
    for ruta in (os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"), EXTRA):
        for r in csv.DictReader(io.open(ruta, encoding="utf-8")):
            if r["juego"] == "2":
                of[(r["fecha"], r["hora"])] = r["codigo"]
    filas = {(r["fecha"], r["hora"]): RV.codigo_de_nombre(r["animal"]) for r in base}
    dif = sorted(k for k in filas if k in of and of[k] != filas[k])
    nuevos = sorted(k for k in of if k not in filas)
    print("RD: CSV hasta", max(k[0] for k in filas), "| cotejo con API oficial:", sum(k in of for k in filas),
          "sorteos,", len(dif), "diferencias (manda la API):", dif, "| se añaden", len(nuevos), "sorteos de la API")
    filas.update(of)
    with io.open(RD_CSV_EXT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh); w.writerow(["fecha", "hora", "animal"])
        for (f, h), c in sorted(filas.items()):
            w.writerow([f, h, RV.NOMBRE[c]])


def la():
    D = LE.cargar(HIST_LA)
    t0 = time.time()
    m = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
    P = LE.normalizar(m.predecir(D, DESDE))
    print("LA:", P.shape, f"{time.time() - t0:.0f}s", D.fecha[DESDE], "..", D.fecha[-1])
    # control de fuga: con el historial cortado en 9357 las filas anteriores no cambian
    m2 = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
    P2 = LE.normalizar(m2.predecir(D.prefijo(LE.CORTE_FIJO), DESDE))
    print("LA control de fuga (corte 9357): max|dif| =", float(np.abs(P[:len(P2)] - P2).max()))
    np.savez_compressed(os.path.join(CACHE, "la.npz"), P=P.astype(np.float32), y=np.asarray(D.seq)[DESDE:],
                        hora=np.asarray(D.hora)[DESDE:], fecha=np.array(D.fecha)[DESDE:], fila=np.arange(DESDE, len(D)))


def rd():
    rd_csv_extendido()
    import datos as DT
    import modelo as MB
    DT.RD_CSV = RD_CSV_EXT
    DT.LA_HIST = HIST_LA
    rdd, la_h, la_h1, la_hoy, tramo = DT.cargar()
    t0 = time.time()
    b0 = LE.cargar_modelo(os.path.join(HERR, "modelos", "secuencia_v3.py"))
    P0, P1, hist = MB.predecir(b0, rdd, la_h, la_h1, la_hoy, DESDE)
    print("RD:", P1.shape, f"{time.time() - t0:.0f}s", rdd.fecha[DESDE], "..", rdd.fecha[-1], "| b final", hist[-1][1].round(3))
    fe = np.array(rdd.fecha)[DESDE:]; ho = np.asarray(rdd.hora)[DESDE:]
    # control: coincide con verificacion/hilo9/datos/cache_todo.npz donde se solapan
    z = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "cache_todo.npz"))
    idx = {(f, int(h)): i for i, (f, h) in enumerate(zip(fe, ho))}
    par = [(i, idx[(str(f), int(h))]) for i, (f, h) in enumerate(zip(z["fecha"], z["hora"])) if (str(f), int(h)) in idx]
    a, b = np.array(par).T
    print("RD control contra cache_todo:", len(par), "filas; y iguales:", bool((z["y"][a] == np.asarray(rdd.seq)[DESDE:][b]).all()),
          "| max|dif P1| =", float(np.abs(z["P1"][a] - P1[b]).max()))
    np.savez_compressed(os.path.join(CACHE, "rd.npz"), P=P1.astype(np.float32), P0=P0.astype(np.float32),
                        y=np.asarray(rdd.seq)[DESDE:], hora=ho, fecha=fe, la_h=la_h[DESDE:], tramo=tramo[DESDE:])


if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)
    que = sys.argv[1:] or ["la", "rd"]
    if "rd" in que:
        rd()
    if "la" in que:
        la()
