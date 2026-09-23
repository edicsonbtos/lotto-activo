# -*- coding: utf-8 -*-
"""Hilo 7: caracterizacion descriptiva de RD Int (solo calentamiento + desarrollo).

No cambia ningun modelo. Mide, sobre las filas 'dev':
  1) evitacion intradia propia (animal que ya salio HOY en RD),
  2) curva de hueco propia (sorteos y dias desde la ultima salida),
  3) memoria cruzada con Lotto Activo (h, h-1, ..., h-11 y 'salio hoy' sin h ni h-1),
  4) union (salio hoy en RD) U (salio hoy en LA),
  5) techo in-sample del Top-3 usando solo esas exclusiones.

Anti-fuga: se trunca en el primer indice con tramo 'test' ANTES de todo; nada de
test/desc/vivo se lee. Toda exposicion del sorteo t usa RD hasta t-1 y LA hasta h:00.

Tasa relativa: O/E contra el azar 1/K (K=38) y razon de tasas Mantel-Haenszel
estratificada por hora (animales expuestos vs no expuestos del mismo sorteo).
IC95 por bootstrap de bloques de jornada.

Uso: python herramientas/rdint/caracterizar.py  -> herramientas/resultados/hilo7_caracterizacion.md
"""
import io, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.dirname(AQUI))
import datos as D
import lotto_eval as LE

K = LE.K
H = 12
B = 1000
SALIDA = os.path.join(os.path.dirname(AQUI), "resultados", "hilo7_caracterizacion.md")


# ---------------------------------------------------------------- datos truncados
def preparar():
    rd, la_h, la_h1, la_hoy, tramo = D.cargar()
    n_fin = int(np.argmax(tramo == "test"))
    assert tramo[n_fin] == "test" and not np.isin(tramo[:n_fin], ["test", "desc", "vivo"]).any()
    rd = rd.prefijo(n_fin)
    tramo = tramo[:n_fin]
    fechas_ok = set(rd.fecha)
    la_dia = {f: v for f, v in D._la_por_fecha().items() if f in fechas_ok}   # solo dias cal/dev
    # LA por sorteo RD: matriz (n, 12) con el ganador LA de cada hora <= h del mismo dia (-1 si no)
    n = len(rd)
    la_m = np.full((n, H), -1)
    for t in range(n):
        dia = la_dia.get(rd.fecha[t], {})
        for hh in range(int(rd.hora[t]) + 1):          # solo h:00 o antes
            la_m[t, hh] = dia.get(hh, -1)
    assert (la_m[np.arange(n), rd.hora] == la_h[:n_fin]).all()
    # LA como secuencia propia (cruza medianoche): la_lag[t, k] = k-esimo sorteo LA hacia atras desde
    # el de h:00 del mismo dia (k=0 es h:00). -1 si falta h:00 o si el salto cruza un dia faltante.
    seq_la = [(f, hh, v) for f in sorted(la_dia) for hh, v in sorted(la_dia[f].items())]
    pos = {(f, hh): i for i, (f, hh, _) in enumerate(seq_la)}
    dnum = {f: i for i, f in enumerate(sorted(fechas_ok))}
    la_lag = np.full((n, 2 * H), -1)
    for t in range(n):
        p = pos.get((rd.fecha[t], int(rd.hora[t])))
        if p is None:
            continue
        for k in range(2 * H):
            if p - k < 0 or dnum[rd.fecha[t]] - dnum[seq_la[p - k][0]] > 1:
                break
            la_lag[t, k] = seq_la[p - k][2]
    return rd, la_m, la_lag, tramo


