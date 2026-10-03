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
# raw vs uniform, by quarter
def q(f): return f[:4]+'Q'+str((int(f[5:7])-1)//3+1)
Q=np.array([q(f) for f in F])
print('trimestre  1o:O/E(unif)  n | resto:O/E(unif) | 1o sobre P_aj')
for qq in sorted(set(Q)):
    a=(Q==qq)&E1; b=(Q==qq)&~E1
    o1=hit[a].sum(); e1=(k[a]/38).sum(); o2=hit[b].sum(); e2=(k[b]/38).sum()
    ok=a&~np.isnan(PA[:,0]); s3=''
    if ok.any(): s3=f"{hit[ok].sum()}/{(PA[ok]*W[ok]).sum():.1f}"
    print(f"{qq} {o1:3d}/{e1:5.1f}={o1/e1:4.2f} n={a.sum():3d} | {o2:4d}/{e2:6.1f}={o2/e2:4.2f} | {s3}")
# cal months
print('cal por mes 1o:', [(m, int(hit[(T=='cal')&E1&np.array([f[:7]==m for f in F])].sum()), round((k[(T=='cal')&E1&np.array([f[:7]==m for f in F])]/38).sum(),1)) for m in sorted(set(f[:7] for f in F[T=='cal']))])
# heterogeneity: cal vs posterior, raw uniform baseline for all
a=(T=='cal')&E1; b=(T!='cal')&E1
oa,ea=hit[a].sum(),(k[a]/38).sum(); ob,eb=hit[b].sum(),(k[b]/38).sum()
print('raw unif: cal',oa,round(ea,1),'post',ob,round(eb,1),'p(cal>=oa | total)=',1-stats.binom.cdf(oa-1,oa+ob,ea/(ea+eb)))
# E under P_aj vs uniform for window on first draws (motor bias?)
r=np.where(E1&~np.isnan(PA[:,0]))[0]
print('1o post-cal: E P_aj',round((PA[r]*W[r]).sum(),1),'E unif',round((k[r]/38).sum(),1),'O',hit[r].sum())
# 2nd draw of day in cal (hora 2) as control
for h in range(1,12):
    a=(T=='cal')&(H==h)&~E1; print(f"cal hora{h}: {hit[a].sum()}/{(k[a]/38).sum():.1f}",end='; ')
print()
