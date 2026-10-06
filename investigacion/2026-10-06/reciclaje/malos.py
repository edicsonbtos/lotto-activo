import sys, numpy as np
from datetime import date
sys.path.insert(0,"/home/user/lotto-activo/herramientas"); import lotto_eval as LE
S=sys.argv[1]; D=LE.cargar(S+"/hist_0605.txt"); YS=np.asarray(D.seq); FD=np.array(D.fecha)
z=np.load(S+"/prod_0605.npz",allow_pickle=True); P,t,y,f,h=z["P"],z["t"],z["y"],z["f"],z["h"]
o=np.argsort(-P,1,kind="stable"); rk=np.argmax(o==y[:,None],1); in15=rk<15; m15=np.take_along_axis(P,o[:,:15],1).sum(1)
fu=np.unique(FD); di={d:i for i,d in enumerate(fu)}; dn=np.array([di[x] for x in FD])
def back(T):
    w=YS[T]; p=np.where(YS[:T]==w)[0]; return (T-p[-1], dn[T]-dn[p[-1]]) if len(p) else (None,None)
rec=np.array([back(T)[1] in (1,2) for T in t])
POS=["0","00"]+[str(i) for i in range(1,37)]
N="Delfín Ballena Carnero Toro Ciempiés Alacrán León Rana Perico Ratón Águila Tigre Gato Caballo Mono Paloma Zorro Oso Pavo Burro Chivo Cochino Gallo Camello Cebra Iguana Gallina Vaca Perro Zamuro Elefante Caimán Lapa Ardilla Pescado Venado Jirafa Culebra".split()
hrs="8a 9a 10a 11a 12p 1p 2p 3p 4p 5p 6p 7p".split()
print("== domingo 4-oct ==")
for i in np.where(f=="2026-10-04")[0]:
    g,dd=back(t[i]); print(f"{hrs[h[i]]:4} {POS[y[i]]:>2} {N[y[i]]:9} puesto {rk[i]+1:2d}  salió hace {g} sorteos / {dd} d")
k=f=="2026-10-04"; print(f"Top-15 {in15[k].sum()}/12 (esperaba {m15[k].sum():.1f}); reciclados (ayer/anteayer) {rec[k].sum()}/12")
dias={}
for i,d in enumerate(f): dias.setdefault(d,[]).append(i)
ds=[d for d,v in dias.items() if len(v)==12 and d>="2026-01-01"]
H=np.array([in15[dias[d]].sum() for d in ds]); R=np.array([rec[dias[d]].sum() for d in ds]); E=np.array([m15[dias[d]].sum() for d in ds])
print(f"\n== 2026 ({len(ds)} días, {ds[0]}..{ds[-1]}) ==")
print(f"Top-15 por día: media {H.mean():.2f}/12 (motor esperaba {E.mean():.2f}); 4 o menos: {np.sum(H<=4)} días (1 cada {len(ds)/np.sum(H<=4):.1f}); 8 o más: {np.sum(H>=8)}")
rng=np.random.default_rng(0); sim=(rng.random((20000,len(ds),12))<np.array([m15[dias[d]] for d in ds])[None]).sum(2)
print(f"si el motor dijera la verdad, días ≤4 esperados: {np.mean(np.sum(sim<=4,1)):.1f} [{np.percentile(np.sum(sim<=4,1),2.5):.0f}-{np.percentile(np.sum(sim<=4,1),97.5):.0f}]")
print("distribución:", {int(k):int(np.sum(H==k)) for k in range(13) if np.sum(H==k)})
for lo,hi,lab in ((0,4,"malos ≤4"),(5,7,"normales 5-7"),(8,12,"buenos ≥8")):
    s=(H>=lo)&(H<=hi); print(f"  {lab:13} {s.sum():3d} días | reciclados {R[s].mean():.2f}/12")
# rachas de días malos
run=0; runs=[]
for x in H<=4:
    if x: run+=1
    elif run: runs.append(run); run=0
if run: runs.append(run)
print(f"rachas de días malos seguidos: {dict(zip(*np.unique(runs,return_counts=True)))}")
pares=[(a,b) for a,b in zip(range(len(ds)-1),range(1,len(ds))) if di[ds[b]]-di[ds[a]]==1]
a=np.array([H[i] for i,j in pares]); b=np.array([H[j] for i,j in pares])
print(f"día siguiente a un día malo: {b[a<=4].mean():.2f}/12 (n={np.sum(a<=4)}); tras normal/bueno: {b[a>4].mean():.2f}; corr {np.corrcoef(a,b)[0,1]:+.2f}")
dow=np.array([date.fromisoformat(d).weekday() for d in ds]); nm="lun mar mié jue vie sáb dom".split()
print("por día de semana (Top-15 medio / % días malos):", "  ".join(f"{nm[k]} {H[dow==k].mean():.1f}/{np.mean(H[dow==k]<=4)*100:.0f}%" for k in range(7)))
# por mes
mes=np.array([d[:7] for d in ds])
print("por mes:", "  ".join(f"{m[5:]}: {H[mes==m].mean():.1f}" for m in sorted(set(mes))))
