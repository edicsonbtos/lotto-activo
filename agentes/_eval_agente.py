# -*- coding: utf-8 -*-
"""Evaluacion walk-forward generica para cualquier agente.

Uso:
    python agentes/_eval_agente.py <modulo_agente> [N_SORTEOS]

Ejemplo:
    python agentes/_eval_agente.py agente_hazard 1500

Carga historial.txt, y para cada t en [n-N, n) predice con seq[:t] (SOLO el
pasado) y mide:
  * top-1 : el animal que salio es el de mayor puntaje
  * top-3 : el animal que salio esta entre los 3 de mayor puntaje
  * log-loss medio sobre softmax de los puntajes estandarizados

Reutilizable por todos los agentes: basta con que el modulo defina una clase
concreta que herede de base.Agente (se toma la primera clase hija encontrada).
"""
import importlib
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import Agente, K, cargar_historial  # noqa: E402

EPS = 1e-12


def _obtener_agente(nombre_modulo):
    mod = importlib.import_module(nombre_modulo)
    for obj in vars(mod).values():
        if isinstance(obj, type) and issubclass(obj, Agente) and obj is not Agente:
            return obj()
    raise SystemExit(f"No se encontro clase Agente en {nombre_modulo!r}")


def softmax_estandar(scores):
    """Softmax de puntajes estandarizados (media 0, std 1) -> probabilidades."""
    m = sum(scores) / len(scores)
    var = sum((s - m) ** 2 for s in scores) / len(scores)
    sd = math.sqrt(var) or 1.0
    z = [(s - m) / sd for s in scores]
    mx = max(z)
    e = [math.exp(x - mx) for x in z]
    tot = sum(e)
    return [x / tot for x in e]


def main():
    modulo = sys.argv[1] if len(sys.argv) > 1 else "agente_hazard"
    n_eval = int(sys.argv[2]) if len(sys.argv) > 2 else 1500

    agente = _obtener_agente(modulo)
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "historial.txt")
    seq, horas, dweek, _ = cargar_historial(ruta)
    n = len(seq)

    t0 = time.time()
    aciertos1 = aciertos3 = 0
    ll_total = 0.0
    for t in range(n - n_eval, n):
        scores = agente.predecir(seq[:t], horas[:t], dweek[:t])
        real = seq[t]
        orden = sorted(range(K), key=lambda i: (-scores[i], i))
        if orden[0] == real:
            aciertos1 += 1
        if real in orden[:3]:
            aciertos3 += 1
        probs = softmax_estandar(scores)
        p = min(max(probs[real], EPS), 1.0)
        ll_total += -math.log(p)

    dt = time.time() - t0
    print(f"Agente     : {agente.nombre} ({modulo})")
    print(f"Descripcion: {agente.descripcion}")
    print(f"Evaluados  : {n_eval} sorteos walk-forward (indices {n - n_eval}..{n - 1})")
    print(f"Top-1      : {aciertos1 / n_eval:.4f}  ({aciertos1}/{n_eval})")
    print(f"Top-3      : {aciertos3 / n_eval:.4f}  ({aciertos3}/{n_eval})")
    print(f"Log-loss   : {ll_total / n_eval:.4f}  (uniforme = {math.log(K):.4f})")
    print(f"Tiempo     : {dt:.1f}s total, {dt / n_eval * 1000:.1f} ms/prediccion")


if __name__ == "__main__":
    main()
