# logit condicional con curva de retraso suavizada (penalizacion 2a diferencia) + covariables
import sys, time, json, numpy as np
from scipy.optimize import minimize
sys.path.insert(0, r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas")
from lotto_eval import cargar, particion, metricas
from haz_feat import feats
K=38
d=cargar(); W,C=particion(len(d)); N=C
G,D,S=feats(d,N); y=d.seq[:N]; hora=d.hora[:N]
dia=d.dia[:N]; ud=dia-dia[0]; ND=ud.max()+1
DC=np.zeros((ND+1,K),int); np.add.at(DC,(ud,y),1)
CUM=np.vstack([np.zeros((1,K),int),np.cumsum(DC,0)])
def lastdays(a,b):  # conteos en dias ud-b .. ud-a
    hi=np.maximum(ud-a+1,0); lo=np.maximum(ud-b,0)
    return CUM[hi]-CUM[lo]
_fc={}
def decfreq(h):
    if h in _fc: return _fc[h]
    a=0.5**(1/h); c=np.ones(K); F=np.zeros((N,K))
    for t in range(N):
        F[t]=c/c.sum(); c*=a; c[y[t]]+=1
    _fc[h]=F; return F

def design(cfg):
    GM=cfg["gmax"]; blocks=[]; pen=[]; off=0
    g=np.minimum(G,GM)
    blocks.append(g-1); pen.append((0,GM)); off=GM
    blocks.append(np.minimum(S,2)+off); off+=3
    if cfg.get("dgap"):
        DM=cfg["dgap"]; blocks.append(np.minimum(D,DM)+off); pen.append((off+1,DM)); off+=DM+1
    for (a,b,cap) in cfg.get("win",[]):
        blocks.append(np.minimum(lastdays(a,b),cap)+off)
        if cfg.get("wpen"): pen.append((off,cap+1))
        off+=cap+1
    for (h,nb) in cfg.get("freq",[]):
        r=decfreq(h)*K
        edges=np.linspace(0.4,1.6,nb-1)
        blocks.append(np.searchsorted(edges,r)+off); pen.append((off,nb)); off+=nb
    return np.stack(blocks,-1), off, pen

def fit(X, yy, nf, pen, lam, w, theta0):
    T=X.shape[0]; rows=np.arange(T); ws=w/w.sum()
    flat=[X[:,:,j].ravel() for j in range(X.shape[2])]
    def f(th):
        s=th[X].sum(-1)
        m=s.max(1,keepdims=True); e=np.exp(s-m); Z=e.sum(1,keepdims=True); p=e/Z
        ll=s[rows,yy]-m[:,0]-np.log(Z[:,0])
        L=-(ws*ll).sum()
        gp=ws[:,None]*p; gp[rows,yy]-=ws
        gr=gp.ravel(); grad=np.zeros(nf)
        for fl in flat: grad+=np.bincount(fl, gr, nf)
        for (a,n) in pen:
            v=th[a:a+n]; d2=v[2:]-2*v[1:-1]+v[:-2]
            L+=lam*(d2**2).sum()
            gg=np.zeros(n); gg[2:]+=2*d2; gg[1:-1]-=4*d2; gg[:-2]+=2*d2
            grad[a:a+n]+=lam*gg
        L+=1e-4*(th**2).sum(); grad+=2e-4*th
        return L,grad
    return minimize(f, theta0, jac=True, method="L-BFGS-B", options={"maxiter":300}).x

def run(cfg, start=300, R=250):
    X,nf,pen=design(cfg); lam=cfg.get("lam",1e-2); hl=cfg.get("hl")
    P=np.zeros((N-W,K)); th=np.zeros(nf)
    for b in range(W,N,R):
        idx=np.arange(start,b)
        w=np.ones(len(idx)) if hl is None else 0.5**((b-idx)/hl)
        th=fit(X[idx],y[idx],nf,pen,lam,w,th)
        e=min(b+R,N); s=th[X[b:e]].sum(-1); p=np.exp(s-s.max(1,keepdims=True)); P[b-W:e-W]=p/p.sum(1,keepdims=True)
    return metricas(P,y[W:]), th

def show(name,m):
    print(f"{name:40s} T1 {m['top1']['tasa']*100:.2f} T3 {m['top3']['tasa']*100:.2f} {m['logver']['bits_por_sorteo']*1000:+.1f}mb q{[round(x*100,1) for x in m['top3_por_cuarto']]}",flush=True)

if __name__=="__main__":
    for cfg in json.loads(sys.argv[1]):
        t=time.time(); m,th=run(cfg); show(json.dumps(cfg),m); print("   %.1f s"%(time.time()-t))
        if cfg.get("print"): print(np.round(th,2))
