import numpy as np
from scipy.stats import binom
z=np.load("vivo_rk.npz",allow_pickle=True); rk=z["rk"]; t=z["t"]; f=z["f"]; P=z["P"]
o=np.argsort(-P,1,kind="stable"); ps=np.take_along_axis(P,o,1)    # probs ordenadas
print(f"vivo total P(<=100/225 | 51,6%) = {binom.cdf(100,225,0.516):.3f};  P(<=100/225 | 49,5% de prueba) = {binom.cdf(100,225,0.495):.3f}")
def plan(*tr):
    w=np.zeros(38)
    for a,b,k in tr: w[a-1:b]=k
    return w
E={"Top-1":plan((1,1,1)),"Top-2":plan((1,2,1)),"Top-3":plan((1,3,1)),"Top-4":plan((1,4,1)),"Top-5":plan((1,5,1)),
   "Top-5 escalonado 2-2-2-1-1":plan((1,3,2),(4,5,1)),"Top-8":plan((1,8,1)),"Top-10":plan((1,10,1)),
   "Top-15 plano":plan((1,15,1)),"Top-15 ponderado 3-2-1":plan((1,3,3),(4,5,2),(6,15,1)),"Top-20":plan((1,20,1))}
seg={"dev":t<9357,"prueba":(t>=9357)&(f<"2026-09-15"),"vivo":f>="2026-09-15"}
rng=np.random.default_rng(3)
def roi(w):  # retorno por ficha de cada sorteo
    return 30*w[rk]/w.sum()-1
def roi_var(kind,thr):
    # fichas proporcionales a p (top-k) o planas a los p>thr
    if kind=="prop":
        W=np.where(np.arange(38)[None,:]<thr, ps, 0)
    else:
        W=(ps>thr).astype(float)
    tot=W.sum(1); g=np.where(tot>0, 30*W[np.arange(len(rk)),rk]/np.maximum(tot,1e-12)-1, np.nan)
    return g
res={}
for nom,w in E.items(): res[nom]=roi(w)
for k in (5,10): res[f"proporcional a p, Top-{k}"]=roi_var("prop",k)
for th in (1/30,0.036,0.04): res[f"valor: todos con p>{th*100:.1f}%"]=roi_var("val",th)
print(f"\n{'estrategia':34s} {'dev':>8s} {'prueba [IC95]':>22s} {'vivo':>8s}  %sorteos jugados")
for nom,g in res.items():
    out=[]
    for s,m in seg.items():
        x=g[m]; x=x[~np.isnan(x)]
        if s=="prueba":
            dias=f[m][~np.isnan(g[m])]; u=sorted(set(dias)); idx={d:i for i,d in enumerate(u)}
            per=np.zeros(len(u)); cnt=np.zeros(len(u))
            np.add.at(per,[idx[d] for d in dias],x); np.add.at(cnt,[idx[d] for d in dias],1)
            bs=[]
            for _ in range(2000):
                j=rng.integers(0,len(u),len(u)); bs.append(per[j].sum()/cnt[j].sum())
            out.append(f"{x.mean()*100:+6.1f}% [{np.percentile(bs,2.5)*100:+5.1f};{np.percentile(bs,97.5)*100:+5.1f}]")
        else: out.append(f"{x.mean()*100:+6.1f}%")
    jug=np.mean(~np.isnan(g[seg['prueba']]))*100
    print(f"{nom:34s} {out[0]:>8s} {out[1]:>22s} {out[2]:>8s}  {jug:5.0f}%")
