import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; dia=d.dia[:CORTE]; hora=d.hora[:CORTE]; n=len(seq)
nuevo=np.r_[True,dia[1:]!=dia[:-1]]
T=np.zeros((3,12,2));Hh=np.zeros((3,12,2))
cnt=np.zeros(K,int); rep=0
for t in range(n):
    if nuevo[t]: cnt[:]=0; rep=0
    per=min(3*t//n,2)
    today=cnt>0
    nt=today.sum()
    if nt: T[per,hora[t],min(rep,1)]+=nt; Hh[per,hora[t],min(rep,1)]+=today[seq[t]]
    if cnt[seq[t]]>0: rep+=1
    cnt[seq[t]]+=1
np.set_printoptions(precision=2,suppress=True,linewidth=200)
for per in range(3):
    print("per",per); print(" sin rep previo:",Hh[per,:,0]/np.maximum(T[per,:,0],1)*K); print(" con rep previo:",Hh[per,:,1]/np.maximum(T[per,:,1],1)*K, T[per,:,1].astype(int))
