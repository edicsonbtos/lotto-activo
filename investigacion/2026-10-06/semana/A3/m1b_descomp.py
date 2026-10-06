from comun import *
# contrafactual pre-registrado: reponderar ganadores MVF para que cada categoría tenga el O/E de SM
CAT = np.full(len(t), 3)               # 0 hoy, 1 ayer, 2 anteayer-no-ayer, 3 resto
H_, A_, AA_ = HOYB[rows, y], AY[rows, y], AA[rows, y]
CAT[(~H_) & (~A_) & AA_] = 2; CAT[(~H_) & A_] = 1; CAT[H_] = 0
Mc = [HOYB, AY & ~HOYB, AA & ~AY & ~HOYB, ~(HOYB | AY | AA)]
def descomp(me, lab, cats=range(4)):
    a = me & MVF; b = me & ~MVF
    O = IN15[a].sum(); E = M15[a].sum(); N = a.sum()
    tgt = {}; 
    for c in cats:
        Ec_a = (P[a] * Mc[c][a]).sum(); oe_b = (CAT[b] == c).sum() / (P[b] * Mc[c][b]).sum()
        tgt[c] = Ec_a * oe_b
    s = sum(tgt.values()); cf = 0.0
    for c in cats:
        mk = CAT[a] == c; cf += tgt[c] / s * N * IN15[a][mk].mean()
    print(f"{lab}: Top-15 MVF obs {O} ({O/N*100:.1f}%), motor {E:.0f} ({E/N*100:.1f}%), contrafactual {cf:.0f} ({cf/N*100:.1f}%)"
          f" -> recupera {(cf-O)/(E-O)*100:.0f}% del déficit")
    for c, nm in zip(cats, ["hoy", "ayer", "anteayer", "resto"]):
        mk = CAT[a] == c
        print(f"     {nm:9} ganadores MVF {mk.sum():4d} (objetivo {tgt[c]/s*N:6.1f}); Top-15 en esa categoría {IN15[a][mk].mean()*100:.1f}%")
descomp(A26, "2026")
descomp(DEV, "dev ")
# cuánto pesa cada sorteo con repetición: Top-15 cuando el ganador ya salió hoy
for era, me in (("dev", DEV), ("2026", A26)):
    m = me & HOYB[rows, y]
    print(f"{era}: si el ganador ya salió hoy, está en el Top-15 el {IN15[m].mean()*100:.1f}% (n={m.sum()}); masa media del motor sobre 'ya salió hoy' {(P*HOYB)[me].sum(1).mean()*100:.1f}%")
