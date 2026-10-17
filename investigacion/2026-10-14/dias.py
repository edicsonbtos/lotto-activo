import json,math,collections,datetime as dt
R=[]
for mod in ("mesa","sombra"):
    for o in range(1,375):
        j=json.load(open(f"{mod}/{o}.json",encoding="utf-8"))
        if "animales" not in j or j.get("winner_rank") is None: continue
        a=j["animales"]; w=j["winner"]; wa=a[w]
        full=all(x["prob"] is not None for x in a)
        ps=sorted((x["prob"] for x in a),reverse=True) if full else [1/38]*38
        R.append(dict(mod=mod,f=j["fecha"],h=j["hora"],rank=j["winner_rank"],p=wa["prob"],gap=wa["gap_dias"],hoy=wa["salio_hoy"],
            e15=sum(ps[:15]),e5=sum(ps[:5]),ent=-sum(x["prob"]*math.log2(x["prob"]) for x in a if x["prob"]) if full else None,full=full,
            nhoy=sum(x["salio_hoy"] for x in a)))
json.dump(R,open("../reg.json","w"))
L=[r for r in R if r["mod"]=="mesa"]
print("sorteos LA vivos:",len(L), "rango",min(r["f"] for r in L),max(r["f"] for r in L))
D=collections.defaultdict(list)
for r in L: D[r["f"]].append(r)
print("fecha      dow n  T15 esp15  T5 esp5 T3  hoyW  gap0W  rankmed")
rows=[]
for f in sorted(D):
    v=D[f]; n=len(v)
    t15=sum(r["rank"]<=15 for r in v); t5=sum(r["rank"]<=5 for r in v); t3=sum(r["rank"]<=3 for r in v)
    e15=sum(r["e15"] for r in v); e5=sum(r["e5"] for r in v)
    hw=sum(r["hoy"] for r in v)
    dow="LMXJVSD"[dt.date.fromisoformat(f).weekday()]
    rows.append((f,dow,n,t15,e15,t5,e5,t3,hw))
    print(f,dow,f"{n:2d} {t15:3d} {e15:5.1f} {t5:3d} {e5:4.1f} {t3:2d} {hw:4d}  {sorted(r['rank'] for r in v)}")
json.dump(rows,open("../dias.json","w"))
