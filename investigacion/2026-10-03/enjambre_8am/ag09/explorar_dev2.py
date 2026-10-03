# (2) detalle filas discrepantes k=3 y (3) estratificación por día de la semana — SOLO dev
from comun import *
dev = filas_primero("dev")
def era(t): return "8:00" if F[t] >= ERA8 else "9:00"
print("k=3 filas discrepantes (dev):")
oc = oa = ec = ea = 0
for t in dev:
    tc, ta = previo(t, 3, "cal"), previo(t, 3, "abierto")
    if tc == ta: continue
    hc = tc is not None and S[t] == S[tc]; ha = ta is not None and S[t] == S[ta]
    oc += hc; oa += ha
    ec += P[t, S[tc]] if tc is not None else 0; ea += P[t, S[ta]] if ta is not None else 0
    if hc or ha: print("  ACIERTO", F[t], "cal" if hc else "", "abierto" if ha else "")
print(f"  cal: O={oc} E={ec:.2f} | abierto: O={oa} E={ea:.2f}")
# k=1 discrepantes: sólo existe la regla abierta
o = sum(S[t] == S[previo(t,1,'abierto')] for t in dev if previo(t,1,'cal') is None)
print("k=1 tras cierre: O =", o)

DN = ["lun","mar","mié","jue","vie","sáb","dom"]
print("\n(3) O/E por día de la semana (dev, regla calendario = producción), contra P sin ajuste")
nmir = 0
for k in (1, 3):
    for e in ("9:00", "8:00"):
        Os, Es = [], []
        lin = f" k={k} {e}: "
        for w in range(7):
            f = [t for t in dev if era(t) == e and DOW[t] == w]
            m, o, ex = oe(f, lambda t: S[previo(t,k,'cal')] if previo(t,k,'cal') is not None else None)
            Os.append(o); Es.append(ex); nmir += 1
            lin += f"{DN[w]} {o}/{ex:.1f}  "
        Os, Es = np.array(Os), np.array(Es)
        # heterogeneidad: dentro del grupo, O_w | total ~ Multinomial(Es/sum)
        Ot = Os.sum(); pw = Es / Es.sum()
        chi = ((Os - Ot*pw)**2 / (Ot*pw)).sum() if Ot > 0 else 0
        # p por Monte Carlo
        rng = np.random.default_rng(1)
        sim = rng.multinomial(max(Ot,1), pw, 20000)
        cs = ((sim - Ot*pw)**2 / (Ot*pw + 1e-12)).sum(1)
        print(lin, f"| heterog. chi2={chi:.1f} p_MC={(cs >= chi).mean() if Ot>0 else 1:.2f}")
# agrupación con sentido: lunes, sábado, domingo vs resto
print("\n grupos (lun / sáb / dom / mar-vie) por era, k=3:")
for e in ("9:00", "8:00"):
    for nom, ws in (("lun",[0]),("sáb",[5]),("dom",[6]),("mar-vie",[1,2,3,4])):
        f = [t for t in dev if era(t) == e and DOW[t] in ws]
        m, o, ex = oe(f, lambda t: S[previo(t,3,'cal')] if previo(t,3,'cal') is not None else None)
        r = poisson_ic(o, ex); nmir += 1
        print(f"  {e} {nom:7s} N={m:3d} O={o:2d} E={ex:5.2f} O/E={r[0]:.2f} [{r[1]:.2f};{r[2]:.2f}]")
# ¿ayer fue día completo? En dev todos los días tienen 11 (era 9:00) o 12 sorteos.
inc = [str(F[first[d]]) for d in dias if T[first[d]]=="dev" and cuenta[d] not in (11,12)]
print("\n días dev incompletos:", inc)
# Probabilidad del motor para el objetivo k=1 por día de la semana (¿el motor ya castiga distinto?)
print("\n mediana P motor del 1º de ayer por dow (dev 8:00):",
      [round(float(np.median([P[t,S[previo(t,1,'cal')]] for t in dev if era(t)=='8:00' and DOW[t]==w and previo(t,1,'cal') is not None])),4) for w in range(7)])
print("celdas O/E miradas:", nmir)
