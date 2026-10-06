from comun import *
C = cats()
print("M1 · Perfil del ganador: O/E contra el motor (Σ P sobre la categoría). Ratio = MVF/SM, IC95 por días\n")
for era, me in (("dev", DEV), ("2026", A26)):
    print(f"== {era} ==   (días MVF {len(set(dayid[me&MVF]))}, SM {len(set(dayid[me&~MVF]))})")
    print(f"{'categoría':26} {'MVF %obs/%mot':>15} {'O/E MVF':>8} {'SM %obs/%mot':>14} {'O/E SM':>7}  ratio [IC95]")
    for k, M in C.items():
        O = M[rows, y].astype(float); E = (P * M).sum(1)
        a = me & MVF; b = me & ~MVF
        r, lo, hi = boot_ratio(O[a], E[a], O[b], E[b], dayid[a], dayid[b], B=1000)
        print(f"{k:26} {O[a].mean()*100:6.1f}/{E[a].mean()*100:5.1f}  {O[a].sum()/E[a].sum():7.2f}  {O[b].mean()*100:6.1f}/{E[b].mean()*100:5.1f} {O[b].sum()/E[b].sum():7.2f}  {r:.2f} [{lo:.2f}; {hi:.2f}]")
    print()
