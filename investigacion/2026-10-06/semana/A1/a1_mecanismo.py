"""A1 (complemento, descriptivo, no pre-registrado): cronología del efecto por día y huella del operador.
Uso: python a1_mecanismo.py <SP>"""
import sys, numpy as np
from datetime import date
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); import lotto_eval as LE
S = sys.argv[1]
D = LE.cargar(S + "/hist_0605.txt"); YS = np.asarray(D.seq); FD = np.array(D.fecha)
z = np.load(S + "/prod_0605.npz", allow_pickle=True); P, t, y, f, h = z["P"], z["t"], z["y"], z["f"], z["h"].astype(int)
o = np.argsort(-P, 1, kind="stable"); rk = np.argmax(o == y[:, None], 1)
in15 = (rk < 15).astype(float); m15 = np.take_along_axis(P, o[:, :15], 1).sum(1)
dow = np.array([date.fromisoformat(d).weekday() for d in f]); MVF = np.isin(dow, [2, 3, 4])
NOM = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

print("=== Cronología trimestral: Top-15 O/E por día de la semana ===")
print("trim     " + " ".join(f"{d:>5}" for d in NOM) + "   mié-vie  resto")
qs = sorted(set(x[:4] + "-T" + str((int(x[5:7]) - 1) // 3 + 1) for x in f))
for q in qs:
    mq = np.array([(x[:4] + "-T" + str((int(x[5:7]) - 1) // 3 + 1)) == q for x in f])
    r = [in15[mq & (dow == k)].sum() / m15[mq & (dow == k)].sum() for k in range(7)]
    a = mq & MVF; b = mq & ~MVF
    print(f"{q}  " + " ".join(f"{v:5.2f}" for v in r) + f"   {in15[a].sum()/m15[a].sum():6.2f} {in15[b].sum()/m15[b].sum():6.2f}")

# Huella del operador sobre el historial completo, por día y era (sin motor)
fu = np.unique(FD); di = {d: i for i, d in enumerate(fu)}; dn = np.array([di[x] for x in FD])
dowH = np.array([date.fromisoformat(x).weekday() for x in FD])
era = np.where(FD < "2024-03-07", "pre", np.where(FD <= "2025-12-19", "dev", np.where(FD >= "2026-01-01", "2026", "gap")))
rep = np.zeros(len(YS)); recy = np.zeros(len(YS)); erec = np.zeros(len(YS))
inicio = {}
for i in range(len(YS)):
    d = dn[i]
    if d not in inicio: inicio[d] = i
    rep[i] = YS[i] in YS[inicio[d]:i]
lo = np.searchsorted(dn, dn - 2); hi = np.searchsorted(dn, dn)
for i in range(len(YS)):
    s = np.unique(YS[lo[i]:hi[i]]); recy[i] = YS[i] in s; erec[i] = len(s) / 38
print("\n=== Huella del operador (historial, sin motor), por era y día ===")
print("rep = repite un animal ya salido HOY (esperado iid por sorteo: (k)/38, k sorteos previos del día)")
print("rec = sale de los ganadores de ayer/anteayer; esperado iid = |conjunto|/38")
k_prev = np.array([i - inicio[dn[i]] for i in range(len(YS))])
for e in ("dev", "2026"):
    print(f"--- {e} ---")
    for grp, nm in [([k], NOM[k]) for k in range(7)] + [([2, 3, 4], "mié-vie"), ([0, 1, 5, 6], "sáb-mar")]:
        m = (era == e) & np.isin(dowH, grp) & (lo < hi)
        print(f"  {nm:8} rep {rep[m].sum():4.0f}/{(k_prev[m]/38).sum():6.1f} esp (O/E {rep[m].sum()/(k_prev[m]/38).sum():.2f})"
              f" | rec {recy[m].mean()*100:5.1f}% vs iid {erec[m].mean()*100:5.1f}% (O/E {recy[m].sum()/erec[m].sum():.2f})")

print("\n=== Huella 'repite hoy' O/E por semestre y día (historial completo) ===")
print("sem       n_días " + " ".join(f"{d:>5}" for d in NOM))
sem = np.array([x[:4] + ("-S1" if int(x[5:7]) <= 6 else "-S2") for x in FD])
for s in sorted(set(sem)):
    ms = sem == s
    r = []
    for k in range(7):
        m = ms & (dowH == k); e = (k_prev[m] / 38).sum(); r.append(rep[m].sum() / e if e > 0 else np.nan)
    print(f"{s}  {len(set(FD[ms])):5d}  " + " ".join(f"{v:5.2f}" for v in r))
print("\n=== Transición mensual 2025-07..2026-10: 'repite hoy' O/E (dom | mié-vie | resto) ===")
for ms in sorted(set(x[:7] for x in FD if "2025-07" <= x[:7])):
    mm = np.array([x.startswith(ms) for x in FD])
    def oe(g):
        m = mm & np.isin(dowH, g); e = (k_prev[m] / 38).sum(); return rep[m].sum() / e
    print(f"  {ms}: dom {oe([6]):.2f} | mié-vie {oe([2,3,4]):.2f} | lun-mar-sáb {oe([0,1,5]):.2f}")
