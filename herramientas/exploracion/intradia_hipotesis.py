import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
from scipy.optimize import minimize
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; dia=d.dia[:CORTE]; n=len(seq); ar=np.arange(n)
nuevo=np.r_[True,dia[1:]!=dia[:-1]]; didx=np.cumsum(nuevo)-1
ini=np.maximum.accumulate(np.where(nuevo,ar,0)); k=ar-ini
G=np.empty((n,K),np.int64); DD=np.empty((n,K),np.int64); DIST=np.empty((n,K),np.int64); CNT=np.zeros((n,K),np.int64)
last=np.full(K,-10**6); lastd=np.full(K,-10**6)
# distinct since last appearance: number of distinct other values seen since last[i]
for t in range(n):
    G[t]=t-last; DD[t]=didx[t]-lastd
    v=seq[t]; last[v]=t; lastd[v]=didx[t]
G=np.minimum(G,10**6)
# distinct count since last occurrence: for each t,i compute via cumulative scan
seen_since=np.zeros((K,K),bool)  # seen_since[i,j]: j seen since i last
for t in range(n):
    DIST[t]=seen_since.sum(1)
    v=seq[t]; seen_since[:,v]=True; seen_since[v,:]=False
oh=np.zeros((n,K)); oh[ar,seq]=1; C=np.vstack([np.zeros(K),np.cumsum(oh,0)])
hoy=(C[ar]-C[ini]).astype(int)
A=slice(200,n); R=slice(W-200,None)  # fit rows 200..n ; report on W..CORTE
def fit(tablas,dense=None):
    # tablas: list of (idx (n,K), size) idx 0 = reference
    offs=[];o=0
    for idx,s in tablas: offs.append(o); o+=s
    I=[(idx[200:]+of) for (idx,s),of in zip(tablas,offs)]
    y=seq[200:]; m=len(y); P=o
    def f(w):
        S=sum(w[ii] for ii in I)
        for ii,of,(idx,s) in zip(I,offs,tablas): pass
        S=S-S.max(1,keepdims=True); lz=np.log(np.exp(S).sum(1)); lp=S[np.arange(m),y]-lz
        p=np.exp(S-lz[:,None]); g=np.zeros(P)
        for ii in I:
            g+=np.bincount(ii[np.arange(m),y],minlength=P)-np.bincount(ii.ravel(),p.ravel(),minlength=P)
        mask=np.ones(P); 
        for of in offs: mask[of]=0
        return -lp.sum()+0.5*1e-3*(w*w).sum(), (-g+1e-3*w)*mask
    r=minimize(f,np.zeros(P),jac=True,method="L-BFGS-B")
    w=r.x; S=sum(w[ii] for ii in I); S=S-S.max(1,keepdims=True); lz=np.log(np.exp(S).sum(1)); lp=S[np.arange(m),y]-lz
    lpR=lp[W-200:]
    return (lpR.mean()+np.log(K))/np.log(2)*1000, w, offs
def cap(x,c): return np.minimum(x,c)
res={}
sal=(hoy>0).astype(int)
res['hoy']=fit([(sal,2)])
res['hoy x veces']=fit([(cap(hoy,2),3)])
kk=np.broadcast_to(k[:,None],(n,K))
res['hoy x k']=fit([(np.where(hoy>0,cap(kk,11),0),12)])
for m in (6,8,10,11,12,14,18):
    res[f'ventana {m}']=fit([((G<=m).astype(int),2)])
for c in (8,10,12,15,20):
    res[f'ciclo distintos<{c}']=fit([((DIST<c).astype(int),2)])
res['gap exacto 1..40']=fit([(np.where(G<=40,G,0),41)])
res['dist exacto 0..37']=fit([(cap(DIST,37),38)])
res['hoy x k + gap(no hoy) 1..40']=fit([(np.where(hoy>0,cap(kk,11),0),12),(np.where((hoy==0)&(G<=40),G,0),41)])
res['hoy x k + dias(1..5)']=fit([(np.where(hoy>0,cap(kk,11),0),12),(np.where((hoy==0)&(DD<=5),DD,0),6)])
res['hoy x k + dias x k']=fit([(np.where(hoy>0,cap(kk,11),0),12),(np.where((hoy==0)&(DD<=4),(DD-1)*12+kk+1,0),49)])
res['hoy x k + dist(no hoy)']=fit([(np.where(hoy>0,cap(kk,11),0),12),(np.where(hoy==0,cap(DIST,37)+1,0),39)])
res['hoy x k + gap(no hoy)+dias']=fit([(np.where(hoy>0,cap(kk,11),0),12),(np.where((hoy==0)&(G<=40),G,0),41),(np.where((hoy==0)&(DD<=5),DD,0),6)])
for kx,v in res.items(): print(f"{kx:35s} {v[0]:+7.2f} mbits  npar={len(v[1])}")
np.save(os.path.join(os.path.dirname(__file__),'intradia_w.npy'),res['hoy x k + dias x k'][1])
print(np.round(res['hoy x k + dias x k'][1],2))
print(np.round(res['hoy x k + gap(no hoy) 1..40'][1],2))
