import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
SCR=sys.argv[1]; BASE=sys.argv[2]
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; P=np.load(f"{SCR}/base_{BASE}.npy"); n=len(P); T=np.arange(W,CORTE); y=seq[W:]
num=np.array([0,0]+list(range(1,37)))
rows=np.arange(n); L1=seq[T-1]; L2=seq[T-2]
np.set_printoptions(precision=2,suppress=True,linewidth=220)
# residuo transicion (prev, cand) -> O-E  (38x38)
O=np.zeros((K,K)); E=np.zeros((K,K)); V=np.zeros((K,K))
np.add.at(O,(L1,y),1)
for c in range(K): np.add.at(E[:,c],L1,P[:,c]); np.add.at(V[:,c],L1,P[:,c]*(1-P[:,c]))
Z=(O-E)/np.sqrt(V)
lab=["0","00"]+[str(i) for i in range(1,37)]
col=np.where(np.arange(K)<2,3,(num-1)%3)
for a in range(4):
  for b in range(4):
    ma=col==a; mb=col==b
    o=O[np.ix_(ma,mb)].sum(); ee=E[np.ix_(ma,mb)].sum(); v=V[np.ix_(ma,mb)].sum()
    print("col prev",a,"cand",b,"O=%d E=%.1f ratio=%.3f z=%+.2f"%(o,ee,o/ee,(o-ee)/np.sqrt(v)))
# por candidato: sum over prev in col2
m2=col==2
print("cand z | prev col2:", {lab[c]: round(((O[m2,c].sum()-E[m2,c].sum())/np.sqrt(V[m2,c].sum())),1) for c in range(K)})
print("prev z | cand col2:", {lab[c]: round(((O[c,m2].sum()-E[c,m2].sum())/np.sqrt(V[c,m2].sum())),1) for c in range(K)})
# por cuartos
f=(col[L1]==2)[:,None]&(col==2)[None,:]
for q in np.array_split(rows,4):
    o=f[q,y[q]].sum(); ee=(P[q]*f[q]).sum(); print("cuarto O=%d E=%.1f r=%.2f"%(o,ee,o/ee))
# diag de Z por diferencia
dv=np.array([0,37]+list(range(1,37)))
for k in range(K):
    msk=((dv[None,:]-dv[:,None])%K)==k
    o=O[msk].sum(); ee=E[msk].sum(); v=V[msk].sum()
    print("dif",k,"r=%.2f z=%+.1f"%(o/ee,(o-ee)/np.sqrt(v)), end=" | ")
print()
