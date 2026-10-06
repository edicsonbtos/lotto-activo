import sys, numpy as np
from datetime import date
from scipy.stats import chi2
S=sys.argv[1]; z=np.load(S+"/prod_0605.npz",allow_pickle=True); P,t,y,f,h=z["P"],z["t"],z["y"],z["f"],z["h"]
o=np.argsort(-P,1,kind="stable"); rk=np.argmax(o==y[:,None],1); in15=rk<15; m15=np.take_along_axis(P,o[:,:15],1).sum(1)
dow=np.array([date.fromisoformat(d).weekday() for d in f]); nm="lun mar mié jue vie sáb dom".split()
for lab,m in (("dev (mar-24..dic-25)",t<9357),("2026 (ene..5-oct)",f>="2026-01-01")):
    O=np.array([in15[m&(dow==k)].sum() for k in range(7)]); E=np.array([m15[m&(dow==k)].sum() for k in range(7)]); V=np.array([(m15*(1-m15))[m&(dow==k)].sum() for k in range(7)])
    zz=(O-E)/np.sqrt(V); x2=(zz**2).sum(); p=chi2.sf(x2,7)
    mm=m&np.isin(dow,[2,3,4]); rr=m&~np.isin(dow,[2,3,4])
    print(f"{lab}: " + "  ".join(f"{nm[k]} O/E {O[k]/E[k]:.2f} (z{zz[k]:+.1f})" for k in range(7)) + f"\n   prueba conjunta 7 días: p = {p:.3f};  mié-vie {in15[mm].mean()*100:.1f}% vs resto {in15[rr].mean()*100:.1f}%")
