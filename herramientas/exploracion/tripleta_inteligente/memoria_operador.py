# -*- coding: utf-8 -*-
"""¿El operador "recuerda" por SORTEOS o por DÍAS? (solo desarrollo, descriptivo)
O/E de repetir el animal que salió k sorteos atrás, separando si entre medio hubo una noche o no.
Uso: python herramientas/exploracion/tripleta_inteligente/memoria_operador.py -> salida_memoria_operador.txt"""
import csv, io, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); import lotto_eval as LE  # noqa: E402
SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)
D = LE.cargar(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt"))
seq, dia, hora = D.seq, D.dia, D.hora
T = range(2000, 9357)
def oe(pares):
    o = sum(seq[t] == seq[s] for t, s in pares); e = len(pares) / 38
    return o / e if e else float("nan"), len(pares)
log("1) Lotto Activo: O/E de repetir el animal de k sorteos atrás (1,00 = azar; <1 = lo evita; >1 = lo recicla)")
log("    k | misma jornada      | cruzando la noche  ")
for k in list(range(1, 13)) + [14, 16, 18, 20, 24, 30, 36]:
    a = [(t, t - k) for t in T if dia[t - k] == dia[t]]
    b = [(t, t - k) for t in T if dia[t - k] != dia[t] and dia[t] - dia[t - k] <= 3]
    ra, na = oe(a); rb, nb = oe(b)
    log(f"   {k:2d} | {ra:5.2f} (n={na:5d})   | {rb:5.2f} (n={nb:5d})")
# 2) feriados: tras un día SIN sorteos, ¿se sigue evitando lo último que salió?
log("\n2) Después de un día SIN sorteos (feriado/hueco ≥ 2 días): O/E de repetir lo de los últimos 12 sorteos")
pares_h = []; pares_n = []
for t in T:
    if t > 0 and dia[t] != dia[t - 1]:          # primer sorteo de la jornada
        hueco = dia[t] - dia[t - 1]
        for k in range(1, 13):
            (pares_h if hueco >= 2 else pares_n).append((t, t - k))
r, n = oe(pares_h); r2, n2 = oe(pares_n)
log(f"   tras feriado: O/E {r:.2f} (n={n}, {n//12} mañanas)   tras una noche normal: O/E {r2:.2f} (n={n2})")
# 3) RD Internacional (su propio juego) y el cruce RD -> LA, misma jornada vs cruzando la noche
rd = {}
NOM = {"DELFIN": "0", "BALLENA": "00"}
import re, unicodedata
def cod(nm):
    s = re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", nm.upper()))
    sys.path.insert(0, os.path.join(RAIZ, "herramientas", "rdint")); import datos as RDD
    return RDD.ANIMALES.get(s)
filas = []
with io.open(os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv"), encoding="utf-8") as fh:
    for r_ in csv.DictReader(fh):
        c = cod(r_["animal"])
        if c is not None and "2024-03-01" <= r_["fecha"] < "2025-07-01":
            filas.append((r_["fecha"], int(r_["hora"][:2]) - 8, LE.IDX[c]))
filas.sort(); rs = np.array([x[2] for x in filas]); rf = [x[0] for x in filas]
log("\n3) RD Internacional consigo mismo (desarrollo de RD), O/E de repetir k sorteos atrás")
log("    k | misma jornada      | cruzando la noche")
for k in (1, 2, 3, 4, 6, 8, 12, 16, 20, 24):
    a = [(t, t - k) for t in range(k, len(rs)) if rf[t] == rf[t - k]]
    b = [(t, t - k) for t in range(k, len(rs)) if rf[t] != rf[t - k]]
    oa = sum(rs[t] == rs[s] for t, s in a) / (len(a) / 38) if a else float("nan")
    ob = sum(rs[t] == rs[s] for t, s in b) / (len(b) / 38) if b else float("nan")
    log(f"   {k:2d} | {oa:5.2f} (n={len(a):5d})   | {ob:5.2f} (n={len(b):5d})")
rdmap = {(f, h): a for f, h, a in filas}
log("\n4) Cruce RD -> LA: LA h:00 repite el RD de j sorteos de RD atrás (mismo día vs. el de anoche)")
for j in (1, 2, 3):
    a = []; b = []
    for t in T:
        f, h = D.fecha[t], int(hora[t])
        hh = h - j
        if hh >= 0 and (f, hh) in rdmap:
            a.append(seq[t] == rdmap[(f, hh)])
        elif hh < 0:
            from datetime import date, timedelta
            fa = (date.fromisoformat(f) - timedelta(days=1)).isoformat()
            if (fa, 12 + hh) in rdmap:
                b.append(seq[t] == rdmap[(fa, 12 + hh)])
    log(f"   j={j}: mismo día O/E {np.mean(a)*38:.2f} (n={len(a)})   de anoche O/E {np.mean(b)*38 if b else float('nan'):.2f} (n={len(b)})")
io.open(os.path.join(AQUI, "salida_memoria_operador.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")

# 5) ¿Es "el primer sorteo del día" o es "el de las 8:00"? Antes de nov-2024 el primero era el de las 9:00.
log("\n5) Primer sorteo del día: ¿evita lo de ayer? (O/E de que salga un animal que salió ayer)")
ult = {}
P0 = LE.normalizar(np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "calor_cache.npz"))["P"])
pos = np.argmax(LE.rankings(P0) == D.seq[2000:9357][:, None], 1)
por_dia = {}
for t in range(len(seq)):
    por_dia.setdefault(dia[t], set()).add(int(seq[t]))
for nom, cond in (("9:00 cuando ERA el primero (antes de nov-2024)", lambda t: hora[t] == 1 and dia[t - 1] != dia[t]),
                  ("8:00 (primero desde nov-2024)", lambda t: hora[t] == 0),
                  ("9:00 cuando ya hay 8:00 (segundo)", lambda t: hora[t] == 1 and dia[t - 1] == dia[t])):
    ts = [t for t in T if cond(t) and (dia[t] - 1) in por_dia]
    o = sum(seq[t] in por_dia[dia[t] - 1] for t in ts); e = sum(len(por_dia[dia[t] - 1]) / 38 for t in ts)
    t15 = np.mean([pos[t - 2000] < 15 for t in ts])
    log(f"   {nom}: O/E de 'salió ayer' {o/e:.2f}  Top-15 {100*t15:.1f} %  (n={len(ts)})")
# 6) El animal de las 8:00, ¿lo evita el resto del día como a los demás?
log("\n6) ¿El resto del día evita el animal de las 8:00 igual que el de las 9:00? (O/E de repetirlo, de 10:00 a 19:00)")
for h0, nom in ((0, "animal de las 8:00"), (1, "animal de las 9:00 (con 8:00 antes)")):
    o = e = 0
    for t in T:
        if hora[t] >= 2 and t - (hora[t] - h0) >= 0:
            s = t - (hora[t] - h0)
            if dia[s] == dia[t] and hora[s] == h0 and (h0 == 0 or (s > 0 and dia[s - 1] == dia[s])):
                o += seq[t] == seq[s]; e += 1 / 38
    log(f"   {nom}: O/E {o/e:.2f} (n={int(round(e*38))})")
io.open(os.path.join(AQUI, "salida_memoria_operador.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
