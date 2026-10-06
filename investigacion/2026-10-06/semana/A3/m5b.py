exec(open("m5_ablacion_regla.py").read().split("fit = ")[0])
fit = (f >= "2026-01-01") & (f <= "2026-06-30"); tst = (f >= "2026-07-01")
for g, gm in (("MVF", MVF),):
    r = minimize(nll, [0, 0], args=(fit & gm,), method="Nelder-Mead"); a, b = np.exp(r.x)
    m = tst & gm; Qm = aplica(r.x, m); ym = y[m]; ii = np.arange(m.sum()); mb = 1000*np.log2(Qm[ii, ym]/P[m][ii, ym])
    oq = np.argsort(-Qm, 1, kind="stable"); h15 = (np.argmax(oq == ym[:, None], 1) < 15).mean()
    print(f"(c) ajuste 26-T1+T2, prueba 26-T3 MVF: ×{a:.2f} hoy, ×{b:.2f} anteayer → {mb.mean():+.1f} mbits/sorteo (n={m.sum()}), Top-15 {IN15[m].mean()*100:.1f}% → {h15*100:.1f}%")
