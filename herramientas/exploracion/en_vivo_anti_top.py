import sys, math, json
sys.path.insert(0, ".claude/skills/lotto-marcador")
from marcador import leer
from concurrent.futures import ThreadPoolExecutor
total = leer("/api/mesa?offset=0")["total"]
with ThreadPoolExecutor(8) as ex:
    regs = list(ex.map(lambda o: leer(f"/api/mesa?offset={o}"), range(1, total)))
pu = [r["winner_rank"] for r in regs if r.get("winner_rank") and r.get("modelo")=="ensamble_v2"]
n=len(pu); print("n",n)
def z(k,n,p): return (k/n-p)/math.sqrt(p*(1-p)/n)
for a,b in ((1,15),(1,5),(16,38),(24,38),(29,38),(34,38),(1,19),(20,38)):
    k=sum(a<=p<=b for p in pu); N=b-a+1; p0=N/38
    ret=k/n*30/N-1
    print(f"puestos {a}-{b} ({N} animales): {k}/{n}={k/n*100:.1f}% azar {p0*100:.1f}% z={z(k,n,p0):+.2f} retorno plano {ret*100:+.1f}% (equilibrio {N/30*100:.1f}%)")
# por mitades cronologicas (pu viene de mas reciente a mas viejo)
h=n//2
for nom,s in (("reciente",pu[:h]),("viejo",pu[h:])):
    m=len(s); print(nom,m,"top15",sum(p<=15 for p in s)/m, "bottom15(24-38)",sum(p>=24 for p in s)/m)
