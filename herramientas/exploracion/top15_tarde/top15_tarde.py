# -*- coding: utf-8 -*-
"""Top-15 de los dos últimos sorteos con descarte (PREREGISTRO.md de esta carpeta).

En las horas 10 y 11 (LA 18:00/19:00, RD 18:30/19:30) se mandan al final del orden del modelo actual:
HOY (ya salió hoy en ese juego), HERMANO (último del otro juego) y FRÍO(d) (> d días sin salir).
¿Sube el acierto del Top-15?

Uso: python predecir.py              (una vez, genera cache/)
     python top15_tarde.py dev       (desarrollo: mide 23 variantes y elige)
     python top15_tarde.py ciega     (2026-01-01..09-29, UNA vez; se niega a repetir)
"""
import hashlib, json, os, sys, time
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, HERR); sys.path.insert(0, os.path.join(HERR, "rdint")); sys.path.insert(0, AQUI)
import lotto_eval as LE
import predecir as PR

K = 38; HORAS = (10, 11); B = 10000
UMBRALES = (3, 4, 5, 6, 7)
F5 = np.array([2, 2, 2, 1, 1] + [0] * (K - 5), float)
F15 = np.array([3, 3, 3, 2, 2] + [1] * 10 + [0] * (K - 15), float)
PRE = os.path.join(AQUI, "PREREGISTRO.md")
REGISTRO = os.path.join(AQUI, "registro.jsonl")
CIEGA = ("2026-01-01", "2026-09-29"); MITAD = "2026-05-15"


# ----------------------------------------------------------------- reglas (solo pasado)
def hoy_mask(seq, fechas):
    out = np.zeros((len(seq), K), bool)
    for t in range(1, len(seq)):
        if fechas[t] == fechas[t - 1]:
            out[t] = out[t - 1]; out[t, seq[t - 1]] = True
    return out


def dias_sin_salir(seq, fechas):
    """(n, K): días de calendario entre la fecha del sorteo t y la última salida ANTES de t."""
    dias = np.array([date.fromisoformat(f).toordinal() for f in fechas])
    ult = np.full(K, -10 ** 6); out = np.zeros((len(seq), K), np.int64)
    for t, (s, d) in enumerate(zip(seq, dias)):
        out[t] = d - ult
        ult[s] = d
    return out


def juego_la():
    D = LE.cargar(PR.HIST_LA)
    seq = np.asarray(D.seq); fe = list(D.fecha); hr = np.asarray(D.hora)
    import datos as DT
    DT.RD_CSV = PR.RD_CSV_EXT; DT.LA_HIST = PR.HIST_LA
    rd, *_ = DT.cargar()
    rdd = {(f, int(h)): int(s) for f, h, s in zip(rd.fecha, rd.hora, rd.seq)}
    herm = np.array([rdd.get((f, int(h) - 1), -1) if h > 0 else -1 for f, h in zip(fe, hr)])
    z = np.load(os.path.join(PR.CACHE, "la.npz"))
    fila = z["fila"]
    assert (z["y"] == seq[fila]).all() and (z["fecha"] == np.array(fe)[fila]).all()
    return dict(P=z["P"].astype(np.float64), y=seq[fila], hora=hr[fila], fecha=np.array(fe)[fila],
                hoy=hoy_mask(seq, fe)[fila], dss=dias_sin_salir(seq, fe)[fila], herm=herm[fila],
                dev=(fila >= LE.W) & (fila < LE.CORTE_FIJO))


def juego_rd():
    import datos as DT
    DT.RD_CSV = PR.RD_CSV_EXT; DT.LA_HIST = PR.HIST_LA
    rd, la_h, *_ = DT.cargar()
    seq = np.asarray(rd.seq); fe = list(rd.fecha)
    z = np.load(os.path.join(PR.CACHE, "rd.npz"))
    fila = np.arange(PR.DESDE, len(seq))
    assert (z["y"] == seq[fila]).all() and (z["fecha"] == np.array(fe)[fila]).all()
    return dict(P=z["P"].astype(np.float64), y=seq[fila], hora=np.asarray(rd.hora)[fila], fecha=np.array(fe)[fila],
                hoy=hoy_mask(seq, fe)[fila], dss=dias_sin_salir(seq, fe)[fila], herm=la_h[fila],
                dev=z["tramo"] == "dev")


