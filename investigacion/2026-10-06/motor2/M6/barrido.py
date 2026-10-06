# -*- coding: utf-8 -*-
"""M6: barrido O/E contra PROD en AJUSTE (BH 10 %), confirmación en ELECCION (Bonferroni). Guarda caché de rasgos."""
import sys, os, time, json
import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rasgos as R
from scipy.stats import norm
t0 = time.time()
rdD = A.LE.cargar("/home/user/lotto-activo/rdint_historial.txt")
rd = {(f, int(h)): int(s) for f, h, s in zip(rdD.fecha, rdD.hora, rdD.seq)}
nom, fam, M, DF = R.construir(A.D.seq, A.D.hora, list(A.D.fecha), rd, A.T)
print("rasgos", len(nom), M.shape, f"{time.time()-t0:.0f}s")
np.savez_compressed(os.path.join(A.SP, "m6_rasgos.npz"), M=M, DF=DF, nom=np.array(nom), fam=np.array(fam))
y = A.Y; P = A.PROD
hit = M[:, np.arange(len(y)), y]            # (k, n)
q = (M * P[None]).sum(2)                    # (k, n)
def stats(m):
    out = []
    for k in range(len(nom)):
        s = m & DF[k]
        O = hit[k, s].sum(); E = q[k, s].sum(); Vv = (q[k, s] * (1 - q[k, s])).sum()
        z = (O - E) / np.sqrt(Vv) if Vv > 0 else 0.0
        out.append((int(s.sum()), int(O), E, O / E if E > 0 else np.nan, z))
    return out
res = {tr: stats(A.TRAMOS[tr]) for tr in ("AJUSTE", "ELECCION", "ANTIGUO")}
zA = np.array([r[4] for r in res["AJUSTE"]]); pA = 2 * norm.sf(np.abs(zA))
K = len(nom); o = np.argsort(pA); thr = 0.10 * np.arange(1, K + 1) / K
pas = pA[o] <= thr; kmax = np.max(np.where(pas)[0]) + 1 if pas.any() else 0
sobrev = set(o[:kmax].tolist())
print(f"BH 10 %: {kmax} supervivientes de {K}")
with open("barrido.tsv", "w") as fh:
    fh.write("rasgo\tfam\tnA\tOA\tEA\tOE_A\tzA\tpA\tOE_E\tzE\tOE_ANT\tzANT\tBH\n")
    for k in o:
        a, e, an = res["AJUSTE"][k], res["ELECCION"][k], res["ANTIGUO"][k]
        fh.write(f"{nom[k]}\t{fam[k]}\t{a[0]}\t{a[1]}\t{a[2]:.1f}\t{a[3]:.3f}\t{a[4]:+.2f}\t{pA[k]:.2g}\t{e[3]:.3f}\t{e[4]:+.2f}\t{an[3]:.3f}\t{an[4]:+.2f}\t{int(k in sobrev)}\n")
print("top-30 por p en AJUSTE:")
for k in o[:30]:
    a, e, an = res["AJUSTE"][k], res["ELECCION"][k], res["ANTIGUO"][k]
    print(f"{nom[k]:28s} {fam[k]} O={a[1]:4d} E={a[2]:6.1f} O/E A {a[3]:.2f} z {a[4]:+.2f} p {pA[k]:.1e} | ELEC {e[3]:.2f} z {e[4]:+.2f} | ANT {an[3]:.2f} z {an[4]:+.2f}{'  *BH' if k in sobrev else ''}")
ks = sorted(sobrev, key=lambda k: pA[k]); kk = max(len(ks), 1)
conf = []
for k in ks:
    a, e = res["AJUSTE"][k], res["ELECCION"][k]
    pe = norm.sf(e[4] * np.sign(a[4]))
    ok = pe < 0.05 / kk
    if ok: conf.append(nom[k])
    print(f"CONFIRMACION {nom[k]}: ELEC O/E {e[3]:.3f} z {e[4]:+.2f} p1 {pe:.2g} umbral {0.05/kk:.2g} -> {'CONFIRMA' if ok else 'no'}")
json.dump(dict(sobrevivientes=[nom[k] for k in ks], confirmados=conf), open("confirmados.json", "w"), ensure_ascii=False, indent=1)
# resumen por familia: max |z| en AJUSTE y nº con p<0.01
for f in sorted(set(fam)):
    idx = [k for k in range(K) if fam[k] == f]
    print(f"familia {f}: {len(idx)} rasgos, p<0.01 en AJUSTE: {sum(pA[k] < 0.01 for k in idx)} (esperado {0.01*len(idx):.1f}), max|z| {max(abs(zA[k]) for k in idx):.2f}")
print(f"{time.time()-t0:.0f}s")
