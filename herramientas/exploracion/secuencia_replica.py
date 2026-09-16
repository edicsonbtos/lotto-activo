# Replica en el calentamiento [200,2000): base logit_final ajustada in-sample en [200,CORTE)
import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
sys.path.insert(0,"modelos"); import logit_final as lf
SCR=sys.argv[1]
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
dd=d.prefijo(CORTE); seq=dd.seq
est,Pen,nm=lf.construir(dd,lf.CFG_FINAL); Pen=Pen+np.eye(Pen.shape[0])
b=lf.ajustar(est,slice(200,CORTE),seq[200:CORTE],np.ones(CORTE-200),Pen)
z=lf.logits(est,b,slice(0,CORTE)); z-=z.max(1,keepdims=True); P=np.exp(z); P/=P.sum(1,keepdims=True)
np.save(f"{SCR}/base_insample.npy",P)
num=np.array([0,0]+list(range(1,37))); dv=np.array([0,37]+list(range(1,37)))
col=np.where(np.arange(K)<2,3,(num-1)%3)
for a,bb in [(200,W),(W,CORTE)]:
    T=np.arange(a,bb); y=seq[T]; Pp=P[T]; L=seq[T-1]; rows=np.arange(len(T))
    f=(col[L]==2)[:,None]&(col==2)[None,:]
    o=f[rows,y].sum(); ee=(Pp*f).sum(); v=(Pp*(1-Pp)*f).sum()
    print(a,bb,"col2->col2 O=%d E=%.1f r=%.3f z=%+.2f"%(o,ee,o/ee,(o-ee)/np.sqrt(v)))
    for fam,cl in [("sameCol",lambda L:(col[L][:,None]==col[None,:])&(col[None,:]<3)),
                   ("dif1..4",lambda L:np.isin((dv[None,:]-dv[L][:,None])%K,[1,2,3,4])),
                   ("dif13..27",lambda L:np.isin((dv[None,:]-dv[L][:,None])%K,range(13,28)))]:
        f=cl(L); o=f[rows,y].sum(); ee=(Pp*f).sum(); v=(Pp*(1-Pp)*f).sum()
        print("   ",fam,"O=%d E=%.1f r=%.3f z=%+.2f"%(o,ee,o/ee,(o-ee)/np.sqrt(v)))