# ----------------------------------------------------------------- variantes y métricas
def variantes():
    v = [("HOY", ("HOY",), None), ("HERM", ("HERM",), None), ("HOY+HERM", ("HOY", "HERM"), None)]
    for d in UMBRALES:
        for reg in (("FRIO",), ("HOY", "FRIO"), ("HERM", "FRIO"), ("HOY", "HERM", "FRIO")):
            v.append(("+".join(r if r != "FRIO" else f"FRIO{d}" for r in reg), reg, d))
    return v


def mascara(d, reglas, umbral):
    n = len(d["y"]); X = np.zeros((n, K), bool)
    if "HOY" in reglas:
        X |= d["hoy"]
    if "HERM" in reglas:
        g = d["herm"]; ok = g >= 0; X[np.flatnonzero(ok), g[ok]] = True
    if "FRIO" in reglas:
        X |= d["dss"] > umbral
    return X


def puestos(P, X):
    """Puesto (0..37) del ganador con los descartados al final (conservan su orden)."""
    orden = LE.rankings(P - 2.0 * X)
    return orden


def medidas(P, y, X):
    orden = puestos(P, X)
    pos = np.argmax(orden == y[:, None], axis=1)
    return dict(pos=pos, t15=(pos < 15).astype(float), t5=(pos < 5).astype(float),
                r15p=(30 * F15[pos] - F15.sum()) / F15.sum(), r15=(30 * (pos < 15) - 15) / 15.0,
                r5=(30 * F5[pos] - F5.sum()) / F5.sum(), orden=orden)


def boot(v, fe, rng, niveles=((0.625, 99.375), (2.5, 97.5))):
    u, g = np.unique(fe, return_inverse=True)
    S = np.bincount(g, v, len(u)); C = np.bincount(g, minlength=len(u)).astype(float)
    k = rng.integers(0, len(u), (B, len(u)))
    b = S[k].sum(1) / C[k].sum(1)
    return float(v.mean()), [[float(x) for x in np.percentile(b, q)] for q in niveles]


def pct(x):
    return f"{100 * x:5.2f} %"


