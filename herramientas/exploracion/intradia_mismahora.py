import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; dia=d.dia[:CORTE]; hora=d.hora[:CORTE]; n=len(seq)
nuevo=np.r_[True,dia[1:]!=dia[:-1]]; didx=np.cumsum(nuevo)-1
# LH[h][i] = lista de días en que i salió a la hora h
last_at=np.full((12,K),-100)   # último día en que i salió a hora h
Tl=np.zeros(12);Hl=np.zeros(12); cnt=np.zeros(K,int)
T=np.zeros(9);Hh=np.zeros(9)
for t in range(n):
    if nuevo[t]: cnt[:]=0
    elig=cnt==0; h=hora[t]; dd=didx[t]-last_at[h]
    b=np.where(elig, np.minimum(dd,8), 0)  # 1..7 días, 8=+ ; 0 = no elegible
    Tl[h]+=elig.sum(); Hl[h]+=elig[seq[t]]
    for j in range(1,9):
        m=b==j; T[j]+=m.sum()/ (elig.sum()) ; Hh[j]+=m[seq[t]]
    v=seq[t]; last_at[h,v]=didx[t]; cnt[v]+=1
print("dias desde misma hora -> ratio obs/esperado (entre elegibles):", np.round(Hh[1:]/T[1:],3), Hh[1:].astype(int))
