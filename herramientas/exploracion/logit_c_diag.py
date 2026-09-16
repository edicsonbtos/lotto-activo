import sys, numpy as np
sys.path.insert(0, r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas")
from lotto_eval import cargar, particion
K=38
d=cargar(); w,c=particion(len(d)); N=c
seq=d.seq[:N]; dia=d.dia[:N]; hora=d.hora[:N]
G=np.zeros((N,K),int); S=np.zeros((N,K),int); kk=np.zeros(N,int); DD=np.zeros((N,K),int)
last=np.full(K,-10**6); lastd=np.full(K,-10**6); cnt=np.zeros(K,int); cur=-1; k=0
dayidx=np.cumsum(np.r_[0, dia[1:]!=dia[:-1]])
for t in range(N):
    if dia[t]!=cur: cnt[:]=0; cur=dia[t]; k=0
    G[t]=np.minimum(t-last,999); S[t]=cnt; kk[t]=k; DD[t]=dayidx[t]-lastd
    v=seq[t]; last[v]=t; lastd[v]=dayidx[t]; cnt[v]+=1; k+=1
Y=np.zeros((N,K),bool); Y[np.arange(N),seq]=True
sl=slice(300,N); G,S,kk,DD,Y=G[sl],S[sl],kk[sl],DD[sl],Y[sl]
K2=np.broadcast_to(kk[:,None],G.shape)
def r(m): return f"{Y[m].mean()*38:.2f}({m.sum()})" if m.sum()>200 else "   -   "
print("S>0 rate by k:", [r((S>0)&(K2==x)) for x in range(1,12)])
print("S==0 rate by k:", [r((S==0)&(K2==x)) for x in range(0,12)])
print("S==0 by days-ago (rows) x k (cols 0..11)")
for dd in range(1,6):
    print(dd, [r((S==0)&(DD==dd)&(K2==x)) for x in range(0,12)])
print("S==0, DD==1: by position yesterday offset g-k")
for g in range(1,13):
    print(g, [r((S==0)&(DD==1)&(G-K2==g)) for x in [0]])
