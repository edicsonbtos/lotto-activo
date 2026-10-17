import json,math,random,collections,statistics as st,datetime as dt
R=json.load(open("reg.json"))
L=[r for r in R if r["mod"]=="mesa"]; S={(r["f"],r["h"]):r for r in R if r["mod"]=="sombra"}
D=collections.defaultdict(list)
for r in L: D[r["f"]].append(r)
fs=sorted(D)
hits=[sum(r["rank"]<=15 for r in D[f]) for f in fs]; ns=[len(D[f]) for f in fs]
p=sum(hits)/sum(ns); print(f"Top15 global {sum(hits)}/{sum(ns)} = {p:.3f}  (azar 15/38={15/38:.3f})")
T5=sum(r["rank"]<=5 for r in L); T3=sum(r["rank"]<=3 for r in L); print(f"Top5 {T5}/{len(L)}={T5/len(L):.3f} (azar .132); Top3 {T3}={T3/len(L):.3f} (azar .079)")
# overdispersion: observed var of daily rate vs binomial
obs=st.pvariance([h-n*p for h,n in zip(hits,ns)]); exp=st.mean([n*p*(1-p) for n in ns])
print(f"varianza diaria observada {obs:.2f} vs binomial esperada {exp:.2f}")
# permutation: shuffle draws across days, compute var of daily hits
allh=[r["rank"]<=15 for f in fs for r in D[f]]; cnt=0;N=20000
for _ in range(N):
    random.shuffle(allh); i=0; v=[]
    for n in ns: v.append(sum(allh[i:i+n])-n*p); i+=n
    if st.pvariance(v)>=obs: cnt+=1
print("p (días más dispares que el azar):",cnt/N)
# chance of best/worst day
print("mejor día:",max(zip(hits,fs)),"peor:",min(zip(hits,fs)))
# autocorrelation day t vs t+1
x=hits[:-1];y=hits[1:]
def corr(a,b):
    ma,mb=st.mean(a),st.mean(b); return sum((i-ma)*(j-mb) for i,j in zip(a,b))/math.sqrt(sum((i-ma)**2 for i in a)*sum((j-mb)**2 for j in b))
print("corr día t vs t+1:",round(corr(x,y),3))
# good vs bad days: winner traits
good=[f for f,h,n in zip(fs,hits,ns) if h/n>=7/12]; bad=[f for f,h,n in zip(fs,hits,ns) if h/n<=4/12]
print("buenos",good); print("malos",bad)
def traits(days):
    v=[r for f in days for r in D[f]]
    g=collections.Counter("hoy" if r["hoy"] else ("1d" if r["gap"]==1 else "2-5d" if r["gap"]<=5 else "6+d") for r in v)
    return len(v),{k:round(c/len(v),2) for k,c in sorted(g.items())}
mid=[f for f in fs if f not in good and f not in bad]
for nm,ds in (("buenos",good),("medios",mid),("malos",bad)): print(nm,traits(ds))
# overall by winner gap: hit rate top15
G=collections.defaultdict(lambda:[0,0])
for r in L:
    k="repite hoy" if r["hoy"] else ("1d" if r["gap"]==1 else "2-5d" if r["gap"]<=5 else "6+d"); G[k][0]+=r["rank"]<=15; G[k][1]+=1
print("Top15 según tipo de ganador:",{k:f"{a}/{b}={a/b:.2f}" for k,(a,b) in G.items()})
# by hour
H=collections.defaultdict(lambda:[0,0])
for r in L: H[r["h"]][0]+=r["rank"]<=15; H[r["h"]][1]+=1
print("Top15 por hora:",{8+h:f"{a}/{b}" for h,(a,b) in sorted(H.items())})
W=collections.defaultdict(lambda:[0,0])
for f,h,n in zip(fs,hits,ns): d="LMXJVSD"[dt.date.fromisoformat(f).weekday()]; W[d][0]+=h; W[d][1]+=n
print("Top15 por día semana:",{d:f"{a}/{b}={a/b:.2f}" for d,(a,b) in W.items()})
# pre-day signal: model confidence (mean e15) vs hits, among full days
fz=[f for f in fs if all(r["full"] for r in D[f])]
print("corr confianza del modelo (e15 medio) vs aciertos:",round(corr([st.mean(r['e15'] for r in D[f]) for f in fz],[sum(r['rank']<=15 for r in D[f])/len(D[f]) for f in fz]),3), "n días",len(fz))
# within-day: does morning (first 6) predict afternoon?
m=[sum(r["rank"]<=15 for r in D[f] if r["h"]<6) for f in fs]; a=[sum(r["rank"]<=15 for r in D[f] if r["h"]>=6) for f in fs]
print("corr mañana vs tarde mismo día:",round(corr(m,a),3))
# calibration: sum prob of winner-in-top15 expected vs observed
ef=[r for r in L if r["full"]]; print("calibración Top15 esperado",round(sum(r["e15"] for r in ef),1),"observado",sum(r["rank"]<=15 for r in ef),"n",len(ef))
# shadow ag12 per day
print("\nfecha  vivo ag12  (Top15)")
tv=ts=0
for f in fs:
    v=[S.get((f,r["h"])) for r in D[f]]
    if None in v: continue
    a1=sum(r["rank"]<=15 for r in D[f]); a2=sum(x["rank"]<=15 for x in v); tv+=a1; ts+=a2
print("totales días comparables vivo",tv,"ag12",ts)
