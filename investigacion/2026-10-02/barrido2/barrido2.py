# -*- coding: utf-8 -*-
"""Barrido 2 (PREREGISTRO_barrido2.md). Reusa la maquinaria de Turing (barrido.py). Solo desarrollo."""
import json, os, sys, time
from collections import deque
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
TUR = os.path.join(RAIZ, "investigacion", "2026-09-18", "a_estadistica")
sys.path.insert(0, TUR); sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import barrido as BA

SEED = 20261002
K = 38
ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
NUM = np.array([0, 0] + list(range(1, 37)))            # idx -> numero ("0" y "00" -> 0)
VERDE = np.arange(K) < 2
COLOR = np.array([2 if i < 2 else (0 if NUM[i] in ROJOS else 1) for i in range(K)])
PAR = np.where(VERDE, 2, NUM % 2)
QUAD = np.array([3 if i == 1 else (0 if NUM[i] <= 9 else 1 if NUM[i] <= 19 else 2 if NUM[i] <= 29 else 3) for i in range(K)])
MOD3 = np.where(VERDE, 3, NUM % 3)
MOD4 = np.where(VERDE, 4, NUM % 4)
DOC = np.array([3 if i < 2 else (0 if NUM[i] <= 12 else 1 if NUM[i] <= 24 else 2) for i in range(K)])


def circ(a, b):
    d = np.abs(a - b) % K
    return np.minimum(d, K - d)


