# -*- coding: utf-8 -*-
"""S1 parte 2: estrategias con el selector contra 'jugar todos' y contra la jugada de referencia. Guarda selector_S1.npz."""
import sys, os, json
import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A  # noqa: E402

SP = A.SP; n = len(A.T); AQUI = os.path.dirname(os.path.abspath(__file__))
PR = np.load(SP + "/S1_pred.npz"); Z = np.load(SP + "/S1_rasgos.npz", allow_pickle=True)
M4 = np.load(SP + "/motor2_M4.npz")["P"]
RDD = A.LE.cargar("/home/user/lotto-activo/rdint_historial.txt")
RD = {(f, int(h)): int(s) for f, h, s in zip(RDD.fecha, RDD.hora, RDD.seq)}
CON_RD = np.array([A.H[i] == 0 or (A.F[i], int(A.H[i]) - 1) in RD for i in range(n)])
FI = np.array([2, 2, 2, 1, 1]); W15 = np.array([3, 3, 3, 2, 2] + [1] * 10)
U = (0.50, 0.52, 0.54, 0.56, 0.58, 0.60)
RNG = np.random.default_rng(11)
L = []
def pr(s): print(s, flush=True); L.append(s)


def ref_top5():
    st = np.full(n, 8.0); pay = np.zeros(n)
    for i in range(n):
        o = list(np.argsort(-A.PROD[i], kind="stable")[:6])
        r = RD.get((A.F[i], int(A.H[i]) - 1), -1) if A.H[i] >= 1 else -1
        if r in o[:5]: o.remove(r)
        o = o[:5]
        if A.Y[i] in o: pay[i] = 30 * FI[o.index(A.Y[i])]
    return st, pay


def top15(P, ponderado=False, cambio=False):
    o = np.argsort(-P, 1, kind="stable")[:, :16]
    st = np.zeros(n); pay = np.zeros(n)
    for i in range(n):
        oo = list(o[i])
        if cambio and A.H[i] >= 1:
            r = RD.get((A.F[i], int(A.H[i]) - 1), -1)
            if r in oo[:15]: oo.remove(r)
        oo = oo[:15]; w = W15 if ponderado else np.ones(15)
        st[i] = w.sum()
        if A.Y[i] in oo: pay[i] = 30 * w[oo.index(A.Y[i])]
    return st, pay


