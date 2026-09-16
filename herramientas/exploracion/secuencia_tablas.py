import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
SCR=sys.argv[1]; BASE=sys.argv[2]
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; P=np.load(f"{SCR}/base_{BASE}.npy"); n=len(P); T=np.arange(W,CORTE); y=seq[W:]
num=np.array([0,0]+list(range(1,37))); dv=np.array([0,37]+list(range(1,37)))
rows=np.arange(n)
def tabla(A,B,ka,kb,L,name):
    O=np.zeros((ka,kb));E=np.zeros((ka,kb));V=np.zeros((ka,kb))
    ca=A[L]; np.add.at(O,(ca,B[y]),1)
    for c in range(K):
        np.add.at(E[:,B[c]],ca,P[:,c]); np.add.at(V[:,B[c]],ca,P[:,c]*(1-P[:,c]))
    print(name); print("ratio\n",np.round(O/E,3)); print("z\n",np.round((O-E)/np.sqrt(V),1))
col=np.where(np.arange(K)<2,3,(num-1)%3); doc=np.where(np.arange(K)<2,3,(num-1)//12)
alto=np.where(np.arange(K)<2,2,(num>18).astype(int)); fila=np.where(np.arange(K)<2,12,(num-1)//3)
tercio=np.where(np.arange(K)<2,3,(num-1)//12)
for k in (1,2,3):
    L=seq[T-k]
    tabla(col,col,4,4,L,f"col lag{k}")
    tabla(alto,alto,3,3,L,f"alto lag{k}")
    tabla(doc,doc,4,4,L,f"docena lag{k}")
for k in (1,2):
    L=seq[T-k]; r=[];z=[]
    for m in range(K):
        f=((dv[None,:]-dv[L][:,None])%K)==m
        o=f[rows,y].sum(); ee=(P*f).sum(); v=(P*(1-P)*f).sum(); r.append(o/ee); z.append((o-ee)/np.sqrt(v))
    print("difval lag",k," ".join(f"{m}:{zz:+.1f}" for m,zz in enumerate(z)))
