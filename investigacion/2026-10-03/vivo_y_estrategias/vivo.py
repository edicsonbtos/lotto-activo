import sys, numpy as np, collections, math
sys.path.insert(0,"/home/user/lotto-activo"); sys.path.insert(0,"/home/user/lotto-activo/herramientas")
import lotto_eval as LE, prediccion as PR
from scipy.stats import binom
D=LE.cargar("hist_hoy.txt"); S=np.asarray(D.seq); H=np.asarray(D.hora); F=np.array(D.fecha)
z=np.load("wf_hoy.npz"); P=z["P"]; d0=int(z["desde"]); n=len(S)
t=np.arange(d0,n); y=S[t]; f=F[t]; h=H[t]
o=np.argsort(-P,1,kind="stable"); rk=np.argmax(o==y[:,None],1)
mass15=np.take_along_axis(P,o[:,:15],1).sum(1)
v=f>="2026-09-15"
hit=rk<15
print(f"VIVO desde 15-sep: {v.sum()} sorteos. Top-15 {hit[v].sum()}/{v.sum()} = {hit[v].mean()*100:.1f}%  (motor esperaba {mass15[v].mean()*100:.1f}%)")
for a,b in (("2026-09-15","2026-09-24"),("2026-09-25","2026-10-03"),("2026-09-27","2026-10-03"),("2026-09-30","2026-10-03")):
    m=v&(f>=a)&(f<=b); k=hit[m].sum(); N=m.sum(); e=mass15[m].mean()
    print(f"  {a}..{b}: {k}/{N} = {k/N*100:.1f}%   esperado {e*100:.1f}%   P(tan bajo o menos | motor) = {binom.cdf(k,N,e):.3f}")
print("  por día:", " ".join(f"{d[5:]}:{hit[v&(f==d)].sum()}/{(v&(f==d)).sum()}" for d in sorted(set(f[v]))))
# ¿qué tan seguido una racha de 7 días baja así en prueba?
pr=(t>=9357)&(f<"2026-09-15"); dias=sorted(set(f[pr])); tasa=[hit[pr&(f==d)].mean() for d in dias]; cnt=[(pr&(f==d)).sum() for d in dias]
w7=[sum(hit[pr&(f==d)].sum() for d in dias[i:i+7])/sum(cnt[i:i+7]) for i in range(len(dias)-6)]
print(f"  En prueba (dic-25..sep-26), ventanas de 7 días con Top-15 <= 45%: {np.mean(np.array(w7)<=0.45)*100:.0f}% de las ventanas; peor {min(w7)*100:.0f}%, mejor {max(w7)*100:.0f}%")
np.savez("vivo_rk.npz", rk=rk, t=t, f=f, h=h, P=P)
