# -*- coding: utf-8 -*-
"""ag03 — exploración SOLO en cal (conteos crudos) y dev (contra P_aj). No toca prueba ni vivo."""
import numpy as np
from scipy import stats
from comun import *

G = grupos()
CONTRASTES = []          # (nombre, p)


def reg(nombre, p):
    CONTRASTES.append((nombre, p))
    return p


F_cal = np.where(prim & (tramo == "cal"))[0]
F_dev9 = np.where(prim & (tramo == "dev") & (hora == 1))[0]
F_dev8 = np.where(prim & (tramo == "dev") & (hora == 0))[0]
F_dev = np.concatenate([F_dev9, F_dev8])
F_era9 = np.concatenate([F_cal, F_dev9])           # crudo, primer sorteo 9:00
F_crudo = np.concatenate([F_cal, F_dev])            # crudo, todo pre-prueba
O_cal = np.where(~prim & ((tramo == "cal") | (tramo == "dev")))[0]   # demás horas, pre-prueba

print("n primer: cal", len(F_cal), "dev9", len(F_dev9), "dev8", len(F_dev8), "| demás horas", len(O_cal))

# ---------------- A. crudo contra azar 1/38 ----------------
print("\n=== A. Primer sorteo (cal+dev) contra uniforme 1/38 ===")
for nom, F in (("todo", F_crudo), ("era9", F_era9), ("era8", F_dev8)):
    c = np.bincount(seq[F], minlength=38)
    chi = stats.chisquare(c)
    print(f"{nom:5s} n={len(F)} chi2 por animal={chi.statistic:.1f} (37 gl) p={reg('A_animal_'+nom, chi.pvalue):.3f}"
          f"  min={c.min()} max={c.max()} ({POS[c.argmax()]})")
for g, lab in G.items():
    cats = sorted(set(lab) - {-1})
    m = np.isin(seq[F_crudo], np.where(lab >= 0)[0])
    obs = np.array([(lab[seq[F_crudo]] == k).sum() for k in cats])
    ex = np.array([(lab == k).sum() for k in cats], float); ex = ex / ex.sum() * obs.sum()
    p = stats.chisquare(obs, ex).pvalue
    print(f"  {g:14s} obs={obs.tolist()} esp={np.round(ex,1).tolist()} p={reg('A_'+g, p):.3f}")

# ---------------- B. primer sorteo vs demás horas (crudo) ----------------
print("\n=== B. Primer sorteo vs demás horas (cal+dev, crudo, tabla 2xk; demás horas por hora no difieren bajo H0) ===")
c1 = np.bincount(seq[F_crudo], minlength=38); c2 = np.bincount(seq[O_cal], minlength=38)
p = stats.chi2_contingency(np.vstack([c1, c2]))[1]
print(f"  animal 2x38 p={reg('B_animal', p):.3f}")
for g, lab in G.items():
    cats = sorted(set(lab) - {-1})
    t = np.array([[(lab[seq[F]] == k).sum() for k in cats] for F in (F_crudo, O_cal)])
    p = stats.chi2_contingency(t)[1]
    fr = t / t.sum(1, keepdims=True)
    print(f"  {g:14s} primer%={np.round(100*fr[0],1).tolist()} resto%={np.round(100*fr[1],1).tolist()} p={reg('B_'+g, p):.3f}")

# ---------------- C. contra el motor P_aj en dev ----------------
print("\n=== C. Contra P_aj (dev, primer sorteo): O/E por categoría y por era ===")
for g, lab in G.items():
    cats = sorted(set(lab) - {-1})
    for k in cats:
        mem = lab == k
        s = []
        for nom, F in (("dev", F_dev), ("9:00", F_dev9), ("8:00", F_dev8)):
            O, E = oe_grupo(F, mem); s.append((O, E))
        O, E = s[0]
        lo, hi = poisson_ic(O)
        p = p_dos_colas_poisson(O, E)
        if len(cats) > 2 or k == cats[-1]:      # en binarias basta una categoría (la otra es el complemento salvo 0/00)
            reg(f"C_{g}_{k}", p)
        print(f"  {g:14s} cat={k} O/E dev={O/E:.2f} [{lo/E:.2f};{hi/E:.2f}] p={p:.3f}"
              f"  | 9:00 {s[1][0]/s[1][1]:.2f}  8:00 {s[2][0]/s[2][1]:.2f}")
# por animal: estadístico tipo chi2 de O contra E (sum P_aj)
O = np.bincount(seq[F_dev], minlength=38); E = Paj[F_dev].sum(0)
chi = ((O - E) ** 2 / E).sum()
print(f"  animal: chi2(O vs E motor)={chi:.1f} 37 gl p={reg('C_animal', stats.chi2.sf(chi, 37)):.3f}")
z = (O - E) / np.sqrt(E)
for i in np.argsort(-np.abs(z))[:6]:
    print(f"    {POS[i]:>3s} O={O[i]} E={E[i]:.1f} O/E={O[i]/E[i]:.2f} z={z[i]:+.2f}")
