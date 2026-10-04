import numpy as np
z=np.load("vivo_rk.npz",allow_pickle=True); rk=z["rk"]; t=z["t"]; f=z["f"]; P=z["P"]
o=np.argsort(-P,1,kind="stable"); ps=np.take_along_axis(P,o,1)
seg={"dev":t<9357,"prueba":(t>=9357)&(f<"2026-09-15")}
for N in (5,15,20):
    hit=rk<N; mass=ps[:,:N].sum(1)
    run=np.zeros(len(hit),int)   # fallos seguidos ANTES del sorteo
    for i in range(1,len(hit)): run[i]=0 if hit[i-1] else run[i-1]+1
    print(f"Top-{N}: tasa real (y la que esperaba el motor) según los fallos seguidos previos")
    for s,m in seg.items():
        cells=[]
        for a,b,lab in ((0,0,"tras acierto"),(1,2,"1-2 fallos"),(3,5,"3-5"),(6,10,"6-10"),(11,999,">10")):
            mm=m&(run>=a)&(run<=b)
            if mm.sum()<30: continue
            cells.append(f"{lab}: {hit[mm].mean()*100:4.1f}% ({mass[mm].mean()*100:4.1f}) n={mm.sum()}")
        print(f"  {s:7s} "+" | ".join(cells))
    # día anterior bueno/malo
    dias=sorted(set(f)); r={d:hit[f==d].mean() for d in dias}
    prev=np.array([r.get(dias[max(0,dias.index(d)-1)]) for d in f])
    for s,m in seg.items():
        lo=m&(prev<=np.quantile(prev[m],0.25)); hi_=m&(prev>=np.quantile(prev[m],0.75))
        print(f"  {s:7s} día anterior flojo -> {hit[lo].mean()*100:.1f}%   día anterior bueno -> {hit[hi_].mean()*100:.1f}%")
