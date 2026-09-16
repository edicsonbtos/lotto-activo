# -*- coding: utf-8 -*-
import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

PARSED = os.path.join(core.CRUDOS, "parsed")

tz = [json.loads(l) for l in io.open(os.path.join(PARSED, "tuazar_todas.jsonl"), encoding="utf-8")]

# 1) cobertura por semana de cada loteria en tuazar
por_sem = defaultdict(set)
for r in tz:
    sem = core.lunes(__import__("datetime").date(*map(int, r["fecha"].split("-")))).isoformat()
    por_sem[sem].add(r["loteria"])
print("== cobertura tuazar por semana (objetivos) ==")
for sem in sorted(por_sem):
    objs = [s for s in ("lottoactivo","lottoactivordint","lagranjita","selvaplus","guacharoactivo") if s in por_sem[sem]]
    print(sem, objs)

# 2) tablero tuazar guacharoactivo completo
print("\n== tablero TZ guacharoactivo ==")
pn = defaultdict(Counter)
for r in tz:
    if r["loteria"] == "guacharoactivo":
        pn[r["numero"]][core.norm(r["animal"])] += 1
for n in sorted(pn):
    print(n, pn[n].most_common(3))

# 3) pareo empirico LH-animal -> TZ-numero para guacharo y selvaplus y lagranjita
print("\n== pareo LH animal -> TZ numero (mayoria) ==")
for slug in ("lagranjita", "selvaplus", "guacharoactivo", "lottoactivordint"):
    lh = [json.loads(l) for l in io.open(os.path.join(PARSED, "lh_%s.jsonl" % slug), encoding="utf-8")]
    tzs = {(r["fecha"], r["hora"]): r["numero"] for r in tz if r["loteria"] == slug}
    par = defaultdict(Counter)
    for r in lh:
        n = tzs.get((r["fecha"], r["hora"]))
        if n is not None:
            par[core.norm(r["animal"])][n] += 1
    print("--", slug, "(pares posibles:", len(par), ")")
    for a, c in sorted(par.items()):
        top, v = c.most_common(1)[0]
        marca = "" if v == sum(c.values()) else "  <-- split %s" % dict(c)
        print("   %-18s -> %d%s" % (a, top, marca))
