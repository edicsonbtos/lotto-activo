import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import correccion as C; A = C.A
aj = np.where(A.TRAMOS["AJUSTE"])[0]
for lista in (["RD1:igual"], ["par_evita"], ["RD1:igual", "par_evita", "RD2:igual"]):
    X = C.X_de(lista); B = C.walk_forward(X); A.evaluar(C.aplicar(X, B), "+".join(lista) + "_wf")
# mezcla log-lineal sobre V1 wf
Pw = np.load(os.path.join(A.SP, "m6_V1_conf_wf.npy")).astype(float)
for w in (0.5, 0.8, 1.2, 1.5):
    Q = A.PROD ** (1 - w) * Pw ** w; A.evaluar(Q / Q.sum(1, keepdims=True), f"V1_mezcla_w{w}", tramos=("ELECCION",))
# par_evita por subgrupos (O/E contra PROD)
z = np.load(os.path.join(A.SP, "m6_rasgos.npz")); nom = list(z["nom"]); k = nom.index("par_evita")
M = z["M"][k]; DF = z["DF"][k]; y = A.Y; P = A.PROD; hit = M[np.arange(len(y)), y]; q = (M * P).sum(1)
def oe(s): s = s & DF; O, E, V = hit[s].sum(), q[s].sum(), (q[s] * (1 - q[s])).sum(); return f"O/E {O/E:.3f} z {(O-E)/np.sqrt(V):+.2f} (O {O}, E {E:.0f})"
for tr in ("ANTIGUO", "AJUSTE", "ELECCION"):
    m = A.TRAMOS[tr]
    print(tr, "todo", oe(m), "| mié-vie", oe(m & np.isin(A.DOW, [2, 3, 4])), "| resto", oe(m & ~np.isin(A.DOW, [2, 3, 4])), "| h<6", oe(m & (A.H < 6)), "| h>=6", oe(m & (A.H >= 6)))
m = A.TRAMOS["ELECCION"]
for mes in ("2026-03", "2026-04", "2026-05", "2026-06"): print(mes, oe(m & np.array([f.startswith(mes) for f in A.F])))
print("tamaño medio del conjunto par_evita:", M[DF].sum(1).mean(), " masa PROD:", q[DF].mean())
# Top-5 con la regla de cambio RD (h-1):30 ya aplicada en vivo: quitar el RD1 del Top-5 de PROD y de V1
r = M  # placeholder
rd = z["M"][nom.index("RD1:igual")]
def ret_swap(P, msk):
    i = np.where(msk)[0]; Pp = P[i].copy(); Pp[rd[i]] = 0; o = np.argsort(-Pp, 1, kind="stable"); rk = np.argmax(o == y[i][:, None], 1)
    return (np.where(rk < 5, 30 * A.FICHAS[np.minimum(rk, 4)], 0) / 8 - 1).mean() * 100, np.mean(rk < 5) * 100, np.mean(rk < 15) * 100
for tr in ("AJUSTE", "ELECCION"):
    print(tr, "PROD+cambioRD ret/top5/top15 %.1f %.2f %.2f" % ret_swap(P, A.TRAMOS[tr]), "| V1+cambioRD %.1f %.2f %.2f" % ret_swap(Pw, A.TRAMOS[tr]))
