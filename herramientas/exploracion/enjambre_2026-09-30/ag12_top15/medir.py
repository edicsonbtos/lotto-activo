# -*- coding: utf-8 -*-
"""Camino 2 (PREREGISTRO.md de esta carpeta): (a) tamaño de muestra para la sombra de ag12,
(b) regla de cambio RD (h-1):30 -> Top-15 de LA h:00, (c) ag12 en 2026-04-01..2026-09-16 (réplica).
Solo lee: historial.txt, rdint_hist.csv, cachés ya calculadas. No toca nada de producción.
Uso: python medir.py  -> resultados.json + salida en consola. La confirmación (b) se corre una vez."""
import csv, io, json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HERR = os.path.join(RAIZ, "herramientas")
MOTOR = os.path.join(os.path.dirname(RAIZ), "lotto-activo-motor", "motor_nuevo", "reciente")
sys.path.insert(0, HERR); sys.path.insert(0, os.path.join(HERR, "rdint"))
import lotto_eval as LE
from datos import ANIMALES, sin_acentos

REG = os.path.join(AQUI, "registro.jsonl")
PAGO = 30
F_POND = np.array([0] + [3, 3, 3, 2, 2] + [1] * 10 + [0] * 23, float)   # por puesto 1..38
F_PLANO = np.array([0] + [1] * 15 + [0] * 23, float)
F_T5 = np.array([0] + [2, 2, 2, 1, 1] + [0] * 33, float)
DEV = ("2024-03-01", "2025-06-30")
CONF = ("2026-04-01", "2026-09-16")


def ret(f, pos):
    return (PAGO * f[pos] - f.sum()) / f.sum()


def ic(x, dia, reps=2000, semilla=20260930, alfa=0.05):
    x = np.asarray(x, float)
    _, inv = np.unique(dia, return_inverse=True)
    s = np.bincount(inv, weights=x); c = np.bincount(inv)
    rng = np.random.default_rng(semilla)
    B = rng.integers(0, len(s), size=(reps, len(s)))
    m = s[B].sum(1) / c[B].sum(1)
    return [float(x.mean()), float(np.percentile(m, 100 * alfa / 2)), float(np.percentile(m, 100 * (1 - alfa / 2))),
            float(m.std())]


def mbits(P, y):
    P = np.clip(P, 1e-9, None); P = P / P.sum(1, keepdims=True)
    return 1000 * np.log2(P[np.arange(len(y)), y] * 38)


