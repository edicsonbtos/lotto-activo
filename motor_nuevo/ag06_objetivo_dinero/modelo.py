# -*- coding: utf-8 -*-
"""ag06_objetivo_dinero / V_dinero (primaria, NO pasó la barra): ensamble_v2 walk-forward (del repo) +
reordenador lineal entrenado con pérdida de dinero (Top-5 escalonado, rango suave):
P = softmax(c · (log P_ens + x·w)), w y c congelados en parametros.json (ajustados solo con filas < 9357).
Fila j usa solo datos[:desde+j]. Admite jornadas de 11 o 12 sorteos (usa hora y día reales)."""
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
    nombre = "ag06_objetivo_dinero_V_dinero"

    def __init__(self, parametros=os.path.join(AQUI, "parametros.json"), P_ens=None):
        cfg = json.load(open(parametros, encoding="utf-8"))
        assert cfg["nombres"] == R.NOMBRES
        self.w = np.array(cfg["w"], float); self.c = float(cfg["c"])
        self.P_ens = P_ens

    def predecir(self, datos, desde):
        P = self.P_ens if self.P_ens is not None else _ensamble().predecir(datos, desde)
        P = np.clip(np.asarray(P, float), 1e-12, None)
        X = R.construir(datos, desde).astype(float)
        z = self.c * (np.log(P / P.sum(1, keepdims=True)) + X @ self.w)
        z -= z.max(1, keepdims=True)
        Q = np.exp(z)
        return Q / Q.sum(1, keepdims=True)
