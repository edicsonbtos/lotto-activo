"""Valida que nucleo.correr_mes (parámetros por omisión) reproduce la matriz congelada motor0_S2.npz, y mide el CPU."""
import sys, time, resource, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/ciego/T2")
import nucleo as N
Pf = np.load(N.SP + "/motor0_S2.npz")["P"]
for mes in sys.argv[1:]:
    t0 = time.time(); c0 = resource.getrusage(resource.RUSAGE_SELF); c0 = c0.ru_utime + c0.ru_stime
    o = N.correr_mes(mes)
    c1 = resource.getrusage(resource.RUSAGE_SELF); c1 = c1.ru_utime + c1.ru_stime
    d = np.abs(o["P"] - Pf[o["filas"] - N.A.T[0]]).max()
    print(mes, "filas", len(o["filas"]), "árboles", o["bs"], "max|ΔP|", d, f"pared {time.time()-t0:.0f}s CPU {c1-c0:.0f}s", flush=True)
