import numpy as np
z=np.load("vivo_rk.npz",allow_pickle=True); rk=z["rk"]; t=z["t"]; f=z["f"]
def plan(*w): a=np.zeros(38); a[:len(w)]=w; return a
E={"Top-1":plan(1),"Top-2":plan(1,1),"Top-3":plan(1,1,1),"2-1":plan(2,1),"3-2-1":plan(3,2,1),"2-2-1":plan(2,2,1),"2-2-1-1-1":plan(2,2,1,1,1),
   "2-2-2-1-1 (actual)":plan(2,2,2,1,1),"3-3-2-1":plan(3,3,2,1),"Top-4":plan(1,1,1,1),"Top-5":plan(1,1,1,1,1)}
dev=t<9357; pr=(t>=9357)&(f<"2026-09-15"); vi=f>="2026-09-15"
sem=np.array([x[:4]+("a" if x[5:7]<="06" else "b") for x in f])
print(f"{'reparto':20s} {'dev':>7s} {'prueba':>7s} {'vivo':>7s}   por semestre (retorno por ficha)")
res={}
for nom,w in E.items():
    g=30*w[rk]/w.sum()-1; res[nom]=g
    ss="  ".join(f"{s}:{g[sem==s].mean()*100:+4.0f}" for s in sorted(set(sem)))
    print(f"{nom:20s} {g[dev].mean()*100:+6.1f}% {g[pr].mean()*100:+6.1f}% {g[vi].mean()*100:+6.1f}%   {ss}")
d=res["Top-2"]-res["2-2-2-1-1 (actual)"]
rng=np.random.default_rng(1)
for nm,m in (("dev",dev),("prueba",pr)):
    u=sorted(set(f[m])); idx=np.searchsorted(u,f[m]); s=np.bincount(idx,d[m]); c=np.bincount(idx)
    b=[s[j].sum()/c[j].sum() for j in (rng.integers(0,len(u),len(u)) for _ in range(3000))]
    print(f"Top-2 menos actual, {nm}: {d[m].mean()*100:+.1f} pp por ficha, IC95 [{np.percentile(b,2.5)*100:+.1f}; {np.percentile(b,97.5)*100:+.1f}]")
