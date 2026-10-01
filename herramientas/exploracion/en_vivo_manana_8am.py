import sys, math, collections, numpy as np
sys.path.insert(0, ".claude/skills/lotto-marcador"); sys.path.insert(0,"herramientas")
from marcador import leer
from concurrent.futures import ThreadPoolExecutor
total = leer("/api/mesa?offset=0")["total"]
with ThreadPoolExecutor(8) as ex:
    regs = list(ex.map(lambda o: leer(f"/api/mesa?offset={o}"), range(1, total)))
R=[r for r in regs if r.get("winner_rank") and r.get("modelo")=="ensamble_v2"]
R.sort(key=lambda r:(r["fecha"],r["hora"]))
byday=collections.defaultdict(list)
for r in R: byday[r["fecha"]].append(r)
days=sorted(byday)
print("=== LIVE 8:00: ganador, puesto, hueco, ¿salio ayer?, prob del modelo ===")
rows=[]
for i,d in enumerate(days):
    m=[r for r in byday[d] if r["hora"]==min(x["hora"] for x in byday[d])]
    # 8:00 = hora 0 de la web? usar hora_txt
    m=[r for r in byday[d] if r["hora_txt"].startswith("8:00")]
    if not m: continue
    r=m[0]; w=r["winner_num"]
    ay=set(x["winner_num"] for x in byday[days[i-1]]) if i>0 else set()
    ult=[x for x in byday[days[i-1]]][-1]["winner_num"] if i>0 else None
    a={x["num"]:x for x in r["animales"]}
    ok=len(a)==38 and all(x.get("prob") for x in a.values())
    ps=sum(x["prob"] for x in a.values()) if ok else 1
    pay=sum(a[k]["prob"] for k in ay if k in a)/ps if ok else float('nan')
    gw=a[w]["gap_dias"] if w in a else None
    rows.append((d,w,r["winner_nombre"],r["winner_rank"],gw,w in ay,w==ult,pay))
    print(f"{d} {w:>3} {r['winner_nombre'][:10]:<10} puesto {r['winner_rank']:>2} hueco {gw} ayer={'SI' if w in ay else 'no'} ultimo_ayer={'SI' if w==ult else 'no'} masa_modelo_en_animales_de_ayer={pay*100:.0f}%")
print()
n=len(rows); k=sum(x[5] for x in rows); 
print(f"salio ayer: {k}/{n}; base azar 12 sorteos/38 ~ {(1-(37/38)**12)*100:.0f}%; el modelo esperaba {np.nanmean([x[7] for x in rows])*100:.0f}% (media)")
r11=[x for x in rows if x[0]>="2026-09-21"]
print("racha (desde 09-21):",len(r11),"salio ayer",sum(x[5] for x in r11),"promedio masa modelo",np.nanmean([x[7] for x in r11]))
print("ultimo_ayer en toda la serie:",sum(x[6] for x in rows),"/",n)
print("huecos de los ganadores 8:00:",[x[4] for x in rows])
# mismos stats para el resto de horas en vivo
tot=ay_=0
for i,d in enumerate(days[1:],1):
    ay=set(x["winner_num"] for x in byday[days[i-1]])
    for r in byday[d]:
        if r["hora_txt"].startswith("8:00"): continue
        tot+=1; ay_+= r["winner_num"] in ay
print(f"otras horas: salio ayer {ay_}/{tot} = {ay_/tot*100:.1f}%")
# DEV historico
import lotto_eval as LE
Dt=LE.cargar(); d0=np.load("herramientas/exploracion/calor_cache.npz"); P=d0["P"]; y=d0["y"].astype(int)
Pn=P/P.sum(1,keepdims=True)
seq=Dt.seq; dia=Dt.dia; hora=Dt.hora
bydia=collections.defaultdict(set)
for s,dd in zip(seq,dia): bydia[dd].add(s)
hit=exp=tot=0; hit_o=exp_o=tot_o=0
for j in range(len(P)):
    g=LE.W+j; ayer=bydia.get(dia[g]-1)
    if not ayer: continue
    msk=np.zeros(38,bool); msk[list(ayer)]=True
    e=Pn[j][msk].sum(); h=y[j] in ayer
    if hora[g]==8: tot+=1; hit+=h; exp+=e
    else: tot_o+=1; hit_o+=h; exp_o+=e
print(f"\nDEV 8:00: ganador salio ayer {hit}/{tot}={hit/tot*100:.1f}% ; modelo esperaba {exp/tot*100:.1f}%")
print(f"DEV otras horas: {hit_o/tot_o*100:.1f}% ; modelo esperaba {exp_o/tot_o*100:.1f}%")
