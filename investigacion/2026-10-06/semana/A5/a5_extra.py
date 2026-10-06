"""A5 extra (NO pre-registrado, añadido tras ver salida.txt; adversarial): ¿la temperatura C2 es de mié-vie o de todo 2026?
¿qué tan extrema es la terna mié-vie en plata entre las 35 ternas? ¿y en dev?"""
import sys, itertools, numpy as np
sys.argv = sys.argv[:2]
exec(open(__file__.replace("a5_extra.py", "a5.py")).read().split("RES = {}")[0])
print("\n== C2 placebo: temperatura ajustada en otros grupos de días")
for lab, fit, test in (("directa", AJ, PR), ("inversa", PR, AJ)):
    for nom, days in (("mié-vie", [2, 3, 4]), ("sáb-mar", [0, 1, 5, 6]), ("todos", list(range(7)))):
        T = fit_temp(fit, days); r = np.isin(dow, days); dl = dlog_temp(T, r)
        mb, lo, hi = boot(1000 * dl, test); tt = test & r
        print(f"  {lab} {nom:8}: T = {T:.3f}  Δmbits/sorteo {mb:+6.2f} [{lo:+.2f}; {hi:+.2f}]  por sorteo tocado {1000*dl[tt].mean():+6.2f}")
    oos = []
    for tr in itertools.combinations(range(7), 3):
        r = np.isin(dow, tr); T = fit_temp(fit, list(tr)); oos.append((tr, T, 1000 * dlog_temp(T, r)[test].mean()))
    v = np.array([x[2] for x in oos]); k = [i for i, x in enumerate(oos) if x[0] == (2, 3, 4)][0]
    print(f"  {lab} 35 ternas (temperatura): prueba mediana {np.median(v):+.2f}, p90 {np.percentile(v,90):+.2f}; mié-jue-vie {v[k]:+.2f} (puesto {int((v>v[k]).sum())+1}/35); T de las ternas {min(x[1] for x in oos):.2f}..{max(x[1] for x in oos):.2f}")
print("\n  T de todos los días en dev:", fit_temp(DEV, list(range(7))), " T mié-vie en dev:", fit_temp(DEV, [2, 3, 4]))
print("\n== Plata Top-5 escalonado: retorno/ficha terna − resto, las 35 ternas")
g0 = ganancia(RK0) / 8
for lab, m in (("dev 2024-25", DEV), ("AJUSTE", AJ), ("PRUEBA", PR), ("2026 entero", AJ | PR)):
    dd = []
    for tr in itertools.combinations(range(7), 3):
        a = m & np.isin(dow, tr); b = m & ~np.isin(dow, tr); dd.append((tr, 100 * (g0[a].mean() - g0[b].mean())))
    v = np.array([x[1] for x in dd]); k = [i for i, x in enumerate(dd) if x[0] == (2, 3, 4)][0]
    print(f"  {lab:12}: mié-jue-vie {v[k]:+6.1f} pp (puesto {int((v<v[k]).sum())+1}/35 por lo malo); ternas: mín {v.min():+.1f}, p10 {np.percentile(v,10):+.1f}, mediana {np.median(v):+.1f}")
# dev: no jugar mié-vie
for nom, sel in (("todos", DEV), ("sin mié-vie", DEV & ~MVF), ("solo mié-vie", DEV & MVF)):
    print(f"  dev {nom:12}: retorno {100*g0[sel].mean():+6.1f} %/ficha  n sorteos {sel.sum()}")
