import json,glob,datetime as dt,numpy as np
from scipy import stats
DOW=['lun','mar','mie','jue','vie','sab','dom']
def cargar(m):
    R={}
    for f in glob.glob(f"raw/{m}/*.json"):
        d=json.load(open(f))
        if d['offset']==0 or d['winner_rank'] is None: continue
        an=sorted([a for a in d['animales'] if a['rank'] is not None],key=lambda a:a['rank'])
        pr=[a['prob'] for a in an]
        e5=sum(pr[:5]) if all(p is not None for p in pr[:5]) and pr else None
        e15=sum(pr[:15]) if all(p is not None for p in pr[:15]) and len(pr)>=15 else None
        e3=sum(pr[:3]) if len(pr)>=3 and all(p is not None for p in pr[:3]) else None
        R[(d['fecha'],d['hora'])]=dict(f=d['fecha'],h=d['hora']+8,dow=dt.date.fromisoformat(d['fecha']).weekday(),r=d['winner_rank'],e3=e3,e5=e5,e15=e15)
    return sorted(R.values(),key=lambda x:(x['f'],x['h']))
def wil(k,n):
    return stats.beta.ppf(.025,k,n-k+1) if k>0 else 0, stats.beta.ppf(.975,k+1,n-k) if k<n else 1
def tabla(rows,key,labels,out,tag):
    L=[]
    for k,tk in (('5',5),('15',15)):
        obs=[];n=[];ex=[]
        for lab in labels:
            s=[x for x in rows if (DOW[x['dow']] if key=='dow' else x[key])==lab]
            hit=sum(x['r']<=tk for x in s); obs.append(hit); n.append(len(s))
            e=[x['e'+k] for x in s if x['e'+k] is not None]; ex.append(np.mean(e) if e else None)
        obs=np.array(obs);n=np.array(n); p=obs.sum()/n.sum()
        exp=p*n; chi=((obs-exp)**2/(n*p*(1-p))).sum(); df=len(labels)-1; pv=1-stats.chi2.cdf(chi,df)
        out.append(f"\n{tag} Top-{k}  (global {100*p:.1f}%; uniforme {100*tk/38:.1f}%)  chi2={chi:.1f} gl={df} p={pv:.3f}")
        for lab,o,nn,e in zip(labels,obs,n,ex):
            lo,hi=wil(o,nn); es=f"{100*e:.1f}%" if e else "  - "
            out.append(f"  {lab!s:>4}: {o:3d}/{nn:3d} = {100*o/nn:5.1f}%  IC95[{100*lo:4.1f};{100*hi:4.1f}]  modelo {es}")
    return
def retorno(rows,out,tag):
    out.append(f"\n{tag} retorno por ficha (paga 30x; neto/apostado)")
    for nm,fn,stake in (("Top5 esc 2-2-2-1-1",lambda r:(2 if r<=3 else 1)*30-8 if r<=5 else -8,8),("Top3 plano",lambda r:30-3 if r<=3 else -3,3)):
        out.append(f"  {nm}")
        allv=np.array([fn(x['r']) for x in rows])/stake
        for lab,sel in [(DOW[i],[x for x in rows if x['dow']==i]) for i in range(7)]+[('TOTAL',rows)]:
            v=np.array([fn(x['r']) for x in sel])/stake; n=len(v)
            if n==0: continue
            se=v.std(ddof=1)/np.sqrt(n)
            out.append(f"    {lab:>5}: n={n:3d} retorno {100*v.mean():+6.1f}%  IC95[{100*(v.mean()-1.96*se):+6.1f};{100*(v.mean()+1.96*se):+6.1f}]")
for m in ("la","principal"):
    rows=cargar(m); out=[f"=== modelo={m}  n={len(rows)} desde {rows[0]['f']} {rows[0]['h']}h hasta {rows[-1]['f']} {rows[-1]['h']}h"]
    tabla(rows,'dow',DOW,out,m)
    tabla(rows,'h',list(range(8,20)),out,m)
    retorno(rows,out,m)
    # lo mismo solo semana actual
    wk=[x for x in rows if '2026-10-16'<=x['f']<='2026-10-23']
    for k in (5,15,3):
        out.append(f"semana 16-23oct {m}: Top-{k} {sum(x['r']<=k for x in wk)}/{len(wk)}  esperado modelo {sum(x['e'+str(k)] for x in wk if x['e'+str(k)]):.1f}")
    open(f"tabla_{m}.txt","w").write("\n".join(out)); print("\n".join(out))