# ----------------------------------------------------------------- análisis de un juego en un tramo
def analiza(nombre, d, sel, rng, elegida=None):
    s = sel & np.isin(d["hora"], HORAS)
    P, y, fe = d["P"][s], d["y"][s], d["fecha"][s]
    n = len(y); r = np.arange(n)
    sub = {k: v[s] for k, v in d.items() if isinstance(v, np.ndarray) and len(v) == len(d["y"])}
    out = {"n": int(n), "jornadas": int(len(np.unique(fe))), "desde": str(fe[0]), "hasta": str(fe[-1])}
    print(f"\n## {nombre}: {n} sorteos de las horas 10-11, {out['jornadas']} jornadas ({fe[0]} .. {fe[-1]})")
    base = medidas(P, y, np.zeros((n, K), bool))
    out["actual"] = {q: float(base[q].mean()) for q in ("t15", "t5", "r15p", "r15", "r5")}
    out["actual"]["masa15"] = float(np.take_along_axis(P, base["orden"][:, :15], 1).sum(1).mean())
    out["actual"]["ic_t15"] = boot(base["t15"], fe, rng)[1][1]
    out["actual"]["ic_r15p"] = boot(base["r15p"], fe, rng)[1][1]
    print(f"  Top-15 actual: acierto {pct(out['actual']['t15'])} (el modelo se da {pct(out['actual']['masa15'])}; azar 39,47 %)"
          f"  IC95 [{pct(out['actual']['ic_t15'][0])}; {pct(out['actual']['ic_t15'][1])}]")
    print(f"  retorno/ficha: Top-15 ponderado {out['actual']['r15p']*100:+.1f} %, Top-15 plano {out['actual']['r15']*100:+.1f} %,"
          f" Top-5 escalonado {out['actual']['r5']*100:+.1f} %")

    # D1: ¿el modelo ya lo sabe?
    H = sub["hoy"]; G = mascara(sub, ("HERM",), None) & ~H; F = (sub["dss"] > 4) & ~H & ~G; C = ~(H | G | F)
    out["D1"] = {}
    print(f"  tamaño medio: HOY {H.sum(1).mean():.1f}, HERMANO aparte {G.sum(1).mean():.2f}, FRÍO(4) aparte {F.sum(1).mean():.1f},"
          f" quedan {C.sum(1).mean():.1f}  (quedan < 15 en {(C.sum(1) < 15).mean()*100:.1f} % de los sorteos)")
    for nom, M in [("HOY", H), ("HERMANO", G), ("FRÍO(4)", F), ("quedan", C)]:
        obs = int(M[r, y].sum()); eu = M.sum() / K; em = float((P * M).sum())
        out["D1"][nom] = {"obs": obs, "esp_azar": eu, "esp_modelo": em, "por_animal": obs / max(M.sum(), 1)}
        print(f"  D1 {nom:8s} salieron {obs:4d} | azar {eu:6.1f} (O/E {obs/eu:.2f}) | modelo {em:6.1f} (O/E {obs/em:.2f})"
              f" | {100*obs/max(M.sum(),1):.2f} % por animal")
    out["D1"]["quedan<15"] = float((C.sum(1) < 15).mean())

    # D2: qué lleva el Top-15 actual
    top = np.zeros((n, K), bool); np.put_along_axis(top, base["orden"][:, :15], True, 1)
    U = H | G | F
    fx = medidas(P, y, U)
    topf = np.zeros((n, K), bool); np.put_along_axis(topf, fx["orden"][:, :15], True, 1)
    sale, entra = top & ~topf, topf & ~top
    out["D2"] = {}
    for nom, M in [("HOY", H), ("HERMANO", G), ("FRÍO(4)", F)]:
        out["D2"][nom] = {"en_top15": float((top & M).sum(1).mean()), "ganó": int((top & M)[r, y].sum())}
    out["D2"]["salen"] = {"por_sorteo": float(sale.sum(1).mean()), "ganó": int(sale[r, y].sum()), "modelo": float((P * sale).sum())}
    out["D2"]["entran"] = {"por_sorteo": float(entra.sum(1).mean()), "ganó": int(entra[r, y].sum()), "modelo": float((P * entra).sum())}
    print("  D2 el Top-15 actual trae de media: " + ", ".join(f"{k} {v['en_top15']:.2f} (ganó {v['ganó']})" for k, v in out["D2"].items() if k in ("HOY", "HERMANO", "FRÍO(4)")))
    print(f"     con la idea salen {out['D2']['salen']['por_sorteo']:.2f} por sorteo (ganaron {out['D2']['salen']['ganó']}, el modelo esperaba"
          f" {out['D2']['salen']['modelo']:.1f}) y entran {out['D2']['entran']['por_sorteo']:.2f} (ganaron {out['D2']['entran']['ganó']},"
          f" el modelo esperaba {out['D2']['entran']['modelo']:.1f})")

    # Variantes
    out["variantes"] = {}
    print("  variante                 Top-15    Δ Top-15 [IC 98,75 %]        Δ ret. ponderado   Δ ret. plano")
    for nom, reg, um in variantes():
        m = medidas(P, y, mascara(sub, reg, um))
        dv, (ic9875, ic95) = boot(m["t15"] - base["t15"], fe, rng)
        dr = boot(m["r15p"] - base["r15p"], fe, rng)
        dp = boot(m["r15"] - base["r15"], fe, rng)
        out["variantes"][nom] = {"t15": float(m["t15"].mean()), "dif": dv, "ic9875": ic9875, "ic95": ic95,
                                 "t5": float(m["t5"].mean()), "r15p": float(m["r15p"].mean()), "dif_r15p": dr[0], "ic95_r15p": dr[1][1],
                                 "r15": float(m["r15"].mean()), "dif_r15": dp[0], "ic95_r15": dp[1][1],
                                 "reglas": list(reg), "umbral": um}
        marca = " <- H1" if nom == "HOY+HERM+FRIO4" else (" <- H2" if nom == elegida else "")
        print(f"  {nom:22s} {pct(m['t15'].mean())}  {dv*100:+5.2f} pp [{ic9875[0]*100:+5.2f}; {ic9875[1]*100:+5.2f}]"
              f"   {dr[0]*100:+5.2f} pp           {dp[0]*100:+5.2f} pp{marca}")

    # D4: Top-N para 50/60/70 % y plano en C
    curva = np.array([(base["pos"] < k).mean() for k in range(1, K + 1)])
    curvaf = np.array([(fx["pos"] < k).mean() for k in range(1, K + 1)])
    out["D4"] = {"curva_actual": curva.tolist(), "curva_idea": curvaf.tolist(),
                 "N_para": {str(q): int(np.argmax(curva >= q / 100) + 1) for q in (50, 60, 70)},
                 "N_para_idea": {str(q): int(np.argmax(curvaf >= q / 100) + 1) for q in (50, 60, 70)}}
    num = 30 * C[r, y] - C.sum(1)
    out["D4"]["plano_C"] = {"ret": float(num.sum() / C.sum()), "acierto": float(C[r, y].mean()), "tam": float(C.sum(1).mean())}
    print(f"  D4 Top-N para 50/60/70 %: actual {out['D4']['N_para']}, con la idea {out['D4']['N_para_idea']}")
    print(f"     jugar plano todo lo que queda ({out['D4']['plano_C']['tam']:.1f} animales): acierto {pct(out['D4']['plano_C']['acierto'])},"
          f" retorno {out['D4']['plano_C']['ret']*100:+.1f} % por ficha")

    # Mitades (solo ciega)
    if elegida is not None or fe[0] >= CIEGA[0]:
        out["mitades"] = {}
        for nm, mm in [("ene-may", fe <= MITAD), ("may-sep", fe > MITAD)]:
            fila = {"n": int(mm.sum()), "actual": float(base["t15"][mm].mean())}
            for v in {"HOY+HERM+FRIO4", elegida} - {None}:
                reg, um = out["variantes"][v]["reglas"], out["variantes"][v]["umbral"]
                fila[v] = float(medidas(P[mm], y[mm], mascara({k: x[mm] for k, x in sub.items()}, reg, um))["t15"].mean())
            out["mitades"][nm] = fila
            print(f"  mitad {nm}: " + ", ".join(f"{k} {v*100:.2f} %" if isinstance(v, float) else f"{k} {v}" for k, v in fila.items()))
    return out


