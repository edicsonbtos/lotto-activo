# ag02: segunda mirada en dev: ventana de día, placebo de corrimientos en el primer sorteo. Sin prueba.
import numpy as np
from scipy import stats
exec(open('explorar_dev.py').read().split("print('n filas")[0])
U = np.full((n, 38), 1/38)
dev = T == 'dev'; cal = T == 'cal'; era9 = dev & E1 & (H == 1); era8 = dev & E1 & (H == 0); resto = dev & ~E1
def oeset(mask, codes_list, Pm):
    # codes_list: lista de arrays de índice (-1 = no válido); objetivo = unión (sin duplicar)
    r = np.where(mask)[0]; o = 0; e = 0.0
    for t in r:
        s = {int(a[t]) for a in codes_list if a[t] >= 0}
        o += S[t] in s; e += sum(Pm[t, j] for j in s)
    return o, e, o / e
W3 = [FI['D-1'], FI['D0'], FI['D+1']]; W2 = [FI['D-1'], FI['D+1']]
for nom, L in (('ventana D-1..D+1', W3), ('D±1 sin D0', W2), ('D0,D+1', [FI['D0'], FI['D+1']])):
    a9 = oeset(era9, L, PA); a8 = oeset(era8, L, PA); ad = oeset(dev & E1, L, PA); rs = oeset(resto, L, P)
    c1 = oeset(cal & E1, L, U); c2 = oeset(cal & ~E1, L, U)
    N = ad[0] + rs[0]; pi = ad[1] / (ad[1] + rs[1]); pint = stats.binom.cdf(ad[0], N, pi)
    print(f"{nom:18s} 9:00 {a9[0]}/{a9[1]:.1f}={a9[2]:.2f}  8:00 {a8[0]}/{a8[1]:.1f}={a8[2]:.2f}  dev1º {ad[0]}/{ad[1]:.1f}={ad[2]:.2f} p_bajo={stats.poisson.cdf(ad[0], ad[1]):.4f} | resto {rs[0]}/{rs[1]:.1f}={rs[2]:.2f} | p_inter(1º<resto, unilateral)={pint:.3f} | cal1º {c1[0]}/{c1[1]:.1f}={c1[2]:.2f} cal resto {c2[2]:.2f}")
print('placebo de corrimientos D+s en el primer sorteo (dev, vs P_aj) y resto (vs P):')
for s in range(-8, 9):
    a = idx(dd + s); x = oe(dev & E1, a, PA); y = oe(resto, a, P); c = oe(cal & E1, a, U)
    print(f"  s={s:+d}: 1º {x[0]:2d}/{x[1]:5.1f}={x[2]:.2f}   resto {y[2]:.2f}   cal1º {c[2]:.2f}")
# por año calendario dentro del primer sorteo (cal+dev): ventana
for per in (('2023-09', '2024-03-07'), ('2024-03-08', '2024-11-27'), ('2024-11-28', '2025-06-30'), ('2025-07-01', '2025-12-19')):
    m = E1 & (F >= per[0]) & (F <= per[1] + 'z')
    print('periodo', per, 'n', m.sum(), 'ventana vs 1/38:', oeset(m, W3, U), 'D0 vs1/38', oe(m, FI['D0'], U)[:3])
