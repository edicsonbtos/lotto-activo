# ag06 — ajuste SOLO en dev de la corrección del primer sorteo: q ∝ P_aj^β · exp(θ[bin de hueco])
# bins de hueco en días (0 = salió ayer): A={0,1}, B={2,3}, C={4,5,6}, D={7+ o nunca}
import os, json, numpy as np
from scipy import optimize
AQUI = os.path.dirname(os.path.abspath(__file__))
R = np.load(os.path.join(AQUI, "rasgos.npz"))
TR, ERA, Y, PA = R["TR"], R["ERA"], R["Y"], R["PA"]
hd = R["hdias"]
BIN = np.select([hd <= 1, hd <= 3, hd <= 6], [0, 1, 2], 3)
ONE = np.eye(4)[BIN]  # (filas, 38, 4)

def q_de(par, m, usa_beta, usa_bins):
    beta = par[0] if usa_beta else 1.0
    th = par[1:5] if usa_bins else np.zeros(4)
    L = beta * np.log(PA[m]) + ONE[m] @ th
    L -= L.max(1, keepdims=True); q = np.exp(L); return q / q.sum(1, keepdims=True)

def obj(par, m, usa_beta, usa_bins, lam):
    q = q_de(par, m, usa_beta, usa_bins)
    ll = np.log(q[np.arange(m.sum()), Y[m]]).sum()
    pen = lam * (np.sum((par[1:5] if usa_bins else 0) ** 2) + ((par[0] - 1) ** 2 if usa_beta else 0))
    return -ll + pen

def ajustar(m, usa_beta, usa_bins, lam):
    r = optimize.minimize(obj, np.array([1.0, 0, 0, 0, 0]), args=(m, usa_beta, usa_bins, lam), method="L-BFGS-B")
    return r.x

def mbits(par, m, usa_beta, usa_bins):
    q = q_de(par, m, usa_beta, usa_bins)
    i = np.arange(m.sum())
    return 1000 * np.mean(np.log2(q[i, Y[m]] / PA[m][i, Y[m]]))

dev = TR == "dev"; e9 = dev & (ERA == 9); e8 = dev & (ERA == 8)
CAND = {"C1_temperatura": (True, False), "C2_bins_hueco": (False, True), "C3_temp+bins": (True, True)}
print("Validación cruzada entre eras (ajusta en una era, mide en la otra), mbits por primer sorteo")
elec = {}
for nom, (ub, ui) in CAND.items():
    for lam in (0, 2, 5, 10, 20, 50):
        a = mbits(ajustar(e9, ub, ui, lam), e8, ub, ui); b = mbits(ajustar(e8, ub, ui, lam), e9, ub, ui)
        print(f"{nom:16s} λ={lam:3d}  9→8 {a:+6.1f}  8→9 {b:+6.1f}  media {(a+b)/2:+6.1f}")
        if nom not in elec or (a + b) / 2 > elec[nom][1]: elec[nom] = (lam, (a + b) / 2)
print()
PAR = {}
for nom, (ub, ui) in CAND.items():
    lam = max(elec[nom][0], 2)  # suavizado mínimo λ=2 aunque la VC prefiera 0
    p = ajustar(dev, ub, ui, lam)
    PAR[nom] = dict(lam=lam, beta=float(p[0]) if ub else 1.0, theta=[float(x) for x in p[1:5]] if ui else [0.0]*4,
                    usa_beta=ub, usa_bins=ui)
    th = np.array(PAR[nom]["theta"]); mult = np.exp(th)
    print(f"{nom}: λ={lam} β={PAR[nom]['beta']:.3f} mult bins A,B,C,D = {np.round(mult,3)}  "
          f"dev in-sample {mbits(p, dev, ub, ui):+.1f} (era9 {mbits(p, e9, ub, ui):+.1f}, era8 {mbits(p, e8, ub, ui):+.1f}) mbits")
json.dump(PAR, open(os.path.join(AQUI, "parametros_dev.json"), "w"), indent=1)