def calibracion(nombre, d, sel):
    """D3: masa que el modelo da a su Top-15 contra el acierto real, por hora."""
    P, y, h = d["P"][sel], d["y"][sel], d["hora"][sel]
    orden = LE.rankings(P); pos = np.argmax(orden == y[:, None], axis=1)
    masa = np.take_along_axis(P, orden[:, :15], 1).sum(1)
    out = {}
    for nom, m in [("todas", np.ones(len(y), bool)), ("10-11", np.isin(h, HORAS))] + [(f"h{k}", h == k) for k in range(12)]:
        if m.any():
            out[nom] = {"n": int(m.sum()), "acierto": float((pos[m] < 15).mean()), "masa": float(masa[m].mean()),
                        "mbits": float((1000 * np.log2(P[m, y[m]] * K)).mean())}
    print(f"  D3 {nombre}: Top-15 todas las horas {pct(out['todas']['acierto'])} (modelo {pct(out['todas']['masa'])}),"
          f" horas 10-11 {pct(out['10-11']['acierto'])} (modelo {pct(out['10-11']['masa'])}); por hora: "
          + " ".join(f"{k[1:]}:{v['acierto']*100:.0f}" for k, v in out.items() if k.startswith("h")))
    return out


def todas_horas(nombre, d, sel, rng):
    """D5 (contexto): las mismas reglas en todas las horas."""
    P, y, fe = d["P"][sel], d["y"][sel], d["fecha"][sel]
    sub = {k: v[sel] for k, v in d.items() if isinstance(v, np.ndarray) and len(v) == len(d["y"])}
    base = medidas(P, y, np.zeros((len(y), K), bool))
    out = {"n": int(len(y)), "actual": float(base["t15"].mean())}
    for nom, reg, um in [("HOY", ("HOY",), None), ("HERM", ("HERM",), None), ("FRIO4", ("FRIO",), 4),
                         ("HOY+HERM+FRIO4", ("HOY", "HERM", "FRIO"), 4)]:
        m = medidas(P, y, mascara(sub, reg, um))
        dv, (_, ic95) = boot(m["t15"] - base["t15"], fe, rng)
        out[nom] = {"t15": float(m["t15"].mean()), "dif": dv, "ic95": ic95}
    print(f"  D5 {nombre}, todas las horas ({len(y)} sorteos): actual {pct(out['actual'])}; "
          + "; ".join(f"{k} {v['dif']*100:+.2f} pp [{v['ic95'][0]*100:+.2f}; {v['ic95'][1]*100:+.2f}]" for k, v in out.items() if k not in ("n", "actual")))
    return out


