#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SONDA DESECHABLE - teoria inversa: excluir 13, apostar a los 25 restantes.

Pregunta del usuario (2026-09-21): si en vez de acertar el animal que SALE
acertamos los 13 que NO salen, podriamos apostar 1 unidad a cada uno de los
25 restantes. Con pago 30x eso deja +5 por ronda ganada y -25 por ronda
perdida.

  EV(ronda) = 30*p - 25,  p = P(el ganador este entre mis 25)
  equilibrio: p >= 25/30 = 83.333%   (azar: 25/38 = 65.789%)
  o, visto al reves: los 13 excluidos deben bajar de 34.211% a 16.667%.

CLAVE: "apostar a 25 y excluir 13" ES apostar al Top-25 del mismo motor. Por
eso la sonda no mide un caso suelto sino la curva completa k=1..37 de
  ROI(k) = (30*aciertos_k - k*n) / (k*n)
que unifica Top-1, Top-3 y la propuesta de 25 en un solo grafico. El caso del
usuario es k=25 (m=13 excluidos).

Estructura que conviene ver antes de leer numeros: apostando a 38-m animales
con pago 30x, si m <= 8 se apuesta a 30 o mas unidades para cobrar 30, asi que
NINGUNA exclusion, ni perfecta, puede dar ganancia. Hay que excluir >= 9.

NULA EXACTA: bajo H0 (sorteos iid uniformes e independientes del pasado) el
rango del ganador es uniforme sobre los 38 puestos SEA CUAL SEA el modelo. Por
eso aciertos_k ~ Binomial(n, k/38) exacto y el p-valor no necesita
estratificar por hora (a diferencia del contraste de dos proporciones del hilo
de la racha del favorito, que si lo necesitaba). El desglose por hora que
imprime al final es DESCRIPTIVO: elegir la mejor hora al verla seria
sobreajuste, por eso se marca con Bonferroni de 12.

