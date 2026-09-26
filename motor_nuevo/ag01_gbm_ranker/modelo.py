# -*- coding: utf-8 -*-
"""ag01_gbm_ranker, variante B (apilada): ensamble_v2 walk-forward + corrección LightGBM congelada.

P(i) ∝ P_ens(i) · exp(f(x_i)), con f = árboles de modelo_B.txt (softmax condicional por sorteo),
entrenados SÓLO con filas [2000, 9357) de historial.txt (ver experimento.py). Nada se reajusta aquí.
Las variables de la fila j salen de datos[:desde+j] (variables.py); el ensamble_v2 es walk-forward.
Funciona con días de 11 o 12 sorteos (usa hora, posición en el día y días de calendario).
"""
import importlib.util, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
import variables as V  # noqa: E402

K = 38


def _ensamble():
    ruta = os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py")
    spec = importlib.util.spec_from_file_location("ensamble_v2_ag01", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.Modelo()


class Modelo:
    nombre = "ag01_gbm_apilado"

    def __init__(self, archivo=os.path.join(AQUI, "modelo_B.txt")):
        import lightgbm as lgb
        self.bst = lgb.Booster(model_file=archivo)

    def corregir(self, datos, desde, P_ens):
        n = len(datos)
        X = V.construir(np.asarray(datos.seq), np.asarray(datos.hora), np.asarray(datos.dia), desde, n)
        XB, lp = V.con_ensamble(X, np.asarray(P_ens, float))
        s = self.bst.predict(XB.reshape(-1, XB.shape[2]), raw_score=True).reshape(-1, K) + lp
        s -= s.max(1, keepdims=True); p = np.exp(s)
        return p / p.sum(1, keepdims=True)

    def predecir(self, datos, desde):
        P_ens = _ensamble().predecir(datos, desde)
        return self.corregir(datos, desde, P_ens)
