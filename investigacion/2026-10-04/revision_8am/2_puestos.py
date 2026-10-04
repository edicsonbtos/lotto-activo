import sys, json, numpy as np
sys.path.insert(0,"/home/user/lotto-activo"); sys.path.insert(0,"/home/user/lotto-activo/herramientas"); sys.path.insert(0,"/home/user/lotto-activo/herramientas/modelos")
import lotto_eval as LE, prediccion as PR, exposicion as EX
from datetime import date, timedelta
from scipy.stats import binom
D=LE.cargar("hist.txt"); S=np.asarray(D.seq); H=np.asarray(D.hora); F=np.array(D.fecha)
z=np.load("wf.npz"); P=z["P"].copy(); d0=int(z["desde"]); n=len(S)
POS=EX.POS
NOM="Delfín Ballena Carnero Toro Ciempiés Alacrán León Rana Perico Ratón Águila Tigre Gato Caballo Mono Paloma Zorro Oso Pavo Burro Chivo Cochino Gallo Camello Cebra Iguana Gallina Vaca Perro Zamuro Elefante Caimán Lapa Ardilla Pescado Venado Jirafa Culebra".split()
man=json.load(open("/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad/man.json"))
i8=[i for i in range(n) if F[i]=="2026-10-04" and H[i]==0][0]
print("validación 8am hoy: max|wf-base| =", np.abs(P[i8-d0]-np.array(man["base"])).max())
# B = con ajuste primer sorteo
first={}
for i in range(n): first.setdefault(F[i],(int(H[i]),int(S[i])))
B=P.copy()
for t in range(d0,n):
    if t>0 and F[t-1]==F[t]: continue
    f0=date.fromisoformat(F[t]); m=np.ones(38)
    for k,mu in PR.AJUSTE_PRIMER.items():
        x=first.get((f0-timedelta(days=k)).isoformat())
        if x and x[0]==H[t]: m[x[1]]*=mu
    q=B[t-d0]*m; B[t-d0]=q/q.sum()
C=np.array([EX.aplicar(B[t-d0],F[t],int(H[t])) for t in range(d0,n)])
np.savez("vers.npz",A=P,B=B,C=C)
t=np.arange(d0,n); y=S[t]; f=F[t]; h=H[t]
def rk(M):
    o=np.argsort(-M,1,kind="stable"); return np.argmax(o==y[:,None],1), np.take_along_axis(M,o[:,:15],1).sum(1)
rA,mA=rk(P); rB,mB=rk(B); rC,mC=rk(C)
print("\nÚltimos 2 días, puesto del ganador (1=favorito) A=motor sin ajuste, B=producción, C=+fecha/hora(sombra)")
for j in np.where(f>="2026-10-03")[0]:
    print(f"  {f[j]} {['8a','9a','10a','11a','12p','1p','2p','3p','4p','5p','6p','7p'][h[j]]:>3}  {POS[y[j]]:>2} {NOM[y[j]]:9} A:{rA[j]+1:2d} B:{rB[j]+1:2d} C:{rC[j]+1:2d}  {'TOP15' if rB[j]<15 else ''}")
v=f>="2026-09-15"
for nom,r,m in (("A",rA,mA),("B",rB,mB),("C",rC,mC)):
    k=(r[v]<15).sum(); N=v.sum(); print(f"\n{nom} vivo desde 15-sep: Top-15 {k}/{N}={k/N*100:.1f}% esperado {m[v].mean()*100:.1f}%  P={binom.cdf(k,N,m[v].mean()):.3f}")
    e8=v&(h==0); print(f"   8:00  {(r[e8]<15).sum()}/{e8.sum()}   resto {(r[v&(h>0)]<15).sum()}/{(v&(h>0)).sum()}")
print("\npor día (B):", " ".join(f"{d[5:]}:{(rB[v&(f==d)]<15).sum()}/{(v&(f==d)).sum()}" for d in sorted(set(f[v]))))
print("8:00 en vivo (B), puesto:", " ".join(f"{d[5:]}:{rB[v&(f==d)&(h==0)][0]+1}" for d in sorted(set(f[v])) if (v&(f==d)&(h==0)).any()))
# senal mbits
pw=np.log2(B[np.arange(len(t)),y]*38)*1000
print(f"\nseñal B vivo: {pw[v].mean():+.0f} mbits (azar 0)   prueba [9357,15sep): {pw[(t>=9357)&~v].mean():+.0f}")
for d in sorted(set(f[v]))[-7:]: print(f"  {d}: {pw[v&(f==d)].mean():+.0f} mbits")
