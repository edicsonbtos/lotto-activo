# -*- coding: utf-8 -*-
"""La "brecha" del operador en 2026 (PREREGISTRO_brecha_2026.md).

Uso (desde la raíz): python herramientas/exploracion/brecha_2026.py
Necesita numpy, scipy y lightgbm. Reutiliza el historial y la caché de hora_8am_ciega.py (~70 s si no existen).
Salida: brecha_2026_salida.txt y brecha_2026.json.
"""
import csv, json, os, sys, time
from datetime import date, timedelta
from multiprocessing import Pool
import numpy as np
from scipy.optimize import minimize

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402
import hora_8am_ciega as H8  # noqa: E402

K = 38
SEMILLA, B_BOOT, N_SIM = 20261002, 10000, 2000
TRAMOS = {"2025": ("2025-01-01", "2025-12-19"), "2026-A": ("2025-12-19", "2026-06-01"),
          "2026-B": ("2026-06-01", "2026-09-30")}
F5 = np.array([2, 2, 2, 1, 1], float)                       # Top-5 escalonado (8 fichas)
F15 = np.array([3, 3, 3, 2, 2] + [1] * 10, float)           # Top-15 ponderado (23 fichas)
SALIDA = os.path.join(AQUI, "brecha_2026_salida.txt")
LINEAS = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LINEAS.append(s)


def num(n):
    """Índice de lotto_eval del animal cuyo número es n (0..36), o None."""
    return LE.IDX.get(str(n)) if 0 <= n <= 36 else None


# --------------------------------------------------------------------------- datos cruzados
def cargar_rd_lard():
    from rdint.datos import ANIMALES, sin_acentos
    RD, LARD = {}, {}
    for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv"), encoding="utf-8")):
        cod = ANIMALES.get(sin_acentos(r["animal"]))
        if cod is not None:
            RD[(r["fecha"], int(r["hora"][:2]) - 8)] = LE.IDX[cod]
    choques = 0
    for ruta in (os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"),
                 os.path.join(AQUI, "enjambre_2026-09-30", "reentreno", "oficial_extra.csv")):
        for r in csv.DictReader(open(ruta, encoding="utf-8")):
            if r["juego"] == "2":
                assert r["hora"].endswith(":30"), r
                k = (r["fecha"], int(r["hora"][:2]) - 8)
                choques += k in RD and RD[k] != LE.IDX[r["codigo"]]
                RD[k] = LE.IDX[r["codigo"]]
            elif r["juego"] == "3":
                LARD[(r["fecha"], int(r["hora"][:2]))] = LE.IDX[r["codigo"]]
    log(f"RD: {len(RD)} sorteos ({min(RD)[0]}..{max(RD)[0]}), {choques} discrepancias rdint_hist/API (gana la API); "
        f"LARD: {len(LARD)} ({min(LARD)[0]}..{max(LARD)[0]})")
    return RD, LARD


