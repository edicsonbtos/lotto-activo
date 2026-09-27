# -*- coding: utf-8 -*-
"""Batería de formas de JUGAR con el motor que ya existe (ensamble_v2), sin tocar el pronóstico (2026-09-27).

Cada estrategia recibe la fila de 38 probabilidades de un sorteo y devuelve fichas por animal. Se mide el
retorno por ficha (pago 30) y la ganancia por sorteo, por mitades de desarrollo, con IC95 por bloques de jornada.

  python estrategias_v2.py dev      exploración en desarrollo [2000, 9357)
  python estrategias_v2.py ciega    UNA vez, candidatos congelados en PREREGISTRO_estrategias_v2.md
"""
import json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import lotto_eval as LE  # noqa: E402

PAGO = 30
EQ = 1 / PAGO


def por_puesto(fichas):
    f = np.array(fichas, float)
    def g(P):
        R = np.argsort(-P, axis=1, kind="stable")[:, :len(f)]
        S = np.zeros_like(P); np.put_along_axis(S, R, f[None, :], axis=1)
        return S
    return g


def umbral(tau):
    return lambda P: (P >= tau).astype(float)


def kelly(escala=100.0):
    # fichas proporcionales a la ventaja (p - 1/30), redondeadas a enteros
    return lambda P: np.round(np.clip(P - EQ, 0, None) * escala)


def solo_horas(base, horas):
    def g(P, hora):
        S = base(P); S[~np.isin(hora, list(horas))] = 0
        return S
    g.usa_hora = True
    return g


ESTRATEGIAS = {
    "T5 escalonado 2-2-2-1-1 (actual)": por_puesto([2, 2, 2, 1, 1]),
    "Top-1": por_puesto([1]),
    "Top-2": por_puesto([1, 1]),
    "Top-3": por_puesto([1, 1, 1]),
    "Top-3 escalonado 2-1-1": por_puesto([2, 1, 1]),
    "Top-5 plano": por_puesto([1] * 5),
    "Top-15 ponderado 3-2-1": por_puesto([3] * 5 + [2] * 5 + [1] * 5),
    "Top-15 plano": por_puesto([1] * 15),
    "Valor p>=3,33%": umbral(EQ),
    "Valor p>=3,6%": umbral(0.036),
    "Valor p>=4%": umbral(0.04),
    "Valor p>=4,5%": umbral(0.045),
    "Kelly proporcional": kelly(),
}


def correr(P, y, hora, dia, estr):
    S = estr(P, hora) if getattr(estr, "usa_hora", False) else estr(P)
    fich = S.sum(1); cobro = PAGO * S[np.arange(len(y)), y]
    return fich, cobro


def ic_bloques(g, f, dia, B=3000, semilla=7):
    _, inv = np.unique(dia, return_inverse=True)
    gs = np.bincount(inv, weights=g); fs = np.bincount(inv, weights=f)
    rng = np.random.default_rng(semilla); I = rng.integers(0, len(gs), size=(B, len(gs)))
    r = gs[I].sum(1) / np.maximum(fs[I].sum(1), 1)
    return np.percentile(r, [2.5, 97.5])


def tabla(P, y, hora, dia, estrategias, titulo):
    print(f"\n=== {titulo} (n={len(y)}) ===")
    print(f"{'estrategia':34s} {'fichas/sorteo':>13s} {'gana/sorteo':>11s} {'retorno':>8s}  IC95          cobra 1 de c/")
    out = {}
    for nom, e in estrategias.items():
        f, c = correr(P, y, hora, dia, e)
        g = c - f
        ret = g.sum() / max(f.sum(), 1)
        lo, hi = ic_bloques(g, f, dia)
        jugados = f > 0
        cobra = (c > 0).sum()
        print(f"{nom:34s} {f.mean():13.2f} {g.mean():+11.2f} {ret*100:+7.1f}%  [{lo*100:+5.1f};{hi*100:+5.1f}]"
              f"   {jugados.sum()/max(cobra,1):5.1f}")
        out[nom] = {"ret": float(ret), "ic": [float(lo), float(hi)], "gana_sorteo": float(g.mean()),
                    "fichas_sorteo": float(f.mean())}
    return out


def por_hora(P, y, hora, dia, titulo):
    print(f"\n--- {titulo}: Top-5 escalonado por hora (retorno) y aciertos Top-5 observados/esperados ---")
    e = ESTRATEGIAS["T5 escalonado 2-2-2-1-1 (actual)"]
    f, c = correr(P, y, hora, dia, e)
    R = np.argsort(-P, axis=1, kind="stable")[:, :5]
    hit5 = (R == y[:, None]).any(1); esp5 = np.take_along_axis(P, R, 1).sum(1)
    for h in range(12):
        m = hora == h
        if m.sum() < 50:
            continue
        print(f"  hora {h:2d} ({8+h:2d}:00)  n={m.sum():4d}  retorno {((c-f)[m].sum()/f[m].sum())*100:+6.1f}%  "
              f"Top-5 {hit5[m].mean()*100:5.1f}% vs esperado {esp5[m].mean()*100:5.1f}%")


