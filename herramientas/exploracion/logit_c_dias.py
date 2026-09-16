import sys; sys.path.insert(0,r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas")
import numpy as np, lotto_eval as L
d=L.cargar(); w,c=L.particion(len(d)); seq=d.seq[:c]; dia=d.dia[:c]
days={}
for s,dd in zip(seq,dia): days.setdefault(dd,[]).append(s)
keys=sorted(days); sets=[set(days[k]) for k in keys]; lens=[len(days[k]) for k in keys]
ov=[len(sets[i]&sets[i-1]) for i in range(1,len(sets)) if lens[i]==12 and lens[i-1]==12]
rng=np.random.default_rng(0)
idx=[i for i in range(len(sets)) if lens[i]==12]
ovr=[len(sets[rng.choice(idx)]&sets[rng.choice(idx)]) for _ in range(20000)]
print("overlap consecutive mean",np.mean(ov),"var",np.var(ov),"| random pairs",np.mean(ovr),np.var(ovr))
print("dist",np.bincount(ov,minlength=9)/len(ov)); print("rand",np.bincount(ovr,minlength=9)/len(ovr))
ov2=[len(sets[i]&sets[i-2]) for i in range(2,len(sets)) if lens[i]==12 and lens[i-2]==12]
print("lag2",np.mean(ov2))
ov3=[len(sets[i]&(sets[i-1]|sets[i-2])) for i in range(2,len(sets)) if lens[i]==12]
ovr3=[len(sets[rng.choice(idx)]&(sets[rng.choice(idx)]|sets[rng.choice(idx)])) for _ in range(20000)]
print("vs union last2",np.mean(ov3),np.var(ov3),"rand",np.mean(ovr3),np.var(ovr3))
# by periods
half=len(ov)//2; print("overlap early/late", np.mean(ov[:half]), np.mean(ov[half:]), np.mean(ov[-150:]))
