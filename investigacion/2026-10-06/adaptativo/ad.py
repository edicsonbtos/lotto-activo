import sys, numpy as np
from datetime import date
S=sys.argv[1]
z=np.load(S+"/prod_0605.npz",allow_pickle=True); P,t,y,f,h=z["P"],z["t"],z["y"],z["f"],z["h"]; n=len(y)
fu=sorted(set(f)); di={d:i for i,d in enumerate(fu)}; dn=np.array([di[x] for x in f])
dow=np.array([date.fromisoformat(d).weekday() for d in f])
# para cada fila: conjunto "ya salió hoy" (filas anteriores del mismo día)
hoy=[]; cur=None
for i in range(n):
    if f[i]!=cur: cur=f[i]; s=[]
    hoy.append(np.array(sorted(set(s)),int)); s=s+[int(y[i])]
mass=np.array([P[i,hoy[i]].sum() for i in range(n)]); hit=np.array([y[i] in hoy[i] for i in range(n)])
# agregados por día
dO=np.zeros(len(fu)); dE=np.zeros(len(fu)); np.add.at(dO,dn,hit); np.add.at(dE,dn,mass)
ddow=np.array([date.fromisoformat(d).weekday() for d in fu])
def factores(K,a,semanal):
    r=np.ones(len(fu))
    for j in range(len(fu)):
        prev=[k for k in range(j-1,-1,-1) if (ddow[k]==ddow[j] if semanal else True)][:K*(1 if semanal else 7)]
        O=dO[prev].sum(); E=dE[prev].sum(); r[j]=np.clip((O+a)/(E+a),0.5,3)
    return r
def aplicar(r):
    Q=P.copy()
    for i in range(n):
        if len(hoy[i]): Q[i,hoy[i]]*=r[dn[i]]
    return Q/Q.sum(1,keepdims=True)
def dmb(Q,m):
    v=1000*np.log2(Q[m,y[m]]/P[m,y[m]]); ds=f[m]; u=sorted(set(ds)); per=np.array([v[ds==d].sum() for d in u]); N=len(v)
    se=np.sqrt(((per-v.mean()*np.array([np.sum(ds==d) for d in u]))**2).sum()*len(u)/(len(u)-1))/N
    return v.mean(), v.mean()-1.645*se, v.mean()+1.645*se
def topk(Q,m,k):
    o=np.argsort(-Q[m],1,kind="stable"); return np.mean(np.argmax(o==y[m][:,None],1)<k)*100
def plata(Q,m):
    o=np.argsort(-Q[m],1,kind="stable"); rk=np.argmax(o==y[m][:,None],1); fi=np.array([2,2,2,1,1])
    return (np.where(rk<5,30*fi[np.minimum(rk,4)],0)/8-1).mean()*100
devA=(t>=2000)&(t<=5687); devB=(t>5687)&(t<9357); y26=f>="2026-01-01"
# 1) elección en dev-A
res=[]
for K in (4,8,13,26):
    for a in (3,10,30):
        for sem in (True,False):
            Q=aplicar(factores(K,a,sem)); res.append((dmb(Q,devA)[0],K,a,sem,Q))
mejor={sem:max([r for r in res if r[3]==sem],key=lambda r:r[0]) for sem in (True,False)}
for sem,lab in ((True,"AD (semanal)"),(False,"GL (control)")):
    g,K,a,_,Q=mejor[sem]; print(f"{lab}: elegido en dev-A K={K} a={a}  (dev-A {g:+.2f} mbits)")
    for nm,m in (("dev-B",devB),("2026",y26),("dom dev-B",devB&(dow==6)),("mié-vie 2026",y26&np.isin(dow,[2,3,4])),("resto 2026",y26&~np.isin(dow,[2,3,4]))):
        mb,lo,hi=dmb(Q,m)
        print(f"   {nm:13} Δmbits {mb:+6.2f} [{lo:+6.2f};{hi:+6.2f}]  Top-15 {topk(P,m,15):.1f}->{topk(Q,m,15):.1f}  Top-5 {topk(P,m,5):.1f}->{topk(Q,m,5):.1f}  plata Top-5 {plata(P,m):+.1f}%->{plata(Q,m):+.1f}%")
np.save(S+"/ad_factores.npy",factores(mejor[True][1],mejor[True][2],True))