SOLO TRAMO DE DESARROLLO. El tramo de prueba ya se miro una vez el 2026-09-14
y no se vuelve a tocar por una idea nueva.
"""
import argparse, json, math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, HERR)

import numpy as np
import lotto_eval as ev


def curva_roi(pos, n, pago):
    """ROI por unidad apostada para cada k = 1..37 (apostar 1 a cada Top-k)."""
    filas = []
    for k in range(1, ev.K):
        hits = int(np.sum(pos < k))
        tasa = hits / n
        m = ev.K - k                       # animales excluidos
        umbral = k / pago                  # tasa minima para no perder
        lo, hi = ev.wilson(hits, n)
        z = (hits - n * (k / ev.K)) / math.sqrt(n * (k / ev.K) * (1 - k / ev.K))
        filas.append({
            "k": k, "excluidos": m, "aciertos": hits, "tasa": tasa,
            "azar": k / ev.K, "ic95": [lo, hi],
            "umbral_equilibrio": umbral,
            "roi": (pago * hits - k * n) / (k * n),
            "z_vs_azar": z,
            "p_valor": ev.binom_sf(hits, n, k / ev.K),
            "viable": k < pago,            # con k >= 30 se apuesta >= 30 para cobrar 30: nunca gana
        })
    return filas


def por_hora(pos, hora, n, k, pago):
    """Desglose descriptivo del caso k. Bonferroni de 12 sobre el p-valor."""
    out = []
    p0 = k / ev.K
    for h in range(12):
        sel = hora == h
        nh = int(sel.sum())
        if nh == 0:
            continue
        hits = int(np.sum(pos[sel] < k))
        tasa = hits / nh
        lo, hi = ev.wilson(hits, nh)
        z = (hits - nh * p0) / math.sqrt(nh * p0 * (1 - p0))
        p = ev.binom_sf(hits, nh, p0)
        out.append({"hora": h, "n": nh, "aciertos": hits, "tasa": tasa,
                    "ic95": [lo, hi], "z": z, "p_valor": p,
                    "p_bonferroni": min(1.0, p * 12),
                    "roi": (pago * hits - k * nh) / (k * nh)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hist", default=ev.HIST)
    ap.add_argument("--modelo", default=os.path.join(HERR, "modelos", "ensamble_v2.py"))
    ap.add_argument("--pago", type=float, default=ev.PAGO, help="cuanto paga el acierto (por defecto 30)")
    ap.add_argument("--excluidos", type=int, default=13, help="cuantos animales se dejan fuera")
    ap.add_argument("--sin-fuga", action="store_true")
    ap.add_argument("--json", default=os.path.join(HERR, "resultados", "sonda_inversa13.json"))
    a = ap.parse_args()

    pago = a.pago
    k_caso = ev.K - a.excluidos           # animales a los que se apuesta

    datos = ev.cargar(a.hist)
    n_tot = len(datos)
    w, corte = ev.particion(n_tot)
    print(f"historial: {n_tot} sorteos | calentamiento [0,{w}) | DESARROLLO [{w},{corte})"
          f" | prueba [{corte},{n_tot}) NO SE MIRA", flush=True)
    print(f"caso del usuario: excluir {a.excluidos}, apostar a {k_caso}, pago {pago:g}x", flush=True)

    modelo = ev.cargar_modelo(a.modelo)
    print(f"modelo: {modelo.nombre}", flush=True)

    if not a.sin_fuga:
        print("prueba de fuga (look-ahead)...", flush=True)
        ok, c, diff = ev.prueba_fuga(modelo, datos, w)
        if not ok:
            print(f"ABORTA: FUGA DE DATOS, filas <= {c} cambian (dif {diff:.3g})")
            return 1
        print("  sin fuga", flush=True)

    print("walk-forward (unos 5 min)...", flush=True)
    P = ev.normalizar(modelo.predecir(datos, w))
    if P.shape != (n_tot - w, ev.K):
        print(f"ABORTA: forma {P.shape}, esperaba {(n_tot - w, ev.K)}")
        return 1

    # Solo desarrollo.
    P = P[: corte - w]
    y = datos.seq[w:corte]
    hora = datos.hora[w:corte]
    n = len(y)

    orden = ev.rankings(P)                                  # mismo desempate que lotto_eval
    pos = np.argmax(orden == y[:, None], axis=1)            # 0 = el modelo lo puso primero

    filas = curva_roi(pos, n, pago)
    caso = next(f for f in filas if f["k"] == k_caso)
    q = 1.0 - caso["tasa"]                                  # masa que cae en los excluidos

    # ---------------------------------------------------------------- informe
    print()
    print("=" * 78)
    print(f"CASO DEL USUARIO  -  excluir {a.excluidos} / apostar a {k_caso}   (n={n} sorteos de desarrollo)")
    print("=" * 78)
    print(f"  el ganador cae en los {a.excluidos} excluidos : {q*100:6.2f}%   (azar {a.excluidos/ev.K*100:.2f}%)")
    print(f"  hace falta bajar de                   : {(1 - k_caso/pago)*100:6.2f}%")
    print(f"  el ganador cae en los {k_caso} apostados : {caso['tasa']*100:6.2f}%"
          f"  IC95 [{caso['ic95'][0]*100:.2f}-{caso['ic95'][1]*100:.2f}]")
    print(f"  hace falta subir a                    : {k_caso/pago*100:6.2f}%")
    ev_ronda = pago * caso["tasa"] - k_caso
    print(f"  EV por ronda de {k_caso:>2} unidades        : {ev_ronda:+7.3f}   (ROI {caso['roi']*100:+.2f}%)")
    print(f"  veredicto                             : "
          f"{'GANA' if ev_ronda > 0 else 'PIERDE'}")
    print()

    print("-" * 78)
    print("CURVA COMPLETA  -  apostar 1 unidad a cada uno del Top-k")
    print("-" * 78)
    print(f"{'k':>3} {'excl':>5} {'tasa':>8} {'azar':>7} {'umbral':>7} {'ROI':>9} {'z':>7}  nota")
    for f in filas:
        nota = "" if f["viable"] else "imposible (se apuesta >= pago)"
        marca = " <== CASO" if f["k"] == k_caso else ""
        print(f"{f['k']:>3} {f['excluidos']:>5} {f['tasa']*100:7.2f}% {f['azar']*100:6.2f}% "
              f"{f['umbral_equilibrio']*100:6.2f}% {f['roi']*100:+8.2f}% {f['z_vs_azar']:+7.2f}  {nota}{marca}")
    mejor = max((f for f in filas if f["viable"]), key=lambda f: f["roi"])
    print(f"\n  mejor k viable: {mejor['k']} (excluye {mejor['excluidos']}), ROI {mejor['roi']*100:+.2f}%")

    print()
    print("-" * 78)
    print(f"DESGLOSE POR HORA del caso k={k_caso}  (DESCRIPTIVO - elegir hora al verla = sobreajuste)")
    print("-" * 78)
    hs = por_hora(pos, hora, n, k_caso, pago)
    print(f"{'hora':>4} {'n':>6} {'en los 25':>10} {'umbral':>7} {'ROI':>9} {'z':>7} {'p(bonf)':>9}")
    for h in hs:
        print(f"{h['hora']:>4} {h['n']:>6} {h['tasa']*100:9.2f}% {k_caso/pago*100:6.2f}% "
              f"{h['roi']*100:+8.2f}% {h['z']:+7.2f} {h['p_bonferroni']:9.3f}")
    ganadoras = [h for h in hs if h["roi"] > 0]
    print(f"\n  horas con ROI>0: {[h['hora'] for h in ganadoras] or 'ninguna'}")
    if ganadoras:
        print("  OJO: con 12 horas miradas, ~0.6 salen positivas por puro azar. Mirar p(bonf).")

    salida = {"n_desarrollo": n, "pago": pago, "excluidos": a.excluidos, "k_caso": k_caso,
              "modelo": modelo.nombre, "caso": caso, "q_excluidos": q,
              "ev_por_ronda": ev_ronda, "curva": filas, "por_hora": hs}
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    print(f"\njson -> {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
