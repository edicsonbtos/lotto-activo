# ag05 — comprobaciones extra SOLO en dev: coleccionista con más simulaciones por era, y el mejor candidato en mbits
import numpy as np
from comun import *
DEV = TR == "dev"; rng = np.random.default_rng(7)
def T_col(y):
    n=len(y); out=[]
    for s in range(n):
        seen=set()
        for t in range(s,n):
            seen.add(y[t])
            if len(seen)==38: out.append(t-s+1); break
    return np.mean(out) if out else np.nan
for lab, m in (("9:00", DEV&(ERA=="9:00")), ("8:00", DEV&(ERA=="8:00")), ("dev", DEV)):
    r=np.where(m)[0]; Tobs=T_col(Y[r]); cum=PA[r].cumsum(1)
    su=np.array([T_col(rng.integers(0,38,len(r))) for _ in range(1000)])
    sp=np.array([T_col((rng.random(len(r))[:,None]>cum).sum(1).clip(0,37)) for _ in range(1000)])
    print(f"{lab} n={len(r)} T_obs={Tobs:.1f} azar {su.mean():.1f} p={np.mean(su<=Tobs):.3f} | P_aj {sp.mean():.1f} p={np.mean(sp<=Tobs):.3f}")
# mejor candidato de (1): posiciones {2,4,5}; multiplicador ajustado en dev con suavizado
G = POS[:,:,[2,4,5]].any(2); O,E = oe(DEV,G); mlt=(O+.5)/(E+.5)
for lab, m in (("9:00", DEV&(ERA=="9:00")), ("8:00", DEV&(ERA=="8:00")), ("dev", DEV)):
    r=np.where(m)[0]; q=aplicar(np.where(G,mlt,1.0)); v=mbits(q,r)
    print(lab, f"mult={mlt:.3f}", "mbits=%.1f [%.1f; %.1f] P<=0=%.3f"%boot(v))