# ¿el motor en el primer sorteo es más/menos "plano"?
ent = lambda Q: -(Q * np.log2(Q)).sum(1).mean()
Fo = np.where(~prim & (tramo == "dev"))[0]
print(f"  entropía media P_aj: primer {ent(Paj[F_dev]):.3f} bits, demás {ent(Paj[Fo]):.3f}  (log2 38 = {np.log2(38):.3f})")
ll = lambda F: 1000 * np.mean(np.log2(38 * Paj[F, seq[F]]))
print(f"  mbits del motor vs uniforme: primer dev {ll(F_dev):+.1f} (9:00 {ll(F_dev9):+.1f}, 8:00 {ll(F_dev8):+.1f}); demás horas dev {ll(Fo):+.1f}")

# ---------------- D. cambio entre eras ----------------
print("\n=== D. ¿Cambió la distribución del primer sorteo entre la era 9:00 y la 8:00? ===")
c9 = np.bincount(seq[F_era9], minlength=38); c8 = np.bincount(seq[F_dev8], minlength=38)
print(f"  crudo animal 2x38 p={reg('D_animal', stats.chi2_contingency(np.vstack([c9, c8]))[1]):.3f}")
for g, lab in G.items():
    cats = sorted(set(lab) - {-1})
    t = np.array([[(lab[seq[F]] == k).sum() for k in cats] for F in (F_era9, F_dev8)])
    p = stats.chi2_contingency(t)[1]
    fr = t / t.sum(1, keepdims=True)
    print(f"  {g:14s} 9:00%={np.round(100*fr[0],1).tolist()} 8:00%={np.round(100*fr[1],1).tolist()} p={reg('D_'+g, p):.3f}")
# contra motor: residuos por animal correlacionados entre eras?
r9 = np.bincount(seq[F_dev9], minlength=38) - Paj[F_dev9].sum(0)
r8 = np.bincount(seq[F_dev8], minlength=38) - Paj[F_dev8].sum(0)
rho, prho = stats.spearmanr(r9, r8)
print(f"  residuos por animal (O-E motor) era9 vs era8: Spearman {rho:+.2f} p={reg('D_resid_corr', prho):.3f}")

# ---------------- E. popularidad: número de la fecha / de la hora en el primer sorteo ----------------
print("\n=== E. 'Popularidad' en el primer sorteo (dev, contra P_aj): número = día del mes, día±1, hora 12h ===")
dd = np.array([int(f[8:10]) for f in fecha]); mm = np.array([int(f[5:7]) for f in fecha])
h12 = np.where(hora == 0, 8, 9)       # en el primer sorteo: 8 o 9


def obj_oe(F, objetivo):
    """objetivo(t) -> código numérico 1..36 o None"""
    O = E = 0.0
    for t in F:
        k = objetivo(t)
        if k is None or not (1 <= k <= 36): continue
        i = k + 1
        O += seq[t] == i; E += Paj[t, i]
    return O, E


for nom, fn in (("dia_mes", lambda t: dd[t]), ("dia_mes+1", lambda t: dd[t] + 1), ("dia_mes-1", lambda t: dd[t] - 1),
                ("hora_12h", lambda t: h12[t]), ("mes", lambda t: mm[t])):
    s = [obj_oe(F, fn) for F in (F_dev, F_dev9, F_dev8)]
    O, E = s[0]; lo, hi = poisson_ic(int(O))
    p = p_dos_colas_poisson(int(O), E)
    print(f"  {nom:10s} O={int(O)} E={E:.1f} O/E={O/E:.2f} [{lo/E:.2f};{hi/E:.2f}] p={reg('E_'+nom, p):.3f}"
          f" | 9:00 {s[1][0]:.0f}/{s[1][1]:.1f}  8:00 {s[2][0]:.0f}/{s[2][1]:.1f}")
# misma cosa en las demás horas de dev, como control
Fo = np.where(~prim & (tramo == "dev"))[0]
O, E = obj_oe(Fo, lambda t: dd[t]); print(f"  control demás horas dev, dia_mes: O/E={O/E:.2f} (O={int(O)}, E={E:.1f})")
# crudo en cal (primer sorteo) contra 1/38
Oc = sum(seq[t] == dd[t] + 1 for t in F_cal if dd[t] <= 36)
print(f"  crudo cal (primer) dia_mes: O={Oc} E={len(F_cal)/38:.1f}")

print(f"\nTOTAL contrastes mirados en dev/cal: {len(CONTRASTES)}")
ps = np.array([p for _, p in CONTRASTES])
print(f"  p<0,05: {(ps<0.05).sum()} (esperados por azar ≈ {0.05*len(ps):.1f}); Bonferroni 0,05/{len(ps)} = {0.05/len(ps):.4f}")
for nom, p in sorted(CONTRASTES, key=lambda x: x[1])[:10]:
    print(f"   {nom:25s} p={p:.4f}  Holm-ajustada≈{min(1, p*len(ps)):.3f}")