# --------------------------------------------------------------------------- batería
def bateria(D, RD, LARD, filas):
    """X[j, f, i] = True si el animal i está en el conjunto de la variable f antes del sorteo filas[j]."""
    seq = np.asarray(D.seq); hora = np.asarray(D.hora); dia = np.asarray(D.dia); F = D.fecha
    n = len(seq)
    por_dia = {}
    for t in range(n):
        por_dia.setdefault(dia[t], {})[int(hora[t])] = int(seq[t])
    nombres = []
    def nom(x):
        nombres.append(x); return len(nombres) - 1
    GB = [(1, 1), (2, 2), (3, 3), (4, 6), (7, 11), (12, 17), (18, 23), (24, 35), (36, 47), (48, 71), (72, 107),
          (108, 179), (180, 10 ** 9)]
    DB = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 6), (7, 9), (10, 14), (15, 10 ** 9)]
    iG = [nom(f"G hueco {a}-{b} sorteos" if a != b else f"G hueco {a} sorteo(s)") for a, b in GB]
    iD = [nom(f"D hueco {a}-{b} días" if a != b else f"D hueco {a} días") for a, b in DB]
    iC24 = [nom(f"C {k} veces en últimos 24") for k in ("0", "1", "2", "3+")]
    iC72 = [nom(f"C {k} veces en últimos 72") for k in ("0-1", "2", "3", "4", "5+")]
    iH = {(c, g): nom(f"H salió hoy {c} ({g})") for c in ("1 vez", "2+ veces") for g in ("8-11", "12-15", "16-19")}
    iY = {k: nom("Y " + k) for k in ("ayer misma hora", "ayer h±1", "ayer mañana 8-11", "ayer mediodía 12-15",
                                     "ayer tarde 16-19", "ayer 19:00", "ayer 2+ veces", "anteayer misma hora",
                                     "hace 7 días misma hora", "misma hora en los últimos 7 días")}
    iS = {k: nom("S " + k) for k in ("anterior ±1", "anterior ±2", "misma cifra final que el anterior",
                                     "cifras invertidas del anterior", "el de hace dos sorteos")}
    iR = {k: nom("R " + k) for k in ("RD (h-1):30", "RD (h-2):30", "RD (h-3):30", "RD hoy antes de h", "RD ayer",
                                     "RD (h-1):30 ±1", "misma cifra final que RD (h-1):30")}
    iL = {k: nom("L " + k) for k in ("LARD (h-1):00", "LARD hoy antes de h")}
    iF = {k: nom("F " + k) for k in ("día del mes", "día+1", "día-1", "hora 12 h", "mes", "día de la semana")}
    iA = [nom(f"A animal {LE.POS[i]}") for i in range(K)]
    iM = {k: nom("M (8:00) " + k) for k in ("LA ayer 19:00", "RD ayer 19:30", "LARD ayer 20:00-21:00",
                                           "LA ayer (cualquiera)", "LA anteayer (cualquiera)")}
    NF = len(nombres)
    X = np.zeros((len(filas), NF, K), bool)
    # estado incremental
    last = np.full(K, -10 ** 9); lastd = np.full(K, -10 ** 9)
    hist = []
    j = 0; filas_set = {f: k for k, f in enumerate(filas)}
    def fecha_menos(f, d):
        return (date.fromisoformat(f) - timedelta(days=d)).isoformat()
    for t in range(n):
        if t in filas_set:
            j = filas_set[t]; x = X[j]; h = int(hora[t]); dd = dia[t]; f = F[t]
            g = t - last; gd = dd - lastd
            for k, (a, b) in enumerate(GB):
                x[iG[k]] = (g >= a) & (g <= b)
            for k, (a, b) in enumerate(DB):
                x[iD[k]] = (gd >= a) & (gd <= b)
            c24 = np.bincount(seq[max(0, t - 24):t], minlength=K); c72 = np.bincount(seq[max(0, t - 72):t], minlength=K)
            x[iC24[0]] = c24 == 0; x[iC24[1]] = c24 == 1; x[iC24[2]] = c24 == 2; x[iC24[3]] = c24 >= 3
            x[iC72[0]] = c72 <= 1; x[iC72[1]] = c72 == 2; x[iC72[2]] = c72 == 3; x[iC72[3]] = c72 == 4; x[iC72[4]] = c72 >= 5
            hoy = por_dia.get(dd, {}); hoyc = np.bincount([v for hh, v in hoy.items() if hh < h], minlength=K)
            gr = "8-11" if h <= 3 else ("12-15" if h <= 7 else "16-19")
            x[iH[("1 vez", gr)]] = hoyc == 1; x[iH[("2+ veces", gr)]] = hoyc >= 2
            ay = por_dia.get(dd - 1, {}); an = por_dia.get(dd - 2, {}); s7 = por_dia.get(dd - 7, {})
            def pon(idx, vals):
                for v in vals:
                    if v is not None:
                        x[idx, v] = True
            pon(iY["ayer misma hora"], [ay.get(h)]); pon(iY["ayer h±1"], [ay.get(h - 1), ay.get(h + 1)])
            pon(iY["ayer mañana 8-11"], [ay.get(k) for k in range(0, 4)])
            pon(iY["ayer mediodía 12-15"], [ay.get(k) for k in range(4, 8)])
            pon(iY["ayer tarde 16-19"], [ay.get(k) for k in range(8, 12)]); pon(iY["ayer 19:00"], [ay.get(11)])
            ayc = np.bincount(list(ay.values()), minlength=K) if ay else np.zeros(K, int)
            x[iY["ayer 2+ veces"]] = ayc >= 2
            pon(iY["anteayer misma hora"], [an.get(h)]); pon(iY["hace 7 días misma hora"], [s7.get(h)])
            pon(iY["misma hora en los últimos 7 días"], [por_dia.get(dd - k, {}).get(h) for k in range(1, 8)])
            p1 = int(seq[t - 1]); p2 = int(seq[t - 2]); n1 = int(LE.POS[p1])
            pon(iS["anterior ±1"], [num(n1 - 1), num(n1 + 1)]); pon(iS["anterior ±2"], [num(n1 - 2), num(n1 + 2)])
            pon(iS["misma cifra final que el anterior"], [num(m) for m in range(37) if m % 10 == n1 % 10 and m != n1])
            if n1 >= 10 and n1 % 10 != n1 // 10:
                pon(iS["cifras invertidas del anterior"], [num(int(str(n1)[::-1]))])
            pon(iS["el de hace dos sorteos"], [p2])
            r1 = RD.get((f, h - 1)) if h >= 1 else RD.get((fecha_menos(f, 1), 11))
            pon(iR["RD (h-1):30"], [r1]); pon(iR["RD (h-2):30"], [RD.get((f, h - 2)) if h >= 2 else None])
            pon(iR["RD (h-3):30"], [RD.get((f, h - 3)) if h >= 3 else None])
            pon(iR["RD hoy antes de h"], [RD.get((f, k)) for k in range(h)])
            pon(iR["RD ayer"], [RD.get((fecha_menos(f, 1), k)) for k in range(12)])
            if r1 is not None:
                m1 = int(LE.POS[r1])
                pon(iR["RD (h-1):30 ±1"], [num(m1 - 1), num(m1 + 1)])
                pon(iR["misma cifra final que RD (h-1):30"], [num(m) for m in range(37) if m % 10 == m1 % 10 and m != m1])
            hc = 8 + h
            pon(iL["LARD (h-1):00"], [LARD.get((f, hc - 1)) if hc - 1 >= 8 else None])
            pon(iL["LARD hoy antes de h"], [LARD.get((f, k)) for k in range(8, hc)])
            dm = int(f[8:]); mes = int(f[5:7]); dw = date.fromisoformat(f).isoweekday()
            pon(iF["día del mes"], [num(dm)]); pon(iF["día+1"], [num(dm + 1)]); pon(iF["día-1"], [num(dm - 1)])
            pon(iF["hora 12 h"], [num(hc if hc <= 12 else hc - 12)]); pon(iF["mes"], [num(mes)])
            pon(iF["día de la semana"], [num(dw)])
            for i in range(K):
                x[iA[i], i] = True
            if h == 0:
                ya = fecha_menos(f, 1)
                pon(iM["LA ayer 19:00"], [ay.get(11)]); pon(iM["RD ayer 19:30"], [RD.get((ya, 11))])
                pon(iM["LARD ayer 20:00-21:00"], [LARD.get((ya, 20)), LARD.get((ya, 21))])
                pon(iM["LA ayer (cualquiera)"], list(ay.values())); pon(iM["LA anteayer (cualquiera)"], list(an.values()))
        v = int(seq[t]); last[v] = t; lastd[v] = dia[t]
    return X, nombres


