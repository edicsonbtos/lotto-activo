# -*- coding: utf-8 -*-
"""Época actual (nov-2025..sep-2026), descriptivo: (1) ¿una racha de aciertos predice el siguiente? (Top-15 a las
8:00 y Top-5 escalonado en todas las horas), y "apostar hasta perder" contra jugar siempre; (2) a las 8:00, ¿cuánto
sale cada animal según su grupo (ayer / 2-3 d / frío)? Antes: reentreno/sub.py todo I|S|H.
Uso: python .../rachas_y_grupos.py -> salida_rachas_y_grupos.txt"""
import io, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno"); sys.path.insert(0, RE)
import comun as C  # noqa: E402
LE = C.LE; SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s); SAL.append(s)
D = LE.cargar(os.path.join(RE, "historial_la.txt")); seq = np.asarray(D.seq); n = len(seq)
L = C.cargar_L("todo", ["I", "S", "H"]); P = C.combinar(L, seq[C.ARRANQUE:], LE.W, **C.COMB["base"])
T = [t for t in range(LE.W, n) if D.fecha[t] >= "2025-11-01"]
pos = {t: int(np.where(np.argsort(-P[t - LE.W], kind="stable") == seq[t])[0][0]) for t in T}
f5 = np.zeros(38); f5[:5] = [2, 2, 2, 1, 1]
def tras_racha(serie, nombre):
    x = np.array(serie, int); base = x.mean()
    log(f"\n{nombre}: acierta {100*base:.1f} % en general (n={len(x)})")
    for k in (1, 2, 3, 5):
        s = [i for i in range(k, len(x)) if x[i - k:i].all()]
        f = [i for i in range(k, len(x)) if not x[i - k:i].any()]
        log(f"  tras {k} aciertos seguidos: {100*x[s].mean():.1f} % (n={len(s)})   |   tras {k} fallos seguidos: "
            f"{100*x[f].mean() if f else float('nan'):.1f} % (n={len(f)})")
ocho = [t for t in T if D.hora[t] == 0]
tras_racha([pos[t] < 15 for t in ocho], "Top-15 a las 8:00 (madrugada tras madrugada)")
tras_racha([pos[t] < 5 for t in T], "Top-5 en todas las horas (sorteo tras sorteo)")
# "apostar hasta perder": jugar el Top-5 escalonado solo mientras el anterior acertó (y reengancharse tras un acierto)
r = np.array([(30 * f5[pos[t]] - 8) / 8 for t in T]); h = np.array([pos[t] < 5 for t in T])
solo_tras_acierto = r[1:][h[:-1]]
log(f"\nTop-5 escalonado, retorno por ficha: jugar SIEMPRE {100*r.mean():+.1f} % ({len(r)} jugadas) | "
    f"jugar solo después de un acierto {100*solo_tras_acierto.mean():+.1f} % ({len(solo_tras_acierto)} jugadas)")
# grupos a las 8:00
ult = np.full(38, -10**6); GD = np.zeros((n, 38), int)
for t in range(n):
    GD[t] = D.dia[t] - ult; ult[seq[t]] = D.dia[t]
log("\nA las 8:00 (época actual): cuánto sale cada animal según su grupo (1,00 = azar)")
for nom, lo, hi in (("salió ayer", 1, 1), ("hace 2-3 días", 2, 3), ("frío (4+ días)", 4, 10**6)):
    m = np.array([(GD[t] >= lo) & (GD[t] <= hi) for t in ocho]); y = np.array([seq[t] for t in ocho])
    o = m[np.arange(len(ocho)), y].sum(); e = m.sum() / 38
    log(f"  {nom:<16} cada animal sale {o/e:.2f} veces lo normal; hay ~{m.sum(1).mean():.0f} animales así cada mañana; "
        f"ganan {100*o/len(ocho):.0f} % de las madrugadas")
io.open(os.path.join(AQUI, "salida_rachas_y_grupos.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")

log("\n¿Inercia real o meses buenos/malos? Top-15 8:00: tras acierto vs tras fallo, (a) por época, (b) DENTRO de cada mes")
for nom, a, b in (("2025 (dic-2024..oct-2025)", "2024-12-01", "2025-10-31"), ("época actual (nov-2025..sep-2026)", "2025-11-01", "2026-09-30")):
    ts = [t for t in range(LE.W, n) if D.hora[t] == 0 and a <= D.fecha[t] <= b]
    x = np.array([int(np.where(np.argsort(-P[t - LE.W], kind="stable") == seq[t])[0][0]) < 15 for t in ts])
    mes = np.array([D.fecha[t][:7] for t in ts])
    tras_h = x[1:][x[:-1]]; tras_f = x[1:][~x[:-1]]
    # Mantel-Haenszel por mes: diferencia ponderada dentro de cada mes
    num = den = 0.0
    for m in np.unique(mes[1:]):
        s = mes[1:] == m; prev = x[:-1][s]; cur = x[1:][s]
        a1, n1 = cur[prev].sum(), prev.sum(); a0, n0 = cur[~prev].sum(), (~prev).sum()
        if n1 and n0:
            w = n1 * n0 / (n1 + n0); num += w * (a1 / n1 - a0 / n0); den += w
    log(f"  {nom}: tras acierto {100*tras_h.mean():.1f} % | tras fallo {100*tras_f.mean():.1f} % | "
        f"diferencia {100*(tras_h.mean()-tras_f.mean()):+.1f} pp; DENTRO del mismo mes {100*num/den:+.1f} pp")
io.open(os.path.join(AQUI, "salida_rachas_y_grupos.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")

log("\nÉpoca actual, por mitades (descriptivo) y en plata (Top-15 plano y Top-5 escalonado a las 8:00)")
ts = [t for t in range(LE.W, n) if D.hora[t] == 0 and D.fecha[t] >= "2025-11-01"]
ps = np.array([int(np.where(np.argsort(-P[t - LE.W], kind="stable") == seq[t])[0][0]) for t in ts])
x = ps < 15; fe = [D.fecha[t] for t in ts]
for nom, a, b in (("nov-2025..abr-2026", "2025-11-01", "2026-04-30"), ("may-2026..sep-2026", "2026-05-01", "2026-09-30")):
    s = np.array([a <= f <= b for f in fe])[1:]
    th = x[1:][s & x[:-1]]; tf = x[1:][s & ~x[:-1]]
    log(f"  {nom}: tras acierto {100*th.mean():.1f} % (n={len(th)}) | tras fallo {100*tf.mean():.1f} % (n={len(tf)})")
r15 = (30 * (ps < 15) - 15) / 15; r5 = (30 * f5[ps] - 8) / 8
for nom, s in (("tras un acierto del Top-15", x[:-1]), ("tras un fallo del Top-15", ~x[:-1])):
    log(f"  {nom}: Top-15 plano {100*r15[1:][s].mean():+.1f} % | Top-5 escalonado {100*r5[1:][s].mean():+.1f} % por ficha (n={s.sum()})")
io.open(os.path.join(AQUI, "salida_rachas_y_grupos.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
