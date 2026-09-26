# Chequeo independiente: tasa cruda de "sucesor de s1" (sin ensamble) en desarrollo, y por mitades
import os, sys, numpy as np
V=os.path.dirname(os.path.abspath(__file__)); MN=os.path.dirname(os.path.dirname(V)); sys.path.insert(0,MN)
import arnes as A
D=A.datos().prefijo(A.CORTE); s=np.asarray(D.seq)
P,y=A.base(); P=P/P.sum(1,keepdims=True)
last={}
o=e=n=0; res=[]
for t in range(1,A.CORTE):
    a=s[t-1]
    if t>=A.W and a in last and last[a]+1<t-1:
        c=s[last[a]+1]; j=t-A.W
        res.append((j, s[t]==c, P[j,c]))
    # actualizar ocurrencia anterior de s[t-1]: registrar posicion t-1
    last[a]=t-1
r=np.array(res,float); h=A.CORTE-A.W
for nom,m in (("todo",r[:,0]>=0),("m1",r[:,0]<h/2),("m2",r[:,0]>=h/2)):
    O=r[m,1].sum(); E=r[m,2].sum(); print(nom,"n",int(m.sum()),"O",int(O),"E_ens %.1f"%E,"O/E %.3f"%(O/E),"z %.2f"%((O-E)/np.sqrt(E)),"base 1/38 %.1f"%(m.sum()/38))