# --------------------------------------------------------------------------- estadística
def oe(X, P, y):
    """O, E y varianza por variable."""
    q = np.einsum("tfi,ti->tf", X, P)
    O = X[np.arange(len(y)), :, y].sum(0).astype(float)
    return O, q.sum(0), (q * (1 - q)).sum(0), q


def _sim(args):
    semilla, nsim, X, P, E, V = args
    rng = np.random.default_rng(semilla); c = P.cumsum(1); out = np.empty(nsim)
    for s in range(nsim):
        ys = np.minimum((rng.random(len(P))[:, None] > c).sum(1), K - 1)
        O = X[np.arange(len(ys)), :, ys].sum(0)
        z = np.where(V > 0, (O - E) / np.sqrt(np.maximum(V, 1e-12)), 0)
        out[s] = np.abs(z).max()
    return out


def boot_ratio(dias, Ot, Et, B=B_BOOT, semilla=SEMILLA):
    """Bootstrap por jornada de sum(O)/sum(E). Ot, Et: (n,) por sorteo."""
    u, inv = np.unique(dias, return_inverse=True)
    so = np.bincount(inv, Ot, len(u)); se = np.bincount(inv, Et, len(u))
    idx = np.random.default_rng(semilla).integers(0, len(u), (B, len(u)))
    return so[idx].sum(1) / se[idx].sum(1)


