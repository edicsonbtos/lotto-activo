import numpy as np
z=np.load("vivo_rk.npz",allow_pickle=True); rk=z["rk"]; t=z["t"]; f=z["f"]; h=z["h"]
seg={"dev":t<9357,"prueba":(t>=9357)&(f<"2026-09-15"),"vivo":f>="2026-09-15"}
rng=np.random.default_rng(0)
def ic(x,m):
    d=f[m]; u=sorted(set(d)); idx=np.searchsorted(u,d); s=np.bincount(idx,x[m]); c=np.bincount(idx)
    b=[s[j].sum()/c[j].sum() for j in (rng.integers(0,len(u),len(u)) for _ in range(1500))]
    return np.percentile(b,[2.5,97.5])
print("Top-N plano: acierto % y retorno por ficha (paga 30)")
for N in (10,12,15,17,19,20,22,25):
    hit=(rk<N).astype(float); roi=30*hit/N-1
    out=[]
    for s,m in seg.items():
        lo,hi=ic(roi,m) if s=="prueba" else (np.nan,np.nan)
        out.append(f"{s}: {hit[m].mean()*100:5.1f}% {roi[m].mean()*100:+5.1f}%"+(f" [{lo*100:+.1f};{hi*100:+.1f}]" if s=="prueba" else ""))
    print(f"  Top-{N:2d}  "+"   ".join(out))
