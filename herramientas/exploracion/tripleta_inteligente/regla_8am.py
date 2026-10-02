# -*- coding: utf-8 -*-
"""Anexo 4 del PREREGISTRO: la regla de las 8:00 en el motor (parte A) y en la tripleta (parte B, modelo T8).
Antes: cd herramientas/exploracion/enjambre_2026-09-30/reentreno && for k in I S H; do python sub.py todo $k; done
Uso: python herramientas/exploracion/tripleta_inteligente/regla_8am.py -> regla_8am.json, salida_regla_8am.txt
Corre una sola vez (escribe en registro_final.jsonl)."""
import io, json, os, sys, time
from math import comb
import numpy as np
from scipy.optimize import minimize
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno")
sys.path.insert(0, RE); sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import comun as C  # noqa: E402
import tripleta_ventana as TV  # noqa: E402
LE = C.LE
SALIDA = os.path.join(AQUI, "regla_8am.json")
if os.path.exists(SALIDA):
    sys.exit("Ya se corrió (regla_8am.json). No se repite.")
K = 38; V = 12; PAGO = 45; SEM = 20261002; B = 3000; CORTE = LE.CORTE_FIJO; MITAD = 5688
SAL = []; RES = {}
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)
D = LE.cargar(os.path.join(RE, "historial_la.txt")); seq = np.asarray(D.seq); dia = np.asarray(D.dia)
hora = np.asarray(D.hora); n = len(seq)
POST0 = next(i for i, f in enumerate(D.fecha) if f >= "2025-12-18")
def boot(v, dd, w=None):
    w = np.ones(len(v)) if w is None else w
    u, g = np.unique(dd, return_inverse=True); s = np.bincount(g, v * w); c = np.bincount(g, w)
    rng = np.random.default_rng(SEM); i = rng.integers(0, len(u), (B, len(u))); bs = s[i].sum(1) / c[i].sum(1)
    return float((v * w).sum() / w.sum()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
# hueco en días de cada animal antes de cada sorteo
ult = np.full(K, -10**6); GD = np.zeros((n, K), int)
for t in range(n):
    GD[t] = dia[t] - ult; ult[seq[t]] = dia[t]

# ============================ PARTE A
log("PARTE A — ¿el motor ya está optimizado para las 8:00?")
L = C.cargar_L("todo", ["I", "S", "H"]); P = C.combinar(L, seq[C.ARRANQUE:], LE.W, **C.COMB["base"])  # filas W..n-1
grupos = {"salió ayer": (1, 1), "hace 2-3 días": (2, 3), "hace 4+ días": (4, 10**7)}
ocho_dev = [t for t in range(LE.W, CORTE) if hora[t] == 0]
ocho_post = [t for t in range(POST0, n) if hora[t] == 0]
A1 = {}
for nom, (lo, hi) in grupos.items():
    m = (GD[ocho_dev] >= lo) & (GD[ocho_dev] <= hi)
    o = sum(m[i, seq[t]] for i, t in enumerate(ocho_dev)); e = sum(P[t - LE.W][m[i]].sum() for i, t in enumerate(ocho_dev))
    A1[nom] = dict(obs=int(o), esp_motor=float(e), oe=float(o / e))
    log(f"  A1 {nom}: sale {int(o)}, el motor esperaba {e:.1f} → O/E contra el motor {o/e:.2f}")
optim = all(0.90 <= v["oe"] <= 1.10 for v in A1.values())
RES["A1"] = A1; RES["A1_motor_optimizado"] = optim
log("  =>", "EL MOTOR YA ESTÁ OPTIMIZADO PARA LAS 8:00" if optim else "hay margen: se prueba la corrección A2")
if not optim:
    def Xg(ts):
        X = np.zeros((len(ts), K, 2))
        for i, t in enumerate(ts):
            X[i, :, 0] = GD[t] == 1; X[i, :, 1] = (GD[t] >= 2) & (GD[t] <= 3)
        return X
    Xd = Xg(ocho_dev); Ld = np.log(np.array([P[t - LE.W] for t in ocho_dev])); yd = seq[ocho_dev]
    def f(w):
        z = Ld + Xd @ w; z -= z.max(1, keepdims=True); lse = np.log(np.exp(z).sum(1))
        return -(z[np.arange(len(yd)), yd] - lse).sum()
    w = minimize(f, np.zeros(2), method="L-BFGS-B").x
    log(f"  A2 multiplicadores (ajustados en desarrollo): salió ayer ×{np.exp(w[0]):.2f}, hace 2-3 d ×{np.exp(w[1]):.2f}")
    Xp = Xg(ocho_post); Lp = np.log(np.array([P[t - LE.W] for t in ocho_post])); yp = seq[ocho_post]
    z = Lp + Xp @ w; z -= z.max(1, keepdims=True); Pc = np.exp(z); Pc /= Pc.sum(1, keepdims=True); P0 = np.exp(Lp)
    mb = (np.log2(Pc[np.arange(len(yp)), yp]) - np.log2(P0[np.arange(len(yp)), yp])) * 1000
    f5 = np.zeros(K); f5[:5] = [2, 2, 2, 1, 1]
    def r5(PP):
        pos = np.argmax(np.argsort(-PP, 1, kind="stable") == yp[:, None], 1); return (30 * f5[pos] - 8) / 8, pos
    ra, pa = r5(P0); rb, pb = r5(Pc)
    dd = dia[ocho_post]
    RES["A2"] = dict(mult=[float(np.exp(x)) for x in w], n=len(ocho_post), dif_mbits=boot(mb, dd),
                     top5esc_base=float(ra.mean()), top5esc_corr=float(rb.mean()), dif_top5esc=boot(rb - ra, dd),
                     top15_base=float(np.mean(pa < 15)), top15_corr=float(np.mean(pb < 15)))
    x = RES["A2"]
    RES["A2"]["veredicto"] = "PASA → sombra" if x["dif_mbits"][1][0] > 0 else "NO PASA"
    log(f"  A2 post-desarrollo (8:00, n={len(ocho_post)}): dif mbits {x['dif_mbits'][0]:+.1f} [{x['dif_mbits'][1][0]:+.1f}; "
        f"{x['dif_mbits'][1][1]:+.1f}]; Top-5 escalonado {100*x['top5esc_base']:+.1f} % → {100*x['top5esc_corr']:+.1f} %; "
        f"Top-15 {100*x['top15_base']:.1f} % → {100*x['top15_corr']:.1f} %  => {x['veredicto']}")

# ============================ PARTE B
log("\nPARTE B — tripleta con la regla de las 8:00 (T8)")
X0, Y, nombres = TV.construir(D)
KK = np.zeros(n, int); k = 0
for t in range(n):
    k = 0 if (t == 0 or dia[t] != dia[t - 1]) else k + 1; KK[t] = k
ayer1 = np.zeros((n, K), bool)
pdia = {}
for t in range(n):
    pdia.setdefault(dia[t], set()).add(int(seq[t]))
hoy1 = np.zeros((n, K), bool); ocho_hoy = np.zeros((n, K), bool)
for t in range(n):
    for a in pdia.get(dia[t] - 1, ()):
        ayer1[t, a] = True
    s = t - KK[t]
    for j in range(s, t):
        hoy1[t, seq[j]] = True
    if KK[t] >= 1 and hora[s] == 0:
        ocho_hoy[t, seq[s]] = True
extra = [((ayer1 & ~hoy1) & (KK[:, None] == kk)).astype(np.float32) for kk in range(12)] + [ocho_hoy.astype(np.float32)]
X8 = np.concatenate([X0, np.stack(extra, 2)], axis=2)
FIN = n - V + 1
t0 = time.time()
Pb = TV.Modelo().predecir(X0, Y, LE.W, FIN); P8 = TV.Modelo().predecir(X8, Y, LE.W, FIN)
log(f"  modelos ajustados en {time.time()-t0:.0f}s")
ini = np.arange(LE.W, FIN); Yv = Y[LE.W:FIN]
SALE = [set(seq[t:t + V].tolist()) for t in ini]
def mbits(Pp):
    p = np.clip(Pp, 1e-6, 1 - 1e-6); return (Yv * np.log2(p) + (1 - Yv) * np.log2(1 - p)).mean(1) * 1000
dmb = mbits(P8) - mbits(Pb)
def ev(Pp, estr):
    o = np.argsort(-Pp, 1, kind="stable"); h = np.zeros(len(ini)); f = np.zeros(len(ini))
    for i in range(len(ini)):
        cs = [o[i, :3]] if estr == "C3" else [o[i, :3], o[i, 3:6]]
        f[i] = len(cs); h[i] = sum(all(a in SALE[i] for a in c) for c in cs)
    return (PAGO * h - f) / f
tramos = {"dev-B": (ini >= MITAD) & (ini <= CORTE - V), "post-desarrollo": (ini >= POST0)}
RES["B"] = {}
for nom, sel in tramos.items():
    dd = dia[ini][sel]
    r = dict(n=int(sel.sum()), dif_mbits=boot(dmb[sel], dd))
    for e in ("A", "C3"):
        vb = ev(Pb[sel], e) if False else None
    eA_b = ev(Pb, "A")[sel]; eA_8 = ev(P8, "A")[sel]; eC_b = ev(Pb, "C3")[sel]; eC_8 = ev(P8, "C3")[sel]
    r.update(evA_base=boot(eA_b, dd), evA_T8=boot(eA_8, dd), evC3_base=boot(eC_b, dd), evC3_T8=boot(eC_8, dd),
             dif_evA=boot(eA_8 - eA_b, dd))
    RES["B"][nom] = r
    log(f"  {nom} ({r['n']} ventanas): dif mbits/animal {r['dif_mbits'][0]:+.2f} [{r['dif_mbits'][1][0]:+.2f}; {r['dif_mbits'][1][1]:+.2f}]; "
        f"EV A base {100*r['evA_base'][0]:+.0f} % → T8 {100*r['evA_T8'][0]:+.0f} % (dif {100*r['dif_evA'][0]:+.1f} pp "
        f"[{100*r['dif_evA'][1][0]:+.0f}; {100*r['dif_evA'][1][1]:+.0f}]); EV C3 {100*r['evC3_base'][0]:+.0f} % → {100*r['evC3_T8'][0]:+.0f} %")
b1, b2 = RES["B"]["dev-B"], RES["B"]["post-desarrollo"]
pasa = b1["dif_mbits"][1][0] > 0 and b2["dif_mbits"][1][0] > 0 and b2["evA_T8"][0] >= b2["evA_base"][0]
RES["B_veredicto"] = "PASA" if pasa else "NO PASA"
log("  =>", RES["B_veredicto"])
json.dump(RES, io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
io.open(os.path.join(AQUI, "salida_regla_8am.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
with io.open(os.path.join(RAIZ, "herramientas", "registro_final.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"),
                         "modelo": "regla 8:00 en motor (A) y tripleta T8 (B); réplica débil 2025-12-18..2026-09-29",
                         "preregistro": "herramientas/exploracion/tripleta_inteligente/PREREGISTRO.md (anexo 4)",
                         "A1_motor_optimizado": RES["A1_motor_optimizado"], "A2": RES.get("A2", {}).get("veredicto"),
                         "B": RES["B_veredicto"]}, ensure_ascii=False) + "\n")