def boot_media(dias, v, B=B_BOOT, semilla=SEMILLA):
    u, inv = np.unique(dias, return_inverse=True)
    s = np.bincount(inv, v, len(u)); c = np.bincount(inv, minlength=len(u))
    idx = np.random.default_rng(semilla).integers(0, len(u), (B, len(u)))
    return s[idx].sum(1) / c[idx].sum(1)


def ajustar(Xs, P, y, lam=1.0):
    """Logit condicional con offset log P: P' ∝ P·exp(X·β). Xs: (n, f, K)."""
    L0 = np.log(P); Xf = Xs.astype(float)
    def f(b):
        z = L0 + np.einsum("tfi,f->ti", Xf, b); zm = z.max(1, keepdims=True)
        e = np.exp(z - zm); S = e.sum(1); p = e / S[:, None]
        nll = -(z[np.arange(len(y)), y] - zm[:, 0] - np.log(S)).sum() + 0.5 * lam * (b ** 2).sum()
        g = -(Xf[np.arange(len(y)), :, y] - np.einsum("ti,tfi->tf", p, Xf)).sum(0) + lam * b
        return nll, g
    r = minimize(f, np.zeros(Xs.shape[1]), jac=True, method="L-BFGS-B")
    return r.x


def aplicar(Xs, P, b):
    z = np.log(P) + np.einsum("tfi,f->ti", Xs.astype(float), b); z -= z.max(1, keepdims=True)
    p = np.exp(z); return p / p.sum(1, keepdims=True)


def medir(Pm, y, dias, Pref=None, nombre=""):
    o = LE.rankings(Pm); pos = np.argmax(o == y[:, None], 1)
    mb = 1000 * np.log2(Pm[np.arange(len(y)), y] * K)
    g5 = np.where(pos < 5, 30 * F5[np.minimum(pos, 4)], 0) - F5.sum()
    g15 = np.where(pos < 15, 30 * F15[np.minimum(pos, 14)], 0) - F15.sum()
    r = dict(mbits=float(mb.mean()), top5=float((pos < 5).mean()), top15=float((pos < 15).mean()),
             ret5=float(g5.sum() / (F5.sum() * len(y))), ret15=float(g15.sum() / (F15.sum() * len(y))))
    if Pref is not None:
        mr = 1000 * np.log2(Pref[np.arange(len(y)), y] * K)
        bb = boot_media(dias, mb - mr)
        r["dmbits"] = float((mb - mr).mean()); r["dmbits_ic95"] = [float(np.percentile(bb, 2.5)), float(np.percentile(bb, 97.5))]
        o2 = LE.rankings(Pref); p2 = np.argmax(o2 == y[:, None], 1)
        bt = boot_media(dias, (pos < 15).astype(float) - (p2 < 15))
        r["dtop15"] = float(((pos < 15).astype(float) - (p2 < 15)).mean())
        r["dtop15_ic95"] = [float(np.percentile(bt, 2.5)), float(np.percentile(bt, 97.5))]
    log(f"  {nombre:<34} mbits {r['mbits']:+6.1f}  Top-5 {r['top5'] * 100:5.2f} %  Top-15 {r['top15'] * 100:5.2f} %  "
        f"ret Top-5 esc {r['ret5'] * 100:+5.1f} %  ret Top-15 pond {r['ret15'] * 100:+5.1f} %"
        + (f"   Δmbits {r['dmbits']:+5.1f} [{r['dmbits_ic95'][0]:+.1f}; {r['dmbits_ic95'][1]:+.1f}]  "
           f"ΔTop-15 {r['dtop15'] * 100:+.2f} pp [{r['dtop15_ic95'][0] * 100:+.2f}; {r['dtop15_ic95'][1] * 100:+.2f}]"
           if Pref is not None else ""))
    return r


