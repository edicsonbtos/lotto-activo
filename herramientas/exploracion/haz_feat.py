import sys, numpy as np
sys.path.insert(0, r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas")
from lotto_eval import cargar, particion
K=38
def feats(d, N):
    seq=d.seq[:N]; dia=d.dia[:N]; hora=d.hora[:N]
    G=np.zeros((N,K),int); D=np.zeros((N,K),int); S=np.zeros((N,K),int)
    last=np.full(K,-10**6); lastday=np.full(K,-10**6); cnt=np.zeros(K,int); cur=-1
    for t in range(N):
        if dia[t]!=cur: cnt[:]=0; cur=dia[t]
        G[t]=np.minimum(t-last, 10**6); D[t]=dia[t]-lastday; S[t]=cnt
        v=seq[t]; last[v]=t; lastday[v]=dia[t]; cnt[v]+=1
    return G,D,S
if __name__=="__main__":
    d=cargar(); w,c=particion(len(d)); N=c
    G,D,S=feats(d,N); Y=np.zeros((N,K),bool); Y[np.arange(N),d.seq[:N]]=True
    sl=slice(200,N)
    G,D,S,Y=G[sl],D[sl],S[sl],Y[sl]; h=d.hora[:N][sl]
    print("rate by (g, sameday>0) x38")
    for g in range(1,16):
        m=G==g
        a=Y[m&(S>0)].mean()*38 if (m&(S>0)).sum() else np.nan
        b=Y[m&(S==0)].mean()*38 if (m&(S==0)).sum() else np.nan
        print(g, round(a,2),(m&(S>0)).sum(), round(b,2),(m&(S==0)).sum())
    print("rate by daygap D (S==0) and g bucket")
    for dd in range(0,6):
        for lo,hi in [(1,6),(6,12),(12,20),(20,30),(30,60)]:
            m=(D==dd)&(G>=lo)&(G<hi)&(S==0)
            if m.sum()>300: print(dd,lo,hi,round(Y[m].mean()*38,3),m.sum())
    print("sameday count")
    for s in range(3): m=S==s; print(s, Y[m].mean()*38, m.sum())
    print("by hora: #distinct so far effect: rate of unseen-today numbers by hora")
    for hh in range(12):
        m=(h==hh)[:,None]&(S==0)
        print(hh, round(Y[m].mean()*38,3))
