# -*- coding: utf-8 -*-
"""Tramos mañana (h 0..5) y tarde (h 6..11): ¿rinde distinto la jugada? Ver PREREGISTRO_tramos_manana_tarde.md.
Solo desarrollo: LA calor_cache.npz (filas [2000,9357)), RD rdint/cache_dev.npz (P1)."""
import os, sys, hashlib, json
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, HERR)
import lotto_eval as LE

B = 5000
rng = np.random.default_rng(20260929)
K = 38
PRE = os.path.join(AQUI, "PREREGISTRO_tramos_manana_tarde.md")
print("preregistro sha256", hashlib.sha256(open(PRE, "rb").read()).hexdigest())


def juego_la():
    z = np.load(os.path.join(AQUI, "calor_cache.npz"))
    d = LE.cargar()
    return z["P"], z["y"], np.asarray(d.hora[LE.W:LE.CORTE_FIJO]), np.asarray(d.dia[LE.W:LE.CORTE_FIJO])


def juego_rd():
    z = np.load(os.path.join(HERR, "rdint", "cache_dev.npz"))
    return z["P1"], z["y"], z["hora"], z["dia"]


def retornos(P, y):
    orden = np.argsort(-P, 1, kind="stable")
    puesto = (orden == y[:, None]).argmax(1)
    top15 = 30 * (puesto < 15) / 15 - 1
    fichas = np.array([2, 2, 2, 1, 1] + [0] * (K - 5))
    top5 = 30 * fichas[puesto] / 8 - 1
    mb = 1000 * np.log2(np.clip(P[np.arange(len(y)), y], 1e-12, None) * K)
    return {"top15": top15, "top5": top5}, puesto < 15, mb


def por_dia(v, dia, m):
    """Suma y conteo por jornada dentro de la máscara m."""
    u, inv = np.unique(dia, return_inverse=True)
    s = np.bincount(inv, weights=v * m, minlength=len(u)); c = np.bincount(inv, weights=m.astype(float), minlength=len(u))
    return s, c


def analiza(nombre, P, y, hora, dia):
    R, acierto, mb = retornos(P, y)
    man = hora <= 5; tar = hora >= 6
    u = np.unique(dia); mitad = np.isin(dia, u[: len(u) // 2])
    out = {}
    print(f"\n## {nombre}: {len(y)} sorteos, {len(u)} jornadas")
    print(f"  acierto Top-15: mañana {acierto[man].mean()*100:.2f} %  tarde {acierto[tar].mean()*100:.2f} %  (azar 39,47 %)")
    print(f"  mbits frente al uniforme: mañana {mb[man].mean():+.1f}  tarde {mb[tar].mean():+.1f}")
    for est, v in R.items():
        fila = {}
        for tramo, sel in [("entero", np.ones(len(y), bool)), ("mitad1", mitad), ("mitad2", ~mitad)]:
            sm, cm = por_dia(v, dia, man & sel); st, ct = por_dia(v, dia, tar & sel)
            keep = (cm + ct) > 0
            sm, cm, st, ct = sm[keep], cm[keep], st[keep], ct[keep]
            idx = rng.integers(0, len(sm), size=(B, len(sm)))
            bm = sm[idx].sum(1) / cm[idx].sum(1); bt = st[idx].sum(1) / ct[idx].sum(1); bd = bt - bm
            rm, rt = sm.sum() / cm.sum(), st.sum() / ct.sum()
            ic = lambda b, a: [float(np.percentile(b, a)), float(np.percentile(b, 100 - a))]
            fila[tramo] = {"manana": rm, "tarde": rt, "dif": rt - rm,
                           "ic95_dif": ic(bd, 2.5), "ic9875_dif": ic(bd, 0.625),
                           "ic9875_manana": ic(bm, 0.625), "ic9875_tarde": ic(bt, 0.625)}
            f = fila[tramo]
            print(f"  {est:5s} {tramo:6s} mañana {rm*100:+6.1f} %  tarde {rt*100:+6.1f} %  "
                  f"tarde−mañana {f['dif']*100:+6.1f} pp  IC98,75 [{f['ic9875_dif'][0]*100:+.1f}; {f['ic9875_dif'][1]*100:+.1f}]"
                  + (f"   mañana IC98,75 [{f['ic9875_manana'][0]*100:+.1f}; {f['ic9875_manana'][1]*100:+.1f}]"
                     f"  tarde [{f['ic9875_tarde'][0]*100:+.1f}; {f['ic9875_tarde'][1]*100:+.1f}]" if tramo == "entero" else ""))
        e, m1, m2 = fila["entero"], fila["mitad1"], fila["mitad2"]
        hay = (e["ic9875_dif"][0] > 0 or e["ic9875_dif"][1] < 0) and np.sign(m1["dif"]) == np.sign(m2["dif"]) == np.sign(e["dif"])
        pos = [t for t in ("manana", "tarde") if e[f"ic9875_{t}"][0] > 0 and m1[t] > 0 and m2[t] > 0]
        nota = ("; los dos tramos dan retorno > 0 (no hay tramo que evitar)" if len(pos) == 2 else
                f"; solo {pos[0]} da retorno > 0" if pos else "; ningún tramo da retorno > 0 seguro")
        fila["veredicto"] = ("HAY DIFERENCIA" if hay else "NO PASA") + nota
        print(f"  -> {est}: {fila['veredicto']}")
        out[est] = fila
    return out


res = {"LA": analiza("Lotto Activo (desarrollo)", *juego_la()), "RD": analiza("RD Internacional (desarrollo)", *juego_rd())}
json.dump(res, open(os.path.join(AQUI, "tramos_manana_tarde.json"), "w", encoding="utf-8"), indent=1, default=float)
