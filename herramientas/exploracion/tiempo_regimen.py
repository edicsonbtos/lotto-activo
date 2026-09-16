import sys; sys.path.insert(0,'.')
import numpy as np
from lotto_eval import cargar, particion
d=cargar(); seq=d.seq; n=len(seq); w,corte=particion(n)
print(n,w,corte, d.fecha[0], d.fecha[corte], d.fecha[-1])
K=38
last=np.full(K,-1); G=np.zeros(n,int)  # gap of observed
gapsall=[]
for t in range(n):
    G[t]= t-last[seq[t]] if last[seq[t]]>=0 else 999
    last[seq[t]]=t
# per segment of 1000 draws (only < corte), hazard for g bins
bins=[(1,1),(2,2),(3,6),(7,12),(13,30),(31,60),(61,999)]
# exposure: for each t, gaps of all numbers
last=np.full(K,-1); expo=np.zeros((n,len(bins)))
for t in range(n):
    g=np.where(last>=0,t-last,999)
    for bi,(a,b) in enumerate(bins): expo[t,bi]=np.sum((g>=a)&(g<=b))
    last[seq[t]]=t
seg=800
for s in range(0,corte,seg):
    e=min(s+seg,corte); r=[]
    for bi,(a,b) in enumerate(bins):
        h=np.sum((G[s:e]>=a)&(G[s:e]<=b)); x=expo[s:e,bi].sum()
        r.append(h/x*K if x else 0)
    # distinct per day
    dd=d.dia[s:e]; days=np.unique(dd); dist=[len(set(seq[s:e][dd==k])) for k in days]; cnt=[np.sum(dd==k) for k in days]
    dist12=[a for a,c in zip(dist,cnt) if c==12]
    print(d.fecha[s], ' '.join(f'{x:.2f}' for x in r), f'dist12={np.mean(dist12) if dist12 else 0:.2f} n12={len(dist12)} spd={np.mean(cnt):.1f}')
