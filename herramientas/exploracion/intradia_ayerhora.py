import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; dia=d.dia[:CORTE]; hora=d.hora[:CORTE]; n=len(seq)
nuevo=np.r_[True,dia[1:]!=dia[:-1]]
T=np.zeros((12,12));H=np.zeros((12,12)); Tl=np.zeros(12); Hl=np.zeros(12)
lasth=np.full(K,-1); lastday=np.full(K,-10); day=-1; cnt=np.zeros(K,int)
prevh=np.full(K,-1)  # hora ayer
for t in range(n):
    if nuevo[t]:
        day+=1; cnt[:]=0
    elig=(cnt==0)
    y_mask=(lastday==day-1)&elig
    for i in np.where(y_mask)[0]:
        T[hora[t],lasth[i]]+=1; H[hora[t],lasth[i]]+=(seq[t]==i)
    # rate among eligible (not today) baseline
    Tl[hora[t]]+=elig.sum(); Hl[hora[t]]+=elig[seq[t]]
    v=seq[t]; lasth[v]=hora[t]; lastday[v]=day; cnt[v]+=1
base=Hl/Tl
np.set_printoptions(precision=2,suppress=True,linewidth=200)
R=H/np.maximum(T,1)/base[:,None]
print("filas: hora hoy, cols: hora de salida ayer (relativo a elegibles)"); print(R)
print("diag", np.mean([R[h,h] for h in range(1,12)]), "fuera", np.mean(R[1:,1:][~np.eye(11,dtype=bool)]))
print("n diag", sum(H[h,h] for h in range(12)), sum(T[h,h] for h in range(12)))
