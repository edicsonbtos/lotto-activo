# -*- coding: utf-8 -*-
"""OPERACION TURING - ENJAMBRE A: barrido masivo de hipotesis predictoras.

Objetivo: certificar si queda ALGUNA senal residual explotable sobre el
ensamble_v2 en el tramo de DESARROLLO [W, CORTE_FIJO), o cerrar el espacio.

Protocolo (identico en espiritu a herramientas/lotto_eval.py y a la fase
exploratoria 2026-09-15, pero a escala N>=300):

  1. Se congela UNA vez la salida walk-forward de ensamble_v2 (log-prob por
     sorteo y animal) sobre desarrollo. Eso es la LINEA BASE. (~5 min, cache.)
  2. Cada hipotesis se materializa como una feature causal: un log-rate
     empirico estimado SOLO con el pasado (cuentas acumuladas estrictas < t).
     Para animal i en el sorteo t:  F[t,i] = log rate( bucket(i,t) ),
     rate(g) = (wins<t[g] + a*p0) / (expo<t[g] + a),  p0 = 1/38.
     Se centra por fila (tilt puro). Ninguna feature ve el futuro: las cuentas
     usan cumsum desplazado un paso (exclusivo de t).
  3. Se anhade la feature al logit congelado con UN peso escalar w ajustado por
     maxima verosimilitud (sonda directa, la misma tecnica ya validada). El
     aporte = 1000 * media_fila( log2 p_con[y] - log2 p_base[y] )  [mbits].
  4. Compuerta de supervivencia: OOF por cuartos. Para el cuarto q, w se ajusta
     con los otros 3 cuartos y se puntua q. SENAL exige aporte OOF > 0 en 4/4
     cuartos Y q(Benjamini-Hochberg) < 0.05 sobre p-valor de bloque-dia.
  5. Referencia de relevancia: el ensamble entero saca +120 mbits sobre
     uniforme; el oraculo walk-forward de la politica medible es 10.38% Top-3,
     POR DEBAJO del ensamble (12.89%). Por construccion ninguna feature residual
     puede acercarse a +120 mbits: eso NO es el umbral de la compuerta, es la
     vara de "vale la pena integrarlo". La compuerta real es la de 4/4 + BH.

Reproduccion:
  $env:PYTHONIOENCODING="utf-8"
  cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo
  python investigacion\\2026-09-18\\a_estadistica\\barrido.py            # completo
  python investigacion\\2026-09-18\\a_estadistica\\barrido.py --smoke    # rapido (mecanica)
  python investigacion\\2026-09-18\\a_estadistica\\barrido.py --rebuild  # recalcula la base

NO toca el tramo de prueba (>= CORTE_FIJO): todo se trunca a datos.prefijo(CORTE).
NO toca produccion, pesos, modelos ni registros. Solo lee.
"""
import argparse
import itertools
import json
import os
import sys
import time

import numpy as np

SEED = 20260918
np.random.seed(SEED)

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
HERR = os.path.join(RAIZ, "herramientas")
sys.path.insert(0, HERR)
import lotto_eval as LE  # noqa: E402

CACHE = os.path.join(AQUI, "baseline_dev.npz")
K = 38
P0 = 1.0 / K


# --------------------------------------------------------------------------- #
#  1. Linea base congelada
# --------------------------------------------------------------------------- #
def construir_base(smoke=False, rebuild=False):
    datos = LE.cargar()
    W, CORTE = LE.W, LE.CORTE_FIJO
    assert len(datos) >= CORTE, "faltan datos de desarrollo"
    dev = datos.prefijo(CORTE)                      # <-- el futuro (>=CORTE) NO entra
    desde = (CORTE - 400) if smoke else W
    tag = "smoke" if smoke else "full"
    cache = CACHE.replace(".npz", "_%s.npz" % tag)

    if os.path.exists(cache) and not rebuild:
        z = np.load(cache, allow_pickle=True)
        return z, datos, W, CORTE, desde, cache

    t0 = time.time()
    modelo = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
    out = LE.normalizar(modelo.predecir(dev, desde))          # (CORTE-desde, 38)
    Lb = np.log(np.clip(out, 1e-9, None))
    Lb -= Lb.mean(1, keepdims=True)
    y = np.asarray(dev.seq)[desde:CORTE]                       # ganadores dev
    np.savez(cache,
             Lb=Lb, y=y,
             seq=np.asarray(dev.seq), hora=np.asarray(dev.hora),
             dow=np.asarray(dev.dow), dia=np.asarray(dev.dia),
             desde=desde, W=W, CORTE=CORTE,
             segs=time.time() - t0)
    z = np.load(cache, allow_pickle=True)
    return z, datos, W, CORTE, desde, cache


