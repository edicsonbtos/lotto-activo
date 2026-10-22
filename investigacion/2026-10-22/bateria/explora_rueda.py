# EXPLORATORIO (post-hoc, no decide): O/E por distancia en la rueda al ganador de 1, 2 y 3 sorteos antes (mismo día).
import sys, os, numpy as np
RAIZ = os.path.abspath("../../.."); sys.path.insert(0, RAIZ + "/herramientas"); sys.path.insert(0, ".")
import lotto_eval as LE
from rasgos import POSR, NUM
D = LE.cargar(RAIZ + "/verificacion/hilo9/datos/historial.txt")
c = np.load(RAIZ + "/verificacion/hilo9/datos/calor_cache.npz"); P = c["P"] / c["P"].sum(1, keepdims=True); y = c["y"]
T0 = 2000
pr = np.array([POSR[i] for i in range(38)])
for lag in (1, 2, 3):
    o = np.zeros(20); e = np.zeros(20)
    for i in range(len(y)):
        t = T0 + i
        if D.dia[t - lag] != D.dia[t]: continue
        r = POSR[D.seq[t - lag]]
        dist = np.minimum((pr - r) % 38, (r - pr) % 38)
        np.add.at(e, dist, P[i]); o[dist[y[i]]] += 1
    print(f"lag {lag}: " + " ".join(f"d{d}:{o[d]/e[d]:.2f}" for d in range(0, 20)))
    print("        z d1:", round((o[1]-e[1])/np.sqrt(e[1]),2), " d2:", round((o[2]-e[2])/np.sqrt(e[2]),2), " d1-3:", round((o[1:4].sum()-e[1:4].sum())/np.sqrt(e[1:4].sum()),2))
# también noche->8:00 (anterior = último de ayer)
o = np.zeros(20); e = np.zeros(20)
for i in range(len(y)):
    t = T0 + i
    if D.dia[t - 1] == D.dia[t]: continue
    r = POSR[D.seq[t - 1]]; dist = np.minimum((pr - r) % 38, (r - pr) % 38)
    np.add.at(e, dist, P[i]); o[dist[y[i]]] += 1
print("8:00 vs último de ayer d1:", round(o[1]/e[1],2), "n_esp", round(e[1],1))
