# -*- coding: utf-8 -*-
"""Las rachas de aciertos y fallos, ¿dicen algo del sorteo siguiente?

Responde a la pregunta de siempre: "van 3 fallos seguidos, ¿ya toca?" y su
gemela "van 3 aciertos, ¿esta caliente?".

Metodo: se construye un rankeador Top-15 por regla (el mejor de los que se
midieron en top15_ventana48.py: no salio hoy + calor a 150) y se puntua
walk-forward sobre el desarrollo [2000, 9357). Eso da 7.357 aciertos/fallos
reales, encadenados en el tiempo. Sobre esa cadena se mide:

  1. El reparto de longitudes de racha, contra lo que da un proceso SIN
     memoria con la misma tasa.
  2. P(acierto | vengo de k fallos seguidos), k = 0..5.
  3. P(acierto | vengo de k aciertos seguidos), k = 0..5.

Si el sorteo tuviera memoria, (2) subiria con k ("ya toca") o (3) subiria
("esta caliente"). Si salen planas, la racha no informa de nada.

Se incluye un CONTROL de azar puro: un rankeador aleatorio. Sus rachas tienen
que salir iguales de planas. Si el control diera algo, el metodo estaria mal.

Solo stdlib. Solo lectura.
"""
import os, random
from collections import deque, Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HIST = os.path.join(RAIZ, "historial.txt")
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K, TOPN, W0, CORTE = 38, 15, 2000, 9357


def cargar():
    filas = []
    with open(HIST, encoding="utf-8") as f:
        for ln in f:
            p = ln.split()
            if len(p) == 3 and p[2] in IDX:
                filas.append((p[0], int(p[1]), IDX[p[2]]))
    filas.sort(key=lambda r: (r[0], r[1]))
    return [r[0] for r in filas], [r[2] for r in filas]


def cadena_aciertos(fecha, seq, modo, semilla=20260922):
    """Devuelve la lista de 0/1 (fallo/acierto Top-15) sorteo a sorteo."""
    rng = random.Random(semilla)
    cnt150, col150 = [0] * K, deque()
    hoy, dia_ant = [0] * K, None
    out = []
    for t in range(len(seq)):
        if fecha[t] != dia_ant:
            hoy, dia_ant = [0] * K, fecha[t]
        if W0 <= t < CORTE:
            if modo == "regla":
                clave = [-1000 * hoy[i] + cnt150[i] for i in range(K)]
            else:                                   # control: azar puro
                clave = [rng.random() for _ in range(K)]
            # desempate aleatorio justo -> acierto binario, sin inflar
            orden = sorted(range(K), key=lambda i: (-clave[i], rng.random()))
            out.append(1 if orden.index(seq[t]) < TOPN else 0)
        a = seq[t]
        cnt150[a] += 1; col150.append(a)
        if len(col150) > 150:
            cnt150[col150.popleft()] -= 1
        hoy[a] += 1
    return out


def rachas(bits, valor):
    """Longitudes de las rachas seguidas de `valor`."""
    out, c = [], 0
    for b in bits:
        if b == valor:
            c += 1
        elif c:
            out.append(c); c = 0
    if c:
        out.append(c)
    return out


def ic95(k, n):
    if not n:
        return 0.0, 0.0, 0.0
    t = k / n
    e = 1.96 * (t * (1 - t) / n) ** 0.5
    return t, max(0, t - e), min(1, t + e)


def condicional(bits, valor, etiqueta, tasa):
    """P(acierto | vengo de k seguidos de `valor`)."""
    print(f"\n  {etiqueta}")
    print(f"  {'racha previa':<16}{'sorteos':>9}{'aciertan':>10}{'tasa':>9}{'IC95':>17}")
    print("  " + "-" * 62)
    for k in range(0, 6):
        n = a = 0
        for i in range(k, len(bits) - 1):
            # los k sorteos que acaban en i tienen que ser todos `valor`;
            # con k=0 no se exige nada y sale la tasa global
            if k and not all(bits[i - j] == valor for j in range(k)):
                continue
            n += 1
            a += bits[i + 1]
        t, lo, hi = ic95(a, n)
        marca = ""
        if n and not (lo <= tasa <= hi):
            marca = "  <-- se sale"
        print(f"  {k:<16}{n:>9}{a:>10}{100*t:>8.1f}%{100*lo:>8.1f}-{100*hi:<8.1f}{marca}")
    print(f"  (tasa global = {100*tasa:.1f} %; si la columna es plana, la racha no informa)")


def analizar(bits, titulo):
    n = len(bits)
    tasa = sum(bits) / n
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)
    print(f"  n = {n} sorteos, tasa Top-15 = {100*tasa:.2f} %")

    print(f"\n  Reparto de rachas, observado vs SIN memoria:")
    print(f"  {'largo':<8}{'fallos obs':>12}{'esperado':>11}{'aciertos obs':>14}{'esperado':>11}")
    print("  " + "-" * 56)
    rf, ra = Counter(rachas(bits, 0)), Counter(rachas(bits, 1))
    tf, ta = sum(rf.values()), sum(ra.values())
    q = 1 - tasa
    for L in range(1, 8):
        ef = tf * (1 - q) * q ** (L - 1)
        ea = ta * (1 - tasa) * tasa ** (L - 1)
        print(f"  {L:<8}{rf.get(L,0):>12}{ef:>11.1f}{ra.get(L,0):>14}{ea:>11.1f}")
    print(f"  {'8+':<8}{sum(v for k,v in rf.items() if k>=8):>12}"
          f"{tf*q**7:>11.1f}{sum(v for k,v in ra.items() if k>=8):>14}{ta*tasa**7:>11.1f}")

    condicional(bits, 0, "P(acierto | vengo de k FALLOS seguidos)   <- '¿ya toca?'", tasa)
    condicional(bits, 1, "P(acierto | vengo de k ACIERTOS seguidos) <- '¿esta caliente?'", tasa)


if __name__ == "__main__":
    fecha, seq = cargar()
    analizar(cadena_aciertos(fecha, seq, "regla"),
             "A. RANKEADOR POR REGLA (no salio hoy + calor 150)")
    analizar(cadena_aciertos(fecha, seq, "control"),
             "B. CONTROL: RANKEADOR AL AZAR (tiene que salir igual de plano)")

    print("\n" + "=" * 70)
    print("C. ¿ES RARO VER 3 Y 3 EN UN MISMO DIA?")
    print("=" * 70)
    p = 0.5307
    rng = random.Random(7)
    R, c3 = 200000, 0
    for _ in range(R):
        d = [1 if rng.random() < p else 0 for _ in range(12)]
        mf = ma = f = a = 0
        for b in d:
            f = 0 if b else f + 1; a = a + 1 if b else 0
            mf, ma = max(mf, f), max(ma, a)
        if mf >= 3 and ma >= 3:
            c3 += 1
    print(f"\n  En una jornada de 12 sorteos, con el modelo sano (53,1 %),")
    print(f"  P(ver una racha de 3+ fallos Y una de 3+ aciertos) = {c3/R:.3f}")
    print(f"  Es decir: pasa en {100*c3/R:.0f} de cada 100 jornadas.")
