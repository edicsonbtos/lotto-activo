import sys, numpy as np
from scipy.optimize import minimize_scalar
S=sys.argv[1]; z=np.load(S+"/prod_0605.npz",allow_pickle=True); P,t,y,f=z["P"],z["t"],z["y"],z["f"]
def Q(T,m): q=P[m]**T; return q/q.sum(1,keepdims=True)
devA=(t>=2000)&(t<=5687); devB=(t>5687)&(t<9357); y26=f>="2026-01-01"; vivo=f>="2026-09-15"
T=minimize_scalar(lambda T:-np.log(Q(T,devA)[np.arange(devA.sum()),y[devA]]).sum(),bounds=(0.3,2),method="bounded").x
print(f"T elegido en dev-A: {T:.3f}")
for nm,m in (("dev-B",devB),("2026",y26),("vivo",vivo)):
    q=Q(T,m); p=P[m]; yy=y[m]; v=1000*np.log2(q[np.arange(len(yy)),yy]/p[np.arange(len(yy)),yy])
    ds=f[m]; u=sorted(set(ds)); per=np.array([v[ds==d].sum() for d in u]); cnt=np.array([np.sum(ds==d) for d in u])
    se=np.sqrt(((per-v.mean()*cnt)**2).sum()*len(u)/(len(u)-1))/len(v)
    o=np.argsort(-p,1,kind="stable"); real=np.mean(np.argmax(o==yy[:,None],1)<15)*100
    pr=np.take_along_axis(p,o[:,:15],1).sum(1).mean()*100; pq=np.take_along_axis(q,o[:,:15],1).sum(1).mean()*100
    Topt=minimize_scalar(lambda T2:-np.log((p**T2/(p**T2).sum(1,keepdims=True))[np.arange(len(yy)),yy]).sum(),bounds=(0.3,2),method="bounded").x
    print(f"{nm:6} Δmbits {v.mean():+5.2f} [{v.mean()-1.645*se:+5.2f};{v.mean()+1.645*se:+5.2f}] | Top-15 real {real:.1f}%  prometido {pr:.1f}% -> {pq:.1f}% | T óptimo de este tramo {Topt:.2f}")
