import sys, numpy as np, collections
sys.path.insert(0,"/home/user/lotto-activo"); sys.path.insert(0,"/home/user/lotto-activo/herramientas")
import lotto_eval as LE, prediccion as PR
sys.path.insert(0,"/home/user/lotto-activo/herramientas/modelos"); import exposicion as EX
D=LE.cargar("hist_full.txt"); S=np.asarray(D.seq); H=np.asarray(D.hora); F=D.fecha
z=np.load("wf_desde2000.npz"); P=z["P"]; d0=int(z["desde"]); n=len(S)
first=set()
seen=set()
for t in range(n):
    if F[t] not in seen: seen.add(F[t]); first.add(t)
V={k:[] for k in "ABCD"}   # filas: (t, rank del ganador, masa top15)
def rk(p,w):
    p=np.asarray(p,float); o=np.argsort(-p,kind="stable"); return int(np.nonzero(o==w)[0][0]), p[o[:15]].sum()
for t in range(d0,n):
    p=P[t-d0]; w=S[t]
    b=p
    if t in first:
        m,_=PR.ajuste_primer_sorteo(D.prefijo(t),F[t],int(H[t]))
        if m is not None: b=p*m; b=b/b.sum()
    c=EX.aplicar(b,F[t],int(H[t])); d=EX.aplicar_8am(b,F[t],int(H[t]))
    for k,q in zip("ABCD",(p,b,c,d)): V[k].append((t,)+rk(q,w))
np.save("sim15.npy",{k:np.array(v) for k,v in V.items()},allow_pickle=True)
print("ok", len(V["A"]))