def elegir(res_juego):
    """H2: la de mayor Δ en desarrollo; empates: menos reglas, luego umbral 4."""
    v = res_juego["variantes"]
    clave = lambda k: (round(v[k]["dif"], 12), -len(v[k]["reglas"]), -(abs((v[k]["umbral"] or 4) - 4)))
    mejor = max(v, key=clave)
    return mejor if v[mejor]["dif"] > 0 else None


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "dev"
    sha = hashlib.sha256(open(PRE, "rb").read()).hexdigest()
    print("modo", modo, "| PREREGISTRO.md sha256", sha)
    rng = np.random.default_rng(20261001)
    juegos = {"LA": ("Lotto Activo", juego_la()), "RD": ("RD Internacional", juego_rd())}
    res = {"modo": modo, "sha_prereg": sha}
    if modo == "dev":
        for j, (nombre, d) in juegos.items():
            res[j] = analiza(nombre, d, d["dev"], rng)
            res[j]["D3"] = calibracion(nombre, d, d["dev"])
            res[j]["D5"] = todas_horas(nombre, d, d["dev"], rng)
            res[j]["elegida"] = elegir(res[j])
            print(f"  ELEGIDA para H2 ({j}): {res[j]['elegida']}")
    else:
        if os.path.exists(REGISTRO):
            sys.exit("La prueba ciega ya se corrió (registro.jsonl). No se repite.")
        dev = json.load(open(os.path.join(AQUI, "resultados_dev.json"), encoding="utf-8"))
        for j, (nombre, d) in juegos.items():
            sel = (d["fecha"] >= CIEGA[0]) & (d["fecha"] <= CIEGA[1])
            el = dev[j]["elegida"]
            el = el if el != "HOY+HERM+FRIO4" else None
            res[j] = analiza(nombre, d, sel, rng, elegida=el or "HOY+HERM+FRIO4")
            res[j]["D3"] = calibracion(nombre, d, sel)
            res[j]["D5"] = todas_horas(nombre, d, sel, rng)
            ver = {}
            for h, v in [("H1", "HOY+HERM+FRIO4"), ("H2", el)]:
                if v is None:
                    ver[h] = {"variante": None, "veredicto": "no se prueba (en desarrollo nada mejoró o es la misma que H1)"}
                    continue
                x = res[j]["variantes"][v]
                ver[h] = {"variante": v, "dif": x["dif"], "ic9875": x["ic9875"], "veredicto": "PASA" if x["ic9875"][0] > 0 else "NO PASA"}
            res[j]["veredictos"] = ver
            for h, x in ver.items():
                print(f"  {j} {h}: {x['variante']} -> {x['veredicto']}" + (f"  Δ {x['dif']*100:+.2f} pp [{x['ic9875'][0]*100:+.2f}; {x['ic9875'][1]*100:+.2f}]" if "dif" in x else ""))
    salida = os.path.join(AQUI, f"resultados_{modo}.json")
    json.dump(res, open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    if modo == "ciega":
        with open(REGISTRO, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "sha_prereg": sha,
                                 "veredictos": {j: res[j]["veredictos"] for j in ("LA", "RD")}}, ensure_ascii=False, default=float) + "\n")


if __name__ == "__main__":
    main()
