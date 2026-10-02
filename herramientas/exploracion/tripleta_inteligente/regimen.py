# -*- coding: utf-8 -*-
"""(a) ¿El motor ya sabe que el animal de las 8:00 queda "quemado" el resto del día? (desarrollo)
(b) Línea de tiempo mensual de la fuerza de la estructura (mbits y Top-15 del ensamble walk-forward recalculado,
    descriptivo; incluye meses del tramo de prueba, que ya se miraron mes a mes en el enjambre del 30-09).
Antes: cd herramientas/exploracion/enjambre_2026-09-30/reentreno && for k in I S H; do python sub.py todo $k; done
Uso: python herramientas/exploracion/tripleta_inteligente/regimen.py -> salida_regimen.txt"""
import io, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno"); sys.path.insert(0, RE)
import comun as C  # noqa: E402
LE = C.LE; SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)
D = LE.cargar(os.path.join(RE, "historial_la.txt")); seq = np.asarray(D.seq); n = len(seq)
L = C.cargar_L("todo", ["I", "S", "H"]); P = C.combinar(L, seq[C.ARRANQUE:], LE.W, **C.COMB["base"])
pos = np.argmax(np.argsort(-P, 1, kind="stable") == seq[LE.W:][:, None], 1)
log("(a) El animal de las 8:00 en el resto del día (10:00-19:00), desarrollo: ¿cuánto le da el motor y cuánto sale?")
o = e = 0
for t in range(LE.W, LE.CORTE_FIJO):
    if D.hora[t] >= 2:
        s = t - D.hora[t]
        if s >= 0 and D.dia[s] == D.dia[t] and D.hora[s] == 0:
            o += seq[t] == seq[s]; e += P[t - LE.W, seq[s]]
log(f"   sale {o} veces; el motor esperaba {e:.1f} (O/E contra el motor {o/e:.2f})")
log("\n(b) Fuerza de la estructura mes a mes (ensamble walk-forward): mbits y Top-15")
mes = np.array([f[:7] for f in D.fecha[LE.W:]])
mb = np.log2(P[np.arange(len(P)), seq[LE.W:]] * 38) * 1000
for m in sorted(set(mes)):
    s = mes == m
    if s.sum() < 100: continue
    hay8 = np.mean(D.hora[LE.W:][s] == 0) > 0.05
    log(f"   {m}  mbits {mb[s].mean():6.1f}  Top-15 {100*np.mean(pos[s] < 15):5.1f} %  {'(con 8:00)' if hay8 else ''}  n={s.sum()}")
io.open(os.path.join(AQUI, "salida_regimen.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")

log("\n(c) ¿El mes pasado anticipa el siguiente? (persistencia del régimen)")
f5 = np.zeros(38); f5[:5] = [2, 2, 2, 1, 1]; r5 = (30 * f5[pos] - 8) / 8
meses = [m for m in sorted(set(mes)) if (mes == m).sum() >= 200]
mbm = np.array([mb[mes == m].mean() for m in meses]); r5m = np.array([r5[mes == m].mean() for m in meses])
log(f"   correlación mbits(mes) vs mbits(mes siguiente): {np.corrcoef(mbm[:-1], mbm[1:])[0,1]:+.2f}  (n={len(meses)-1})")
log(f"   correlación mbits(mes) vs retorno Top-5 escalonado(mes siguiente): {np.corrcoef(mbm[:-1], r5m[1:])[0,1]:+.2f}")
alto = mbm[:-1] >= np.median(mbm[:-1])
log(f"   Top-5 escalonado el mes siguiente: tras un mes FUERTE {100*r5m[1:][alto].mean():+.1f} %, tras uno FLOJO {100*r5m[1:][~alto].mean():+.1f} %")
log("(d) Sacar el animal de las 8:00 del Top-5 el resto del día (exploratorio, desarrollo)")
r5b = r5.copy(); cambios = 0
orden = np.argsort(-P, 1, kind="stable")
for t in range(LE.W, LE.CORTE_FIJO):
    if D.hora[t] >= 1:
        s = t - D.hora[t]
        if s >= 0 and D.dia[s] == D.dia[t] and D.hora[s] == 0:
            o_ = list(orden[t - LE.W]); a = int(seq[s])
            if a in o_[:5]:
                cambios += 1; o_.remove(a); o_.append(a); p_ = o_.index(int(seq[t]))
                r5b[t - LE.W] = (30 * f5[p_] - 8) / 8
dv = slice(0, LE.CORTE_FIJO - LE.W)
log(f"   cambia en {cambios} sorteos; Top-5 escalonado {100*r5[dv].mean():+.2f} % -> {100*r5b[dv].mean():+.2f} % por ficha")
io.open(os.path.join(AQUI, "salida_regimen.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
