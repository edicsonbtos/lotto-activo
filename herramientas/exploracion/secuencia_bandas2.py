import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
SCR=sys.argv[1]
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]
oh=np.zeros((CORTE,K)); oh[np.arange(CORTE),seq]=1; C=np.vstack([np.zeros(K),np.cumsum(oh,0)])
def score(P,T,F):
    y=seq[T]; rows=np.arange(len(T))
    F=F-(P*F).sum(1,keepdims=True); return F[rows,y].sum()/np.sqrt((P*F*F).sum())
Pl=np.load(f"{SCR}/base_logit_final.npy"); Ph=np.load(f"{SCR}/base_hazard_actual.npy"); Pi=np.load(f"{SCR}/base_insample.npy")
T=np.arange(W,CORTE)
for nm,P,TT in [("logit",Pl,T),("hazard",Ph,T),("insample_dev",Pi[W:CORTE],T),("insample_warm[900,2000)",Pi[900:W],np.arange(900,W))]:
    print(nm, " ".join(f"{a}:{score(P,TT,C[TT-a]-C[TT-a-50]):+.1f}" for a in range(0,900,50)))
# por cuartos, banda [250,550)
for i,q in enumerate(np.array_split(np.arange(len(T)),4)):
    TT=T[q]; print("cuarto",i, round(score(Pl[q],TT,C[TT-250]-C[TT-550]),2), round(score(Pl[q],TT,C[TT]-C[TT-150]),2))
# uniforme como base (sin modelo): conteo banda
U=np.full((len(T),K),1/K)
print("uniforme", " ".join(f"{a}:{score(U,T,C[T-a]-C[T-a-50]):+.1f}" for a in range(0,900,50)))
