# -*- coding: utf-8 -*-
"""Filtros de la tarde (PREREGISTRO_filtros_tarde.md): en las horas 10 y 11 se quitan los que salieron hoy,
el último del gemelo (LA<->RD) y los fríos (> 7 días sin salir). ¿Se gana jugando lo que queda?

Uso: python filtros_tarde.py dev      (exploración)
     python filtros_tarde.py ciega    (UNA vez)
"""
import hashlib, json, os, sys
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
RAIZ = os.path.dirname(HERR)
sys.path.insert(0, HERR); sys.path.insert(0, os.path.join(HERR, "rdint"))
import lotto_eval as LE
import datos as DT

K = 38; HORAS = (10, 11); FRIO = 7; B = 5000
FICHAS5 = np.array([2, 2, 2, 1, 1] + [0] * (K - 5))
FICHAS15 = np.array([3] * 3 + [2] * 2 + [1] * 10 + [0] * (K - 15))
PRE = os.path.join(AQUI, "PREREGISTRO_filtros_tarde.md")
P_RECIENTE = os.path.join(os.path.dirname(RAIZ), "lotto-activo-motor", "motor_nuevo", "reciente", "P_ens_reciente.npy")
REGISTRO = os.path.join(AQUI, "registro_filtros_tarde.jsonl")

corr = json.load(open(os.path.join(HERR, "correccion_historial_2026-09-29.json"), encoding="utf-8"))
MALOS = {c["antes"][:10] for c in corr["cambios"]} | {c["despues"][:10] for c in corr["cambios"]}


def frios(seq, fechas):
    """(n, K) bool: el animal lleva > FRIO días de calendario sin salir antes del sorteo t (solo pasado)."""
    dias = np.array([date.fromisoformat(f).toordinal() for f in fechas])
    ult = np.full(K, -10 ** 6); out = np.zeros((len(seq), K), bool)
    for t, (s, d) in enumerate(zip(seq, dias)):
        out[t] = (d - ult) > FRIO
        ult[s] = d
    return out


def hoy(seq, fechas):
    out = np.zeros((len(seq), K), bool)
    for t in range(1, len(seq)):
        if fechas[t] == fechas[t - 1]:
            out[t] = out[t - 1]; out[t, seq[t - 1]] = True
    return out


def filas_la(modo):
    la = LE.cargar()
    seq = np.asarray(la.seq); fe = la.fecha; hr = np.asarray(la.hora)
    F, H = frios(seq, fe), hoy(seq, fe)
    rd, *_ = DT.cargar()
    rdd = {(f, int(h)): int(s) for f, h, s in zip(rd.fecha, rd.hora, rd.seq)}
    if modo == "dev":
        a, b = LE.W, LE.CORTE_FIJO; P = np.load(os.path.join(AQUI, "calor_cache.npz"))["P"]
    else:
        a, b = LE.CORTE_FIJO, 12511; P = np.load(P_RECIENTE)
    assert len(P) == b - a
    t = np.arange(a, b)
    gem = np.array([rdd.get((fe[i], int(hr[i]) - 1), -1) for i in t])
    return dict(P=P, y=seq[t], hora=hr[t], fecha=np.array(fe)[t], hoy=H[t], frio=F[t], gem=gem)


def filas_rd(modo):
    rd, la_h, *_ = DT.cargar()
    seq = np.asarray(rd.seq); fe = rd.fecha
    F, H = frios(seq, fe), hoy(seq, fe)
    idx = {(f, int(h)): i for i, (f, h) in enumerate(zip(fe, rd.hora))}
    if modo == "dev":
        z = np.load(os.path.join(HERR, "rdint", "cache_dev.npz")); t = z["fila"]; P = z["P1"]
    else:
        z = np.load(os.path.join(HERR, "rdint", "cache_todo.npz"))
        s = np.isin(z["tramo"], ["test", "desc"])
        t = np.array([idx[(str(f), int(h))] for f, h in zip(z["fecha"][s], z["hora"][s])]); P = z["P1"][s]
    assert (seq[t] == (z["y"] if modo == "dev" else z["y"][s])).all()
    return dict(P=P, y=seq[t], hora=np.asarray(rd.hora)[t], fecha=np.array(fe)[t], hoy=H[t], frio=F[t], gem=la_h[t])


def boot(num, den, dias, rng):
    u, g = np.unique(dias, return_inverse=True)
    N = np.bincount(g, num, len(u)); D = np.bincount(g, den, len(u))
    k = rng.integers(0, len(u), (B, len(u)))
    b = N[k].sum(1) / D[k].sum(1)
    return N.sum() / D.sum(), np.percentile(b, [0.625, 99.375]), np.percentile(b, [2.5, 97.5])


def retorno(P, y, fichas, quitar):
    Q = np.where(quitar, -1.0, P)
    orden = np.argsort(-Q, 1, kind="stable")
    puesto = (orden == y[:, None]).argmax(1)
    return 30 * fichas[puesto] - fichas.sum()


