# -*- coding: utf-8 -*-
"""Pronósticos EN SOMBRA (no se juegan ni cambian la web): se guardan junto al congelado del ensamble
para medirlos con sorteos futuros (motor_nuevo/RETOMAR.md).

- ag12: P ∝ P_ens · exp(x·w), 33 variables (27 de ag02 + 6 de pares consecutivos recientes), pesos congelados
  en parametros_V1.json (commit c4a2b17). Pasó la 2.ª prueba ciega en la época reciente (+19,4 mbits).
- ag12_rd: ag12 × 0,50 al animal de RD (h−1):30 y × 0,75 al de RD (h−2):30 (r2_a03_rd_produccion, VB).

corregir(filas, pf, ph, p_ens, rd) -> {"ag12": [38], "ag12_rd": [38] o None}
  filas: [(fecha, hora, idx)] del historial (lo que ya salió); (pf, ph): próximo sorteo;
  p_ens: 38 probabilidades del ensamble para ese sorteo; rd: {(fecha, hora): idx} de RD Internacional.
"""
import json, os, sys
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rasgos12 as R  # noqa: E402

_CFG = json.load(open(os.path.join(AQUI, "parametros_V1.json"), encoding="utf-8"))
assert _CFG["nombres"] == R.NOMBRES
W = np.array(_CFG["w"], float)
RD_MULT = {1: 0.50, 2: 0.75}      # RD (h−1):30 y (h−2):30


class _Datos:
    def __init__(self, filas):
        d0 = date.fromisoformat(filas[0][0])
        self.seq = np.array([s for _, _, s in filas]); self.hora = np.array([h for _, h, _ in filas])
        self.dia = np.array([(date.fromisoformat(f) - d0).days for f, _, _ in filas])
        self.fecha = [f for f, _, _ in filas]

    def __len__(self):
        return len(self.seq)


def _norm(p):
    p = np.clip(np.asarray(p, float), 1e-12, None)
    return p / p.sum()


def corregir(filas, pf, ph, p_ens, rd=None):
    # la fila del próximo sorteo solo usa lo anterior: se añade un sorteo ficticio (su animal no se lee)
    base = list(filas) + [(pf, ph, 0)]      # historial completo: un par (s2,s1) puede tardar > 4000 sorteos en repetirse
    D = _Datos(base)
    X, _ = R.construir(D, len(base) - 1)
    z = np.log(_norm(p_ens)) + X[0].astype(float) @ W
    q = _norm(np.exp(z - z.max()))
    out = {"ag12": [round(float(v), 6) for v in q], "ag12_rd": None}
    if rd is not None:
        q2 = q.copy(); hay = False
        for k, m in RD_MULT.items():
            a = rd.get((pf, ph - k)) if ph - k >= 0 else None
            if a is not None:
                q2[a] *= m; hay = True
        if hay:
            out["ag12_rd"] = [round(float(v), 6) for v in _norm(q2)]
        else:
            out["ag12_rd"] = out["ag12"]
    return out
