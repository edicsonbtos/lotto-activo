import sys, numpy as np
from scipy import stats
sys.path.insert(0,'/home/user/lotto-activo/herramientas'); import lotto_eval as LE
B='/tmp/claude-0/-home-user-lotto-activo/fffc39ca-02e7-4d69-b0fe-674a608a5e21/scratchpad/base8'
z=np.load(B+'/base8.npz'); S,H,F,P,PA,E1,T=z['seq'],z['hora'],z['fecha'],z['P'],z['P_aj'],z['es_primero'],z['tramo']
n=len(S); dd=np.array([int(f[8:10]) for f in F])
def mask(offs, lo):
    M=np.zeros((n,38),bool)
    for s in offs:
        v=dd+s; ok=(v>=lo)&(v<=36); M[np.where(ok)[0], np.array([LE.IDX[str(x)] for x in v[ok]])]=True
    return M
W0=mask((-1,0,1),0); W1=mask((-1,0,1),1)
print('filas donde difieren (dia 1 -> "0"):', (W0!=W1).any(1).sum())
def pb_cdf(ps,o):
    # exact Poisson-binomial lower tail
    d=np.zeros(len(ps)+1); d[0]=1
    for p in ps: d[1:]=d[1:]*(1-p)+d[:-1]*p; d[0]*=(1-p)
    return d[:o+1].sum()
def OE(r,M,Q):
    hit=M[r,S[r]]; pr=(Q[r]*M[r]).sum(1); return int(hit.sum()), pr.sum(), pr
def aplicar(Q,M,m): q=Q*np.where(M,m,1.0); return q/q.sum(1,keepdims=True)
dev,pru=T=='dev',T=='prueba'
for nom,W in (('ag02 (dia1->"0")',W0),('sin "0"',W1)):
    MS={s:mask((s,),0 if W is W0 else 1) for s in (-1,0,1)}
    rr=np.where(dev&~E1)[0]; g={s:(OE(rr,MS[s],P)[0]+.5)/(OE(rr,MS[s],P)[1]+.5) for s in (-1,0,1)}
    Bg=PA.copy()
    for s in (-1,0,1): Bg=np.where(E1[:,None]&~np.isnan(PA),aplicar(Bg,MS[s],g[s]),Bg)
    r1=np.where(dev&E1)[0]; o,e,_=OE(r1,W,PA); m2=(o+.5)/(e+.5)
    rp=np.where(pru&E1)[0]
    for base,bn in ((PA,'P_aj'),(Bg,'B_gen')):
        o,e,pr=OE(rp,W,base); print(f"{nom:18s} prueba vs {bn}: {o}/{e:.1f}={o/e:.2f} p_poisson={stats.poisson.cdf(o,e):.4f} p_exacto={pb_cdf(pr,o):.4f}  (m2={m2:.3f}, g={[round(g[s],3) for s in (-1,0,1)]})")
# prueba interaction: first vs rest
rp=np.where(pru&E1)[0]; rr=np.where(pru&~E1)[0]
o1,e1,_=OE(rp,W1,PA); o2,e2,_=OE(rr,W1,P)
print('interaccion prueba (sin 0): 1o',o1,round(e1,1),'resto',o2,round(e2,1),'p=',stats.binom.cdf(o1,o1+o2,e1/(e1+e2)))
# overlap with hour number (8) on days 7-9
r8=rp[(dd[rp]>=7)&(dd[rp]<=9)]; print('prueba dias 7-9 (ventana contiene la hora 8):',len(r8),'aciertos ventana',W1[r8,S[r8]].sum())
# by-offset & per month prueba
for m in sorted(set(f[:7] for f in F[rp])):
    r=rp[np.array([f[:7]==m for f in F[rp]])]; o,e,_=OE(r,W1,PA); print(m,o,round(e,2),end=' | ')
print()
