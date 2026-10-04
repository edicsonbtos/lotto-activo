import numpy as np
z=np.load("vivo_rk.npz",allow_pickle=True); rk=z["rk"]; t=z["t"]; f=z["f"]; h=z["h"]; P=z["P"]
o=np.argsort(-P,1,kind="stable"); ps=np.take_along_axis(P,o,1); n=len(rk)
dev=t<9357; pr=(t>=9357)&(f<"2026-09-15")
def plan(*w): a=np.zeros(38); a[:len(w)]=w; return a
E={"Top-2":plan(1,1),"Top-5 escal.":plan(2,2,2,1,1),"Top-15":plan(*[1]*15)}
G={k:30*w[rk]/w.sum()-1 for k,w in E.items()}
def roll(x,w):   # media de los w sorteos ANTERIORES (sin incluir el actual)
    c=np.r_[0,np.cumsum(x)]; i=np.arange(n); lo=np.maximum(0,i-w); r=(c[i]-c[lo])/np.maximum(1,i-lo); r[:w]=np.nan; return r
hit15=(rk<15).astype(float); exp15=ps[:,:15].sum(1)
I={"aciertos Top-15 últimos 12":roll(hit15,12),"aciertos Top-15 últimos 36":roll(hit15,36),"aciertos Top-15 últimos 120":roll(hit15,120),
   "aciertos Top-2 últimos 120":roll((rk<2).astype(float),120),"Top-15 real−esperado últimos 120":roll(hit15-exp15,120),
   "confianza p1+p2 ahora":ps[:,:2].sum(1),"confianza masa Top-5 ahora":ps[:,:5].sum(1),"confianza masa Top-15 ahora":exp15}
rng=np.random.default_rng(2)
def dif_ic(g,a,b,m):
    d=f[m]; u=sorted(set(d)); idx=np.searchsorted(u,d)
    sa=np.bincount(idx,g[m]*a[m],len(u)); ca=np.bincount(idx,a[m].astype(float),len(u))
    sb=np.bincount(idx,g[m]*b[m],len(u)); cb=np.bincount(idx,b[m].astype(float),len(u))
    bs=[]
    for _ in range(1000):
        j=rng.integers(0,len(u),len(u)); bs.append(sa[j].sum()/ca[j].sum()-sb[j].sum()/cb[j].sum())
    return np.percentile(bs,[2.5,97.5])
for nom,x in I.items():
    q1,q2=np.nanquantile(x[dev],[1/3,2/3])
    frio=x<=q1; cal=x>q2
    linea=[]
    for e,g in G.items():
        s=[]
        for sn,m in (("dev",dev),("prueba",pr)):
            m=m&~np.isnan(x)
            s.append(f"{g[m&frio].mean()*100:+4.0f}/{g[m&cal].mean()*100:+4.0f}")
        lo,hi=dif_ic(g,cal,frio,pr&~np.isnan(x))
        linea.append(f"{e}: dev {s[0]} prueba {s[1]} [dif {lo*100:+.0f};{hi*100:+.0f}]")
    print(f"{nom}  (frío/caliente)\n   "+"\n   ".join(linea))
# hora del día
print("Por hora (retorno prueba): ", "  ".join(f"{j}:{G['Top-2'][pr&(h==j)].mean()*100:+.0f}/{G['Top-5 escal.'][pr&(h==j)].mean()*100:+.0f}/{G['Top-15'][pr&(h==j)].mean()*100:+.0f}" for j in range(12)))
print("Por hora (retorno dev):    ", "  ".join(f"{j}:{G['Top-2'][dev&(h==j)].mean()*100:+.0f}/{G['Top-5 escal.'][dev&(h==j)].mean()*100:+.0f}/{G['Top-15'][dev&(h==j)].mean()*100:+.0f}" for j in range(12)))