def main():
    hist = os.path.join(RAIZ, "historial.txt")
    la = LE.cargar(hist)
    n = len(la)
    # fechas corregidas en memoria (mismo orden que LE.cargar)
    cambios = {c["antes"]: c["despues"] for c in
               json.load(open(os.path.join(HERR, "correccion_historial_2026-09-29.json"), encoding="utf-8"))["cambios"]}
    tocados = {k.split()[0] for k in cambios} | {v.split()[0] for v in cambios.values()}
    filas = []
    for ln in open(hist, encoding="utf-8"):
        p = ln.split()
        if len(p) == 3 and p[2] in LE.IDX:
            filas.append((p[0], int(p[1]), LE.IDX[p[2]], cambios.get(" ".join(p), " ".join(p)).split()[0]))
    filas.sort(key=lambda r: (r[0], r[1]))
    assert len(filas) == n and all(a[2] == b for a, b in zip(filas, la.seq))
    fecha = np.array([r[3] for r in filas]); hora = np.asarray(la.hora); y_all = np.asarray(la.seq)
    excl = np.array([f in tocados or g in tocados for f, g in zip(fecha, la.fecha)])

    # P del ensamble 2000..n y ag12 9357..n
    z = np.load(os.path.join(HERR, "exploracion", "calor_cache.npz"))
    assert np.array_equal(z["y"].astype(int), y_all[2000:9357])
    Pe = np.vstack([z["P"].astype(np.float32), np.load(os.path.join(MOTOR, "P_ens_reciente.npy")).astype(np.float32)])
    Pa = np.load(os.path.join(MOTOR, "P_ag12_V1.npy")).astype(np.float32)
    assert len(Pe) == n - 2000 and len(Pa) == n - 9357
    idx = np.arange(2000, n)
    y = y_all[idx]; fe = fecha[idx]; ho = hora[idx]; ex = excl[idx]

    rd = {}
    with io.open(os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            c = ANIMALES.get(sin_acentos(r["animal"]))
            if c is not None:
                rd[(r["fecha"], int(r["hora"][:2]) - 8)] = LE.IDX[c]

    def evaluar(P, sel):
        """Puestos sin cambio, con regla Top-5 (la viva) y con regla Top-15, más contadores."""
        orden = LE.rankings(P[sel])[:, :16]
        yy = y[sel]; f_ = fe[sel]; h_ = ho[sel]
        m = len(yy)
        pos0 = np.full(m, 38); pos5 = np.full(m, 38); pos15 = np.full(m, 38)
        cambio = np.zeros(m, bool); gana_rd = np.zeros(m, bool); gana16 = np.zeros(m, bool); hay_rd = np.zeros(m, bool)
        for t in range(m):
            o = [int(a) for a in orden[t]]
            r = rd.get((f_[t], int(h_[t]) - 1)) if h_[t] > 0 else None
            hay_rd[t] = r is not None
            o5 = o[:16]
            if r is not None and r in o[:5]:
                o5 = [a for a in o[:6] if a != r] + [r] + o[6:16]
            o15 = o[:15]
            if r is not None and r in o[:15]:
                o15 = [a for a in o if a != r][:15]
                cambio[t] = True; gana_rd[t] = yy[t] == r; gana16[t] = yy[t] == o[15]
            for arr, lista in ((pos0, o), (pos5, o5), (pos15, o15)):
                if yy[t] in lista[:15]:
                    arr[t] = lista.index(yy[t]) + 1
        return dict(pos0=pos0, pos5=pos5, pos15=pos15, cambio=cambio, gana_rd=gana_rd, gana16=gana16, hay_rd=hay_rd)

    out = {}

    def regla(nombre, P, a, b):
        sel = (fe >= a) & (fe <= b) & ~ex
        e = evaluar(P, sel); dia = fe[sel]; h = ho[sel]
        dp = ret(F_POND, e["pos15"]) - ret(F_POND, e["pos0"])
        dl = ret(F_PLANO, e["pos15"]) - ret(F_PLANO, e["pos0"])
        r = {"ventana": [a, b], "n": int(sel.sum()), "con_rd": int(e["hay_rd"].sum()), "cambios": int(e["cambio"].sum()),
             "gano_el_de_rd": int(e["gana_rd"].sum()), "gano_el_16": int(e["gana16"].sum()),
             "top15_sin": float((e["pos0"] <= 15).mean()), "top15_con": float((e["pos15"] <= 15).mean()),
             "pond_sin": float(ret(F_POND, e["pos0"]).mean()), "pond_con": float(ret(F_POND, e["pos15"]).mean()),
             "plano_sin": float(ret(F_PLANO, e["pos0"]).mean()), "plano_con": float(ret(F_PLANO, e["pos15"]).mean()),
             "d_pond_ic95": ic(dp * 100, dia)[:3], "d_plano_ic95": ic(dl * 100, dia)[:3],
             "t5_escalonado_con_regla_viva": float(ret(F_T5, e["pos5"]).mean()),
             "por_hora_d_pond_pp": {int(k): [int((h == k).sum()), round(float(dp[h == k].mean() * 100), 2)]
                                    for k in np.unique(h)}}
        out[nombre] = r
        print(nombre, json.dumps(r, ensure_ascii=False), flush=True)
        return r, e, sel

    # (b) desarrollo
    rdev, _, _ = regla("b_desarrollo", Pe, *DEV)
    if rdev["d_pond_ic95"][0] <= 0:
        out["b_veredicto"] = "NO PASA (desarrollo <= 0; no se mira la confirmación)"
    else:
        if os.path.exists(REG):
            sys.exit("La confirmación (b) ya se corrió (registro.jsonl). No se repite.")
        rc, ec, selc = regla("b_confirmacion", Pe, *CONF)
        lo = rc["d_pond_ic95"][1]
        out["b_veredicto"] = "PASA" if rc["d_pond_ic95"][0] > 0 and lo > 0 else "NO PASA"

        # (c) réplica ag12 en la misma ventana
        sel9 = selc.copy(); sel9[:9357 - 2000] = False
        assert sel9.sum() == selc.sum()
        Pa_full = np.zeros_like(Pe); Pa_full[9357 - 2000:] = Pa
        ra, ea, _ = regla("c_ag12_con_regla15", Pa_full, *CONF)
        yy = y[selc]; dia = fe[selc]
        mb_e = mbits(Pe[selc].astype(float), yy); mb_a = mbits(Pa_full[selc].astype(float), yy)
        pe_rank = LE.rankings(Pe[selc]); pa_rank = LE.rankings(Pa_full[selc])
        pe = np.argmax(pe_rank == yy[:, None], 1) + 1; pa = np.argmax(pa_rank == yy[:, None], 1) + 1
        out["c_replica_ag12"] = {
            "n": int(len(yy)), "mbits_ens": float(mb_e.mean()), "mbits_ag12": float(mb_a.mean()),
            "d_mbits_ic95": ic(mb_a - mb_e, dia)[:3],
            "top3": [float((pe <= 3).mean()), float((pa <= 3).mean())],
            "top5": [float((pe <= 5).mean()), float((pa <= 5).mean())],
            "top15": [float((pe <= 15).mean()), float((pa <= 15).mean())],
            "ret_t5_esc": [float(ret(F_T5, pe).mean()), float(ret(F_T5, pa).mean())],
            "d_ret_t5_ic95_pp": ic((ret(F_T5, pa) - ret(F_T5, pe)) * 100, dia)[:3],
            "ret_t15_pond": [float(ret(F_POND, pe).mean()), float(ret(F_POND, pa).mean())],
            "d_ret_pond_ic95_pp": ic((ret(F_POND, pa) - ret(F_POND, pe)) * 100, dia)[:3],
            "ret_t15_plano": [float(ret(F_PLANO, pe).mean()), float(ret(F_PLANO, pa).mean())],
            "ag12_mas_regla15_pond": ra["pond_con"], "ens_mas_regla15_pond": rc["pond_con"]}
        print("c_replica_ag12", json.dumps(out["c_replica_ag12"], ensure_ascii=False), flush=True)
        with open(REG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"corrida": "b_confirmacion+c", "b": rc, "veredicto": out["b_veredicto"]}) + "\n")

    # (a) tamaño de muestra: varianza de Δ mbits en la 2.ª ciega (filas 9357.., sin días tocados)
    s9 = np.zeros(len(y), bool); s9[9357 - 2000:] = True; s9 &= ~ex
    Pa_full = np.zeros_like(Pe); Pa_full[9357 - 2000:] = Pa
    d = mbits(Pa_full[s9].astype(float), y[s9]) - mbits(Pe[s9].astype(float), y[s9])
    sd_fila = float(d.std(ddof=1)); m_, lo_, hi_, se_b = ic(d, fe[s9], reps=4000)
    sd_ef = max(sd_fila, se_b * np.sqrt(len(d)))
    za, zb = 1.6449, 0.8416
    N = {f"efecto_{e_}": int(np.ceil(((za + zb) * sd_ef / e_) ** 2)) for e_ in (19.4, 15.0, 10.0)}
    out["a_tamano"] = {"n_ciega": int(len(d)), "d_mbits_ciega_sin_dias_tocados": m_, "sd_por_sorteo": sd_fila,
                       "sd_efectiva_bloques": float(se_b * np.sqrt(len(d))), "N_80pct_unilateral_5pct": N}
    print("a_tamano", json.dumps(out["a_tamano"]), flush=True)
    json.dump(out, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