def metr(st, pay, m):
    """Retorno por ficha, IC 90 por jornadas (bootstrap), fichas netas/día, máx. caída, % jugado."""
    ds = A.F[m]; u, inv = np.unique(ds, return_inverse=True)
    S = np.bincount(inv, st[m], len(u)); Pp = np.bincount(inv, pay[m], len(u)); nd = len(u)
    ret = Pp.sum() / S.sum() - 1 if S.sum() > 0 else np.nan
    bs = []
    for _ in range(1000):
        k = RNG.integers(0, nd, nd); s = S[k].sum(); bs.append(Pp[k].sum() / s - 1 if s > 0 else np.nan)
    lo, hi = np.nanpercentile(bs, [5, 95])
    net = pay[m] - st[m]; cum = np.cumsum(net); dd = (np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max()
    jug = st[m] > 0
    hit = (pay[m] > 0)[jug].mean() if jug.any() else np.nan
    return dict(ret=ret, lo=lo, hi=hi, neto_dia=(Pp - S).sum() / nd, caida=dd, jugado=jug.mean(), fichas_dia=S.sum() / nd,
                acierto=hit, per_dia=Pp - S, S=S, Pp=Pp)


def pareado(a, b, B=2000):
    """IC 90 % por jornadas de la diferencia (a − b) en fichas netas/día y en retorno por ficha."""
    nd = len(a["S"]); d1 = []; d2 = []
    for _ in range(B):
        k = RNG.integers(0, nd, nd)
        d1.append((a["per_dia"][k] - b["per_dia"][k]).mean())
        sa = a["S"][k].sum(); sb = b["S"][k].sum()
        d2.append((a["Pp"][k].sum() / sa if sa else np.nan) - (b["Pp"][k].sum() / sb if sb else np.nan))
    return np.nanpercentile(d1, [5, 95]), np.nanpercentile(d2, [5, 95])


def linea(nom, r):
    return (f"  {nom:38} ret/ficha {100*r['ret']:+6.1f}% [{100*r['lo']:+5.0f};{100*r['hi']:+5.0f}] | netas/día {r['neto_dia']:+6.2f} "
            f"| fichas/día {r['fichas_dia']:6.1f} | máx. caída {r['caida']:6.0f} | jugado {100*r['jugado']:5.1f}% | acierto {100*r['acierto']:5.1f}%")


if __name__ == "__main__":
    st_ref, pay_ref = ref_top5()
    planes = {}
    for mot, P in (("PROD", A.PROD), ("M4", M4)):
        planes[mot] = {"plano": top15(P), "pond": top15(P, ponderado=True)}
    planes["PROD"]["plano_cambio"] = top15(A.PROD, cambio=True)
    out = {}; elegido = {}
    for mot in ("PROD", "M4"):
        p = PR[f"{mot}__LR"]
        pr(f"\n===== Motor {mot} · selector = LR calibrada (P̂ walk-forward). Filas con RD disponible (como incremento.py)")
        # elegir u en AJUSTE: máx. fichas netas/día del T15 plano con selector
        mA = A.TRAMOS["AJUSTE"] & CON_RD
        best = None
        for u in U:
            sel = np.nan_to_num(p) >= u; st, pay = planes[mot]["plano"]
            r = metr(st * sel, pay * sel, mA)
            if best is None or r["neto_dia"] > best[1]: best = (u, r["neto_dia"])
        u_p = best[0]
        best = None
        for u in U:
            sel = np.nan_to_num(p) >= u; st, pay = planes[mot]["pond"]
            r = metr(st * sel, pay * sel, mA)
            if best is None or r["neto_dia"] > best[1]: best = (u, r["neto_dia"])
        u_w = best[0]; elegido[mot] = dict(u_plano=u_p, u_pond=u_w)
        pr(f"  umbral elegido en AJUSTE (máx. netas/día): plano u={u_p}, ponderado u={u_w}")
        mult = np.select([np.nan_to_num(p) >= .60, np.nan_to_num(p) >= .55, np.nan_to_num(p) >= .50], [3, 2, 1], 0)
        for tr in ("AJUSTE", "ELECCION"):
            m = A.TRAMOS[tr] & CON_RD
            pr(f" --- {tr} (n={m.sum()}, días={len(set(A.F[m]))})")
            R = {}
            R["REF Top-5 PROD +cambio (todos)"] = metr(st_ref, pay_ref, m)
            st, pay = planes[mot]["plano"]; R["T15 plano todos"] = metr(st, pay, m)
            st, pay = planes[mot]["pond"]; R["T15 ponderado todos"] = metr(st, pay, m)
            if mot == "PROD":
                st, pay = planes[mot]["plano_cambio"]; R["T15 plano +cambio RD todos (info)"] = metr(st, pay, m)
            for u in U:
                sel = np.nan_to_num(p) >= u
                st, pay = planes[mot]["plano"]; R[f"T15 plano si P̂≥{u:.2f}" + (" *" if u == u_p else "")] = metr(st * sel, pay * sel, m)
            for u in U:
                sel = np.nan_to_num(p) >= u
                st, pay = planes[mot]["pond"]; R[f"T15 ponderado si P̂≥{u:.2f}" + (" *" if u == u_w else "")] = metr(st * sel, pay * sel, m)
            st, pay = planes[mot]["plano"]; R["T15 plano graduado 0/1/2/3×"] = metr(st * mult, pay * mult, m)
            sel = np.nan_to_num(p) >= u_p
            R[f"REF + T15 plano si P̂≥{u_p:.2f} (info)"] = metr(st_ref + st * sel, pay_ref + pay * sel, m)
            # controles: mismo número de sorteos jugados elegidos al azar (dentro del tramo)
            for k, r in R.items(): pr(linea(k, r))
            # pareados oficiales
            ref = R["REF Top-5 PROD +cambio (todos)"]
            for k_sel, k_all in ((f"T15 plano si P̂≥{u_p:.2f} *", "T15 plano todos"), (f"T15 ponderado si P̂≥{u_w:.2f} *", "T15 ponderado todos"),
                                 ("T15 plano graduado 0/1/2/3×", "T15 plano todos")):
                a = R[k_sel]
                (l1, h1), _ = pareado(a, ref); _, (l2, h2) = pareado(a, R[k_all])
                pr(f"    pareado {k_sel:28}: netas/día − REF {a['neto_dia']-ref['neto_dia']:+6.2f} [{l1:+.2f};{h1:+.2f}] | "
                   f"ret/ficha − '{k_all}' {100*(a['ret']-R[k_all]['ret']):+5.1f} pp [{100*l2:+.1f};{100*h2:+.1f}]")
            # placebo: jugar al azar la misma fracción de sorteos que el selector (media de 200 sorteos aleatorios)
            frac = R[f"T15 plano si P̂≥{u_p:.2f} *"]["jugado"]
            st, pay = planes[mot]["plano"]; rr = []
            for _ in range(200):
                sel = RNG.random(n) < frac; rr.append(metr(st * sel, pay * sel, m)["ret"])
            pr(f"    placebo azar con la misma fracción jugada ({100*frac:.1f}%): ret/ficha medio {100*np.nanmean(rr):+.1f}% (p5..p95 {100*np.nanpercentile(rr,5):+.1f}..{100*np.nanpercentile(rr,95):+.1f})")
            out[(mot, tr)] = {k: {kk: (float(vv) if np.isscalar(vv) else None) for kk, vv in v.items() if kk not in ("per_dia", "S", "Pp")} for k, v in R.items()}
    # selector_S1.npz
    sv = dict(t=A.T, f=A.F, h=A.H)
    for mot in ("PROD", "M4"):
        p = PR[f"{mot}__LR"]; sv[f"P_{mot}"] = p; sv[f"P_{mot}_gbm"] = PR[f"{mot}__GBM"]
        sv[f"jugar_{mot}"] = (np.nan_to_num(p) >= elegido[mot]["u_plano"]).astype(np.int8)
        sv[f"fichas_grad_{mot}"] = np.select([np.nan_to_num(p) >= .60, np.nan_to_num(p) >= .55, np.nan_to_num(p) >= .50], [3, 2, 1], 0).astype(np.int8)
    sv["umbrales"] = json.dumps(elegido)
    np.savez_compressed(SP + "/selector_S1.npz", **sv)
    json.dump({f"{a}|{b}": v for (a, b), v in out.items()}, open(os.path.join(AQUI, "estrategias.json"), "w"), indent=1, ensure_ascii=False)
    open(os.path.join(AQUI, "salida_estrategias.txt"), "w").write("\n".join(L) + "\n")
