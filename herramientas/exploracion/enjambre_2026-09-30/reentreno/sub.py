# -*- coding: utf-8 -*-
"""Predicciones walk-forward de UN submodelo (desde la fila 1000, como ensamble.py) -> cache/<fase>_<clave>.npy (float32).
Uso: python sub.py dev|todo <clave>     (claves en SPECS)
     python sub.py todo congelado_<I|S|H>   (ajuste UNA vez en la fila de 2026-04-01, sin reentrenar despues)"""
import importlib.util, os, sys, time, tracemalloc
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, HERR)
import lotto_eval as LE
MOD = os.path.join(HERR, "modelos")
CACHE = os.path.join(AQUI, "cache"); os.makedirs(CACHE, exist_ok=True)
ARRANQUE = 1000

def cargar_mod(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(MOD, nombre + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def secuencia_ventana(ventana, **kw):
    """secuencia_v3 entrenada SOLO con los ultimos `ventana` sorteos (peso plano)."""
    sv3 = cargar_mod("secuencia_v3"); sf = sv3._sf
    class M(sv3.Modelo):
        def predecir(self, datos, desde):
            seq = np.asarray(datos.seq); n = len(seq)
            est, Pen, _ = sf.construir(datos, self.cfg)
            Pen = Pen + self.lam * np.eye(Pen.shape[0])
            out = np.empty((n - desde, LE.K)); beta = None
            for T in range(desde, n, self.R):
                a = max(self.inicio, T - ventana)
                beta = sf.ajustar(est, slice(a, T), seq[a:T], np.ones(T - a), Pen, beta)
                b = min(T + self.R, n)
                z = sf.logits(est, beta, slice(T, b)); z -= z.max(1, keepdims=True)
                p = np.exp(z); out[T - desde:b - desde] = p / p.sum(1, keepdims=True)
            return out
    return M(**kw)

SPECS = {
    "I": ("intradia_v2", {}), "S": ("secuencia_v3", {}), "H": ("haz_v1", {}),
    "I_v1": ("intradia_v2", dict(tau=500, ventana=2500)), "S_v1": ("secuencia_v3", dict(tau=1000)),
    "H_v1": ("haz_v1", dict(vida_media=1000, ventana=3000, cada=250)),
    "I_v2": ("intradia_v2", dict(tau=None, ventana=2200)), "S_v2": ("secuencia_ventana", dict(tau=None)),
    "H_v2": ("haz_v1", dict(vida_media=1e9, ventana=2200, cada=250)),
    "I_v3": ("intradia_v2", dict(R=84)), "S_v3": ("secuencia_v3", dict(R=84)), "H_v3": ("haz_v1", dict(cada=84)),
}
CONGELA = {"I": ("intradia_v2", dict(R=10**7)), "S": ("secuencia_v3", dict(R=10**7)), "H": ("haz_v1", dict(cada=10**7))}

def datos(fase):
    D = LE.cargar(os.path.join(AQUI, "historial_la.txt"))
    return D.prefijo(LE.CORTE_FIJO) if fase == "dev" else D

def fila_inicio_conf(D):
    return next(i for i, f in enumerate(D.fecha) if f >= "2026-04-01")

if __name__ == "__main__":
    fase, clave = sys.argv[1], sys.argv[2]
    ruta = os.path.join(CACHE, f"{fase}_{clave}.npy")
    if os.path.exists(ruta):
        print("ya existe", ruta); sys.exit()
    D = datos(fase); t0 = time.time(); tracemalloc.start()
    if clave.startswith("congelado_"):
        nombre, kw = CONGELA[clave.split("_")[1]]
        desde = fila_inicio_conf(D)
    else:
        nombre, kw = SPECS[clave]; desde = ARRANQUE
    if nombre == "secuencia_ventana":
        m = secuencia_ventana(2200, **kw)
    else:
        m = cargar_mod(nombre).Modelo(**kw)
    P = m.predecir(D, desde)
    np.save(ruta, P.astype(np.float32))
    print(fase, clave, P.shape, f"{time.time()-t0:.0f}s", f"pico {tracemalloc.get_traced_memory()[1]/2**20:.0f} MB", flush=True)
