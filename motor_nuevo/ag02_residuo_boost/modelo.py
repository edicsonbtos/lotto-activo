# -*- coding: utf-8 -*-
"""ag02_residuo_boost / V1: ensamble_v2 (walk-forward, herramientas/modelos) + corrección residual lineal
congelada: P ∝ P_ens · exp(x·w), con x = rasgos.construir (27 variables de contenido: tablero, sucesor
de s1, par, ayer). w en parametros.json, ajustado solo con filas < 9357. Fila j usa solo datos[:desde+j].
Funciona con jornadas de 11 o 12 sorteos (usa hora y posición reales de cada jornada)."""
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
    nombre = "ag02_residuo_boost_V1"

    def __init__(self, parametros=os.path.join(AQUI, "parametros.json"), P_ens=None):
        cfg = json.load(open(parametros, encoding="utf-8"))
        assert cfg["nombres"] == R.NOMBRES
        self.w = np.array(cfg["w"], float)
        self.P_ens = P_ens          # opcional: predicciones del ensamble ya calculadas (mismas filas)

    def predecir(self, datos, desde):
        P = self.P_ens if self.P_ens is not None else _ensamble().predecir(datos, desde)
        P = np.clip(np.asarray(P, float), 1e-12, None)
        X, _ = R.construir(datos, desde)
        z = np.log(P / P.sum(1, keepdims=True)) + X.astype(float) @ self.w
        z -= z.max(1, keepdims=True)
        Q = np.exp(z)
        return Q / Q.sum(1, keepdims=True)
