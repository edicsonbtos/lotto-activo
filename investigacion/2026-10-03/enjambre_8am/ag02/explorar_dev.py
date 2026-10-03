# ag02: exploración SOLO en dev (y 'cal' para conteos crudos). No mira prueba ni vivo.
import sys, datetime, numpy as np
from scipy import stats
sys.path.insert(0, '/home/user/lotto-activo/herramientas'); import lotto_eval as LE
BASE = '/tmp/claude-0/-home-user-lotto-activo/fffc39ca-02e7-4d69-b0fe-674a608a5e21/scratchpad/base8'
z = np.load(BASE + '/base8.npz')
S, H, F, DOW, P, PA, E1, T = z['seq'], z['hora'], z['fecha'], z['dow'], z['P'], z['P_aj'], z['es_primero'], z['tramo']
n = len(S)
DT = [datetime.date.fromisoformat(f) for f in F]
dd = np.array([d.day for d in DT]); mm = np.array([d.month for d in DT]); yy = np.array([d.year % 100 for d in DT])
doy = np.array([d.timetuple().tm_yday for d in DT])
h24 = H + 8; h12 = (h24 - 1) % 12 + 1
FEAT = {
 'D0': dd, 'D+1': dd + 1, 'D-1': dd - 1, 'D+2': dd + 2, 'MES': mm, 'D+M': dd + mm, 'AÑO2': yy,
 'H12': h12, 'H12+1': h12 + 1, 'H12-1': h12 - 1,
 'DOW_L1': DOW + 1, 'DOW_D1': (DOW + 1) % 7 + 1, 'DOY37': doy % 37,
 'D_REV': np.array([int(str(x)[::-1]) for x in dd]), 'D*M': dd * mm % 100,
}
def idx(v):
    return np.array([LE.IDX[str(int(x))] if 0 <= x <= 36 else -1 for x in v])
FI = {k: idx(v) for k, v in FEAT.items()}
def oe(mask, a, Pm):
    r = np.where(mask & (a >= 0))[0]
    o = int((S[r] == a[r]).sum()); e = float(Pm[r, a[r]].sum())
    lo, hi = (stats.chi2.ppf(.025, 2*o)/2 if o else 0.0), stats.chi2.ppf(.975, 2*o+2)/2
    p_lo = stats.poisson.cdf(o, e); p_hi = stats.poisson.sf(o-1, e)
    return (o, e, o/e, lo/e, hi/e, p_lo, p_hi, len(r)) if e else (0,0,np.nan,np.nan,np.nan,1,1,0)
dev = T == 'dev'; cal = T == 'cal'
era9 = dev & E1 & (H == 1); era8 = dev & E1 & (H == 0)
resto = dev & ~E1
print('n filas: era9', era9.sum(), 'era8', era8.sum(), 'resto dev', resto.sum())
print(f"{'rasgo':8s} | {'9:00 dev O/E':>22s} | {'8:00 dev O/E':>22s} | {'dev1º O/E  p(bajo) p(alto)':>34s} | {'resto dev O/E':>16s} | p_inter | cal1º O/E(1/38) | cal resto")
U = np.full((n, 38), 1/38)
filas = []
for k, a in FI.items():
    r9 = oe(era9, a, PA); r8 = oe(era8, a, PA); rr = oe(dev & E1, a, PA); rs = oe(resto, a, P)
    # interacción: O1 | O1+O2 ~ Bin(O1+O2, E1/(E1+E2)); dos colas
    N = rr[0] + rs[0]; pi = rr[1] / (rr[1] + rs[1])
    p_int = 2 * min(stats.binom.cdf(rr[0], N, pi), stats.binom.sf(rr[0]-1, N, pi)); p_int = min(p_int, 1)
    c1 = oe(cal & E1, a, U); c2 = oe(cal & ~E1, a, U)
    print(f"{k:8s} | {r9[0]:3d}/{r9[1]:5.1f}={r9[2]:4.2f} [{r9[3]:.2f};{r9[4]:.2f}] | {r8[0]:3d}/{r8[1]:5.1f}={r8[2]:4.2f} [{r8[3]:.2f};{r8[4]:.2f}] | {rr[0]:3d}/{rr[1]:5.1f}={rr[2]:4.2f} {rr[5]:.4f} {rr[6]:.4f} | {rs[0]:4d}/{rs[1]:6.1f}={rs[2]:4.2f} | {p_int:.3f} | {c1[0]:2d}/{c1[1]:4.1f}={c1[2]:4.2f} | {c2[2]:4.2f}")
# Por hora (resto) para D0 y H12, estratificado
for k in ('D0', 'D+1', 'H12'):
    a = FI[k]
    print(k, 'por hora dev:', ' '.join(f"h{h}:{oe(dev & (H == h) & ~E1, a, P)[2]:.2f}" for h in range(12)))
# Control cruzado de la hora: en era 8:00, '9' y en era 9:00, '8'
for nom, msk, cod in (('era8 obj "9"', era8, 9), ('era9 obj "8"', era9, 8), ('era8 obj "8"', era8, 8), ('era9 obj "9"', era9, 9)):
    a = np.full(n, LE.IDX[str(cod)])
    print(nom, oe(msk, a, PA)[:3], 'cal:' , oe(cal & E1 & msk.any() , a, U)[:3] if False else '')
# mismo número fijo en otras horas (¿"8" es esquivado todo el día o solo a las 8:00?)
for cod in (8, 9):
    a = np.full(n, LE.IDX[str(cod)])
    print(f'"{cod}" en no-primeros dev, por hora:', ' '.join(f"h{h}:{oe(dev & (H == h) & ~E1, a, P)[2]:.2f}" for h in range(12)))
    print(f'"{cod}" en cal 1º (9:00) crudo:', oe(cal & E1, a, U)[:3])
