"""Huella exacta de las predicciones de los modelos de secuencia sobre las primeras filas del historial.

Uso: `python tests/oro_modelos.py` escribe tests/oro_secuencia.json (se corrió ANTES de consolidar).
test_modelos_secuencia.py compara contra ese archivo.
"""
import hashlib, json, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

NOMBRES = ("secuencia_v1", "secuencia_v2_dow", "secuencia_final", "secuencia_v3")
N_FILAS, DESDE = 3500, 3000


def huellas():
    datos = LE.cargar().prefijo(N_FILAS)
    out = {}
    for nombre in NOMBRES:
        m = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", nombre + ".py"))
        P = np.ascontiguousarray(m.predecir(datos, DESDE), dtype=np.float64)
        out[nombre] = {"nombre": m.nombre, "forma": list(P.shape), "sha256": hashlib.sha256(P.tobytes()).hexdigest(),
                       "fila0": P[0].tolist(), "fila_ultima": P[-1].tolist(),
                       "suma_cuadrados": float((P ** 2).sum()), "max": float(P.max())}
    return out


if __name__ == "__main__":
    t = time.time()
    h = huellas()
    with open(os.path.join(AQUI, "oro_secuencia.json"), "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps(h, ensure_ascii=False, indent=1)[:1500]); print("segundos: %.1f" % (time.time() - t))
