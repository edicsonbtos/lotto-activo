# Nula por permutación de días completos (preserva la exclusión intradía): z del conteo en banda [250,550) vs uniforme
import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq0=d.seq[:CORTE]; dia=d.dia[:CORTE]
bl=np.split(np.arange(CORTE), np.flatnonzero(np.diff(dia))+1)
def z(seq,a=250,b=550):
    oh=np.zeros((CORTE,K)); oh[np.arange(CORTE),seq]=1; C=np.vstack([np.zeros(K),np.cumsum(oh,0)])
    T=np.arange(W,CORTE); F=C[T-a]-C[T-b]; F=F-F.mean(1,keepdims=True)
    return F[np.arange(len(T)),seq[T]].sum()/np.sqrt((F*F).sum()/K)
rng=np.random.default_rng(0); obs=z(seq0)
nul=[]
for i in range(200):
    o=rng.permutation(len(bl)); s=np.concatenate([seq0[bl[j]] for j in o]); nul.append(z(s))
nul=np.array(nul); print("obs",obs,"nula media",nul.mean(),"sd",nul.std(),"p",(1+np.sum(nul<=obs))/201)
