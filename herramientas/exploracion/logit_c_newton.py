import sys, os, time, importlib.util
H=r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas"; sys.path.insert(0,H)
import numpy as np, lotto_eval as L
spec=importlib.util.spec_from_file_location("m", H+"/modelos/logit_c.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d=L.cargar(); w,c=L.particion(len(d)); dd=d.prefijo(c)
tb,D,_=m.construir(dd,{})
T=c; sl=slice(200,T); N=T-200
cols=[]
for nm,ix,s in tb:
    oh=np.zeros((N,38,s),np.float32); ii=ix[sl]
    np.put_along_axis(oh, ii[:,:,None], 1, axis=2); cols.append(oh[:,:,1:])
X=np.concatenate(cols+[D[sl]],axis=2); dim=X.shape[2]; print(X.shape)
y=dd.seq[sl]; Xf=X.reshape(-1,dim); Xy=X[np.arange(N),y].astype(np.float64).mean(0)
lam=3e-5
t0=time.time(); b=np.zeros(dim)
for it in range(10):
    z=(Xf@b.astype(np.float32)).reshape(N,38).astype(np.float64)
    z-=z.max(1,keepdims=True); e=np.exp(z); S=e.sum(1,keepdims=True); p=e/S
    ll=-(z[np.arange(N),y]-np.log(S[:,0])).mean()+0.5*lam*b@b
    pf=(p/N).astype(np.float32).reshape(-1)
    g=(pf@Xf).astype(np.float64)-Xy+lam*b
    Mbar=np.einsum('nk,nkd->nd',p.astype(np.float32),X).astype(np.float64)
    Hs=((Xf*pf[:,None]).T@Xf).astype(np.float64) - (Mbar.T@Mbar)/N + lam*np.eye(dim)
    step=np.linalg.solve(Hs,g); b=b-step
    print(it, ll, np.abs(g).max(), time.time()-t0)