# --------------------------------------------------------------------------- #
#  2. Covariables causales (buckets por (t, animal), solo pasado)
# --------------------------------------------------------------------------- #
def covariables(seq, hora, dow, dia):
    """Devuelve dict nombre -> matriz de buckets (T, 38) int >=0, causal."""
    T = len(seq)
    idx = np.arange(T)
    cov = {}

    # --- gap exacto por animal (t - ultima aparicion < t); 9999 si nunca ---
    gap = np.full((T, K), 9999, dtype=np.int64)
    last = np.full(K, -1, dtype=np.int64)
    g2 = np.full((T, K), 9999, dtype=np.int64)       # penultimo hueco
    prev_last = np.full(K, -1, dtype=np.int64)
    vhoy = np.zeros((T, K), dtype=np.int64)          # veces hoy antes de t
    cont_hoy = np.zeros(K, dtype=np.int64)
    dia_actual = -1
    for t in range(T):
        if dia[t] != dia_actual:
            dia_actual = dia[t]
            cont_hoy[:] = 0
        m = last >= 0
        gap[t, m] = t - last[m]
        m2 = prev_last >= 0
        g2[t, m2] = last[m2] - prev_last[m2]
        vhoy[t] = cont_hoy
        w = seq[t]
        prev_last[w] = last[w]
        last[w] = t
        cont_hoy[w] += 1
    cov["gap_exact"] = np.clip(gap, 0, 60)                        # 0..60
    cov["gap_bin"] = np.digitize(gap, [2, 3, 4, 6, 9, 13, 21, 38, 61, 110])
    cov["g2_bin"] = np.digitize(g2, [2, 3, 4, 6, 9, 13, 21, 38, 61, 110])
    cov["vhoy"] = np.clip(vhoy, 0, 2)                             # 0,1,2+
    cov["salio_hoy"] = (vhoy > 0).astype(np.int64)

    # --- k / hora / dow (dependen solo de t, se difunden a los 38) ---
    kcol = np.clip(hora, 0, 11)
    cov["k"] = np.repeat(kcol[:, None], K, axis=1)
    cov["dow"] = np.repeat(dow[:, None].astype(np.int64), K, axis=1)
    cov["k_borde"] = np.repeat(np.where(kcol == 0, 0, np.where(kcol >= 10, 2, 1))[:, None], K, axis=1)

    # --- dias desde ultima salida (dd) ---
    diar = np.asarray(dia)
    dd = np.full((T, K), 9999, dtype=np.int64)
    last_dia = np.full(K, -1, dtype=np.int64)
    lastd2 = np.full(K, -1, dtype=np.int64)
    for t in range(T):
        m = last_dia >= 0
        dd[t, m] = diar[t] - last_dia[m]
        w = seq[t]
        last_dia[w] = diar[t]
    cov["dd_bin"] = np.clip(dd, 0, 6)                             # 0..6

    # --- gano el sorteo anterior / vecino de tablero gano el anterior ---
    prev_win = np.full((T, K), 0, dtype=np.int64)
    if T > 1:
        prev = seq[:-1]
        prev_win[1:][np.arange(T - 1), prev] = 1
    cov["win_last"] = prev_win
    neigh = np.zeros((T, K), dtype=np.int64)
    if T > 1:
        for t in range(1, T):
            w = seq[t - 1]
            neigh[t, (w - 1) % K] = 1
            neigh[t, (w + 1) % K] = 1
    cov["neigh_last"] = neigh

    # --- conteos en ventana movil (causal, < t) ---
    for Wn in (12, 24, 38, 76, 150, 300):
        cnt = np.zeros((T, K), dtype=np.int64)
        run = np.zeros(K, dtype=np.int64)
        from collections import deque
        dq = deque()
        for t in range(T):
            cnt[t] = run
            dq.append(seq[t]); run[seq[t]] += 1
            if len(dq) > Wn:
                run[dq.popleft()] -= 1
        cov["cnt%d_bin" % Wn] = np.clip(cnt, 0, 4 if Wn <= 38 else 8)

    # --- racha de fallos global reciente (regimen) difundida a 38 ---
    # tasa de repeticion s(t)==s(t-1) en ventana 100 (changepoint de regimen)
    rep = np.zeros(T, dtype=np.int64)
    rep[1:] = (seq[1:] == seq[:-1]).astype(np.int64)
    reprate = np.zeros(T)
    from collections import deque
    dq = deque(); s = 0
    for t in range(T):
        reprate[t] = s / max(1, len(dq))
        dq.append(rep[t]); s += rep[t]
        if len(dq) > 100:
            s -= dq.popleft()
    cov["regimen_rep"] = np.repeat(np.digitize(reprate, [0.005, 0.015, 0.03])[:, None], K, axis=1)

    return cov


