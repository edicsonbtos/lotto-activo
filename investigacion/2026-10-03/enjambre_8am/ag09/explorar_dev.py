# Exploración SOLO en dev (y 'cal' para conteos crudos). No toca prueba/vivo.
from comun import *
dev = filas_primero("dev"); cal = filas_primero("cal")
# sanity: P_aj == ajuste por calendario
print("max|PAJ - cal|", max(abs(ajustar(t, "cal") - PAJ[t]).max() for t in dev))
ndev = 0
def era(t): return "8:00" if F[t] >= ERA8 else "9:00"
# ---- (2) días donde las reglas discrepan (dev)
print("\n(2) filas dev donde calendario y abiertos dan distinto objetivo")
for k in (1, 2, 3, 4):
    dis = [t for t in dev if previo(t, k, "cal") != previo(t, k, "abierto")]
    print(f" k={k}: {len(dis)} filas:", [str(F[t]) for t in dis])
# ---- tabla O/E por regla (dev, por era), objetivo = primero de hace k días (cal / abierto)
print("\nO/E contra P (motor sin ajuste) en dev por era; misma_hora=True")
for k in (1, 2, 3, 4):
    for modo in ("cal", "abierto"):
        for e in ("9:00", "8:00"):
            f = [t for t in dev if era(t) == e]
            m, o, ex = oe(f, lambda t: S[previo(t, k, modo)] if previo(t, k, modo) is not None else None)
            r = poisson_ic(o, ex); ndev += 1
            print(f" k={k} {modo:8s} {e}: N={m:3d} O={o:2d} E={ex:5.2f} O/E={r[0]:.2f} [{r[1]:.2f};{r[2]:.2f}]")
# ---- (1) primer sorteo tras un cierre: todos los tramos <= dev (cal+dev). Prueba no se mira aquí.
print("\n(1) primeros sorteos tras cierre (cal+dev):")
for t in cal + dev:
    d = int(DI[t]); j = ordinal[d]
    if j == 0 or dias[j] - dias[j - 1] == 1: continue
    t1 = first[dias[j - 1]]; t3 = first[dias[j - 3]]; t3c = first.get(d - 3)
    p1 = P[t, S[t1]] if T[t] != "cal" else np.nan
    print(f" {F[t]} ({T[t]}) cierre {dias[j]-dias[j-1]-1}d gana={S[t]} últ.abierto1º={S[t1]} (p={p1:.3f}) "
          f"abierto-3={S[t3]} cal-3={'—' if t3c is None else S[t3c]} hora prev={H[t1]} hora={H[t]}")
# conteo crudo en cal (contra 1/38) — reglas cal vs abierto
print("\ncal (crudo, 1/38):")
for k in (1, 3):
    for modo in ("cal", "abierto"):
        m = o = 0
        for t in cal:
            tp = previo(t, k, modo)
            if tp is None: continue
            m += 1; o += S[t] == S[tp]
        print(f" k={k} {modo}: N={m} O={o} E={m/38:.2f}")
print("contrastes O/E mirados en esta tabla:", ndev)
