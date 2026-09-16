# Score test: conteo del candidato en bandas de retraso [a,b) frente a la base walk-forward
import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
SCR=sys.argv[1]; BASE=sys.argv[2]; BW=int(sys.argv[3])
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; P=np.load(f"{SCR}/base_{BASE}.npy"); n=len(P); T=np.arange(W,CORTE); y=seq[W:]
oh=np.zeros((CORTE,K)); oh[np.arange(CORTE),seq]=1; C=np.vstack([np.zeros(K),np.cumsum(oh,0)])
rows=np.arange(n)
def score(F):
    F=F-(P*F).sum(1,keepdims=True)   # centrado por fila
    s=F[rows,y].sum(); v=(P*F*F).sum(); return s/np.sqrt(v)
out=[]
for a in range(0,W-BW+1,BW):
    b=a+BW
    F=C[T-a]-C[T-b]
    z=score(F); zq=[score_q for score_q in []]
    out.append((a,b,z))
print(" ".join(f"[{a},{b}):{z:+.1f}" for a,b,z in out))
for w in [100,200,336,500,672,800,1000,1344,1600,2000]:
    print(w, round(score(C[T]-C[T-w]),2), end=" | ")
print()
