# -*- coding: utf-8 -*-
"""Anexo 5: a las 8:00, ¿2 o 3 animales más? Antes: reentreno/sub.py todo I|S|H (cache).
Uso: python herramientas/exploracion/tripleta_inteligente/top_n_8am.py -> salida_top_n_8am.txt"""
import io, json, os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno"); sys.path.insert(0, RE)
import comun as C  # noqa: E402
LE = C.LE; K = 38; SEM = 20261002; SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)
D = LE.cargar(os.path.join(RE, "historial_la.txt")); seq = np.asarray(D.seq); dia = np.asarray(D.dia); hora = np.asarray(D.hora); n = len(seq)
L = C.cargar_L("todo", ["I", "S", "H"]); P = C.combinar(L, seq[C.ARRANQUE:], LE.W, **C.COMB["base"])
POST0 = next(i for i, f in enumerate(D.fecha) if f >= "2025-12-18")
def tabla(nombre, ts, pos, dd):
    log(f"\n{nombre} (n={len(ts)})")
    for N in (15, 16, 17, 18, 20):
        log(f"  Top-{N}: acierta {100*np.mean(pos < N):.1f} %")
    for r in (15, 16, 17):
        log(f"  puesto {r+1}: acierta {100*np.mean(pos == r):.1f} %  (vale la plata si > 3,33 %)")
    for N in (15, 17, 18):
        w = np.zeros(K); w[:N] = [3, 3, 3, 2, 2] + [1] * (N - 5)
        plano = (30 * (pos < N) - N) / N; pond = (30 * w[pos] - w.sum()) / w.sum()
        log(f"  Top-{N} plano {100*plano.mean():+.1f} % por ficha | ponderado {100*pond.mean():+.1f} % por ficha")
    return {N: float(np.mean(pos < N)) for N in (15, 16, 17, 18, 20)} | {f"p{r+1}": float(np.mean(pos == r)) for r in (15, 16, 17)}
R = {}
for nom, ts in (("LA 8:00 desarrollo", [t for t in range(LE.W, LE.CORTE_FIJO) if hora[t] == 0]),
                ("LA 8:00 post-desarrollo (2025-12-18..2026-09-29)", [t for t in range(POST0, n) if hora[t] == 0])):
    pos = np.array([int(np.where(np.argsort(-P[t - LE.W], kind="stable") == seq[t])[0][0]) for t in ts])
    R[nom] = tabla(nom, ts, pos, dia[ts])
# ¿sigue viva la regla en 2026?
pdia = {}
for t in range(n):
    pdia.setdefault(dia[t], set()).add(int(seq[t]))
for nom, ts in (("desarrollo", [t for t in range(LE.W, LE.CORTE_FIJO) if hora[t] == 0]),
                ("post-desarrollo", [t for t in range(POST0, n) if hora[t] == 0])):
    o = sum(seq[t] in pdia.get(dia[t] - 1, ()) for t in ts); e = sum(len(pdia.get(dia[t] - 1, ())) / 38 for t in ts)
    log(f"\nRegla de las 8:00 ({nom}): lo que salió ayer sale O/E {o/e:.2f} (n={len(ts)})")
    R[f"oe_ayer_{nom}"] = o / e
# RD 8:30 (desarrollo de RD)
c = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "cache_todo.npz")); s = c["tramo"] == "dev"
P1 = c["P1"][s].astype(float); y1 = c["y"][s]; h1 = c["hora"][s]
m = h1 == 0
pos1 = np.array([int(np.where(np.argsort(-P1[i], kind="stable") == y1[i])[0][0]) for i in np.where(m)[0]])
R["RD 8:30 desarrollo"] = tabla("RD 8:30 desarrollo de RD", list(np.where(m)[0]), pos1, None)
io.open(os.path.join(AQUI, "salida_top_n_8am.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
with io.open(os.path.join(RAIZ, "herramientas", "registro_final.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": "Top-15..20 a las 8:00 (réplica débil post-desarrollo)",
                         "preregistro": "herramientas/exploracion/tripleta_inteligente/PREREGISTRO.md (anexo 5)",
                         "resultado": {k: v for k, v in R.items() if not isinstance(v, dict)}}, ensure_ascii=False) + "\n")
