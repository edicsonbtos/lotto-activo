# -*- coding: utf-8 -*-
"""ag12_transiciones: ensamble_v2 (walk-forward) + corrección lineal congelada P ∝ P_ens · exp(x·w).
x = 27 variables de ag02 + 6 de transiciones recientes dentro del día (s1→i e i→s1 hace 1, 2-7 y 8-30 jornadas).
w en parametros_V1.json (o parametros_V0.json = solo transiciones), ajustado solo con filas [2000, 9357).
Fila j usa solo datos[:desde+j]. Vale para jornadas de 11 o 12 sorteos (cuenta jornadas del calendario)."""
import importlib.util, json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
import rasgos12 as R  # noqa: E402


def _ensamble():
    ruta = os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py")
    spec = importlib.util.spec_from_file_location("ensamble_v2_ag12", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.Modelo()


class Modelo:
    nombre = "ag12_transiciones"

    def __init__(self, variante="V1", P_ens=None):
        cfg = json.load(open(os.path.join(AQUI, f"parametros_{variante}.json"), encoding="utf-8"))
        assert cfg["nombres"] == R.NOMBRES
        self.w = np.array(cfg["w"], float); self.P_ens = P_ens; self.nombre = f"ag12_{variante}"

    def predecir(self, datos, desde):
        P = self.P_ens if self.P_ens is not None else _ensamble().predecir(datos, desde)
        P = np.clip(np.asarray(P, float), 1e-12, None)
        X, _ = R.construir(datos, desde)
        z = np.log(P / P.sum(1, keepdims=True)) + X.astype(float) @ self.w
        z -= z.max(1, keepdims=True)
        Q = np.exp(z)
        return Q / Q.sum(1, keepdims=True)


class ModeloV0(Modelo):
    def __init__(self, P_ens=None):
        super().__init__("V0", P_ens)
