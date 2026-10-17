import csv,collections,unicodedata,sys,math
import numpy as np
P='../../../scraping/resultados/consolidado_todos.csv'
def nm(s): return ''.join(c for c in unicodedata.normalize('NFD',s.upper().strip()) if unicodedata.category(c)!='Mn')
d=collections.defaultdict(list)
# Identidad del animal = NOMBRE normalizado (el numero se reutiliza: el 0 es Ballena o Delfin segun
# la fuente; en Chance 37/38/6/33 cambia de animal). Sinonimos unificados. Sin nombre -> solo se usa
# el numero si no es ambiguo; el 0 sin nombre se descarta.
ALIAS={'RANA':'SAPO','PEZ':'PESCADO','CIENPIES':'CIEMPIES','OSOHRMIGUERO':'OSO HORMIGUERO'}
def clave(r):
    n=nm(r['animal_nombre']); n=ALIAS.get(n,n)
    if n: return n
    return None if r['animal_numero'] in ('','0','00') else r['animal_numero']
DESCARTADAS=collections.Counter()
for r in csv.DictReader(open(P,encoding='utf-8')):
    k=clave(r)
    if k is None: DESCARTADAS[r['operador']]+=1; continue
    d[r['operador']].append((r['fecha'],r['hora'],k))
if DESCARTADAS: print('filas descartadas por animal ambiguo:',dict(DESCARTADAS))
BINS=[1,2,3,4,5,6,8,10,13,18,25,35,50,80,10**9]
def cub(g):
    for i,b in enumerate(BINS):
        if g<=b: return i
NB=len(BINS)
rng=np.random.default_rng(0)
REV=len(sys.argv)>1
BRK=1 if REV else 0
def run(seq):
    seq=sorted(seq); days=sorted({s[0] for s in seq}); cut=days[len(days)//2]
    syms=collections.Counter(s[2] for s in seq)
    syms=[s for s,c in syms.items() if c>=5]; K=len(syms); ix={s:i for i,s in enumerate(syms)}
    last=np.full(K,-10**6); today=np.zeros(K,bool); curd=None
    hit=np.ones((2,NB))*0.5; exp=np.ones((2,NB))*0.5*0+1  # prior
    hits=np.zeros((2,NB))+0.1; exps=np.zeros((2,NB))+0.1*K
    rows=[]  # (day, logratio, top5hit)
    for t,(f,h,a) in enumerate(seq):
        if f!=curd: curd=f; today[:]=False
        if a not in ix: continue
        g=t-last; gb=np.array([cub(x) for x in g]); td=today.astype(int)
        rate=hits[td,gb]/exps[td,gb]; p=rate/rate.sum()
        j=ix[a]
        if (f<cut) if REV else (f>=cut):
            top=np.argsort(-p)[:5]
            rows.append((f,math.log2(p[j]*K),j in top))
        if (f>=cut) if REV else (f<cut):
            for k in range(K): exps[td[k],gb[k]]+=1
            hits[td[j],gb[j]]+=1
        last[j]=t; today[j]=True
    return K,rows
def boot(rows,fn):
    byd=collections.defaultdict(list)
    for r in rows: byd[r[0]].append(r)
    ds=list(byd); out=[]
    for _ in range(2000):
        s=[r for dd in rng.choice(len(ds),len(ds)) for r in byd[ds[dd]]]
        out.append(fn(s))
    return np.percentile(out,[2.5,97.5])
res=[]
for op,seq in d.items():
    K,rows=run(seq)
    if len(rows)<300: print(op,'pocos'); continue
    mb=np.mean([r[1] for r in rows])*1000; t5=np.mean([r[2] for r in rows]); base=5/K
    ci=boot(rows,lambda s:np.mean([r[1] for r in s])*1000); ci5=boot(rows,lambda s:np.mean([r[2] for r in s])/base)
    res.append((op,K,len(rows),mb,ci,t5*100,base*100,t5/base,ci5))
res.sort(key=lambda x:-x[3])
print(f"{'juego':32s}{'K':>4}{'n':>6}{'mbits':>8}{'IC95':>18}{'Top5%':>7}{'azar%':>7}{'O/E':>6}{'IC O/E':>14}")
for op,K,n,mb,ci,t5,b,oe,ci5 in res:
    flag=(' <-- pasa' if ci[0]>0 and ci5[0]>1 else '')+f'  pago_equilibrio={5/(t5/100):.1f}x'
    print(f"{op:32s}{K:4d}{n:6d}{mb:8.1f} [{ci[0]:6.1f},{ci[1]:6.1f}]{t5:7.1f}{b:7.1f}{oe:6.2f} [{ci5[0]:.2f},{ci5[1]:.2f}]{flag}")
