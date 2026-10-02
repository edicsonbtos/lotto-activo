# -*- coding: utf-8 -*-
"""Descriptivo POSTERIOR a la confirmación de brecha_2026.py (no decide nada; el juez es el vivo).

1. La regla RD aplicada a todo el Top-15 (no solo al Top-5) frente a lo que usa producción, por tramo y por mes.
2. La corrección por exposición (multiplicadores congelados en dev-A) medida en 2026, que nunca la vio.
3. Fuerza de "LA esquiva RD (h-1):30" por hora y por tramo.
4. Las 8:00 mes a mes y la racha en vivo, con los rasgos de cada ganador.
Uso: python herramientas/exploracion/brecha_2026_extra.py   → brecha_2026_extra_salida.txt
"""
import os, sys
from datetime import date, timedelta
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
sys.path.insert(0, os.path.join(RAIZ, "herramientas", "modelos"))
import lotto_eval as LE  # noqa: E402
import hora_8am_ciega as H8  # noqa: E402
import brecha_2026 as B  # noqa: E402
import exposicion as EXP  # noqa: E402

K = 38
LINEAS = []
B.log = H8.log = lambda *a: None          # silencia la carga


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LINEAS.append(s)


def pos_de(orden, y):
    return np.array([o.index(v) for o, v in zip(orden, y)])


