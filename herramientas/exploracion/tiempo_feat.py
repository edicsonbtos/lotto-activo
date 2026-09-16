import sys; sys.path.insert(0,'.')
import numpy as np
from lotto_eval import cargar, particion
d=cargar(); seq=d.seq; n=len(seq); w,corte=particion(n); K=38
last=np.full(K,-1); cnt_today=np.zeros(K,int)
H=np.zeros((101,3)); X=np.zeros((101,3))
for t in range(corte):
    if t>0 and d.dia[t]!=d.dia[t-1]: cnt_today[:]=0
    g=np.where(last>=0,np.minimum(t-last,100),100)
    c=np.minimum(cnt_today,2)
    np.add.at(X,(g,c),1); H[g[seq[t]],c[seq[t]]]+=1
    last[seq[t]]=t; cnt_today[seq[t]]+=1
R=H/np.maximum(X,1)*K
for g in range(1,61): print(g, ' '.join(f'{R[g,c]:.2f}({int(H[g,c])})' for c in range(3)))
