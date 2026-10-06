import sys, numpy as np
sys.path.insert(0,"/home/user/lotto-activo/herramientas"); import lotto_eval as LE
S=sys.argv[1]
D=LE.cargar(S+"/hist_0605.txt"); YS=np.asarray(D.seq); FD=np.array(D.fecha)
z=np.load(S+"/prod_0605.npz",allow_pickle=True); P,t,y,f,h=z["P"],z["t"],z["y"],z["f"],z["h"]
o=np.argsort(-P,1,kind="stable"); rk=np.argmax(o==y[:,None],1); in15=rk<15
m15=np.take_along_axis(P,o[:,:15],1).sum(1); pw=P[np.arange(len(y)),y]; mb=1000*np.log2(pw*38)
fu=np.unique(FD); di={d:i for i,d in enumerate(fu)}; dn=np.array([di[x] for x in FD])
rec=np.array([np.any((YS[:T]==YS[T])&(dn[:T]>=dn[T]-2)&(dn[:T]<dn[T])) for T in t])
# probabilidad del motor de que el ganador sea "reciclado"
prev2=[set(YS[(dn>=dn[T]-2)&(dn<dn[T])]) for T in t]; prec=np.array([P[i,list(s)].sum() for i,s in enumerate(prev2)])
dias={}
for i,d in enumerate(f): dias.setdefault(d,[]).append(i)
def tramo(d): i=dias[d][0]; return "dev" if t[i]<9357 else ("prueba" if d<"2026-09-15" else "vivo")
full=[d for d,v in dias.items() if len(v)==12]
for tr in ("dev","prueba"):
    ds=[d for d in full if tramo(d)==tr]; R=np.array([rec[dias[d]].sum() for d in ds]); E=np.array([prec[dias[d]].sum() for d in ds])
    print(f"\n===== {tr}: {len(ds)} días =====")
    print(f"R medio {R.mean():.2f}/12 (el motor esperaba {E.mean():.2f});  días con R>=9: {np.sum(R>=9)} ({np.mean(R>=9)*100:.1f} %, 1 cada {len(ds)/max(1,np.sum(R>=9)):.0f} días)")
    for lo,hi,lab in ((0,5,"R 0-5"),(6,7,"R 6-7"),(8,8,"R 8"),(9,12,"R 9-12")):
        k=[d for d,r in zip(ds,R) if lo<=r<=hi]; ii=sum((dias[d] for d in k),[])
        if not ii: continue
        print(f"  {lab:7} n={len(k):3d} días | Top-15 {in15[ii].mean()*100:5.1f}% (esperaba {m15[ii].mean()*100:4.1f}) = {in15[ii].sum()/len(k):.1f}/12 por día | señal {mb[ii].mean():+5.0f} mbits")
    # 2. mañana -> tarde
    print("  -- ¿la mañana avisa? (R en 8a-1p -> tarde 2p-7p) --")
    for lo,hi in ((0,2),(3,3),(4,4),(5,6)):
        k=[d for d in ds if lo<=rec[dias[d][:6]].sum()<=hi]; ii=sum((dias[d][6:] for d in k),[])
        O=in15[ii].sum(); Ex=m15[ii].sum(); v=(m15[ii]*(1-m15[ii])).sum(); zz=(O-Ex)/np.sqrt(v)
        Or=rec[ii].sum(); Er=prec[ii].sum()
        print(f"  mañana R {lo}-{hi}: {len(k):3d} días | tarde Top-15 {O/len(ii)*100:5.1f}% vs motor {Ex/len(ii)*100:4.1f}% O/E {O/Ex:.2f} z {zz:+.1f} | tarde reciclados {Or/len(k):.2f}/6 vs motor {Er/len(k):.2f}")
    # 3. día siguiente
    pares=[(a,b) for a,b in zip(ds[:-1],ds[1:]) if di[b]-di[a]==1]
    Ra=np.array([rec[dias[a]].sum() for a,b in pares]); Rb=np.array([rec[dias[b]].sum() for a,b in pares]); Hb=np.array([in15[dias[b]].sum() for a,b in pares])
    print(f"  -- día siguiente -- corr(R hoy, R mañana) {np.corrcoef(Ra,Rb)[0,1]:+.2f};  Top-15 mañana tras R>=9: {Hb[Ra>=9].mean():.2f}/12 (n={np.sum(Ra>=9)}) vs resto {Hb[Ra<9].mean():.2f};  R mañana tras R>=9: {Rb[Ra>=9].mean():.2f} vs {Rb[Ra<9].mean():.2f}")