def analiza(nombre, d, rng):
    s = np.isin(d["hora"], HORAS) & ~np.isin(d["fecha"], list(MALOS))
    P, y, fe = d["P"][s], d["y"][s], d["fecha"][s]
    n = len(y); r = np.arange(n)
    Hm = d["hoy"][s]
    G = np.zeros((n, K), bool); g = d["gem"][s]; G[r[g >= 0], g[g >= 0]] = True
    Gm = G & ~Hm; Fm = d["frio"][s] & ~Hm & ~G
    X = Hm | Gm | Fm; C = ~X
    out = {"n": n, "jornadas": int(len(np.unique(fe)))}
    print(f"\n## {nombre}: {n} sorteos (horas 10-11), {out['jornadas']} jornadas")
    print(f"  tamaño medio: hoy {Hm.sum(1).mean():.1f}, gemelo extra {Gm.sum(1).mean():.2f}, fríos extra {Fm.sum(1).mean():.1f}, quedan C {C.sum(1).mean():.1f}")
    for nom, M in [("hoy", Hm), ("gemelo", Gm), ("fríos", Fm), ("C (lo que queda)", C)]:
        obs = M[r, y].sum(); eu = M.sum() / K; em = (P * M).sum()
        out[nom] = {"obs": int(obs), "esp_azar": eu, "esp_ensamble": em}
        print(f"  {nom:17s} salieron {obs:5d}  esperado azar {eu:7.1f} (O/E {obs/eu:.2f})  ensamble {em:7.1f} (O/E {obs/em:.2f})")
    print(f"  acierto de C: {C[r, y].mean()*100:.1f} %  (azar |C|/38 = {C.sum(1).mean()/K*100:.1f} %)")
    # H1: plano en C
    num = 30 * C[r, y] - C.sum(1); den = C.sum(1).astype(float)
    v, ic, ic95 = boot(num, den, fe, rng)
    out["H1"] = {"ret": v, "ic9875": ic.tolist(), "ic95": ic95.tolist(), "pasa": bool(ic[0] > 0)}
    print(f"  H1 plano en C: {v*100:+.1f} % por ficha  IC98,75 [{ic[0]*100:+.1f}; {ic[1]*100:+.1f}]  -> {'PASA' if ic[0] > 0 else 'NO PASA'}")
    # H2: Top-5 escalonado filtrado menos normal; también Top-15 ponderado (descriptivo)
    for est, f, clave in [("Top-5 escalonado", FICHAS5, "H2"), ("Top-15 ponderado", FICHAS15, "T15")]:
        r0 = retorno(P, y, f, np.zeros_like(X)); r1 = retorno(P, y, f, X)
        den = np.full(n, float(f.sum()))
        a0 = boot(r0, den, fe, rng)[0]; a1 = boot(r1, den, fe, rng)[0]
        dv, dic, _ = boot(r1 - r0, den, fe, rng)
        out[clave] = {"normal": a0, "filtrado": a1, "dif": dv, "ic9875": dic.tolist(), "pasa": bool(dic[0] > 0)}
        tag = ("  -> " + ("PASA" if dic[0] > 0 else "NO PASA")) if clave == "H2" else "  (descriptivo)"
        print(f"  {est}: normal {a0*100:+.1f} %  filtrado {a1*100:+.1f} %  dif {dv*100:+.1f} pp  IC98,75 [{dic[0]*100:+.1f}; {dic[1]*100:+.1f}]{tag}")
    # mitades
    u = np.unique(fe); m1 = np.isin(fe, u[: len(u) // 2])
    for nm, mm in [("mitad1", m1), ("mitad2", ~m1)]:
        h1 = (num[mm]).sum() / C[mm].sum()
        dd = (retorno(P[mm], y[mm], FICHAS5, X[mm]) - retorno(P[mm], y[mm], FICHAS5, np.zeros_like(X[mm]))).mean() / FICHAS5.sum()
        out[nm] = {"H1": h1, "H2": dd}
        print(f"  {nm}: H1 {h1*100:+.1f} %   H2 dif {dd*100:+.1f} pp")
    return out


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "dev"
    sha = hashlib.sha256(open(PRE, "rb").read()).hexdigest()
    print("modo", modo, "| preregistro sha256", sha)
    if modo == "ciega" and os.path.exists(REGISTRO):
        sys.exit("La prueba ciega ya se corrió (registro_filtros_tarde.jsonl). No se repite.")
    rng = np.random.default_rng(20260929)
    res = {"LA": analiza("Lotto Activo", filas_la(modo), rng), "RD": analiza("RD Internacional", filas_rd(modo), rng)}
    json.dump(res, open(os.path.join(AQUI, f"filtros_tarde_{modo}.json"), "w", encoding="utf-8"), indent=1, default=float)
    if modo == "ciega":
        with open(REGISTRO, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"fecha": "2026-09-29", "sha_prereg": sha, "res": res}, default=float) + "\n")


if __name__ == "__main__":
    main()