def estado_rd(rd):
    """Para cada sorteo t: set de animales RD de hoy antes de t, hueco en sorteos y en dias."""
    n = len(rd)
    hoy = np.zeros((n, K), bool)
    gap_s = np.full((n, K), 10**6)            # sorteos desde la ultima salida (1 = el anterior)
    gap_d = np.full((n, K), 10**6)            # dias desde la ultima salida (0 = hoy)
    ult_t = np.full(K, -10**6)
    ult_d = np.full(K, -10**6)
    for t in range(n):
        gap_s[t] = t - ult_t
        gap_d[t] = rd.dia[t] - ult_d
        hoy[t] = gap_d[t] == 0
        ult_t[rd.seq[t]] = t
        ult_d[rd.seq[t]] = rd.dia[t]
    return hoy, gap_s, gap_d


# ---------------------------------------------------------------- estadistica
class Tabla:
    """Acumula por (jornada, hora): a = gano expuesto, n1 = expuestos, e = sum n1/K, v = var."""

    def __init__(self, dias, horas, filas):
        self.ud, self.idd = np.unique(dias[filas], return_inverse=True)
        self.h = horas[filas]
        self.filas = filas

    def acumular(self, a, n1):
        T = np.zeros((len(self.ud), H, 4))
        p = n1 / K
        np.add.at(T, (self.idd, self.h, 0), a)
        np.add.at(T, (self.idd, self.h, 1), n1)
        np.add.at(T, (self.idd, self.h, 2), 1.0)               # sorteos
        np.add.at(T, (self.idd, self.h, 3), p * (1 - p))
        return T


def rr_mh(S):
    """S (..., H, 4) sumado por hora -> O/E y RR Mantel-Haenszel (expuestos vs no expuestos)."""
    a, n1, m = S[..., 0], S[..., 1], S[..., 2]
    c, n0, N = m - a, K * m - n1, K * m
    with np.errstate(divide="ignore", invalid="ignore"):
        num = np.where(N > 0, a * n0 / N, 0).sum(-1)
        den = np.where(N > 0, c * n1 / N, 0).sum(-1)
        oe = a.sum(-1) / (n1.sum(-1) / K)
        rr = num / den
    return oe, rr


def resumir(T, horas_sel=None, semilla=0):
    """T (dias, H, 4). Devuelve dict con O, E, O/E, IC, z, RR_MH, IC."""
    if horas_sel is not None:
        T = T[:, horas_sel, :]
    S = T.sum(0)
    O, E = S[:, 0].sum(), S[:, 1].sum() / K
    z = (O - E) / np.sqrt(max(S[:, 3].sum(), 1e-12))
    oe, rr = rr_mh(S)
    rng = np.random.default_rng(semilla)
    nd = T.shape[0]
    oes, rrs = np.empty(B), np.empty(B)
    for b in range(B):
        Sb = T[rng.integers(0, nd, nd)].sum(0)
        oes[b], rrs[b] = rr_mh(Sb)
    return dict(n=int(S[:, 2].sum()), O=O, E=E, oe=oe, z=z, rr=rr,
                oe_ic=np.nanpercentile(oes, [2.5, 97.5]), rr_ic=np.nanpercentile(rrs, [2.5, 97.5]),
                nexp=S[:, 1].sum() / max(S[:, 2].sum(), 1))


def fila(nombre, r):
    return "| %s | %d | %.1f | %.1f | %.2f [%.2f, %.2f] | %+.1f | %.2f [%.2f, %.2f] | %.2f |" % (
        nombre, r["n"], r["O"], r["E"], r["oe"], r["oe_ic"][0], r["oe_ic"][1], r["z"],
        r["rr"], r["rr_ic"][0], r["rr_ic"][1], r["nexp"])


CAB = ("| medida | sorteos | obs | esp | O/E [IC95] | z | RR MH [IC95] | expuestos/sorteo |\n"
       "|---|---|---|---|---|---|---|---|")