def main():
    H8.armar_historial()
    D, Pall = H8.walk_forward()
    RD, LARD = B.cargar_rd_lard()
    n0 = LE.W
    F = np.array(D.fecha[n0:]); y = np.asarray(D.seq)[n0:]; hora = np.asarray(D.hora)[n0:]; dia = np.asarray(D.dia)[n0:]
    P = Pall / Pall.sum(1, keepdims=True)
    menos1 = lambda f: (date.fromisoformat(f) - timedelta(days=1)).isoformat()
    rd1 = np.array([RD.get((f, h - 1)) if h >= 1 else RD.get((menos1(f), 11)) for f, h in zip(F, hora)], object)
    # La regla solo existe de 9:00 a 19:00 (RD 19:30 de la víspera NO se usa a las 8:00: hilo7_cambio_noche.md).
    rdr = np.array([None if h == 0 else r for r, h in zip(rd1, hora)], object)
    tiene = np.ones(len(y), bool)
    # Orden base (mismo desempate que el marcador)
    O0 = LE.rankings(P)
    base = [list(o) for o in O0]
    def cambio5(o, r):                      # producción: sale del Top-5 y queda 6º
        if r is None or r not in o[:5]:
            return o
        return [x for x in o[:5] if x != r] + [o[5], r] + o[6:]
    def fuera15(o, r):                      # brecha 2026: sale del Top-15 entero y queda 16º
        if r is None or r not in o[:15]:
            return o
        return [x for x in o[:16] if x != r][:15] + [r] + [x for x in o[16:] if x != r]
    # exposición (congelada en dev-A) y su orden
    Pe = np.array([EXP.aplicar(p, f, h) for p, f, h in zip(P, F, hora)])
    Oe = [list(o) for o in LE.rankings(Pe)]
    variantes = {
        "producción (ensamble + cambio Top-5)": [cambio5(o, r) for o, r in zip(base, rdr)],
        "RD fuera de todo el Top-15": [fuera15(o, r) for o, r in zip(base, rdr)],
        "exposición + RD fuera del Top-15": [fuera15(o, r) for o, r in zip(Oe, rdr)],
    }
    PS = {k: pos_de(v, y) for k, v in variantes.items()}
    F5, F15 = B.F5, B.F15
    def met(pos, m):
        p = pos[m]
        g5 = np.where(p < 5, 30 * F5[np.minimum(p, 4)], 0) - F5.sum()
        g15 = np.where(p < 15, 30 * F15[np.minimum(p, 14)], 0) - F15.sum()
        return (p < 5).mean(), (p < 15).mean(), g5.sum() / (F5.sum() * m.sum()), g15.sum() / (F15.sum() * m.sum())
    tramos = [("2025", "2025-01-01", "2025-12-19"), ("2026-A ene-may", "2025-12-19", "2026-06-01"),
              ("2026-B jun-sep", "2026-06-01", "2026-09-30"), ("vivo 14-29 sep", "2026-09-14", "2026-09-30"),
              ("2026 completo", "2025-12-19", "2026-09-30")]
    log("=== 1. Regla RD en todo el Top-15 frente a producción (Top-5 / Top-15 / retorno Top-5 esc. / Top-15 pond.) ===")
    for nom, a, b in tramos:
        m = (F >= a) & (F < b) & tiene
        log(f"-- {nom} (n={m.sum()})")
        for k, pos in PS.items():
            t5, t15, r5, r15 = met(pos, m)
            log(f"   {k:<38} Top-5 {t5 * 100:5.2f} %  Top-15 {t15 * 100:5.2f} %  ret5 {r5 * 100:+5.1f} %  ret15 {r15 * 100:+5.1f} %")
    # IC por jornada de la diferencia en el Top-15 y en el retorno ponderado (2026 completo y 2026-B)
    for nom, a, b in (tramos[2], tramos[4]):
        m = (F >= a) & (F < b) & tiene
        for k in list(PS)[1:]:
            d15 = (PS[k][m] < 15).astype(float) - (PS["producción (ensamble + cambio Top-5)"][m] < 15)
            g = lambda p: np.where(p < 15, 30 * F15[np.minimum(p, 14)], 0) - F15.sum()
            dr = (g(PS[k][m]) - g(PS["producción (ensamble + cambio Top-5)"][m])) / F15.sum()
            b1 = B.boot_media(dia[m], d15); b2 = B.boot_media(dia[m], dr)
            log(f"   {nom}: {k} − producción: Top-15 {d15.mean() * 100:+.2f} pp [{np.percentile(b1, 2.5) * 100:+.2f}; "
                f"{np.percentile(b1, 97.5) * 100:+.2f}], ret. ponderado {dr.mean() * 100:+.2f} pp/ficha "
                f"[{np.percentile(b2, 2.5) * 100:+.2f}; {np.percentile(b2, 97.5) * 100:+.2f}]")
    log("\n-- 2026 mes a mes: Top-15 producción → RD fuera del Top-15 (n)")
    for mes in sorted(set(f[:7] for f in F if f >= "2025-12-19")):
        m = (np.char.startswith(F.astype(str), mes)) & (F >= "2025-12-19") & tiene
        a1 = (PS["producción (ensamble + cambio Top-5)"][m] < 15).mean(); a2 = (PS["RD fuera de todo el Top-15"][m] < 15).mean()
        log(f"   {mes}: {a1 * 100:5.1f} → {a2 * 100:5.1f} %  ({a2 * 100 - a1 * 100:+.1f})  n={m.sum()}")

    log("\n=== 2. Exposición (congelada en dev-A, nunca vio 2026): mbits sobre el ensamble ===")
    mb0 = 1000 * np.log2(P[np.arange(len(y)), y] * K); mbe = 1000 * np.log2(Pe[np.arange(len(y)), y] * K)
    for nom, a, b in tramos:
        m = (F >= a) & (F < b)
        bb = B.boot_media(dia[m], mbe[m] - mb0[m], B=4000)
        log(f"   {nom:<16} Δmbits {np.mean(mbe[m] - mb0[m]):+5.1f} [{np.percentile(bb, 2.5):+.1f}; {np.percentile(bb, 97.5):+.1f}]  n={m.sum()}")

    log("\n=== 3. LA esquiva RD (h-1):30: O/E contra el ensamble por hora ===")
    for nom, a, b in (("2025", "2025-01-01", "2025-12-19"), ("2026", "2025-12-19", "2026-09-30")):
        cel = []
        for h in range(12):
            m = (F >= a) & (F < b) & np.array([v is not None for v in rd1]) & (hora == h)
            r = np.array([v for v in rd1[m]], int)
            O = (y[m] == r).sum(); E = P[m][np.arange(m.sum()), r].sum()
            cel.append(f"{8 + h}:00 {O / E:4.2f}")
        m = (F >= a) & (F < b) & np.array([v is not None for v in rd1]); r = np.array([v for v in rd1[m]], int)
        log(f"   {nom}: total {(y[m] == r).sum() / P[m][np.arange(m.sum()), r].sum():.2f} | " + "  ".join(cel))

    log("\n=== 4. Las 8:00 mes a mes (Top-15 de producción; a las 8:00 no hay regla RD del mismo día) ===")
    p0 = PS["producción (ensamble + cambio Top-5)"]
    for mes in sorted(set(f[:7] for f in F if f >= "2025-01-01")):
        m = np.char.startswith(F.astype(str), mes) & (hora == 0)
        if m.sum():
            log(f"   {mes}: {(p0[m] < 15).sum():2d}/{m.sum():2d} = {(p0[m] < 15).mean() * 100:5.1f} %")
    seq = np.asarray(D.seq); diaG = np.asarray(D.dia); horaG = np.asarray(D.hora)
    log("\n   Ganadores de las 8:00 en vivo (puesto; días desde su última salida; ¿salió ayer? y a qué hora)")
    for i in np.nonzero((F >= "2026-09-14") & (hora == 0))[0]:
        g = n0 + i; v = seq[g]; prev = np.nonzero(seq[:g] == v)[0][-1]
        ayer = [8 + int(horaG[t]) for t in range(g - 14, g) if diaG[t] == diaG[g] - 1 and seq[t] == v]
        log(f"   {F[i]}  {LE.POS[v]:>2}  puesto {p0[i] + 1:2d}  hueco {diaG[g] - diaG[prev]} días  "
            f"ayer: {'sí a las ' + ', '.join(f'{x}:00' for x in ayer) if ayer else 'no'}")
    # 5. ¿Temporadas? acierto Top-15 de cada sorteo contra la tasa de esa misma hora en las 30 jornadas anteriores
    log("\n=== 5. ¿Van por temporadas? Top-15 según la tasa de la MISMA hora en los 30 días anteriores (2025-2026) ===")
    hit = (p0 < 15).astype(float)
    for etiqueta, horas in (("8:00", [0]), ("resto de horas", list(range(1, 12)))):
        alto, bajo = [], []
        for h in horas:
            idx = np.nonzero(hora == h)[0]
            for k, i in enumerate(idx):
                if F[i] < "2025-01-01" or k < 30:
                    continue
                (alto if hit[idx[k - 30:k]].mean() >= 0.55 else bajo).append(i)
        alto, bajo = np.array(alto), np.array(bajo)
        d = hit[alto].mean() - hit[bajo].mean()
        bb = B.boot_media(np.r_[dia[alto], dia[bajo] + 10 ** 6], np.r_[hit[alto] - hit[alto].mean(), hit[bajo] - hit[bajo].mean()], B=1)
        log(f"   {etiqueta:<15} tras 30 días buenos (≥ 55 %): {hit[alto].mean() * 100:5.1f} % (n={len(alto)})   "
            f"tras 30 días flojos: {hit[bajo].mean() * 100:5.1f} % (n={len(bajo)})   diferencia {d * 100:+.1f} pp")
    with open(os.path.join(AQUI, "brecha_2026_extra_salida.txt"), "w", encoding="utf-8") as fo:
        fo.write("\n".join(LINEAS) + "\n")


if __name__ == "__main__":
    main()
