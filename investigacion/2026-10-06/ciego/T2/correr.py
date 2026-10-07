"""Corre las variantes de la batería sobre la submuestra de meses (igual para todas) y guarda cada mes en <SP>/T2/.
python correr.py placebo gap1 ruido s1 s2 s3 s4"""
import sys, os, time, resource, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/ciego/T2")
import nucleo as N
MESES = ["2025-08", "2025-10", "2025-12", "2026-02",      # AJUSTE (4 de 8, alternos)
         "2026-03", "2026-04", "2026-05", "2026-06"]      # ELECCION (los 4)
CFG = {"placebo": dict(perm=1), "placebo2": dict(perm=2), "gap1": dict(gap=1), "ruido": dict(ruido=True),
       "s1": dict(seed=1), "s2": dict(seed=2), "s3": dict(seed=3), "s4": dict(seed=4), "base": dict()}
OUT = N.SP + "/T2"
def cpu():
    r = resource.getrusage(resource.RUSAGE_SELF); return r.ru_utime + r.ru_stime
for var in sys.argv[1:]:
    for mes in MESES:
        f = f"{OUT}/{var}_{mes}.npz"
        if os.path.exists(f): continue
        c0 = cpu(); o = N.correr_mes(mes, **CFG[var])
        np.savez(f, P=o["P"], filas=o["filas"], imp=o["imp"], nm=np.array(o["nm"]), bs=np.array(o["bs"]), freq=o["freq"])
        print(f"{var} {mes} árboles {o['bs']} CPU {cpu()-c0:.0f}s", flush=True)
