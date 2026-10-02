# -*- coding: utf-8 -*-
"""Anexo 1 del PREREGISTRO: réplica débil ÚNICA de la tripleta en abr-sep 2026 (se niega a correr dos veces).
Uso: python herramientas/exploracion/tripleta_inteligente/replica_2026.py -> replica_2026.json, salida_replica_2026.txt"""
import io, json, os, sys, time
from math import comb
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402
import tripleta_ventana as TV  # noqa: E402
SALIDA = os.path.join(AQUI, "replica_2026.json")
if os.path.exists(SALIDA):
    sys.exit("La réplica ya se corrió una vez (replica_2026.json). No se repite.")
K = 38; V = 12; PAGO = 45; SEM = 20261002; B = 3000; SAL = []


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)


D = LE.cargar(os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno", "historial_la.txt"))
n = len(D); FIN = n - V + 1
X, Y, _ = TV.construir(D)
desde = next(i for i, f in enumerate(D.fecha) if f >= "2026-04-01")
P = TV.Modelo().predecir(X, Y, LE.W, FIN)[desde - LE.W:]
ini = np.arange(desde, FIN); seq = np.asarray(D.seq); dia = np.asarray(D.dia)[ini]; fecha = [D.fecha[t] for t in ini]
SALE = [set(seq[t:t + V].tolist()) for t in ini]
base = np.array([comb(len(s), 3) / comb(K, 3) for s in SALE])
orden = np.argsort(-P, axis=1, kind="stable")
log(f"ventanas {len(ini)}: {fecha[0]} .. {fecha[-1]} (última termina {D.fecha[-1]}); azar por tripleta {100*base.mean():.2f} %")


def neg(i):
    d = int(fecha[i][8:10]); return {LE.IDX[str(x)] for x in (d, d + 1) if 1 <= x <= 36}


def lista(i, ln):
    o = orden[i].tolist()
    return [a for a in o if a not in neg(i)] if ln else o


ESTR = {"A": lambda i: [lista(i, False)[:3], lista(i, False)[3:6]], "C3": lambda i: [lista(i, False)[:3]],
        "A_lista_negra": lambda i: [lista(i, True)[:3], lista(i, True)[3:6]], "C3_lista_negra": lambda i: [lista(i, True)[:3]]}
R = {}
u, g = np.unique(dia, return_inverse=True)
rng = np.random.default_rng(SEM); idx = rng.integers(0, len(u), (B, len(u)))
evw = {}
for nom, fn in ESTR.items():
    h = np.zeros(len(ini)); f = np.zeros(len(ini))
    for i in range(len(ini)):
        cs = fn(i); f[i] = len(cs); h[i] = sum(all(a in SALE[i] for a in c) for c in cs)
    num = PAGO * h - f
    sn = np.bincount(g, num); sd = np.bincount(g, f); bs = sn[idx].sum(1) / sd[idx].sum(1)
    evw[nom] = num / f
    R[nom] = dict(tripletas=int(f.sum()), aciertos=int(h.sum()), tasa=float(h.sum() / f.sum()), ev=float(num.sum() / f.sum()),
                  ic95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], cobra=float(np.mean(h > 0)))
    log(f"  {nom:<15} {int(f.sum()):5d} tripletas, {int(h.sum()):3d} aciertos = {100*R[nom]['tasa']:.2f} %  "
        f"EV {100*R[nom]['ev']:+.1f} % [{100*R[nom]['ic95'][0]:+.0f}; {100*R[nom]['ic95'][1]:+.0f}]")
for nom in ("C3", "A_lista_negra", "C3_lista_negra"):
    dv = evw[nom] - evw["A"]; s = np.bincount(g, dv); c = np.bincount(g); bs = s[idx].sum(1) / c[idx].sum(1)
    R[nom]["dif_vs_A"] = [float(dv.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    log(f"  {nom} - A: {100*dv.mean():+.1f} pp [{100*R[nom]['dif_vs_A'][1]:+.0f}; {100*R[nom]['dif_vs_A'][2]:+.0f}]")
ok = R["C3_lista_negra"]["ev"] > 0 and R["C3_lista_negra"]["dif_vs_A"][0] >= 0
R["veredicto"] = "SE ADOPTA C3 + lista negra" if ok else "NO se adopta"
log("Veredicto (anexo 1):", R["veredicto"])
json.dump(R, io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
io.open(os.path.join(AQUI, "salida_replica_2026.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
with io.open(os.path.join(RAIZ, "herramientas", "registro_final.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": "tripleta_ventana: A, C3 y lista negra (réplica débil abr-sep 2026)",
                         "preregistro": "herramientas/exploracion/tripleta_inteligente/PREREGISTRO.md (anexo 1)",
                         "resultado": {k: (round(v["ev"], 3) if isinstance(v, dict) else v) for k, v in R.items()}},
                        ensure_ascii=False) + "\n")
