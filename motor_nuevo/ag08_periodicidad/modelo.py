# -*- coding: utf-8 -*-
"""ag08_periodicidad: ensamble_v2 (walk-forward, del repo) + corrección log-lineal con 8 indicadoras
temporales (salió hace 12/24/36/38/76/84 sorteos; salió a la misma hora hace 1 y 7 días naturales).
θ CONGELADO en parametros.json (ajustado solo con filas [2000, 9357)). P ∝ P_ens · exp(X·θ).
Fila j usa solo datos[:desde+j] y el calendario del propio sorteo. Admite jornadas de 11 o 12 sorteos
(los desfases cuentan sorteos; "misma hora hace k días" usa la fecha y el índice de hora).
OJO: en desarrollo NO mejora al ensamble (−0,45 mbits); se entrega por completitud."""
import importlib.util, json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
import rasgos as R  # noqa: E402


def _ensamble():
    ruta = os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py")
    spec = importlib.util.spec_from_file_location("ensamble_v2", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.Modelo()


class Modelo:
    nombre = "ag08_periodicidad"

    def __init__(self, parametros=os.path.join(AQUI, "parametros.json"), P_ens=None):
        cfg = json.load(open(parametros, encoding="utf-8"))
        self.specs = [tuple(s) for s in cfg["specs"]]; self.theta = np.array(cfg["theta"], float)
        self.P_ens = P_ens

    def predecir(self, datos, desde):
        P = self.P_ens if self.P_ens is not None else _ensamble().predecir(datos, desde)
        P = np.clip(np.asarray(P, float), 1e-12, None); P = P / P.sum(1, keepdims=True)
        X = R.construir(datos, desde, self.specs)
        return R.aplicar(P, X, self.theta)
