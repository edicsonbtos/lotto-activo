import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as L
d = L.cargar(); n = len(d); w, corte = L.particion(n)
seq = d.seq[:corte]; dia = d.dia[:corte]; hora = d.hora[:corte]
key = {(dia[i], hora[i]): seq[i] for i in range(corte)}
days = sorted(set(dia)); prevday = {days[i]: days[i-1] for i in range(1, len(days))}
def rate(fn):
    hit = tot = 0
    for i in range(200, corte):
        c = fn(i)
        if c is None: continue
        tot += 1; hit += (seq[i] == c)
    return hit / tot * 38, tot
for lag in [1, 2, 3, 7]:
    def f(i, lag=lag):
        dd = dia[i]
        for _ in range(lag):
            dd = prevday.get(dd)
            if dd is None: return None
        return key.get((dd, hora[i]))
    print("mismo slot, dias atras", lag, rate(f))
for dh in [-2, -1, 1, 2]:
    print("ayer hora", dh, rate(lambda i, dh=dh: key.get((prevday.get(dia[i]), hora[i] + dh))))
# hoy: k, veces-hoy rates