# --------------------------------------------------------------------------- #
#  3. Feature causal (log-rate empirico) a partir de un bucket
# --------------------------------------------------------------------------- #
def lograte(B, seq, a):
    """B: (T,38) buckets; devuelve F (T,38) = log rate causal, centrado por fila."""
    T = len(seq)
    G = int(B.max()) + 1
    rows = np.arange(T)
    Erow = np.zeros((T, G))
    for col in range(K):
        np.add.at(Erow, (rows, B[:, col]), 1.0)
    wb = B[rows, seq]                          # bucket del ganador
    Wrow = np.zeros((T, G))
    np.add.at(Wrow, (rows, wb), 1.0)
    Ecum = np.cumsum(Erow, axis=0); Ecum = np.vstack([np.zeros((1, G)), Ecum[:-1]])
    Wcum = np.cumsum(Wrow, axis=0); Wcum = np.vstack([np.zeros((1, G)), Wcum[:-1]])
    rate = (Wcum + a * P0) / (Ecum + a)
    F = np.log(rate)[rows[:, None], B]         # (T,38)
    F -= F.mean(1, keepdims=True)
    return F


def catalogo(cov):
    """Genera >=300 hipotesis: singles + pares de interaccion x suavizados."""
    singles = list(cov.keys())
    # base curada para interacciones (evita explosion inutil)
    # gap_exact (61 buckets) queda SOLO como single: en interacciones dispara el
    # espacio de buckets. Los pares usan binnings compactos.
    base_int = ["gap_bin", "g2_bin", "vhoy", "salio_hoy", "k", "dow",
                "k_borde", "dd_bin", "win_last", "neigh_last",
                "cnt12_bin", "cnt24_bin", "cnt38_bin", "cnt76_bin",
                "cnt150_bin", "cnt300_bin", "regimen_rep"]
    specs = []
    for s in singles:
        specs.append(("S", (s,)))
    for x, y in itertools.combinations(base_int, 2):
        specs.append(("I", (x, y)))
    hip = []
    for a in (1.0, 8.0):
        for kind, names in specs:
            hip.append((kind, names, a))
    return hip


def matriz(cov, names):
    if len(names) == 1:
        return cov[names[0]].copy()
    A = cov[names[0]]; B = cov[names[1]]
    gb = int(B.max()) + 1
    return A * gb + B


# --------------------------------------------------------------------------- #
#  4. Sonda: ajuste de peso escalar y aporte en mbits
# --------------------------------------------------------------------------- #
def ajusta_w(Lb, F, y, filas):
    from scipy.optimize import minimize_scalar
    L = Lb[filas]; Fc = F[filas]; yy = y[filas]
    r = np.arange(len(filas))

    def nll(w):
        z = L + w * Fc
        z = z - z.max(1, keepdims=True)
        e = np.exp(z); S = e.sum(1)
        return float(-(z[r, yy] - np.log(S)).sum())

    res = minimize_scalar(nll, bounds=(-3.0, 4.0), method="bounded",
                          options={"xatol": 1e-4})
    return res.x


