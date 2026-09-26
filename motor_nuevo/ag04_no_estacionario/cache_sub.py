# -*- coding: utf-8 -*-
"""Calcula (una vez) las predicciones walk-forward de los submodelos del ensamble_v2
sobre datos.prefijo(9357) desde arranque=1000 (como hace ensamble.py) y las guarda en
cache_sub_<nombre>.npy. Opcionalmente variantes 'rapidas' (olvido corto) de los submodelos.
Uso: python cache_sub.py [base|rapidos]"""
import os, sys, time, importlib.util
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import arnes as A  # noqa

MOD = os.path.join(A.RAIZ, "herramientas", "modelos")

def cargar(nombre, **kw):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(MOD, nombre + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.Modelo(**kw)

VARIANTES = {
    "base": [("intradia_v2", {}), ("secuencia_v3", {}), ("haz_v1", {})],
    "rapidos": [("intradia_v2", dict(tau=400, ventana=1500)), ("haz_v1", dict(vida_media=800, ventana=2000, cada=250))],
}

if __name__ == "__main__":
    grupo = sys.argv[1] if len(sys.argv) > 1 else "base"
    D = A.datos().prefijo(A.CORTE)
    for nombre, kw in VARIANTES[grupo]:
        tag = nombre + ("" if not kw else "_" + "_".join(f"{k}{v}" for k, v in sorted(kw.items())))
        ruta = os.path.join(AQUI, f"cache_sub_{tag}.npy")
        if os.path.exists(ruta):
            print("ya existe", ruta); continue
        t0 = time.time()
        P = cargar(nombre, **kw).predecir(D, 1000)
        np.save(ruta, P.astype(np.float64))
        print(tag, P.shape, f"{time.time()-t0:.0f}s", flush=True)