def rasgos(seq, hora, dow, fechas):
    """Todo causal: en la fila t solo se usa seq[:t]. hora/dow/fecha de la fila t son conocidos de antemano."""
    T = len(seq)
    fe = [date.fromisoformat(f) for f in fechas]
    dom = np.array([d.day for d in fe]); mes = np.array([d.month for d in fe])
    ordn = np.array([d.toordinal() for d in fe])
    ant = np.concatenate([[0], seq[:-1]])
    ant2 = np.concatenate([[0, 0], seq[:-2]])
    ids = np.tile(np.arange(K), (T, 1))
    A = {}; C = {}
    A["quad"] = np.tile(QUAD, (T, 1)); A["par"] = np.tile(PAR, (T, 1)); A["color"] = np.tile(COLOR, (T, 1))
    A["mod3"] = np.tile(MOD3, (T, 1)); A["mod4"] = np.tile(MOD4, (T, 1)); A["doc"] = np.tile(DOC, (T, 1))
    A["mismo_quad_ult"] = (QUAD[None, :] == QUAD[ant][:, None]).astype(int)
    A["mismo_color_ult"] = (COLOR[None, :] == COLOR[ant][:, None]).astype(int)
    A["misma_par_ult"] = (PAR[None, :] == PAR[ant][:, None]).astype(int)
    A["lado_ult"] = np.sign(ids - ant[:, None]).astype(int) + 1
    bd = [1, 2, 4, 8, 14]
    A["dist_ult"] = np.digitize(circ(ids, ant[:, None]), bd)
    ayer = np.full(T, -1); mapa = {}
    for t in range(T):
        ayer[t] = mapa.get((ordn[t] - 1, hora[t]), -1)
        mapa[(ordn[t], hora[t])] = seq[t]
    d_ay = np.where(ayer[:, None] >= 0, circ(ids, ayer[:, None]), 38)
    A["dist_ayer_hora"] = np.digitize(d_ay, bd + [30])
    last_h = np.full((12, K), -10 ** 6)
    g_h = np.zeros((T, K), int); cnt7 = np.zeros((T, K), int); cnt30 = np.zeros((T, K), int)
    q7 = deque(); q30 = deque(); c7 = np.zeros(K, int); c30 = np.zeros(K, int)
    for t in range(T):
        while q7 and q7[0][0] < ordn[t] - 7: c7[q7.popleft()[1]] -= 1
        while q30 and q30[0][0] < ordn[t] - 30: c30[q30.popleft()[1]] -= 1
        cnt7[t] = c7; cnt30[t] = c30
        g_h[t] = np.minimum(ordn[t] - last_h[hora[t]], 400)
        last_h[hora[t], seq[t]] = ordn[t]
        q7.append((ordn[t], seq[t])); c7[seq[t]] += 1
        q30.append((ordn[t], seq[t])); c30[seq[t]] += 1
    A["gap_dias_hora"] = np.digitize(g_h, [2, 3, 4, 6, 9, 14, 22, 40, 100])
    A["cnt7d"] = np.clip(cnt7, 0, 4); A["cnt30d"] = np.clip(cnt30, 0, 6)
    h12 = ((hora + 8 - 1) % 12) + 1
    nm = NUM[None, :]; nv = np.tile(VERDE, (T, 1))
    z = np.zeros((T, K), int)
    z[(nm == dom[:, None]) & ~nv] = 1
    z[(nm == (dom + 1)[:, None]) & (z == 0) & ~nv] = 2
    z[(nm == (dom - 1)[:, None]) & (z == 0) & ~nv] = 3
    z[(nm == h12[:, None]) & (z == 0) & ~nv] = 4
    A["eq_fecha"] = z

    def b(v): return np.repeat(np.asarray(v)[:, None], K, axis=1).astype(int)
    C["hora"] = b(hora); C["dow"] = b(dow)
    C["trim"] = b((mes - 1) // 3); C["tramo_mes"] = b(np.digitize(dom, [11, 21]))
    C["color_ult"] = b(COLOR[ant]); C["quad_ult"] = b(QUAD[ant]); C["par_ult"] = b(PAR[ant])
    C["paso_ult"] = b(np.sign(ant - ant2) + 1)
    run = np.ones(T, int)
    for t in range(2, T):
        run[t] = run[t - 1] + 1 if COLOR[seq[t - 1]] == COLOR[seq[t - 2]] else 1
    C["racha_color"] = b(np.clip(run, 1, 4) - 1)
    lastp = np.full(K, -1); gprev = np.zeros(T, int)
    for t in range(1, T):
        w = seq[t - 1]
        gprev[t] = (t - 1 - lastp[w]) if lastp[w] >= 0 else 999
        lastp[w] = t - 1
    C["gap_prev_ult"] = b(np.digitize(gprev, [6, 20, 50]))
    return A, C


def main():
    z, datos, W, CORTE, desde, cache = BA.construir_base(False, False)
    Lb = z["Lb"]; ydev = z["y"]
    seq = np.asarray(z["seq"]); hora = np.asarray(z["hora"]); dow = np.asarray(z["dow"]); dia = np.asarray(z["dia"])
    fechas = datos.fecha[:CORTE]
    ndev = Lb.shape[0]; off = desde
    A, C = rasgos(seq, hora, dow, fechas)
    A["gap_bin"] = BA.covariables(seq, hora, dow, dia)["gap_bin"]
    triv = {("mismo_quad_ult", "quad_ult"), ("mismo_color_ult", "color_ult"), ("misma_par_ult", "par_ult")}
    specs = []
    for a in (1.0, 8.0):
        for k in A:
            if k != "gap_bin": specs.append(("S", (k,), a))
        for k in A:
            for c in C:
                if (k, c) not in triv: specs.append(("I", (k, c), a))
    print("hipotesis:", len(specs), flush=True)
    dia_dev = dia[off:CORTE]
    qe = np.linspace(0, ndev, 5).astype(int)
    cuartos = [np.arange(qe[i], qe[i + 1]) for i in range(4)]
    todas = np.arange(ndev)
    rng = np.random.default_rng(SEED)
    dias_u = np.unique(dia_dev)
    grupos = [np.where(dia_dev == d)[0] for d in dias_u]
    nds = np.array([len(g) for g in grupos]); nD = len(dias_u)
    boot = 2000; out = []; t0 = time.time()
    for n, (kind, names, a) in enumerate(specs):
        if len(names) == 1: B = A[names[0]]
        else:
            Bc = C[names[1]]; B = A[names[0]] * (int(Bc.max()) + 1) + Bc
        F = BA.lograte(B, seq, a)[off:CORTE]
        wf = BA.ajusta_w(Lb, F, ydev, todas); d = BA.aporte(Lb, F, ydev, wf, todas)
        oof = []
        for q in range(4):
            tr = np.concatenate([cuartos[i] for i in range(4) if i != q])
            oof.append(float(BA.aporte(Lb, F, ydev, BA.ajusta_w(Lb, F, ydev, tr), cuartos[q]).mean()))
        sums = np.array([d[g].sum() for g in grupos])
        s = rng.integers(0, nD, (boot, nD))
        bs = sums[s].sum(1) / nds[s].sum(1)
        p = min(max(float((bs <= 0).mean()), 1.0 / boot), 1.0)
        out.append(dict(id=n, tipo=kind, hip="*".join(names), a=a, mbits=float(d.mean()), w=float(wf),
                        ic_lo=float(np.percentile(bs, 2.5)), ic_hi=float(np.percentile(bs, 97.5)),
                        oof=oof, gate4=bool(all(x > 0 for x in oof)), p=p))
        if (n + 1) % 40 == 0: print(" ", n + 1, "/", len(specs), "%.0fs" % (time.time() - t0), flush=True)
    qs = BA.bh([r["p"] for r in out])
    for r, q in zip(out, qs):
        r["q_bh"] = float(q)
        r["veredicto"] = "SENAL" if (r["gate4"] and q < 0.05 and r["mbits"] > 0) else "RUIDO"
    out.sort(key=lambda r: -r["mbits"])
    json.dump(dict(seed=SEED, n_hip=len(specs), tabla=out), open(os.path.join(AQUI, "barrido2_full.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sen = [r for r in out if r["veredicto"] == "SENAL"]
    print("SENALES:", len(sen), "de", len(specs), "| min q_BH %.3f" % min(r["q_bh"] for r in out))
    print("con 4/4 OOF:", sum(r["gate4"] for r in out), "| p<0.05 sin corregir:", sum(r["p"] < 0.05 for r in out))
    for r in out[:15]:
        print("%-34s a=%g %+6.2f mbits IC[%+.2f,%+.2f] OOF%s q=%.3f %s" % (r["hip"], r["a"], r["mbits"], r["ic_lo"], r["ic_hi"], [round(x, 1) for x in r["oof"]], r["q_bh"], r["veredicto"]))
    print("control positivo eq_fecha:")
    for r in out:
        if r["hip"].startswith("eq_fecha"):
            print("  %-30s a=%g %+6.2f q=%.3f 4/4=%s %s" % (r["hip"], r["a"], r["mbits"], r["q_bh"], r["gate4"], r["veredicto"]))


if __name__ == "__main__":
    main()
