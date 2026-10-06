# -*- coding: utf-8 -*-
"""S1: rasgos del selector (todo con información anterior a h:00). Guarda <SP>/S1_rasgos.npz.
Uso: python rasgos.py          -> construye y guarda
     python rasgos.py fuga     -> altera seq[c:] y comprueba que los rasgos de las filas < c no cambian
"""
import sys, os
import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M1")
import arnes as A  # noqa: E402
import m1  # noqa: E402
import json  # noqa: E402

SP = A.SP
n = len(A.T)
assert (np.diff(A.T) == 1).all()
FD = np.array(A.D.fecha)
RDD = A.LE.cargar("/home/user/lotto-activo/rdint_historial.txt")
RD = {(f, int(h)): int(s) for f, h, s in zip(RDD.fecha, RDD.hora, RDD.seq)}
M4 = np.load(SP + "/motor2_M4.npz")["P"]
MOTORES = {"PROD": A.PROD, "M4": M4}
dias = sorted(set(A.F)); di = {d: k for k, d in enumerate(dias)}; DN = np.array([di[x] for x in A.F]); ND = len(dias)


def rango(P, y):
    o = np.argsort(-P, 1, kind="stable"); return np.argmax(o == y[:, None], 1), o


def rasgos_motor(P, seq, q, pri):
    """Rasgos que dependen del motor. seq: secuencia completa (la etiqueta de fila k es seq[T[k]])."""
    seq = np.asarray(seq); y = seq[A.T]
    rk, o = rango(P, y)
    hit = (rk < 15).astype(float)
    ps = np.sort(P, 1)[:, ::-1]
    masa = ps[:, :15].sum(1); p1 = ps[:, 0]
    ent = -(P * np.log2(np.clip(P, 1e-12, None))).sum(1)
    oe = hit - masa
    # --- de hoy (filas anteriores del mismo día)
    n_hoy = np.zeros(n); hits_hoy = np.zeros(n); oe_hoy = np.zeros(n); reps = np.zeros(n); recic = np.zeros(n)
    # conjuntos por fecha en todo el historial (para reciclaje de ayer/anteayer)
    por_fecha = {}
    for j, f in enumerate(FD): por_fecha.setdefault(f, []).append(j)
    fechas_all = sorted(por_fecha); fi = {f: k for k, f in enumerate(fechas_all)}
    for k in range(n):
        t = A.T[k]; f = FD[t]
        prev = [j for j in por_fecha[f] if j < t]
        n_hoy[k] = len(prev)
        if prev:
            kk = [j - A.T[0] for j in prev]
            kk = [x for x in kk if x >= 0]
            hits_hoy[k] = hit[kk].sum(); oe_hoy[k] = oe[kk].sum()
            vistos = set(); r = 0
            for j in prev:
                if seq[j] in vistos: r += 1
                vistos.add(seq[j])
            reps[k] = r
            a = fi[f]; ayer = set()
            for b in (a - 1, a - 2):
                if b >= 0: ayer |= set(seq[por_fecha[fechas_all[b]]].tolist())
            recic[k] = sum(1 for j in prev if seq[j] in ayer)
    # --- por días pasados
    oe_dia = np.bincount(DN, oe, ND); nd = np.bincount(DN, None, ND)
    cs = np.r_[0, np.cumsum(oe_dia)]
    def ultimos(N):
        d = np.arange(ND); return cs[d] - cs[np.maximum(d - N, 0)]
    U = {N: ultimos(N)[DN] for N in (1, 3, 7, 28)}
    # EWMA por hora (vida media 30 días), por día de la semana (4 semanas) y global (7 días): estado ANTES del día d
    WDd = np.array([A.DOW[DN == d][0] for d in range(ND)])
    lh = 0.5 ** (1 / 30); lw = 0.5 ** (1 / 4); lg = 0.5 ** (1 / 7)
    Sh = np.zeros(12); Wh = np.zeros(12); Sw = np.zeros(7); Ww = np.zeros(7); Sg = 0.0; Wg = 0.0
    eh = np.zeros((ND, 12)); ew = np.zeros(ND); eg = np.zeros(ND)
    oe_dh = np.zeros((ND, 12)); has = np.zeros((ND, 12))
    np.add.at(oe_dh, (DN, A.H), oe); np.add.at(has, (DN, A.H), 1)
    for d in range(ND):
        eh[d] = Sh / (Wh + 5); ew[d] = Sw[WDd[d]] / (Ww[WDd[d]] + 2); eg[d] = Sg / (Wg + 2)
        Sh = lh * Sh + oe_dh[d]; Wh = lh * Wh + has[d]
        w = WDd[d]; Sw[w] = lw * Sw[w] + oe_dia[d] / nd[d]; Ww[w] = lw * Ww[w] + 1
        Sg = lg * Sg + oe_dia[d] / nd[d]; Wg = lg * Wg + 1
    ewh = eh[DN, A.H]; eww = ew[DN]; ewg = eg[DN]
    # --- RD (h-1):30
    rd_disp = np.zeros(n); rd_in15 = np.zeros(n); rd_rk = np.full(n, 38.0)
    pos_rk = np.argsort(o, 1)          # puesto de cada animal
    for k in range(n):
        h = int(A.H[k])
        if h >= 1 and (A.F[k], h - 1) in RD:
            a = RD[(A.F[k], h - 1)]; rd_disp[k] = 1; rd_rk[k] = pos_rk[k, a]; rd_in15[k] = float(pos_rk[k, a] < 15)
    X = dict(hora=A.H.astype(float), dow=A.DOW.astype(float), pri=pri[DN], q=q, n_hoy=n_hoy, hits_hoy=hits_hoy,
             oe_hoy=oe_hoy, oe_1d=U[1], oe_3d=U[3], oe_7d=U[7], oe_28d=U[28], reps_hoy=reps, recic_hoy=recic,
             masa15=masa, ent=ent, p1=p1, ew_hora=ewh, ew_dow=eww, ew_glob=ewg, rd_disp=rd_disp, rd_in15=rd_in15)
    return X, hit, masa, rk


def construir(seq):
    th = m1.cargar("V3")
    _, det = m1.motor(seq, th, "V3", detalle=True)
    out = {}
    for nm, P in MOTORES.items():
        X, hit, masa, rk = rasgos_motor(P, seq, det["q"], det["pri"])
        out[nm] = (X, hit, masa, rk)
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fuga":
        S = np.asarray(A.D.seq).copy(); base = construir(S)
        for c in (8285, 10709):        # cortes en AJUSTE y ELECCION (índices de D.seq)
            S2 = S.copy(); S2[c:] = (S2[c:] + 7) % 38
            alt = construir(S2); kc = c - A.T[0]
            for nm in base:
                for f in base[nm][0]:
                    a = base[nm][0][f][:kc + 1]; b = alt[nm][0][f][:kc + 1]
                    # rasgos de la fila kc (sorteo c) y anteriores no deben cambiar
                    assert np.allclose(a, b), (nm, f, c)
        print("fuga de rasgos: OK (cortes 8285, 10709; filas <= corte idénticas)")
    else:
        out = construir(A.D.seq)
        sv = {}
        for nm, (X, hit, masa, rk) in out.items():
            for f, v in X.items(): sv[f"{nm}__{f}"] = v
            sv[f"{nm}__hit"] = hit; sv[f"{nm}__rk"] = rk
        sv["nombres"] = np.array(list(out["PROD"][0].keys()))
        np.savez_compressed(SP + "/S1_rasgos.npz", **sv)
        print("guardado", len(sv))
