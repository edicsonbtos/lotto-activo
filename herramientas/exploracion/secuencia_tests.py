# Pruebas de residuos secuenciales frente a un modelo base walk-forward (solo tramo desarrollo).
# Nula condicional: y*_t ~ P_base[t] (preserva toda la exclusión que captura el modelo base).
import sys,os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
from scipy.stats import norm
SCR=sys.argv[1]; BASE=sys.argv[2] if len(sys.argv)>2 else "logit_final"
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); K=38
seq=d.seq[:CORTE]; hora=d.hora[:CORTE]; dow=d.dow[:CORTE]; dia=d.dia[:CORTE]
P=np.load(f"{SCR}/base_{BASE}.npy"); n=len(P); T=np.arange(W,CORTE); y=seq[W:]
POS=e.POS
val=np.array([0,37]+list(range(1,37)))           # circulo 0,1..36,00
num=np.array([0,0]+list(range(1,37)))
RED={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
color=np.array([2 if i<2 else (0 if num[i] in RED else 1) for i in range(K)])
WHEEL=["0","28","9","26","30","11","7","20","32","17","5","22","34","15","3","24","36","13","1","00","27","10","25","29","12","8","19","31","18","6","21","33","16","4","23","35","14","2"]
wpos=np.zeros(K,int)
for j,s in enumerate(WHEEL): wpos[e.IDX[s]]=j
par=np.where(np.arange(K)<2,2,num%2)
docena=np.where(np.arange(K)<2,3,(num-1)//12)
columna=np.where(np.arange(K)<2,3,(num-1)%3)
term=np.where(np.arange(K)<2,10,num%10)
alto=np.where(np.arange(K)<2,2,(num>18).astype(int))
cand=np.arange(K)[None,:]

def lag(k): return seq[T-k]
# indice del sorteo misma hora dia anterior (y hace 2 dias, 7 dias)
key={(dia[i],hora[i]):i for i in range(CORTE)}
def mismahora(dd, dh=0):
    r=np.full(n,-1)
    for j,t in enumerate(T):
        i=key.get((dia[t]-dd,hora[t]+dh))
        if i is not None and i<t: r[j]=seq[i]
    return r

fam={}   # nombre -> matriz de clase (n,K) con -1 = sin clase
def circ(a,b,m=K): return (a-b)%m
for k in (1,2,3,4):
    L=lag(k)
    fam[f"difval_lag{k}"]=circ(val[None,:],val[L][:,None])
    fam[f"difwheel_lag{k}"]=circ(wpos[None,:],wpos[L][:,None])
    fam[f"trans_lag{k}"]=L[:,None]*K+cand        # tabla completa 38x38
    fam[f"color_lag{k}"]=color[L][:,None]*3+color[None,:]
    fam[f"par_lag{k}"]=par[L][:,None]*3+par[None,:]
    fam[f"docena_lag{k}"]=docena[L][:,None]*4+docena[None,:]
    fam[f"columna_lag{k}"]=columna[L][:,None]*4+columna[None,:]
    fam[f"term_lag{k}"]=term[L][:,None]*11+term[None,:]
    fam[f"alto_lag{k}"]=alto[L][:,None]*3+alto[None,:]
L1,L2=lag(1),lag(2)
fam["difval_2orden"]=circ(val[None,:],val[L1][:,None])*K+circ(val[L1],val[L2])[:,None]
fam["suma2_mod38"]=((val[L1]+val[L2])[:,None]-val[None,:])%K
fam["suma2_mod10_term"]=((num[L1]+num[L2])%10)[:,None]*11+term[None,:]
for dd,dh,nm in [(1,0,"ayer_h"),(1,-1,"ayer_hm1"),(1,1,"ayer_hp1"),(2,0,"anteayer_h"),(7,0,"semana_h")]:
    M=mismahora(dd,dh); ok=(M>=0)[:,None]
    fam[f"dif_{nm}"]=np.where(ok,circ(val[None,:],val[np.maximum(M,0)][:,None]),-1)
    fam[f"difwheel_{nm}"]=np.where(ok,circ(wpos[None,:],wpos[np.maximum(M,0)][:,None]),-1)
fam["dow_x_num"]=np.broadcast_to(dow[T][:,None]*K+cand,(n,K))
fam["hora_x_num"]=np.broadcast_to(hora[T][:,None]*K+cand,(n,K))
fam["num"]=np.broadcast_to(cand,(n,K))
fam["color_run2"]=(color[L1]*3+color[L2])[:,None]*3+color[None,:]
fam["par_run2"]=(par[L1]*3+par[L2])[:,None]*3+par[None,:]
fam["docena_run2"]=(docena[L1]*4+docena[L2])[:,None]*4+docena[None,:]

rng=np.random.default_rng(1)
NB=300
cP=np.cumsum(P,1); cP[:,-1]=1.0
Ys=[np.minimum((cP<rng.random((n,1))).sum(1),K-1) for _ in range(NB)]
rows=np.arange(n)
res=[]; clases=[]
for nm,C in fam.items():
    C=np.asarray(C); M=int(C.max())+1
    valid=C>=0; Cc=np.where(valid,C,0)
    E=np.bincount(Cc.ravel(),weights=(P*valid).ravel(),minlength=M)
    V=np.bincount(Cc.ravel(),weights=(P*valid).ravel(),minlength=M)  # aprox; exacto abajo
    def obs(yy):
        c=C[rows,yy]; return np.bincount(c[c>=0],minlength=M)
    O=obs(y); keep=E>5
    def x2(o): return np.sum((o[keep]-E[keep])**2/E[keep])
    s=x2(O); sb=np.array([x2(obs(yy)) for yy in Ys])
    pb=(1+np.sum(sb>=s))/(NB+1)
    Ob=np.array([obs(yy) for yy in Ys]); sd=Ob.std(0)+1e-9
    z=(O-E)/sd
    res.append((nm,M,int(keep.sum()),s,sb.mean(),pb))
    for m in np.flatnonzero(keep): clases.append((nm,m,O[m],E[m],z[m]))
from itertools import count
def bh(p):
    p=np.asarray(p); o=np.argsort(p); m=len(p); q=p[o]*m/np.arange(1,m+1)
    q=np.minimum.accumulate(q[::-1])[::-1]; out=np.empty(m); out[o]=np.minimum(q,1); return out
q=bh([r[5] for r in res])
print(f"base={BASE}  familias={len(res)}")
for r,qq in sorted(zip(res,q),key=lambda a:a[0][5]):
    print(f"{r[0]:<22} clases={r[2]:>5} X2={r[3]:9.1f} (nula {r[4]:9.1f})  p_boot={r[5]:.4f}  q_BH={qq:.3f}")
pz=2*norm.sf(np.abs([c[4] for c in clases])); qz=bh(pz)
o=np.argsort(pz)[:25]
print("\nclases individuales (total", len(clases),")")
for i in o: print(clases[i][0],clases[i][1],"O=%d E=%.1f z=%+.2f p=%.2g q=%.3f"%(clases[i][2],clases[i][3],clases[i][4],pz[i],qz[i]))
