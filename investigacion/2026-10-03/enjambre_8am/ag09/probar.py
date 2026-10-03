# Prueba ÚNICA de los candidatos pre-registrados (PREREGISTRO.md). Reproducible: python3 probar.py
from comun import *
FS = (5, 6); M_LV = 2.117
def c1(t): return ajustar(t, "abierto")
def c2(t):
    mult = {1: 0.272}
    if DOW[t] not in FS: mult[3] = M_LV
    return ajustar(t, "cal", mult)
def era(t): return "8:00" if F[t] >= ERA8 else "9:00"
def topk(q, k): return np.argsort(-q, kind="stable")[:k]
def plata(filas, Q, B=2000, semilla=0):
    out = {}
    for k in (5, 15):
        h0 = np.array([S[t] in topk(PAJ[t], k) for t in filas], float)
        h1 = np.array([S[t] in topk(Q[i], k) for i, t in enumerate(filas)], float)
        d = h1 - h0; rng = np.random.default_rng(semilla)
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(B)]
        # retorno por ficha (Top-k plano, paga 30): 30*aciertos/(k*filas) - 1; diferencia = 30*Δaciertos/(k*filas)
        r = 30 * d.mean() / k
        out[k] = (int(h0.sum()), int(h1.sum()), r, 30*np.percentile(bs,2.5)/k, 30*np.percentile(bs,97.5)/k)
    return out
for tr in ("dev", "prueba", "vivo"):
    filas = filas_primero(tr)
    print(f"\n===== {tr} (n={len(filas)})")
    for nom, fn in (("C1 abiertos", c1), ("C2 premio lun-vie", c2)):
        Q = [fn(t) for t in filas]
        ch = sum(np.abs(Q[i] - PAJ[t]).max() > 1e-12 for i, t in enumerate(filas))
        g = mbits(filas, Q)
        rng = np.random.default_rng(0); gg = g[3]
        p = np.mean([gg[rng.integers(0, len(gg), len(gg))].mean() <= 0 for _ in range(2000)])
        pl = plata(filas, Q)
        print(f" {nom}: {g[0]:+.2f} mbits [{g[1]:+.2f};{g[2]:+.2f}] p(≤0)={p:.3f} filas cambiadas={ch}")
        for k, v in pl.items():
            print(f"    Top-{k}: {v[0]} -> {v[1]} aciertos; Δretorno/ficha {v[2]*100:+.2f} pp [{v[3]*100:+.2f};{v[4]*100:+.2f}]")
    # C2: binomial condicional, E contra P sin ajuste
    tgt = lambda t: S[previo(t,3,'cal')] if previo(t,3,'cal') is not None else None
    _, ow, ew = oe([t for t in filas if DOW[t] in FS], tgt)
    _, ol, el = oe([t for t in filas if DOW[t] not in FS], tgt)
    pb = stats.binom.cdf(ow, ow+ol, ew/(ew+el)) if ow+ol > 0 else np.nan
    print(f" k=3 lun-vie O={ol} E={el:.2f} O/E={ol/el:.2f} | sáb-dom O={ow} E={ew:.2f} O/E={ow/ew:.2f} | binom p={pb:.3f}")
    # (1)/(2) filas tras cierre y discrepancias
    for k in (1, 3):
        dis = [t for t in filas if previo(t,k,'cal') != previo(t,k,'abierto')]
        hc = sum(previo(t,k,'cal') is not None and S[t]==S[previo(t,k,'cal')] for t in dis)
        ha = sum(previo(t,k,'abierto') is not None and S[t]==S[previo(t,k,'abierto')] for t in dis)
        ea = sum(P[t, S[previo(t,k,'abierto')]] for t in dis if previo(t,k,'abierto') is not None)
        ec = sum(P[t, S[previo(t,k,'cal')]] for t in dis if previo(t,k,'cal') is not None)
        print(f" k={k} discrepantes={len(dis)}: aciertos cal {hc} (E {ec:.2f}) | abiertos {ha} (E {ea:.2f})")
    # O/E reglas de producción por era en este tramo (referencia)
    for k in (1, 3):
        m, o, ex = oe(filas, lambda t: S[previo(t,k,'cal')] if previo(t,k,'cal') is not None else None)
        r = poisson_ic(o, ex); print(f" ref k={k} cal: N={m} O={o} E={ex:.2f} O/E={r[0]:.2f} [{r[1]:.2f};{r[2]:.2f}]")
# (1) todas las filas tras cierre, todos los tramos
print("\n(1) tras cierre, todos los tramos:")
for d in dias[1:]:
    j = ordinal[d]
    if d - dias[j-1] == 1: continue
    t = first[d]; t1 = first[dias[j-1]]; t3 = first[dias[j-3]]; t3c = first.get(d-3)
    print(f" {F[t]} {T[t]:6s} cierre={d-dias[j-1]-1}d gana={S[t]:2d} 1ºúlt.abierto={S[t1]:2d} 1º-3abiertos={S[t3]:2d} 1º-3cal={'—' if t3c is None else S[t3c]}"
          f" p_motor(últ.abierto)={'—' if np.isnan(P[t,0]) else round(float(P[t,S[t1]]),3)}")
