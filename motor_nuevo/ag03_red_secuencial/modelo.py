# -*- coding: utf-8 -*-
"""ag03_red_secuencial / V_apilado: ensamble_v2 (walk-forward, del repo) + MLP equivariante congelado.
logit_i = log P_ens(i) + g(x_i), x_i = rasgos.construir (últimos 72 ganadores por animal, hora, jornada).
Parámetros en parametros.npz, ajustados solo con filas < 9357. Fila j usa solo datos[:desde+j].
Admite jornadas de 11 o 12 sorteos (usa dia y hora reales)."""
import importlib.util, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
import rasgos as R  # noqa: E402
import red  # noqa: E402


def _ensamble():
    ruta = os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py")
    spec = importlib.util.spec_from_file_location("ensamble_v2", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.Modelo()


class Modelo:
    nombre = "ag03_red_secuencial_apilado"

    def __init__(self, parametros=os.path.join(AQUI, "parametros.npz"), P_ens=None):
        z = np.load(parametros)
        assert list(z["nombres"]) == R.NOMBRES
        self.p = {k: z[k] for k in ("W1", "b1", "w2")}
        self.P_ens = P_ens

    def predecir(self, datos, desde):
        P = self.P_ens if self.P_ens is not None else _ensamble().predecir(datos, desde)
        P = np.clip(np.asarray(P, float), 1e-12, None)
        off = np.log(P / P.sum(1, keepdims=True)).astype(np.float32)
        X = R.construir(datos, desde)
        return red.probs(self.p, X, off)
