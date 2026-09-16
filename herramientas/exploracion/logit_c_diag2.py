import sys, numpy as np
sys.path.insert(0, r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas")
from lotto_eval import cargar, particion
from scipy.stats import chi2
K=38
d=cargar(); w,c=particion(len(d)); N=c
seq=d.seq[:N]; dia=d.dia[:N]; hora=d.hora[:N]
def trans(lag, sameday=None):
    M=np.zeros((K,K))
    for t in range(lag,N):
        if sameday is not None and (dia[t]==dia[t-lag])!=sameday: continue
        M[seq[t-lag],seq[t]]+=1
    np.fill_diagonal(M,0)
    # expected under independence excluding diagonal (approx)
    r=M.sum(1,keepdims=True); cc=M.sum(0,keepdims=True)
    E=r*cc/M.sum(); np.fill_diagonal(E,0); E*=M.sum()/E.sum()
    m=E>0; X=((M-E)**2/np.where(m,E,1))[m].sum(); df=m.sum()-2*K
    return X, df, chi2.sf(X,df)
for lag in [1,2,3,12]: print("trans lag",lag, trans(lag))
# circular distance between consecutive indices
dist=np.abs(seq[1:]-seq[:-1]); print("dist hist", np.bincount(dist,minlength=38)[:10])
# same weekday last week same hour
from collections import defaultdict
key={(dia[i],hora[i]):seq[i] for i in range(N)}
for lagd in [1,7,14]:
    hit=tot=0
    for i in range(N):
        v=key.get((dia[i]-lagd,hora[i]))
        if v is None: continue
        tot+=1; hit+=v==seq[i]
    print("same hour, days back",lagd, hit/tot*38, tot)
# distinct in last 38 draws
