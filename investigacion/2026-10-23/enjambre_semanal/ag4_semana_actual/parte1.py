import csv,numpy as np,json,datetime as dt,collections
RUEDA=["0","28","9","26","30","11","7","20","32","17","5","22","34","15","3","24","36","13","1","00","27","10","25","29","12","8","19","31","18","6","21","33","16","4","23","35","14","2"]
POS={c:i for i,c in enumerate(RUEDA)}
def neigh(p):  # p codigo int !=0 -> set of casillas strings
    i=POS[str(p)]; return [RUEDA[(i-1)%38],RUEDA[(i+1)%38]]
rows=list(csv.DictReader(open('../../../../datos_multiloteria/oficial_multi.csv')))
G={1:[],2:[]}
for r in rows:
    if r['juego'] in('1','2'): G[int(r['juego'])].append((r['fecha'],r['hora'],int(r['codigo'])))
for g in G: G[g].sort()
A,B='2026-10-16','2026-10-23'
M=["max_cuenta_animal","animales_ausentes","repite_mismo_dia","par(1-36)","alto(19-36)","num=dia_fecha","num=hora24","num=hora12","vecino_rueda_prev","cruce_LA(h:00)=RD(h-1:30)","cruce_RD(h:30)=LA(h:00)"]
def build(g):
    d=G[g]; n=len(d)
    lk={(g_,f,h):c for g_ in (1,2) for f,h,c in G[g_] for _ in [0] }
    LA={(f,h):c for f,h,c in G[1]}; RD={(f,h):c for f,h,c in G[2]}
    obs=np.full((n,9),np.nan); exp=np.full((n,9),np.nan)
    # cols: repite,par,alto,dia,h24,h12,vec,cruceA,cruceB
    seen=collections.defaultdict(list)
    for i,(f,h,c) in enumerate(d):
        hh=int(h[:2]); mm=int(h[3:])
        pri=seen[f]
        if pri:
            ds=set(pri); w=sum(2 if x==0 else 1 for x in ds)
            obs[i,0]=float(c in ds); exp[i,0]=w/38
            p=pri[-1]
            if p!=0:
                nb=neigh(p); 
                if c==0: o=0.5*(("0" in nb)+("00" in nb))
                else: o=float(str(c) in nb)
                obs[i,6]=o; exp[i,6]=2/38
        if c!=0:
            obs[i,1]=float(c%2==0); exp[i,1]=.5
            obs[i,2]=float(c>=19); exp[i,2]=.5
        day=int(f[8:]); obs[i,3]=float(c==day); exp[i,3]=1/38 if day<=36 else 0
        obs[i,4]=float(c==hh); exp[i,4]=1/38
        h12=hh-12 if hh>12 else hh; obs[i,5]=float(c==h12); exp[i,5]=1/38
        pc=40/1444
        if g==1:  # LA h:00 vs RD (h-1):30
            k=(f,f"{hh-1:02d}:30")
            if k in RD: obs[i,7]=float(RD[k]==c); exp[i,7]=pc
        else:     # RD h:30 vs LA h:00
            k=(f,f"{hh:02d}:00")
            if k in LA: obs[i,8]=float(LA[k]==c); exp[i,8]=pc
        pri.append(c)
    return d,obs,exp
out={}
for g in (1,2):
    d,obs,exp=build(g); codes=np.array([x[2] for x in d]); fechas=[x[0] for x in d]
    idx=[i for i,f in enumerate(fechas) if A<=f<=B]; s,e=idx[0],idx[-1]+1; N=e-s
    cs=lambda a:np.vstack([np.zeros((1,a.shape[1])),np.nancumsum(a,0)])
    co,ce=cs(obs),cs(exp)
    # valid mask for crosses: ignore NaN exp -> contributes 0 both
    def win(a,b):
        return (co[b]-co[a])-(ce[b]-ce[a]), ce[b]-ce[a], co[b]-co[a]
    def raw(a,b):
        c=np.bincount(np.where(codes[a:b]==0,0,codes[a:b]),minlength=37)
        return c.max(), int((c==0).sum())
    hist=list(range(0,s-N+1))
    res={}
    cur_diff,cur_exp,cur_obs=win(s,e); cur_raw=raw(s,e)
    H=np.array([win(a,a+N)[0] for a in hist]); R=np.array([raw(a,a+N) for a in hist])
    names=["repite_mismo_dia","par(1-36)","alto(19-36)","num=dia_fecha","num=hora24","num=hora12","vecino_rueda_prev","cruce_LA(h:00)=RD(h-1:30)","cruce_RD(h:30)=LA(h:00)"]
    for j,nm in enumerate(names):
        if np.isnan(obs[:,j]).all(): continue
        if (g==1 and j==8) or (g==2 and j==7): continue
        pct=100*(H[:,j]<cur_diff[j]).mean()+50*(H[:,j]==cur_diff[j]).mean()
        res[nm]=dict(obs=float(cur_obs[j]),esp=float(cur_exp[j]),pct=float(pct),hist_lo=float(np.percentile(H[:,j],5)),hist_hi=float(np.percentile(H[:,j],95)),n=int(N))
    for k,nm in enumerate(["max_cuenta_animal","animales_ausentes"]):
        v=cur_raw[k]; pct=100*(R[:,k]<v).mean()+50*(R[:,k]==v).mean()
        res[nm]=dict(obs=float(v),esp=None,pct=float(pct),hist_lo=float(np.percentile(R[:,k],5)),hist_hi=float(np.percentile(R[:,k],95)),n=int(N))
    c=collections.Counter(codes[s:e].tolist())
    # por casilla: 0 = 2 casillas
    exp_c=N/38
    top=sorted(c.items(),key=lambda x:-x[1])[:6]
    absent=[k for k in range(37) if c[k]==0]
    res['_top']=top; res['_ausentes']=absent; res['_N']=int(N); res['_ult']=d[e-1][:2]; res['_nwin']=len(hist)
    res['_freq_exp']=exp_c
    out[g]=res
json.dump(out,open('parte1.json','w'),indent=1)
nm={1:'LA',2:'RD'}
for g in out:
    print(nm[g],out[g]['_N'],out[g]['_ult'],'top',out[g]['_top'],'aus',out[g]['_ausentes'],'esp/animal',round(out[g]['_freq_exp'],2),'(0:x2)')
    for k,v in out[g].items():
        if k[0]=='_':continue
        print(f"  {k:28s} obs={v['obs']:.1f} esp={v['esp'] if v['esp'] is None else round(v['esp'],1)} pct={v['pct']:.0f} [5-95 hist diff {v['hist_lo']:.1f},{v['hist_hi']:.1f}]")
