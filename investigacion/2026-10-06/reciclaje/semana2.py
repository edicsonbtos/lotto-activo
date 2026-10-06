import sys, numpy as np
from datetime import date
sys.path.insert(0,"/home/user/lotto-activo/herramientas"); import lotto_eval as LE
S=sys.argv[1]; D=LE.cargar(S+"/hist_0605.txt"); YS=np.asarray(D.seq); FD=np.array(D.fecha)
z=np.load(S+"/prod_0605.npz",allow_pickle=True); P,t,y,f,h=z["P"],z["t"],z["y"],z["f"],z["h"]
o=np.argsort(-P,1,kind="stable"); rk=np.argmax(o==y[:,None],1); in15=rk<15; m15=np.take_along_axis(P,o[:,:15],1).sum(1)
fu=np.unique(FD); di={d:i for i,d in enumerate(fu)}; dn=np.array([di[x] for x in FD])
prev2=[np.unique(YS[(dn>=dn[T]-2)&(dn<dn[T])]) for T in t]
rec=np.array([y[i] in prev2[i] for i in range(len(t))]); prec=np.array([P[i,prev2[i]].sum() for i in range(len(t))])
dow=np.array([date.fromisoformat(d).weekday() for d in f]); mvf=np.isin(dow,[2,3,4])
def fila(lab,m):
    a=m&mvf; b=m&~mvf
    print(f"{lab:22} mié-vie Top-15 O/E {in15[a].sum()/m15[a].sum():.2f} | resto {in15[b].sum()/m15[b].sum():.2f} || reciclados O/E mié-vie {rec[a].sum()/prec[a].sum():.2f}, resto {rec[b].sum()/prec[b].sum():.2f}  (n días mié-vie {len(set(f[a]))})")
for lab,lo,hi in (("dev 2024","2024-01-01","2024-12-31"),("dev 2025-S1","2025-01-01","2025-06-30"),("dev 2025-S2","2025-07-01","2025-12-31"),
                  ("2026 ene-mar","2026-01-01","2026-03-31"),("2026 abr-jun","2026-04-01","2026-06-30"),("2026 jul-oct","2026-07-01","2026-10-05")):
    fila(lab,(f>=lo)&(f<=hi))
m=(f>="2026-01-01")
for k,nm in zip((2,3,4),("mié","jue","vie")):
    a=m&(dow==k); print(f"2026 {nm}: Top-15 {in15[a].mean()*100:.1f}% (esperaba {m15[a].mean()*100:.1f}) | reciclados {rec[a].mean()*100:.1f}% (motor {prec[a].mean()*100:.1f})")
a=m&~mvf; print(f"2026 resto: Top-15 {in15[a].mean()*100:.1f}% (esperaba {m15[a].mean()*100:.1f}) | reciclados {rec[a].mean()*100:.1f}% (motor {prec[a].mean()*100:.1f})")
