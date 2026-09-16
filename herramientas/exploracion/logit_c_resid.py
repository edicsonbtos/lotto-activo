import sys, os, importlib.util
H=r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas"; sys.path.insert(0,H)
import numpy as np, lotto_eval as L
spec=importlib.util.spec_from_file_location("m", H+"/modelos/logit_s.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d=L.cargar(); w,c=L.particion(len(d)); dd=d.prefijo(c)
M=m.Modelo(tau=3000); P=M.predecir(dd,w)
seq,ar,C,k,G,G2,DD,hoy=m._estado(dd)
sl=slice(w,c); n=c-w
Y=np.zeros((n,38)); Y[np.arange(n),seq[sl]]=1
G=G[sl];G2=G2[sl];DD=DD[sl];hoy=hoy[sl];kk=np.broadcast_to(k[sl][:,None],(n,38))
hora=np.broadcast_to(dd.hora[sl][:,None],(n,38)); dow=np.broadcast_to(dd.dow[sl][:,None],(n,38))
def rep(nombre, key, vals=None):
    out=[]
    for v in (np.unique(key) if vals is None else vals):
        msk=key==v
        o=Y[msk].sum(); e=P[msk].sum()
        if e>30: out.append(f"{v}:{o/e:.2f}({(o-e)/np.sqrt(e):+.1f})")
    print(nombre, " ".join(out))
rep("k", kk)
rep("hora", hora)
rep("dow", dow)
rep("DD", np.minimum(DD,10))
rep("G2", np.minimum(G2,40))
rep("hoy", hoy)
# gap del último día: veces que salió ayer
seq_all=seq; dia=dd.dia
# última hora de salida vs hora actual cuando DD==1
lastk=np.zeros((c,38),int); lk=np.zeros(38,int)
for t in range(c):
    lastk[t]=lk; lk[seq_all[t]]=k[t]
lastk=lastk[sl]
rep("DD1: lastk - k", np.where(DD==1, lastk-kk, 99))
rep("DD2: lastk - k", np.where(DD==2, lastk-kk, 99))
# ya salidos distintos hoy
dist=np.array([len(set(seq_all[t-k[t]:t])) for t in range(w,c)])
rep("repes hoy (k-distintos)", np.broadcast_to((k[sl]-dist)[:,None],(n,38)))
# calibración por decil de prob
q=np.quantile(P, np.linspace(0,1,11)); b=np.digitize(P,q[1:-1])
rep("decil P", b)
