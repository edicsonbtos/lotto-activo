import sys, numpy as np
from datetime import date
S=sys.argv[1]; z=np.load(S+"/prod_0605.npz",allow_pickle=True); P,t,y,f,h=z["P"],z["t"],z["y"],z["f"],z["h"]
o=np.argsort(-P,1,kind="stable"); rk=np.argmax(o==y[:,None],1)
dow=np.array([date.fromisoformat(d).weekday() for d in f]); mvf=np.isin(dow,[2,3,4])
fich=np.array([2,2,2,1,1]); gan=np.where(rk<5, 30*fich[np.minimum(rk,4)], 0)   # Top-5 escalonado, 8 fichas por sorteo, pago 30
def ret(m):
    r=gan[m]/8-1; ds=sorted(set(f[m])); per=np.array([r[f[m]==d].sum() for d in ds]); n=m.sum()
    rng=np.random.default_rng(0); b=[per[rng.integers(0,len(per),len(per))].sum()/n for _ in range(4000)]
    return f"{r.mean()*100:+5.1f}% por ficha [IC95 {np.percentile(b,2.5)*100:+.0f}; {np.percentile(b,97.5)*100:+.0f}]  Top-5 {np.mean(rk[m]<5)*100:.1f}%"
for lab,base in (("dev",t<9357),("2026",f>="2026-01-01")):
    print(f"{lab}: mié-vie {ret(base&mvf)}  |  sáb-mar {ret(base&~mvf)}")
