# fin de semana vs laborables para el premio k=3 (dev + conteo crudo en cal); mbits dev de candidatos
from comun import *
dev = filas_primero("dev"); cal = filas_primero("cal")
def era(t): return "8:00" if F[t] >= ERA8 else "9:00"
FS = (5, 6)
for e in ("9:00", "8:00", "todo"):
    for nom, cond in (("lun-vie", lambda t: DOW[t] not in FS), ("sáb-dom", lambda t: DOW[t] in FS)):
        f = [t for t in dev if (e == "todo" or era(t) == e) and cond(t)]
        m, o, ex = oe(f, lambda t: S[previo(t,3,'cal')] if previo(t,3,'cal') is not None else None)
        r = poisson_ic(o, ex)
        print(f"dev {e:4s} {nom}: N={m} O={o} E={ex:.2f} O/E={r[0]:.2f} [{r[1]:.2f};{r[2]:.2f}]")
# binomial: dado el total, P(fin de semana <= obs)
f = dev
mw, ow, ew = oe([t for t in f if DOW[t] in FS], lambda t: S[previo(t,3,'cal')] if previo(t,3,'cal') is not None else None)
ml, ol, el = oe([t for t in f if DOW[t] not in FS], lambda t: S[previo(t,3,'cal')] if previo(t,3,'cal') is not None else None)
print("binom P(finde<=obs | total) =", stats.binom.cdf(ow, ow+ol, ew/(ew+el)))
for nom, cond in (("lun-vie", lambda t: DOW[t] not in FS), ("sáb-dom", lambda t: DOW[t] in FS)):
    m = o = 0
    for t in cal:
        tp = previo(t, 3, "cal")
        if tp is None or not cond(t): continue
        m += 1; o += S[t] == S[tp]
    print(f"cal crudo k=3 {nom}: N={m} O={o} E={m/38:.2f}")
# multiplicadores de C2 (ajustados en dev, suavizado +0.5)
m_lv = (ol + 0.5) / (el + 0.5)
print(f"C2: m_lv={m_lv:.3f}  (finde sin premio)")
# mbits en dev contra P_aj
Q1 = [ajustar(t, "abierto") for t in dev]
def c2(t):
    mult = {1: 0.272}
    if DOW[t] not in FS: mult[3] = m_lv
    return ajustar(t, "cal", mult)
Q2 = [c2(t) for t in dev]
for nom, Q in (("C1 abiertos", Q1), ("C2 premio solo lun-vie", Q2)):
    for e in ("9:00", "8:00"):
        idx = [i for i, t in enumerate(dev) if era(t) == e]
        g = mbits([dev[i] for i in idx], [Q[i] for i in idx])
        print(f"{nom} dev {e}: {g[0]:+.2f} [{g[1]:+.2f};{g[2]:+.2f}] mbits/1er sorteo; filas cambiadas={sum(np.abs(Q[i]-PAJ[dev[i]]).max()>1e-12 for i in idx)}")