# --------------------------------------------------------------------------- principal
def main():
    t0 = time.time()
    H8.armar_historial()
    D, Pall = H8.walk_forward()
    RD, LARD = cargar_rd_lard()
    F = np.array(D.fecha); n0 = LE.W
    sel = {k: np.nonzero((F[n0:] >= a) & (F[n0:] < b))[0] for k, (a, b) in TRAMOS.items()}
    filas = np.concatenate([sel[k] for k in TRAMOS]) + n0
    X, nombres = bateria(D, RD, LARD, list(filas))
    NF = len(nombres)
    pos_en_X = {f: k for k, f in enumerate(filas)}
    def tramo(k):
        g = sel[k] + n0; jj = np.array([pos_en_X[f] for f in g])
        P = Pall[sel[k]]; P = P / P.sum(1, keepdims=True)
        return X[jj], P, np.asarray(D.seq)[g], np.asarray(D.dia)[g], np.asarray(D.hora)[g]
    T = {k: tramo(k) for k in TRAMOS}
    for k, v in T.items():
        log(f"{k}: {len(v[2])} sorteos, {F[sel[k][0] + n0]}..{F[sel[k][-1] + n0]}")
    log(f"Batería: {NF} variables ({time.time() - t0:.0f} s)")

    res = {}
    for k in TRAMOS:
        Xk, Pk, yk, dk, hk = T[k]
        O, E, V, q = oe(Xk, Pk, yk)
        U = np.full_like(Pk, 1 / K); Ou, Eu, _, _ = oe(Xk, U, yk)
        res[k] = dict(O=O, E=E, V=V, z=np.where(V > 0, (O - E) / np.sqrt(np.maximum(V, 1e-12)), 0), Eu=Eu)

    # ---- nulo del máximo |z| en 2026-A (2.000 simulaciones en 4 núcleos)
    XA, PA, yA, dA, hA = T["2026-A"]
    with Pool(4) as pool:
        partes = pool.map(_sim, [(SEMILLA + s, N_SIM // 4, XA, PA, res["2026-A"]["E"], res["2026-A"]["V"])
                                 for s in range(4)])
    nulo = np.concatenate(partes); umbral = float(np.percentile(nulo, 95))
    log(f"Nulo (2.000 simulaciones con el ganador sorteado del motor): percentil 95 del máximo |z| = {umbral:.2f} "
        f"({time.time() - t0:.0f} s)")

    # ---- tabla completa: 2025 vs 2026-A vs 2026-B, contra el motor y contra el azar
    log("\n=== Perfil completo (O/E contra el MOTOR; entre paréntesis O/E contra el AZAR) ===")
    log(f"{'variable':<44} {'2025':>14} {'2026-A':>20} {'2026-B':>14}")
    for f in range(NF):
        a, b, c = res["2025"], res["2026-A"], res["2026-B"]
        if b["E"][f] < 1 and c["E"][f] < 1:
            continue
        cel = lambda r: f"{r['O'][f] / r['E'][f]:4.2f} ({r['O'][f] / r['Eu'][f]:4.2f})" if r["E"][f] > 0 else "   -   "
        log(f"{nombres[f]:<44} {cel(a):>14} {cel(b):>14} z{b['z'][f]:+5.1f} {cel(c):>14}")

    # ---- descubrir
    zA = res["2026-A"]["z"]; oeA = res["2026-A"]["O"] / np.maximum(res["2026-A"]["E"], 1e-12)
    cand = [f for f in range(NF) if abs(zA[f]) > umbral and abs(oeA[f] - 1) >= 0.10]
    log(f"\n=== Descubrir (2026-A): {len(cand)} candidatas con |z| > {umbral:.2f} y |O/E−1| ≥ 0,10 ===")
    for f in cand:
        log(f"  {nombres[f]:<44} O/E {oeA[f]:.2f}  z {zA[f]:+.2f}")

    # ---- confirmar (2026-B), una vez
    XB, PB, yB, dB, hB = T["2026-B"]
    confirmadas = []
    if cand:
        log(f"\n=== Confirmar (2026-B), una vez: p unilateral < 0,05/{len(cand)} = {0.05 / len(cand):.4f} ===")
        qB = np.einsum("tfi,ti->tf", XB[:, cand], PB)
        OB = XB[np.arange(len(yB)), :, yB][:, cand].astype(float)
        for k, f in enumerate(cand):
            bb = boot_ratio(dB, OB[:, k], qB[:, k])
            r = OB[:, k].sum() / qB[:, k].sum()
            p = float(np.mean(bb >= 1)) if oeA[f] < 1 else float(np.mean(bb <= 1))
            ok = (r < 1) == (oeA[f] < 1) and p < 0.05 / len(cand)
            confirmadas += [f] if ok else []
            log(f"  {nombres[f]:<44} 2026-A {oeA[f]:.2f} → 2026-B {r:.2f} [IC95 {np.percentile(bb, 2.5):.2f}; "
                f"{np.percentile(bb, 97.5):.2f}] p={p:.4f}  => {'CONFIRMADA' if ok else 'no'}")

    # ---- ¿sirve para jugar? corrección ajustada en 2026-A, medida en 2026-B
    log("\n=== Corrección P' ∝ P·exp(Σβx), β ajustados SOLO en 2026-A; medida en 2026-B ===")
    base = medir(PB, yB, dB, None, "Ensamble (producción)")
    salida = dict(umbral=umbral, nombres=nombres, candidatas=[nombres[f] for f in cand],
                  confirmadas=[nombres[f] for f in confirmadas], base_2026B=base,
                  oe={k: (res[k]["O"] / np.maximum(res[k]["E"], 1e-12)).round(3).tolist() for k in TRAMOS},
                  z={k: res[k]["z"].round(2).tolist() for k in TRAMOS})
    for etiqueta, conj in (("candidatas", cand), ("confirmadas", confirmadas)):
        if not conj:
            continue
        b = ajustar(XA[:, conj], PA, yA)
        log(f"  β ({etiqueta}): " + ", ".join(f"{nombres[f]} {v:+.2f}" for f, v in zip(conj, b)))
        salida["correccion_" + etiqueta] = medir(aplicar(XB[:, conj], PB, b), yB, dB, PB, f"Ensamble + {etiqueta}")
    # todas las variables (exploratorio, L2 = 1)
    nz = [f for f in range(NF) if res["2026-A"]["E"][f] >= 5 and not nombres[f].startswith("A ")]
    b = ajustar(XA[:, nz], PA, yA)
    salida["correccion_todas"] = medir(aplicar(XB[:, nz], PB, b), yB, dB, PB, f"Ensamble + todas ({len(nz)}, expl.)")

    # ---- fuerza bruta: LightGBM sobre (sorteo, animal) con offset del ensamble
    try:
        import lightgbm as lgb
        def tabla(Xk, Pk, hk):
            n = len(Pk)
            Z = Xk.transpose(0, 2, 1).reshape(n * K, -1).astype(np.float32)
            extra = np.c_[np.log(Pk).reshape(-1), np.repeat(hk, K), np.tile(np.arange(K), n)].astype(np.float32)
            return np.c_[Z, extra]
        ZA = tabla(XA, PA, hA); ZB = tabla(XB, PB, hB)
        lab = np.zeros((len(yA), K)); lab[np.arange(len(yA)), yA] = 1; lab = lab.reshape(-1)
        off = lambda Pk: np.log(Pk / (1 - Pk)).reshape(-1)
        corte = int(len(yA) * 0.8) * K
        dtr = lgb.Dataset(ZA[:corte], lab[:corte], init_score=off(PA)[:corte])
        dva = lgb.Dataset(ZA[corte:], lab[corte:], init_score=off(PA)[corte:], reference=dtr)
        prm = dict(objective="binary", learning_rate=0.02, num_leaves=15, min_data_in_leaf=200, feature_fraction=0.7,
                   bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=4, seed=SEMILLA)
        m = lgb.train(prm, dtr, 2000, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])
        it = m.best_iteration or 1
        m = lgb.train(prm, lgb.Dataset(ZA, lab, init_score=off(PA)), it)
        s = m.predict(ZB, raw_score=True).reshape(-1, K) + np.log(PB / (1 - PB))
        PL = np.exp(s - s.max(1, keepdims=True)); PL /= PL.sum(1, keepdims=True)
        log(f"  LightGBM: {it} árboles (parada temprana dentro de 2026-A)")
        salida["lightgbm"] = medir(PL, yB, dB, PB, "Ensamble + LightGBM (todas, expl.)")
    except ImportError:
        log("  LightGBM no instalado: se omite.")

    log(f"\nTiempo total: {time.time() - t0:.0f} s")
    with open(SALIDA, "w", encoding="utf-8") as fo:
        fo.write("\n".join(LINEAS) + "\n")
    with open(os.path.join(AQUI, "brecha_2026.json"), "w", encoding="utf-8") as fo:
        json.dump(salida, fo, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
