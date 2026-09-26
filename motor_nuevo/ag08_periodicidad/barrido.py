# -*- coding: utf-8 -*-
"""Barrido prerregistrado: residuos del ensamble_v2 frente a ~1940 variables temporales.
Descubrimiento con BH (q=0,05) en la mitad 1; confirmación en la mitad 2 (Bonferroni unilateral).
Escribe barrido.json. Solo filas [2000, 9357)."""
import json, os, sys
import numpy as np
from scipy.stats import norm, gamma

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import rasgos as R  # noqa: E402

OBJ = [12, 24, 36, 38, 76, 84]


def specs_indicadoras():
    s = [("lag", L) for L in range(1, 169)]
    s += [("dia", k) for k in range(1, 8)]
    s += [("lagA", a, L) for a in range(38) for L in OBJ]
    s += [("gh", b, h) for b in range(8) for h in range(12)]
    s += [("gd", b, d) for b in range(8) for d in range(7)]
    s += [("gdh", d, h) for d in range(7) for h in range(12)]
    s += [("ah", a, h) for a in range(38) for h in range(12)]
    s += [("ad", a, d) for a in range(38) for d in range(7)]
    s += [("tab", L, dl) for L in (1, 2, 12, 38) for dl in range(1, 38)]
    return s


FAM = {"lag": "F1", "dia": "F1b", "lagA": "F2", "gh": "F4", "gd": "F4", "gdh": "F4",
       "ah": "F5", "ad": "F5", "tab": "F6"}


def bh(p, q=0.05):
    p = np.asarray(p); m = len(p); o = np.argsort(p)
    thr = q * np.arange(1, m + 1) / m
    ok = p[o] <= thr
    k = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    sel = np.zeros(m, bool); sel[o[:k]] = True
    return sel


def main():
    D = A.datos(); P, y = A.base(); P = P / P.sum(1, keepdims=True)
    Dd = D.prefijo(A.CORTE)  # nunca se tocan filas >= 9357
    m = len(y); h = m // 2; r = np.arange(m)
    mitades = [slice(0, h), slice(h, m)]
    specs = specs_indicadoras()
    res = []
    for i0 in range(0, len(specs), 40):
        blk = specs[i0:i0 + 40]
        X = R.construir(Dd, A.W, blk)
        for k, s in enumerate(blk):
            F = X[:, :, k]
            e = (F * P).sum(1); hit = F[r, y]
            fila = {"spec": list(s), "fam": FAM[s[0]]}
            for nm, sl in zip(("m1", "m2"), mitades):
                O, E, V = float(hit[sl].sum()), float(e[sl].sum()), float((e[sl] - e[sl] ** 2).sum())
                z = (O - E) / np.sqrt(V) if V > 0 else 0.0
                fila[nm] = {"O": O, "E": E, "z": z, "p": float(2 * norm.sf(abs(z)))}
            res.append(fila)
        print(f"{i0 + len(blk)}/{len(specs)}", flush=True)
    # F3 espectral del residuo
    Y = np.zeros_like(P); Y[r, y] = 1; Rr = Y - P; W = P * (1 - P)
    for nm, sl in zip(("m1", "m2"), mitades):
        pass
    esp = []
    for T in range(2, 201):
        fila_a = {"spec": ["espT", T], "fam": "F3b"}
        filas_A = []
        for nm, sl in zip(("m1", "m2"), mitades):
            t = np.arange(m)[sl]
            c = (Rr[sl] * np.exp(-2j * np.pi * t / T)[:, None]).sum(0)
            I = np.abs(c) ** 2 / W[sl].sum(0)
            fila_a[nm] = {"stat": float(I.sum()), "p": float(gamma.sf(I.sum(), 38))}
            if T in OBJ:
                filas_A.append(I)
        esp.append(fila_a)
        if T in OBJ:
            for a in range(38):
                esp.append({"spec": ["espA", a, T], "fam": "F3a",
                            "m1": {"stat": float(filas_A[0][a]), "p": float(np.exp(-filas_A[0][a]))},
                            "m2": {"stat": float(filas_A[1][a]), "p": float(np.exp(-filas_A[1][a]))}})
    res += esp
    p1 = np.array([f["m1"]["p"] for f in res])
    sel = bh(p1)
    nsup = int(sel.sum())
    conf = []
    for i in np.where(sel)[0]:
        f = res[i]
        if f["fam"].startswith("F3"):
            ok = f["m2"]["p"] < 0.05 / nsup   # espectral: sin signo
        else:
            ok = np.sign(f["m2"]["z"]) == np.sign(f["m1"]["z"]) and norm.sf(abs(f["m2"]["z"])) < 0.05 / nsup
        f["superviviente"] = True; f["confirmado"] = bool(ok)
        conf.append(f)
    # resumen
    print(f"\nPruebas: {len(res)} · supervivientes BH(q=0,05) en mitad 1: {nsup} · confirmados en mitad 2: "
          f"{sum(f['confirmado'] for f in conf)}")
    for f in conf:
        print("  ", f["spec"], f["fam"], "m1", {k: round(v, 4) for k, v in f["m1"].items()},
              "m2", {k: round(v, 4) for k, v in f["m2"].items()}, "CONF" if f["confirmado"] else "no")
    # informativo: p mínimos por familia y los desfases objetivo
    fams = sorted(set(f["fam"] for f in res))
    for fa in fams:
        ps = [f["m1"]["p"] for f in res if f["fam"] == fa]
        print(f"  {fa}: {len(ps)} pruebas · p mín m1 {min(ps):.2e} · n(p<0,05) {sum(p < 0.05 for p in ps)} "
              f"(esperado {0.05 * len(ps):.1f})")
    print("  Desfases objetivo (F1), z m1 / z m2:")
    for f in res:
        if f["spec"][0] == "lag" and f["spec"][1] in OBJ:
            print(f"    L={f['spec'][1]}: {f['m1']['z']:+.2f} / {f['m2']['z']:+.2f}")
    for f in res:
        if f["spec"][0] == "dia":
            print(f"    misma hora hace {f['spec'][1]} días: {f['m1']['z']:+.2f} / {f['m2']['z']:+.2f}")
    json.dump({"n_pruebas": len(res), "n_supervivientes": nsup, "supervivientes": conf, "todas": res},
              open(os.path.join(AQUI, "barrido.json"), "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
