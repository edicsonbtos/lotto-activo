import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
d=e.cargar(); n=len(d); W,CORTE=e.particion(n); K=38
seq=d.seq[:CORTE]; dia=d.dia[:CORTE]; n=len(seq)
nuevo=np.r_[True,dia[1:]!=dia[:-1]]; ar=np.arange(n)
ini=np.maximum.accumulate(np.where(nuevo,ar,0)); k=ar-ini
last=np.full(K,-10**6)
# stats: (g, same_day) -> hits, tot
from collections import defaultdict
H=defaultdict(float);T=defaultdict(float)
# distinct since last appearance
for t in range(n):
    if t>=200:
        g=t-last
        same=(last>=ini[t])
        for i in range(K):
            if g[i]<=24:
                key=(int(g[i]),bool(same[i]))
                T[key]+=1; H[key]+= (seq[t]==i)
    last[seq[t]]=t
print("g  hoy:rate(n)   ayer:rate(n)")
for g in range(1,25):
    s=[]
    for sm in (True,False):
        tt=T[(g,sm)]; s.append(f"{H[(g,sm)]/tt*K if tt else float('nan'):5.2f}({int(tt):6d})")
    print(g,*s)
