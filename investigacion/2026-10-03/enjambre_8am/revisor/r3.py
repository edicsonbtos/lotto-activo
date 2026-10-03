import sys, numpy as np
from scipy import stats
sys.path.insert(0,'/home/user/lotto-activo/herramientas'); import lotto_eval as LE
B='/tmp/claude-0/-home-user-lotto-activo/fffc39ca-02e7-4d69-b0fe-674a608a5e21/scratchpad/base8'
z=np.load(B+'/base8.npz'); S,H,F,P,PA,E1,T=z['seq'],z['hora'],z['fecha'],z['P'],z['P_aj'],z['es_primero'],z['tramo']
n=len(S); dd=np.array([int(f[8:10]) for f in F])
W=np.zeros((n,38),bool)
for s in (-1,0,1):
    v=dd+s; ok=(v>=1)&(v<=36); W[np.where(ok)[0],[LE.IDX[str(x)] for x in v[ok]]]=True
hit=W[np.arange(n),S]; k=W.sum(1)
Q=np.where(E1[:,None],PA,P)
pos=np.zeros(n,int)  # posición en el día (0 = primero)
for t in range(1,n): pos[t]=0 if E1[t] else pos[t-1]+1
for tr in ('cal','dev','prueba'):
    m=T==tr; out=[]
    for p in range(12):
        a=m&(pos==p)
        if a.sum()==0: continue
        o=hit[a].sum(); e=(k[a]/38).sum() if tr=='cal' else (Q[a]*W[a]).sum()
        out.append((p,o,e))
    ratios=[o/e for p,o,e in out]
    print(tr,' '.join(f"{p}:{o}/{e:.1f}={o/e:.2f}" for p,o,e in out))
    # rank of first draw among positions, and heterogeneity chi2
    O=np.array([o for _,o,_ in out]); E=np.array([e for _,_,e in out]); Ex=E*O.sum()/E.sum()
    print('   rango del 1o (menor=1):',1+sum(r<ratios[0] for r in ratios[1:]),'de',len(out),' chi2 heterog p=',round(1-stats.chi2.cdf(((O-Ex)**2/Ex).sum(),len(out)-1),3))
