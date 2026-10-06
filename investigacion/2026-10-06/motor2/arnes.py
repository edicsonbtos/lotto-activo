# -*- coding: utf-8 -*-
"""Arnés común del enjambre "motor 2" (2026-10-06). TODOS los agentes evalúan con esto.

Uso:  import sys; sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
      A.D (lotto_eval.Datos del historial hasta 2026-10-05), A.T (filas evaluables), A.PROD (38 probs de producción por fila)
      A.evaluar(P_nuevo, "nombre", tramos=("AJUSTE","ELECCION"))   # P_nuevo: (len(A.T), 38), fila i = sorteo A.T[i]
Reglas de tramos (no negociables):
  AJUSTE   = 2025-07-01..2026-02-28: ajustar parámetros aquí.
  ELECCION = 2026-03-01..2026-06-30: elegir entre variantes aquí. Se puede mirar todas las veces que haga falta.
  PRUEBA26 = 2026-07-01..2026-10-05: SOLO para la versión final ya congelada, UNA vez (tramos=("PRUEBA26",)).
  ANTIGUO  = antes de 2025-07-01: solo informativo (otro régimen del operador); no sirve para elegir.
             evaluar() deja constancia en registro_prueba26.jsonl de cada mirada.
Cada fila de P_nuevo debe calcularse SOLO con sorteos anteriores (walk-forward); A.chequear_fuga(fn) lo prueba.
"""
import json, os, sys, time
import numpy as np
from datetime import date
AQUI = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
sys.path.insert(0, "/home/user/lotto-activo/herramientas")
import lotto_eval as LE  # noqa: E402

D = LE.cargar(os.path.join(SP, "hist_0605.txt"))
_z = np.load(os.path.join(SP, "prod_0605.npz"), allow_pickle=True)
T = _z["t"].astype(int); PROD = _z["P"]; Y = _z["y"].astype(int); F = _z["f"]; H = _z["h"].astype(int)
DOW = np.array([date.fromisoformat(x).weekday() for x in F])
# Tramos RECIENTES (el operador cambia de régimen; se juzga con su comportamiento actual). Pedido del usuario 2026-10-06.
TRAMOS = {"AJUSTE": (F >= "2025-07-01") & (F <= "2026-02-28"), "ELECCION": (F >= "2026-03-01") & (F <= "2026-06-30"),
          "PRUEBA26": (F >= "2026-07-01"), "ANTIGUO": F < "2025-07-01"}   # ANTIGUO: solo informativo
FICHAS = np.array([2, 2, 2, 1, 1])


def _ic90(v, m):
    ds = F[m]; u, inv = np.unique(ds, return_inverse=True); per = np.bincount(inv, v); cnt = np.bincount(inv)
    se = np.sqrt(((per - v.mean() * cnt) ** 2).sum() * len(u) / (len(u) - 1)) / len(v)
    return v.mean() - 1.645 * se, v.mean() + 1.645 * se


def evaluar(P, nombre, tramos=("AJUSTE", "ELECCION"), extra=None):
    P = np.asarray(P, float); assert P.shape == PROD.shape, P.shape
    P = np.clip(P, 1e-9, None); P = P / P.sum(1, keepdims=True)
    filas = []
    for tr in tramos:
        m = TRAMOS[tr]; i = np.where(m)[0]; yy = Y[i]
        dmb = 1000 * np.log2(P[i, yy] / PROD[i, yy]); lo, hi = _ic90(dmb, m)
        mb = 1000 * np.log2(P[i, yy] * 38).mean()
        o = np.argsort(-P[i], 1, kind="stable"); rk = np.argmax(o == yy[:, None], 1)
        op = np.argsort(-PROD[i], 1, kind="stable"); rkp = np.argmax(op == yy[:, None], 1)
        ret = (np.where(rk < 5, 30 * FICHAS[np.minimum(rk, 4)], 0) / 8 - 1).mean() * 100
        retp = (np.where(rkp < 5, 30 * FICHAS[np.minimum(rkp, 4)], 0) / 8 - 1).mean() * 100
        fila = dict(nombre=nombre, tramo=tr, n=int(len(i)), mbits=round(mb, 1), dmbits_vs_prod=round(dmb.mean(), 2),
                    ic90=[round(lo, 2), round(hi, 2)], top5=round(np.mean(rk < 5) * 100, 2), top5_prod=round(np.mean(rkp < 5) * 100, 2),
                    top15=round(np.mean(rk < 15) * 100, 2), top15_prod=round(np.mean(rkp < 15) * 100, 2),
                    ret_top5=round(ret, 1), ret_top5_prod=round(retp, 1))
        filas.append(fila)
        print(f"[{nombre}] {tr:9} n={fila['n']:5d} mbits {mb:+6.1f} | Δ vs prod {dmb.mean():+6.2f} [{lo:+6.2f};{hi:+6.2f}] | "
              f"Top-5 {fila['top5']:.1f} (prod {fila['top5_prod']:.1f}) | Top-15 {fila['top15']:.1f} (prod {fila['top15_prod']:.1f}) | "
              f"ret Top-5 {ret:+.1f}% (prod {retp:+.1f}%)")
        if tr == "PRUEBA26":
            with open(os.path.join(AQUI, "registro_prueba26.jsonl"), "a", encoding="utf-8") as fh:
                fh.write(json.dumps(dict(cuando=time.strftime("%Y-%m-%d %H:%M:%S"), **fila, extra=extra), ensure_ascii=False) + "\n")
    return filas


def chequear_fuga(fn, cortes=(6000, 9000, 12000)):
    """fn(seq, hora, dow, fecha, i) -> 38 probs para el sorteo i usando solo [:i]. Cambia el futuro y exige mismo resultado."""
    S = np.asarray(D.seq).copy()
    for c in cortes:
        a = fn(S, np.asarray(D.hora), np.asarray(D.dow), list(D.fecha), c)
        S2 = S.copy(); S2[c:] = (S2[c:] + 7) % 38
        b = fn(S2, np.asarray(D.hora), np.asarray(D.dow), list(D.fecha), c)
        assert np.allclose(a, b), f"FUGA en el corte {c}"
    print("chequear_fuga: OK")