LECTURA = """## Lectura (escrita a mano el 2026-09-23 tras la primera corrida; las tablas de arriba mandan)

1. **Evitación propia fuerte y estable.** Un animal que ya salió hoy en RD gana con O/E 0,28
   (z = −23), 0,25 y 0,30 en cada mitad. Casi total de 9:30 a 14:30 (O/E 0,00–0,16) y se afloja al
   final (19:30: 0,50). Repetir dos veces en el día: 1 caso contra 13 esperados.
2. **No es 'hoy', es una ventana de ~12 sorteos que cruza la medianoche.** A las 8:30 lo de ayer
   (hueco ≤ 12) sale con O/E 0,38; a las 9:30 0,68; a las 10:30 0,77; neutro desde 11:30. La curva de
   hueco en sorteos: 1 → 0,14; 2 → 0,24; 3 → 0,34; 4–6 → 0,49; 7–11 → 0,81 (0,97 si se excluye lo de
   hoy). **Hay rebote de reciclaje**: 12–17 → 1,10; 18–23 → 1,22; 24–29 → 1,27; 30–41 → 1,34;
   42–59 → 1,18; 60–89 → 1,07; 150+ → 0,79. En días: día 1 neutro (1,00), días 2–3 ≈ 1,24–1,32,
   4–5 ≈ 1,18, 10+ ≈ 0,88. Igual en ambas mitades.
3. **Memoria cruzada de LA: solo las dos últimas horas, y solo del mismo día.** RD h:30 = LA h:00:
   O/E 0,21 [0,13; 0,29], z = −9,6 (mitades 0,14 y 0,27). = LA (h−1):00: 0,58 [0,46; 0,70], z = −4,9
   (mitades 0,71 y 0,45: inestable). (h−2): 0,79, IC toca 1 en cada mitad. De h−3 hacia atrás el
   signo se invierte (O/E 1,1–1,5). LA de ayer (cruce de medianoche) no se evita. La evitación de
   LA h no se debilita con la hora; la de h−1 sí (neutra desde 17:30).
4. **La 'unión' no es un conjunto prohibido.** En promedio 10,9 animales por sorteo, O/E 0,64, pero
   se descompone: solo-RD-hoy 0,27, ambos 0,31, **solo-LA-hoy 1,03** (neutro). Lo 'casi prohibido' es
   RD hoy (≈ 0–10,7 animales según la hora) + LA h (1 animal) + a medias LA h−1.
5. **Techo.** Excluir RD hoy da 8,95 % de Top-3; excluir la unión 9,08 %: por debajo del 10 % de
   equilibrio incluso in-sample. Bajar animales reparte muy poca masa entre los otros ~30. Solo
   combinando con el rebote de reciclaje (días 2–5) el oráculo in-sample llega a 10,4–10,5 %
   (IC95 ≈ [9,7; 11,2]), 9,95 % en la 1ª mitad y 11,6 % en la 2ª. En mbits: el aporte de LA
   al oráculo (RD hoy + hueco en días) es ≈ +21 mbits in-sample en dev, +22 y +25 por mitad.
"""


