# -*- coding: utf-8 -*-
"""¿Por qué el Top-15 de las 8:00 llega al ~60 %? ¿Se repite en otro horario? (solo desarrollo, descriptivo)
LA: calor_cache (ensamble walk-forward, filas 2000..9356). RD: cache_todo tramo dev (modelo B1 de RD).
Uso: python herramientas/exploracion/tripleta_inteligente/porque_8am.py -> salida_porque_8am.txt"""
import io, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); import lotto_eval as LE  # noqa: E402
SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)
D = LE.cargar(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "calor_cache.npz")); P = LE.normalizar(c["P"]); y = c["y"]
W = 2000; N = len(y); seq = D.seq; H = D.hora[W:W+N]; dia = D.dia
pos = np.argmax(LE.rankings(P) == y[:, None], 1)
# hueco en días del ganador y del resto, por hora
ult = np.full(38, -10**6); gapw = np.zeros(N, int); gaps = np.zeros((N, 38), int)
for t in range(W + N):
    if t >= W:
        gaps[t - W] = dia[t] - ult; gapw[t - W] = dia[t] - ult[seq[t]]
    ult[seq[t]] = dia[t]
ayer = {}
for t in range(W + N):
    ayer.setdefault(dia[t], []).append(int(seq[t]))
log("1) ¿Qué tiene de especial el ganador de las 8:00? O/E (observado/azar) según cuándo salió por última vez")
log("   hora   | salió hoy | ayer (1 d) | hace 2-3 d | hace 4-7 d | hace 8+ d | Top-15")
for h in range(12):
    s = H == h
    fila = []
    for lo, hi in ((0, 0), (1, 1), (2, 3), (4, 7), (8, 10**7)):
        m = (gaps[s] >= lo) & (gaps[s] <= hi)
        o = np.mean((gapw[s] >= lo) & (gapw[s] <= hi)); e = m.mean(1).mean()
        fila.append(f"{o/e:5.2f} ({100*e:4.1f}%)" if e > 0 else "   —        ")
    log(f"   {h+8:2d}:00 | " + " | ".join(fila) + f" | {100*np.mean(pos[s] < 15):.1f} % (n={s.sum()})")
log("   (entre paréntesis: % de animales en esa situación; O/E < 1 = sale menos que al azar)")
# 2) ¿lo explica "evitar lo que salió anoche"? O/E del ganador de la última(s) hora(s) de ayer a las 8:00
log("\n2) A las 8:00: ¿evita lo que salió ANOCHE? O/E de repetir el animal de ayer a las ...")
s8 = np.where(H == 0)[0]
for hh in (11, 10, 9, 8, 6, 3, 1):
    o = e = 0
    for i in s8:
        t = W + i; prev = [j for j in range(t - 12, t) if dia[j] == dia[t] - 1 and D.hora[j] == hh]
        if prev:
            o += y[i] == seq[prev[0]]; e += 1 / 38
    log(f"   ayer {hh+8:2d}:00  O/E {o/e:.2f}  (n={int(round(e*38))})")
# 3) ¿cuánto se concentra la probabilidad? masa Top-15 media y nº de animales "quemados" (salieron en ~24 h)
log("\n3) Animales que salieron en las últimas 24 h (12 sorteos de LA) y masa que el motor da a su Top-15")
for h in range(12):
    s = np.where(H == h)[0]
    rec = np.mean([len(set(seq[W+i-12:W+i].tolist())) for i in s])
    m15 = np.sort(P[s], 1)[:, ::-1][:, :15].sum(1).mean()
    log(f"   {h+8:2d}:00  distintos en las 12 previas {rec:.1f}  masa Top-15 {100*m15:.1f} %  Top-15 real {100*np.mean(pos[s]<15):.1f} %")
# 4) RD Internacional: ¿su primer sorteo (8:30) también es el mejor?
log("\n4) RD Internacional (desarrollo de RD, modelo B1): Top-15 por hora")
r = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "cache_todo.npz")); s = r["tramo"] == "dev"
P1 = r["P1"][s].astype(float); P1 /= P1.sum(1, keepdims=True); y1 = r["y"][s]; h1 = r["hora"][s]
p1 = np.argmax(LE.rankings(P1) == y1[:, None], 1)
for h in range(12):
    m = h1 == h; log(f"   {h+8:2d}:30  Top-15 {100*np.mean(p1[m] < 15):.1f} %  (n={m.sum()})")
io.open(os.path.join(AQUI, "salida_porque_8am.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
