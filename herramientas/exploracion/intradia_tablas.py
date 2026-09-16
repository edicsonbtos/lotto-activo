import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; dia=d.dia[:CORTE]; n=len(seq); ar=np.arange(n)
nuevo=np.r_[True,dia[1:]!=dia[:-1]]; ini=np.maximum.accumulate(np.where(nuevo,ar,0)); k=ar-ini
print("fechas cortes:", d.fecha[0], d.fecha[n//3], d.fecha[2*n//3], d.fecha[n-1])
last=np.full(K,-10**6)
tabs={}
for t in range(n):
    per=min(3*t//n,2)
    g=t-last; today=last>=ini[t]
    for i in np.where(today)[0]:
        key=(per,k[t],int(g[i])); h,tt=tabs.get(key,(0,0)); tabs[key]=(h+(seq[t]==i),tt+1)
    last[seq[t]]=t
for per in range(3):
    print("periodo",per)
    for kk in range(1,12):
        H=sum(tabs.get((per,kk,g),(0,0))[0] for g in range(1,12)); T=sum(tabs.get((per,kk,g),(0,0))[1] for g in range(1,12))
        row=" ".join(f"{tabs[(per,kk,g)][0]/tabs[(per,kk,g)][1]*K:4.2f}" if (per,kk,g) in tabs else "  - " for g in range(1,12))
        print(f" k={kk:2d} tot {H/T*K if T else 0:4.2f} ({H:4d}/{T:5d}) | g: {row}")
# distinct per day by period
import collections
for per in range(3):
    lo,hi=per*n//3,(per+1)*n//3
    ds=collections.defaultdict(list)
    for t in range(lo,hi): ds[dia[t]].append(seq[t])
    c=collections.Counter((len(v),len(set(v))) for v in ds.values()); print(per,sorted(c.items()))