def dev():
    D = LE.cargar()
    c = np.load(os.path.join(AQUI, "calor_cache.npz"))
    P = c["P"] / c["P"].sum(1, keepdims=True); y = c["y"]
    ini = LE.W; n = len(y)
    hora = np.asarray(D.hora)[ini:ini + n]; dia = np.asarray(D.dia)[ini:ini + n]
    m = n // 2
    for nom, sl in (("desarrollo 1.ª mitad", slice(0, m)), ("desarrollo 2.ª mitad", slice(m, n)),
                    ("desarrollo completo", slice(0, n))):
        tabla(P[sl], y[sl], hora[sl], dia[sl], ESTRATEGIAS, nom)
    por_hora(P[:m], y[:m], hora[:m], dia[:m], "1.ª mitad")
    por_hora(P[m:], y[m:], hora[m:], dia[m:], "2.ª mitad")


MN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(AQUI))), "lotto-activo-motor", "motor_nuevo")
REG = os.path.join(AQUI, "registro_estrategias_v2.jsonl")
EXCLUIR = {"2025-12-15", "2025-12-16", "2025-12-17", "2025-12-18", "2025-12-19", "2025-12-25", "2025-12-26",
           "2025-12-27", "2026-01-01", "2026-01-02", "2026-01-03"}


def tramo(nombre):
    from datetime import date
    if nombre == "reciente":
        D = LE.cargar().prefijo(12511); ini = 9357
        P = np.load(os.path.join(MN, "reciente", "P_ens_reciente.npy"))
    else:
        D = LE.cargar(os.path.join(MN, "sellado", "sellado_la.txt")); ini = 2000
        P = np.load(os.path.join(MN, "sellado", "P_ens_sellado.npy"))
    P = P / P.sum(1, keepdims=True)
    y = np.asarray(D.seq)[ini:]; hora = np.asarray(D.hora)[ini:]; dia = np.asarray(D.dia)[ini:]
    F = D.fecha[ini:]
    assert len(P) == len(y)
    ok = np.array([f not in EXCLUIR for f in F])
    dom = np.array([date.fromisoformat(f).weekday() == 6 for f in F])
    return P[ok], y[ok], hora[ok], dia[ok], dom[ok]


def ciega():
    import hashlib
    if os.path.exists(REG):
        sys.exit("Esta prueba ya se corrió (registro_estrategias_v2.jsonl existe). No se repite.")
    out = {"prerregistro_sha256": hashlib.sha256(
        open(os.path.join(AQUI, "PREREGISTRO_estrategias_v2.md"), "rb").read()).hexdigest(), "tramos": {}}
    rng = np.random.default_rng(11); boots = []; deltas = []; pesos = []
    for nom in ("reciente", "sellado"):
        P, y, hora, dia, dom = tramo(nom)
        mb = 1000 * np.log2(P[np.arange(len(y)), y] * 38)
        d = float(mb[dom].mean() - mb[~dom].mean())
        _, inv = np.unique(dia, return_inverse=True)
        s = np.bincount(inv, weights=mb); cn = np.bincount(inv); dd = np.bincount(inv, weights=dom) > 0
        B = []
        for _ in range(4000):
            I = rng.integers(0, len(s), len(s)); j = dd[I]
            B.append(s[I][j].sum() / cn[I][j].sum() - s[I][~j].sum() / cn[I][~j].sum())
        boots.append(np.array(B)); deltas.append(d); pesos.append(dom.sum())
        # repeticiones en el día
        rep = {}
        for k, msk in (("domingo", dom), ("resto", ~dom)):
            dias = {}
            for i in np.nonzero(msk)[0]:
                dias.setdefault(dia[i], []).append(y[i])
            rep[k] = float(np.mean([len(v) - len(set(v)) for v in dias.values()]))
        f, c = correr(P, y, hora, dia, ESTRATEGIAS["T5 escalonado 2-2-2-1-1 (actual)"]); g = c - f
        t5 = {k: float(g[m].sum() / f[m].sum()) for k, m in (("domingo", dom), ("resto", ~dom))}
        sharpe = {}
        for e_nom, e in ESTRATEGIAS.items():
            f2, c2 = correr(P, y, hora, dia, e); g2 = c2 - f2
            sharpe[e_nom] = {"sharpe100": float(100 * g2.mean() / g2.std()), "ret": float(g2.sum() / f2.sum())}
        out["tramos"][nom] = {"n": int(len(y)), "n_domingo": int(dom.sum()), "delta_mbits": d,
                              "mbits_dom": float(mb[dom].mean()), "mbits_resto": float(mb[~dom].mean()),
                              "repeticiones_dia": rep, "t5_escalonado_ret": t5, "estrategias": sharpe}
    w = np.array(pesos, float) / sum(pesos)
    conj = sum(wi * b for wi, b in zip(w, boots)); dconj = float(sum(wi * d for wi, d in zip(w, deltas)))
    lo, hi = np.percentile(conj, [2.5, 97.5])
    out["H_dom"] = {"delta_conjunto": dconj, "ic95": [float(lo), float(hi)],
                    "pasa": bool(hi < 0 and all(d < 0 for d in deltas))}
    with open(REG, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if sys.argv[1:] == ["dev"]:
        dev()
    elif sys.argv[1:] == ["ciega"]:
        ciega()
    else:
        sys.exit("uso: estrategias_v2.py dev | ciega")