def aporte(Lb, F, y, w, filas):
    """mbits medios (con2 - base) sobre 'filas', usando peso w."""
    r = np.arange(len(filas))
    yy = y[filas]
    Lb2 = Lb[filas]
    pb = np.exp(Lb2 - Lb2.max(1, keepdims=True)); pb /= pb.sum(1, keepdims=True)
    z = Lb2 + w * F[filas]; z -= z.max(1, keepdims=True)
    pc = np.exp(z); pc /= pc.sum(1, keepdims=True)
    d = (np.log2(pc[r, yy]) - np.log2(pb[r, yy])) * 1000.0
    return d                                        # aporte por sorteo (mbits)


# --------------------------------------------------------------------------- #
#  5. Barrido
# --------------------------------------------------------------------------- #
def bh(pvals):
    p = np.asarray(pvals); n = len(p)
    order = np.argsort(p)
    q = np.empty(n)
    prev = 1.0
    for rank in range(n - 1, -1, -1):
        i = order[rank]
        val = p[i] * n / (rank + 1)
        prev = min(prev, val)
        q[i] = prev
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()

    z, datos, W, CORTE, desde, cache = construir_base(args.smoke, args.rebuild)
    Lb = z["Lb"]; y = z["y"]
    seq = z["seq"]; hora = z["hora"]; dow = z["dow"]; dia = z["dia"]
    ndev = Lb.shape[0]
    off = desde                                   # fila global t = off + j
    print("base: %s  dev_rows=%d  (t in [%d,%d))  base_secs=%.1f"
          % (os.path.basename(cache), ndev, off, CORTE, float(z["segs"])))

    cov = covariables(seq, hora, dow, dia)        # sobre [0, CORTE)
    # recortar covariables a las filas dev y alinear con Lb
    cov_dev = {k: v[off:CORTE] for k, v in cov.items()}
    ydev = y                                       # ya es seq[off:CORTE]

    dia_dev = np.asarray(dia)[off:CORTE]
    q_edges = np.linspace(0, ndev, 5).astype(int)
    cuartos = [np.arange(q_edges[i], q_edges[i + 1]) for i in range(4)]
    todas = np.arange(ndev)

    hip = catalogo(cov_dev)
    print("hipotesis: %d" % len(hip))

    rng = np.random.default_rng(SEED)
    dias_unicos = np.unique(dia_dev)
    filas_por_dia = {d: np.where(dia_dev == d)[0] for d in dias_unicos}

    filas_out = []
    t0 = time.time()
    for n, (kind, names, a) in enumerate(hip):
        B = matriz(cov_dev, names)
        # el log-rate se estima sobre TODA la historia; aqui B ya es dev-slice,
        # pero las cuentas causales deben incluir el calentamiento -> reconstruir
        # sobre [0,CORTE) y recortar:
        Bfull = matriz(cov, names)
        Ffull = lograte(Bfull, seq, a)
        F = Ffull[off:CORTE]

        # ajuste full-dev + aporte
        w_full = ajusta_w(Lb, F, ydev, todas)
        d_full = aporte(Lb, F, ydev, w_full, todas)
        mbits = float(d_full.mean())

        # OOF por cuartos
        oof = []
        for q in range(4):
            tr = np.concatenate([cuartos[i] for i in range(4) if i != q])
            wq = ajusta_w(Lb, F, ydev, tr)
            dq = aporte(Lb, F, ydev, wq, cuartos[q])
            oof.append(float(dq.mean()))
        oof = np.array(oof)
        gate4 = bool(np.all(oof > 0))

        # p-valor por bloque-dia (bootstrap sobre d_full agrupado por dia)
        medias = np.array([d_full[filas_por_dia[d]].sum() for d in dias_unicos])
        nds = np.array([len(filas_por_dia[d]) for d in dias_unicos])
        obs = medias.sum() / nds.sum()
        boots = np.empty(args.boot)
        nD = len(dias_unicos)
        for b in range(args.boot):
            sel = rng.integers(0, nD, nD)
            boots[b] = medias[sel].sum() / nds[sel].sum()
        se = boots.std()
        ci = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))
        # p una cola H0: aporte<=0
        pval = float((boots <= 0).mean())
        pval = min(max(pval, 1.0 / args.boot), 1.0)

        filas_out.append(dict(
            id=n, tipo=kind, hip="*".join(names), a=a,
            mbits=mbits, w=float(w_full), se=float(se),
            ic_lo=ci[0], ic_hi=ci[1], oof=oof.tolist(),
            gate4=gate4, p=pval))
        if (n + 1) % 50 == 0:
            print("  %d/%d  (%.0fs)" % (n + 1, len(hip), time.time() - t0))

    ps = [r["p"] for r in filas_out]
    qs = bh(ps)
    for r, q in zip(filas_out, qs):
        r["q_bh"] = float(q)
        r["veredicto"] = "SENAL" if (r["gate4"] and q < 0.05 and r["mbits"] > 0) else "RUIDO"

    filas_out.sort(key=lambda r: -r["mbits"])
    tag = "smoke" if args.smoke else "full"
    out_json = os.path.join(AQUI, "barrido_%s.json" % tag)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(dict(seed=SEED, ndev=ndev, off=off, CORTE=int(CORTE),
                       n_hip=len(hip), tabla=filas_out), f, ensure_ascii=False, indent=1)

    # tabla markdown (top 30 + todas las SENAL)
    out_md = os.path.join(AQUI, "tabla_%s.md" % tag)
    señales = [r for r in filas_out if r["veredicto"] == "SENAL"]
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# ENJAMBRE A - barrido (%s)\n\n" % tag)
        f.write("dev_rows=%d, hipotesis=%d, seed=%d, corte=%d\n\n" % (ndev, len(hip), SEED, CORTE))
        f.write("SENALES (gate 4/4 + q_BH<0.05 + mbits>0): **%d**\n\n" % len(señales))
        f.write("| # | hipotesis | a | mbits | IC95 | OOF cuartos | 4/4 | q_BH | veredicto |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        mostrar = (señales + filas_out)[:max(30, len(señales))]
        vistos = set()
        for r in mostrar:
            if r["id"] in vistos:
                continue
            vistos.add(r["id"])
            f.write("| %d | %s | %g | %+.2f | [%+.2f,%+.2f] | %s | %s | %.3f | %s |\n" % (
                r["id"], r["hip"], r["a"], r["mbits"], r["ic_lo"], r["ic_hi"],
                "[" + ", ".join("%+.1f" % x for x in r["oof"]) + "]",
                "SI" if r["gate4"] else "no", r["q_bh"], r["veredicto"]))
        mejor_neg = max((r for r in filas_out if r["veredicto"] == "RUIDO"),
                        key=lambda r: r["mbits"], default=None)
        f.write("\n**Veredicto global**: ")
        if señales:
            f.write("RENDIJA(S) CANDIDATA(S): %d hipotesis sobreviven.\n" % len(señales))
        else:
            f.write("ESPACIO CERRADO. 0 hipotesis sobreviven la compuerta 4/4+BH.\n")
        if mejor_neg:
            f.write("Mejor negativo: `%s` (a=%g) %+.2f mbits IC95 [%+.2f,%+.2f], "
                    "OOF %s, q_BH=%.3f.\n" % (
                        mejor_neg["hip"], mejor_neg["a"], mejor_neg["mbits"],
                        mejor_neg["ic_lo"], mejor_neg["ic_hi"],
                        mejor_neg["oof"], mejor_neg["q_bh"]))
    print("OK -> %s  |  %s" % (out_json, out_md))
    print("SENALES:", len(señales), "/", len(hip))
    if señales:
        for r in señales[:10]:
            print("  SENAL:", r["hip"], "a=%g" % r["a"], "%+.2f mbits" % r["mbits"], "OOF", r["oof"])


if __name__ == "__main__":
    main()
