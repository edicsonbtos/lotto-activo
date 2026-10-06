# Pista mecánica (exploratoria, NO pre-registrada): ¿el déficit de mié-vie se concentra en animales que ya salieron
# en la semana natural (lunes a ayer) del motor (intradia_v2 usa el periodo "semana" lun-dom)?
# Grupos del candidato: A = salió ayer o anteayer; B = salió esta semana natural antes de anteayer (no en A);
# C = salió hoy antes de esta hora; resto. O/E = ganadores del grupo / masa del motor en el grupo. Uso: python semana_motor.py <SP>
import sys, numpy as np
from datetime import date
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); import lotto_eval as LE
SP = sys.argv[1]; D = LE.cargar(SP + "/hist_0605.txt"); YS = np.asarray(D.seq); DIA = np.asarray(D.dia); DOW = np.asarray(D.dow)
z = np.load(SP + "/prod_0605.npz", allow_pickle=True); P, t, y, f, h = z["P"], z["t"], z["y"], z["f"], z["h"]
res = {}
for i, T in enumerate(t):
    d = DIA[T]; lunes = d - DOW[T]
    hoy = set(YS[(DIA == d) & (np.arange(len(YS)) < T)]) if False else None
for lab, msk in (("dev", t < 9357), ("2026", f >= "2026-01-01")):
    acc = {}
    idx = np.where(msk)[0]
    for i in idx:
        T = t[i]; d = DIA[T]; lu = d - DOW[T]
        lo = np.searchsorted(DIA, min(lu, d - 2)); win = slice(lo, T)
        dd = DIA[win]; ss = YS[win]
        Cset = set(ss[dd == d]); Aset = set(ss[(dd >= d - 2) & (dd < d)]) - Cset
        Bset = set(ss[(dd >= lu) & (dd < d - 2)]) - Aset - Cset
        g = "mvf" if DOW[T] in (2, 3, 4) else "resto"
        for nm, S in (("A ayer/anteayer", Aset), ("B semana, antes", Bset), ("C ya hoy", Cset)):
            S = list(S); a = acc.setdefault((g, nm), [0.0, 0.0])
            a[0] += float(y[i] in S); a[1] += P[i, S].sum() if S else 0.0
    print(lab)
    for nm in ("A ayer/anteayer", "B semana, antes", "C ya hoy"):
        print(f"  {nm:16} mié-vie O/E {acc[('mvf',nm)][0]/acc[('mvf',nm)][1]:.2f} (O {acc[('mvf',nm)][0]:.0f}, E {acc[('mvf',nm)][1]:.1f}) | resto {acc[('resto',nm)][0]/acc[('resto',nm)][1]:.2f} (O {acc[('resto',nm)][0]:.0f}, E {acc[('resto',nm)][1]:.1f})")
# Desglose por día de la semana de "C ya hoy" (repetición en el mismo día) en 2026 y dev
for lab, msk in (("dev", t < 9357), ("2026", f >= "2026-01-01")):
    O = np.zeros(7); E = np.zeros(7)
    for i in np.where(msk)[0]:
        T = t[i]; d = DIA[T]; lo = np.searchsorted(DIA, d); S = list(set(YS[lo:T]))
        if S: O[DOW[T]] += float(y[i] in S); E[DOW[T]] += P[i, S].sum()
    print(f"{lab} repetición mismo día por día:", "  ".join(f"{n} {O[k]:.0f}/{E[k]:.1f}={O[k]/E[k]:.2f}" for k, n in enumerate("LMXJVSD")))
