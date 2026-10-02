# -*- coding: utf-8 -*-
"""Anexo 3 del PREREGISTRO: prueba ciega de UNA tripleta al día (C3) en 2025-12-18..2026-03-31. Corre una sola vez.
Uso: python herramientas/exploracion/tripleta_inteligente/ciega_c3.py -> ciega_c3.json, salida_ciega_c3.txt"""
import io, json, os, sys, time
from math import comb
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402
import tripleta_ventana as TV  # noqa: E402
SALIDA = os.path.join(AQUI, "ciega_c3.json")
if os.path.exists(SALIDA):
    sys.exit("La prueba ciega ya se corrió (ciega_c3.json). No se repite.")
K = 38; V = 12; PAGO = 45; SEM = 20261002; B = 3000; SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)
D = LE.cargar(os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno", "historial_la.txt"))
n = len(D); X, Y, _ = TV.construir(D)
desde = next(i for i, f in enumerate(D.fecha) if f >= "2025-12-18")
fin = max(i for i in range(n - V + 1) if D.fecha[i + V - 1] <= "2026-03-31") + 1
P = TV.Modelo().predecir(X, Y, LE.W, fin)[desde - LE.W:]
ini = np.arange(desde, fin); seq = np.asarray(D.seq); dia = np.asarray(D.dia)[ini]; hora = np.asarray(D.hora)[ini]
SALE = [set(seq[t:t + V].tolist()) for t in ini]
base = np.array([comb(len(s), 3) / comb(K, 3) for s in SALE])
orden = np.argsort(-P, axis=1, kind="stable")
log(f"tramo ciego: {D.fecha[ini[0]]} .. último inicio {D.fecha[ini[-1]]} (ventana termina {D.fecha[ini[-1]+V-1]}); "
    f"{len(ini)} inicios, {len(np.unique(dia))} jornadas; azar por tripleta {100*base.mean():.2f} %")
h3 = np.array([float(all(a in SALE[i] for a in orden[i, :3])) for i in range(len(ini))])
h456 = np.array([float(all(a in SALE[i] for a in orden[i, 3:6])) for i in range(len(ini))])
u, g = np.unique(dia, return_inverse=True); rng = np.random.default_rng(SEM); idx = rng.integers(0, len(u), (B, len(u)))
def ev(h, f, sel=None):
    sel = np.ones(len(h), bool) if sel is None else sel
    num = np.where(sel, PAGO * h - f, 0); den = np.where(sel, f, 0)
    sn = np.bincount(g, num, minlength=len(u)); sd = np.bincount(g, den, minlength=len(u))
    bs = sn[idx].sum(1) / np.maximum(sd[idx].sum(1), 1e-9)
    return float(num.sum() / den.sum()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], int(h[sel].sum()), int(den.sum())
R = {}
R["C3"] = dict(zip(("ev", "ic95", "aciertos", "tripletas"), ev(h3, np.ones(len(h3)))))
R["A"] = dict(zip(("ev", "ic95", "aciertos", "tripletas"), ev(h3 + h456, 2 * np.ones(len(h3)))))
for nom, hh in (("C3_8am", 0), ("C3_9am", 1)):
    R[nom] = dict(zip(("ev", "ic95", "aciertos", "tripletas"), ev(h3, np.ones(len(h3)), hora == hh)))
for k, v in R.items():
    log(f"  {k:<7} {v['tripletas']:5d} tripletas, {v['aciertos']:3d} aciertos = {100*v['aciertos']/v['tripletas']:.2f} %  "
        f"EV {100*v['ev']:+.1f} % [{100*v['ic95'][0]:+.0f}; {100*v['ic95'][1]:+.0f}]")
pasa = R["C3"]["ev"] > 0 and R["C3"]["ic95"][0] > 0 and R["C3"]["ev"] >= R["A"]["ev"]
R["veredicto"] = "PASA" if pasa else "NO PASA"
log("Veredicto (anexo 3):", R["veredicto"])
json.dump(R, io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
io.open(os.path.join(AQUI, "salida_ciega_c3.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
with io.open(os.path.join(RAIZ, "herramientas", "registro_final.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": "tripleta_ventana C3 (una al día), prueba ciega 2025-12-18..2026-03-31",
                         "preregistro": "herramientas/exploracion/tripleta_inteligente/PREREGISTRO.md (anexo 3)",
                         "C3_ev": round(R["C3"]["ev"], 3), "C3_ic95": [round(x, 3) for x in R["C3"]["ic95"]],
                         "A_ev": round(R["A"]["ev"], 3), "veredicto": R["veredicto"]}, ensure_ascii=False) + "\n")