# ---------------------------------------------------------------- analisis
def main():
    rd, la_m, la_lag, tramo = preparar()
    n = len(rd)
    y = rd.seq
    hora = np.asarray(rd.hora)
    dias = np.asarray(rd.dia)
    hoy, gap_s, gap_d = estado_rd(rd)
    dev = np.where(tramo == "dev")[0]
    ud = np.unique(dias[dev])
    corte = ud[len(ud) // 2]
    mitades = {"dev": dev, "1a mitad": dev[dias[dev] < corte], "2a mitad": dev[dias[dev] >= corte]}
    out = []
    w = out.append
    w("# Hilo 7 — Caracterización descriptiva de RD Int (solo desarrollo)\n")
    w("Generado por `herramientas/rdint/caracterizar.py`. Datos truncados en el primer sorteo del tramo "
      "`test` (%s); todas las métricas son sobre filas `dev` (%s .. %s, %d sorteos, %d jornadas). "
      "Mitades por jornada: 1ª hasta %s, 2ª desde %s. Nada de test/desc/vivo se leyó.\n" % (
          [d for t, d in D.TRAMOS if t == "test"][0], rd.fecha[dev[0]], rd.fecha[dev[-1]], len(dev),
          len(ud), rd.fecha[dev[dias[dev] < corte][-1]], rd.fecha[dev[dias[dev] >= corte][0]]))
    w("**Veredicto: NA (descriptivo).** Azar: 1/K con K=38 (los 38 animales salen en cal+dev; "
      "Ballena 128 veces en dev, rango del resto 125..187). O/E = observados / esperados por azar; "
      "RR MH = razón de tasas Mantel-Haenszel estratificada por hora, animales expuestos contra no "
      "expuestos del mismo sorteo. IC95 por bootstrap de %d réplicas de jornadas. z = (O−E)/√Σp(1−p) "
      "contra el azar uniforme.\n" % B)

    # ---------- 1) evitacion intradia propia
    w("## 1. Evitación intradía propia: gana un animal que ya salió HOY en RD\n")
    n1 = hoy.sum(1).astype(float)
    a = hoy[np.arange(n), y].astype(float)
    res1 = {}
    w(CAB)
    for nom, f in mitades.items():
        f2 = f[hora[f] > 0]
        T = Tabla(dias, hora, f2).acumular(a[f2], n1[f2])
        res1[nom] = T
        w(fila("salió hoy en RD — " + nom, resumir(T)))
    w("\nPor hora (dev completo):\n")
    w(CAB)
    for h in range(1, H):
        w(fila("%d:30 (hay %.1f en el set)" % (8 + h, n1[dev][hora[dev] == h].mean()), resumir(res1["dev"], [h])))
    # por repeticion: cuantas veces ya salio hoy
    w("\nPor número de veces que ya salió hoy (dev, O/E contra azar):\n")
    cnt_hoy = np.zeros((n, K), int)
    for t in range(1, n):
        if dias[t] == dias[t - 1]:
            cnt_hoy[t] = cnt_hoy[t - 1]
            cnt_hoy[t, y[t - 1]] += 1
    w(CAB)
    f2 = dev[hora[dev] > 0]
    for k in (1, 2):
        e = cnt_hoy >= k if k == 2 else cnt_hoy == 1
        T = Tabla(dias, hora, f2).acumular(e[f2, y[f2]].astype(float), e[f2].sum(1).astype(float))
        w(fila("salió %s hoy" % ("1 vez" if k == 1 else "2+ veces"), resumir(T)))
    w("")

    # ---------- 2) curva de hueco
    w("## 2. Curva de hueco propia de RD\n")
    w("Hueco en sorteos (1 = salió en el sorteo anterior, cruce de día incluido). O/E contra 1/38.\n")
    w(CAB)
    bins_s = [(1, 1), (2, 2), (3, 3), (4, 6), (7, 11), (12, 17), (18, 23), (24, 29), (30, 41), (42, 59),
              (60, 89), (90, 149), (150, 10**7)]
    for lo, hi in bins_s:
        e = (gap_s >= lo) & (gap_s <= hi)
        T = Tabla(dias, hora, dev).acumular(e[dev, y[dev]].astype(float), e[dev].sum(1).astype(float))
        w(fila("%d..%s" % (lo, hi if hi < 10**6 else "∞"), resumir(T)))
    w("\nHueco en días calendario (0 = ya salió hoy; 1 = salió ayer y no hoy; ...):\n")
    w(CAB)
    for lo, hi in [(0, 0), (1, 1), (2, 2), (3, 3), (4, 5), (6, 9), (10, 10**7)]:
        e = (gap_d >= lo) & (gap_d <= hi)
        for nom, f in mitades.items():
            T = Tabla(dias, hora, f).acumular(e[f, y[f]].astype(float), e[f].sum(1).astype(float))
            w(fila("día %d%s — %s" % (lo, "" if hi == lo else ".." + ("∞" if hi > 10**6 else str(hi)), nom), resumir(T)))
    w("\nCruce de medianoche: 'salió ayer y no hoy' (día 1) y hueco ≤12 sorteos sin haber salido hoy, "
      "por hora (dev):\n")
    w(CAB)
    e1 = gap_d == 1
    e12 = (gap_s <= 12) & ~hoy
    T1 = Tabla(dias, hora, dev).acumular(e1[dev, y[dev]].astype(float), e1[dev].sum(1).astype(float))
    T12 = Tabla(dias, hora, dev).acumular(e12[dev, y[dev]].astype(float), e12[dev].sum(1).astype(float))
    for h in range(H):
        w(fila("%d:30 día 1" % (8 + h), resumir(T1, [h])))
        w(fila("%d:30 hueco ≤12, no hoy" % (8 + h), resumir(T12, [h])))
    w("\nHueco en sorteos restringido a animales que NO salieron hoy (separa la evitación intradía "
      "del reciclaje entre días):\n")
    w(CAB)
    for lo, hi in bins_s[4:]:
        e = (gap_s >= lo) & (gap_s <= hi) & ~hoy
        T = Tabla(dias, hora, dev).acumular(e[dev, y[dev]].astype(float), e[dev].sum(1).astype(float))
        w(fila("%d..%s, no hoy" % (lo, hi if hi < 10**6 else "∞"), resumir(T)))
    w("")

    # ---------- 3) memoria cruzada
    w("## 3. Memoria cruzada con Lotto Activo\n")
    w("Solo sorteos con el dato LA requerido (si falta la hora LA el sorteo se omite en esa medida). "
      "LA h−k:00 del mismo día; k=0 es la de 30 min antes.\n")
    w(CAB)
    cruz = {}
    for k in range(0, H):
        hh = hora - k
        ok = hh >= 0
        la_k = np.where(ok, la_m[np.arange(n), np.clip(hh, 0, H - 1)], -1)
        f = dev[la_k[dev] >= 0]
        T = Tabla(dias, hora, f).acumular((y[f] == la_k[f]).astype(float), np.ones(len(f)))
        cruz[k] = (la_k, T)
        w(fila("RD h:30 == LA (h−%d):00" % k if k else "RD h:30 == LA h:00", resumir(T)))
    # salio hoy en LA excluyendo h y h-1
    # LA tuvo 11 sorteos (9:00..19:00) hasta nov-2024; el de 8:00 se agrega despues. 'Completo' =
    # estan todas las horas LA 9:00..h:00 (la de 8:00 se usa si existe).
    completo = np.array([(la_m[t, 1:hora[t] + 1] >= 0).all() and (la_m[t] >= 0).any() for t in range(n)])
    la_set = np.zeros((n, K), bool)
    la_set_resto = np.zeros((n, K), bool)
    for t in range(n):
        v = la_m[t, :hora[t] + 1]
        v = v[v >= 0]
        la_set[t, v] = True
        r = la_m[t, :max(hora[t] - 1, 0)]
        r = r[r >= 0]
        la_set_resto[t, r] = True
    for t in range(n):                       # quitar los animales de h y h-1 aunque hayan salido antes
        for hh in (hora[t], hora[t] - 1):
            if hh >= 0 and la_m[t, hh] >= 0:
                la_set_resto[t, la_m[t, hh]] = False
    f = dev[completo[dev] & (hora[dev] >= 2)]
    T = Tabla(dias, hora, f).acumular(la_set_resto[f, y[f]].astype(float), la_set_resto[f].sum(1).astype(float))
    res_resto = T
    w(fila("salió hoy en LA (≤ h−2), sin los de h y h−1", resumir(T)))
    w("\nLA como secuencia continua: RD h:30 contra el k-ésimo sorteo LA hacia atrás desde h:00, "
      "contando solo los casos en que ese sorteo LA es de AYER (cruza la medianoche), dev:\n")
    w(CAB)
    for k in range(1, 2 * H):
        f = dev[(la_lag[dev, k] >= 0) & (hora[dev] < k)]   # h:00 hoy son h+1 sorteos (o h si no hay 8:00)
        f = f[np.array([la_lag[t, k] >= 0 and la_m[t, :hora[t] + 1][la_m[t, :hora[t] + 1] >= 0].size <= k
                        for t in f], bool)] if len(f) else f
        if len(f) < 100:
            continue
        T = Tabla(dias, hora, f).acumular((y[f] == la_lag[f, k]).astype(float), np.ones(len(f)))
        w(fila("LA k=%d atrás (de ayer)" % k, resumir(T)))
    w("\nPor mitades del desarrollo:\n")
    w(CAB)
    for k in (0, 1, 2):
        la_k = cruz[k][0]
        for nom, fm in list(mitades.items())[1:]:
            ff = fm[la_k[fm] >= 0]
            T = Tabla(dias, hora, ff).acumular((y[ff] == la_k[ff]).astype(float), np.ones(len(ff)))
            w(fila("LA h−%d — %s" % (k, nom), resumir(T)))
    for nom, fm in list(mitades.items())[1:]:
        ff = fm[completo[fm] & (hora[fm] >= 2)]
        T = Tabla(dias, hora, ff).acumular(la_set_resto[ff, y[ff]].astype(float),
                                           la_set_resto[ff].sum(1).astype(float))
        w(fila("LA hoy ≤h−2 sin h,h−1 — " + nom, resumir(T)))
    w("\nPor hora del día (dev): ¿se debilita al final?\n")
    w(CAB)
    for h in range(H):
        w(fila("%d:30 vs LA %d:00" % (8 + h, 8 + h), resumir(cruz[0][1], [h])))
    w("")
    w(CAB)
    for h in range(1, H):
        w(fila("%d:30 vs LA %d:00" % (8 + h, 7 + h), resumir(cruz[1][1], [h])))
    w("")

    # ---------- 4) union
    w("## 4. Unión: (salió hoy en RD) ∪ (salió hoy en LA hasta h:00)\n")
    U = hoy | la_set
    f = dev[completo[dev]]
    w("Sorteos dev con LA completa hasta h:00: %d de %d.\n" % (len(f), len(dev)))
    w(CAB)
    comp = {"unión": U, "solo RD hoy": hoy & ~la_set, "solo LA hoy": la_set & ~hoy, "ambos": hoy & la_set,
            "fuera de la unión": ~U}
    for nom, e in comp.items():
        for nm, fm in mitades.items():
            ff = fm[completo[fm]]
            T = Tabla(dias, hora, ff).acumular(e[ff, y[ff]].astype(float), e[ff].sum(1).astype(float))
            w(fila("%s — %s" % (nom, nm), resumir(T)))
    w("\nTamaño medio de la unión ('casi prohibidos') y tasa por hora (dev):\n")
    w("| hora | sorteos | |RD hoy| | |LA hoy| | |unión| | O/E unión [IC95] | P(gana fuera) obs | azar |")
    w("|---|---|---|---|---|---|---|---|")
    Tu = Tabla(dias, hora, f).acumular(U[f, y[f]].astype(float), U[f].sum(1).astype(float))
    for h in range(H):
        m = f[hora[f] == h]
        r = resumir(Tu, [h])
        w("| %d:30 | %d | %.1f | %.1f | %.1f | %.2f [%.2f, %.2f] | %.3f | %.3f |" % (
            8 + h, len(m), hoy[m].sum(1).mean(), la_set[m].sum(1).mean(), U[m].sum(1).mean(),
            r["oe"], r["oe_ic"][0], r["oe_ic"][1], 1 - U[m, y[m]].mean(), 1 - U[m].sum(1).mean() / K))
    w("")

    # ---------- 5) techo in-sample del Top-3
    w("## 5. Techo in-sample (oráculo optimista) del Top-3\n")
    w("Top-3 elegido al azar entre los NO excluidos (empates repartidos). Acierto esperado por sorteo "
      "= 1[y∉U]·3/(38−|U|). Además, un oráculo multiplicativo con los O/E in-sample de cada categoría "
      "(RD hoy, LA h, LA h−1, LA hoy resto) ajustados en todo dev: el mejor caso, sin penalizar el "
      "sobreajuste. La variante '+ hueco en días' multiplica además por el O/E in-sample del hueco "
      "propio en días (1, 2, 3, 4-5, 6-9, 10+); 'solo RD' usa RD hoy + hueco sin nada de LA: la "
      "diferencia de mbits entre ambas es el techo in-sample del aporte de LA (a comparar con los +5 "
      "mbits del pre-registro). mbits = log-verosimilitud media contra 1/38 del mismo oráculo. Equilibrio del "
      "Top-3 plano: 10 %.\n")

    def top3_esperado(W, yy):
        """W (m, K) pesos; prob de que y caiga en un Top-3 con empates al azar."""
        s = -np.sort(-W, 1)
        umbral = s[:, 2:3]
        mayor = (W > umbral).sum(1)
        igual = (W == umbral).sum(1)
        wy = W[np.arange(len(yy)), yy]
        return np.where(wy > umbral[:, 0], 1.0, np.where(wy == umbral[:, 0], (3 - mayor) / igual, 0.0))

    def oe_cat(e, ff):
        return e[ff, y[ff]].sum() / (e[ff].sum() / K)

    la0 = np.zeros((n, K), bool)
    la1 = np.zeros((n, K), bool)
    v = cruz[0][0]; la0[v >= 0, v[v >= 0]] = True
    v = cruz[1][0]; la1[v >= 0, v[v >= 0]] = True
    w("| esquema | tramo | sorteos | Top-3 | IC95 (bootstrap jornadas) | mbits |")
    w("|---|---|---|---|---|---|")
    for nom, fm in mitades.items():
        ff = fm[completo[fm]]
        for esquema in ("excluir RD hoy", "excluir unión", "oráculo multiplicativo", "oráculo solo RD (hoy + hueco días)",
                        "oráculo + hueco en días"):
            if esquema == "excluir RD hoy":
                Wm = (~hoy[ff]).astype(float)
            elif esquema == "excluir unión":
                Wm = (~U[ff]).astype(float)
            else:
                cats = [hoy, la0, la1, la_set_resto & ~hoy]
                if esquema.startswith("oráculo solo RD"):
                    cats = [hoy]
                if esquema != "oráculo multiplicativo":
                    cats += [(gap_d >= lo) & (gap_d <= hi) for lo, hi in ((1, 1), (2, 2), (3, 3), (4, 5), (6, 9), (10, 10**7))]
                rr = [oe_cat(c, ff) for c in cats]                      # in-sample en el mismo tramo
                Wm = np.ones((len(ff), K))
                for c, r in zip(cats, rr):
                    Wm *= np.where(c[ff], max(r, 1e-3), 1.0)
            acierto = top3_esperado(Wm, y[ff])
            if esquema.startswith("oráculo"):
                P = Wm / Wm.sum(1, keepdims=True)
                mb = 1000 * np.mean(np.log2(P[np.arange(len(ff)), y[ff]] * K))
            else:
                mb = float("nan")
            idd = np.unique(dias[ff], return_inverse=True)[1]
            sa = np.bincount(idd, acierto); sn = np.bincount(idd)
            rng = np.random.default_rng(1)
            bs = []
            for b in range(B):
                i = rng.integers(0, len(sn), len(sn))
                bs.append(sa[i].sum() / sn[i].sum())
            lo, hi = np.percentile(bs, [2.5, 97.5])
            w("| %s | %s | %d | %.2f %% | [%.2f, %.2f] | %s |" % (
                esquema, nom, len(ff), 100 * acierto.mean(), 100 * lo, 100 * hi,
                "—" if np.isnan(mb) else "%+.1f" % mb))
    w("")
    ff = dev[completo[dev]]
    w("O/E in-sample usados por el oráculo (dev completo): RD hoy %.2f, LA h %.2f, LA h−1 %.2f, "
      "LA hoy resto %.2f.\n" % tuple(oe_cat(c, ff) for c in [hoy, la0, la1, la_set_resto & ~hoy]))

    w(LECTURA)
    with io.open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
