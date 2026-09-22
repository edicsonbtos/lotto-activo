# -*- coding: utf-8 -*-
"""PRUEBA CIEGA de la selección por calor. Se ejecuta UNA vez y queda registrada.

Ejecuta exactamente lo preregistrado en PREREGISTRO_calor_lista.md (2026-09-22):
umbrales congelados, Top-3 como caso principal, criterio de éxito fijado de
antemano. No hay variantes ni afinado.

Esta ejecución MIRA EL TRAMO DE PRUEBA [9357, n) y añade una línea a
herramientas/registro_final.jsonl. A propósito no se cachea la matriz del
tramo de prueba: la fricción es parte de la protección.
"""
import json, math, os, sys, time
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERR = os.path.join(RAIZ, "herramientas")
REGISTRO = os.path.join(HERR, "registro_final.jsonl")
sys.path.insert(0, HERR)
import lotto_eval as LE          # noqa: E402

PAGO = 30
# Umbrales CONGELADOS en el preregistro. No se recalculan.
UMBRAL = {3: 0.131055, 5: 0.207155, 15: 0.529157}


def ic95(k, n):
    t = k / n
    e = 1.96 * (t * (1 - t) / n) ** 0.5
    return 100 * (t - e), 100 * (t + e)


def analizar(P, y, topn):
    n = len(P)
    orden = np.argsort(-P, axis=1)[:, :topn]
    ac = np.array([y[i] in orden[i] for i in range(n)], dtype=int)
    calor = np.sort(P, axis=1)[:, -topn:].sum(axis=1)
    u = UMBRAL[topn]
    cal, fri = calor >= u, calor < u
    kc, nc = int(ac[cal].sum()), int(cal.sum())
    kf, nf = int(ac[fri].sum()), int(fri.sum())
    tc, tf = (kc / nc if nc else 0.0), (kf / nf if nf else 0.0)
    se = (tc * (1 - tc) / max(nc, 1) + tf * (1 - tf) / max(nf, 1)) ** 0.5
    z = (tc - tf) / se if se else 0.0
    p = 0.5 * math.erfc(z / 2 ** 0.5)
    lo, hi = ic95(kc, nc) if nc else (0.0, 0.0)
    equil = 100.0 * topn / PAGO
    ev = lambda t: (PAGO * t - topn) / topn * 100
    return dict(topn=topn, umbral=u, n=n, global_tasa=100 * ac.mean(),
                n_cal=nc, k_cal=kc, tasa_cal=100 * tc, ic_cal=[lo, hi],
                n_fri=nf, k_fri=kf, tasa_fri=100 * tf,
                dif=100 * (tc - tf), z=z, p=p, equilibrio=equil,
                ev=ev(tc), ev_ic_bajo=ev(lo / 100),
                pasa_equilibrio=bool(lo > equil), pasa_contraste=bool(p < 0.05))


def main():
    datos = LE.cargar(os.path.join(RAIZ, "historial.txt"))
    w, corte = LE.particion(len(datos))
    print(f"historial: {len(datos)} sorteos")
    print(f"desarrollo [{w}, {corte})   ·   PRUEBA [{corte}, {len(datos)}) "
          f"= {len(datos)-corte} sorteos")
    print("\ncalculando el ensamble walk-forward...", flush=True)
    modelo = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
    P = np.asarray(modelo.predecir(datos, w))
    y = np.asarray(datos.seq[w:])
    P, y = P[corte - w:], y[corte - w:]          # SOLO el tramo de prueba

    res = {t: analizar(P, y, t) for t in (3, 5, 15)}

    for t in (3, 5, 15):
        r = res[t]
        cab = "PRINCIPAL" if t == 3 else "secundario"
        print("\n" + "=" * 72)
        print(f"TOP-{t}  ({cab})   umbral congelado {100*r['umbral']:.4f} %"
              f"   ·   equilibrio {r['equilibrio']:.1f} %")
        print("=" * 72)
        print(f"  tasa global del tramo de prueba: {r['global_tasa']:.2f} %")
        print(f"  CALIENTE: {r['tasa_cal']:.2f} %  ({r['k_cal']}/{r['n_cal']})"
              f"   IC95 {r['ic_cal'][0]:.2f}-{r['ic_cal'][1]:.2f}")
        print(f"  FRÍA:     {r['tasa_fri']:.2f} %  ({r['k_fri']}/{r['n_fri']})")
        print(f"  diferencia {r['dif']:+.2f} pp   z = {r['z']:.2f}   p(una cola) = {r['p']:.4f}")
        print(f"  EV a {PAGO}x jugando la mitad caliente: {r['ev']:+.1f} % "
              f"(IC bajo {r['ev_ic_bajo']:+.1f} %)")
        print(f"  ¿IC entero sobre el equilibrio? {'SI' if r['pasa_equilibrio'] else 'NO'}"
              f"   ·   ¿contraste p<0,05? {'SI' if r['pasa_contraste'] else 'NO'}")

    pr = res[3]
    veredicto = "PASA" if (pr["pasa_equilibrio"] and pr["pasa_contraste"]) else "FALLA"
    print("\n" + "#" * 72)
    print(f"#  VEREDICTO (Top-3, criterio preregistrado): {veredicto}")
    print("#" * 72)
    if veredicto == "FALLA":
        print("#  La regla se descarta. No se reintenta con otro umbral: eso")
        print("#  convertiría la prueba en desarrollo.")

    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "cuando": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modelo": "ensamble_v2 + seleccion por calor",
            "preregistro": "herramientas/exploracion/PREREGISTRO_calor_lista.md",
            "veredicto_top3": veredicto,
            "prueba": {str(t): res[t] for t in (3, 5, 15)},
        }, ensure_ascii=False) + "\n")
    with open(REGISTRO, encoding="utf-8") as f:
        print(f"\nregistro_final.jsonl: {sum(1 for _ in f)} líneas (miradas al tramo de prueba)")


if __name__ == "__main__":
    main()
