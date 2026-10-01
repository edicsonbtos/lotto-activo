import sys, math, random, collections
sys.path.insert(0, ".claude/skills/lotto-marcador")
from marcador import leer
from concurrent.futures import ThreadPoolExecutor
total = leer("/api/mesa?offset=0")["total"]
with ThreadPoolExecutor(8) as ex:
    regs = list(ex.map(lambda o: leer(f"/api/mesa?offset={o}"), range(1, total)))
R=[r for r in regs if r.get("winner_rank") and r.get("modelo")=="ensamble_v2"]
R.sort(key=lambda r:(r["fecha"],r["hora"]))
n=len(R); print("n",n, R[0]["fecha"], R[-1]["fecha"])
# buckets de puesto: observado vs esperado por el modelo
B=[(1,5),(6,15),(16,25),(26,38)]
obs=collections.Counter(); esp=collections.defaultdict(float); m=0
for r in R:
    ps={a["num"]:a.get("prob") for a in r["animales"]}
    if len(ps)!=38 or not all(ps.values()): continue
    m+=1; s=sum(ps.values()); pp=sorted((p/s for p in ps.values()),reverse=True)
    for a,b in B:
        esp[(a,b)]+=sum(pp[a-1:b]); obs[(a,b)]+= a<=r["winner_rank"]<=b
print("buckets (n con probs =",m,")")
for a,b in B:
    N=b-a+1; k=obs[(a,b)]; e=esp[(a,b)]; sd=math.sqrt(e*(1-e/m))
    print(f" {a}-{b}: obs {k} ({k/m*100:.1f}%) esperado modelo {e:.1f} ({e/m*100:.1f}%) azar {N/38*100:.1f}% z_vs_modelo {(k-e)/sd:+.2f}")
# por hora
print("\nPor hora (top15 / azar 39.5%):")
H=collections.defaultdict(list)
for r in R: H[r["hora"]].append(r)
for h in sorted(H):
    s=H[h]; k=sum(x["winner_rank"]<=15 for x in s); k25=sum(16<=x["winner_rank"]<=25 for x in s)
    print(f" {s[0]['hora_txt']:>8} n={len(s):3d} top15={k:3d} ({k/len(s)*100:4.1f}%) 16-25={k25:3d} ({k25/len(s)*100:4.1f}%)")
# 8:00 secuencia por dia
print("\nSecuencia 8:00 (1=Top15):")
s8=[(x["fecha"],x["winner_rank"]) for x in H[min(H)]]
print(" ".join(f"{d[5:]}:{'1' if w<=15 else '0'}({w})" for d,w in s8))
# racha mas larga de top15 en cada hora vs permutacion
def maxrun(v):
    b=c=0
    for x in v:
        c=c+1 if x else 0; b=max(b,c)
    return b
random.seed(1)
print("\nRacha max Top15 por hora vs permutacion (p de ver >= racha):")
for h in sorted(H):
    v=[x["winner_rank"]<=15 for x in H[h]]
    ob=maxrun(v); cnt=0; T=5000
    for _ in range(T):
        w=v[:]; random.shuffle(w); cnt+= maxrun(w)>=ob
    print(f" {H[h][0]['hora_txt']:>8} n={len(v)} racha={ob} p={cnt/T:.3f}")
# racha max sobre TODAS las horas: p de que la mejor hora tenga >= la observada (corrige comparaciones multiples)
best=max(maxrun([x["winner_rank"]<=15 for x in H[h]]) for h in H)
cnt=0;T=3000
allv=[x["winner_rank"]<=15 for x in R]
for _ in range(T):
    random.shuffle(allv); i=0; b=0
    for h in sorted(H):
        L=len(H[h]); b=max(b,maxrun(allv[i:i+L])); i+=L
    cnt+= b>=best
print(f"\nMejor racha entre las {len(H)} horas = {best}; p (con comparaciones multiples) = {cnt/T:.3f}")
# dia a dia: Top15 por dia
D=collections.defaultdict(list)
for r in R: D[r["fecha"]].append(r["winner_rank"])
print("\nPor dia: aciertos Top15 / sorteos")
print(" ".join(f"{d[5:]}:{sum(w<=15 for w in v)}/{len(v)}" for d,v in sorted(D.items())))
# dispersion entre dias (varianza vs binomial)
xs=[(sum(w<=15 for w in v),len(v)) for v in D.values() if len(v)>=4]
p=sum(k for k,_ in xs)/sum(l for _,l in xs)
chi=sum((k-l*p)**2/(l*p*(1-p)) for k,l in xs); print(f"chi2 dispersion entre dias = {chi:.1f} con {len(xs)-1} gl (esperado ~{len(xs)-1})")
