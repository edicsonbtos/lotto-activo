# -*- coding: utf-8 -*-
"""r2_a03_rd_produccion: ag12 V1 + RD Internacional (h:30). Delta frente a ag12 V1 en desarrollo [2000, 9357).

Uso: PYTHONIOENCODING=utf-8 python motor_nuevo/r2_a03_rd_produccion/experimento.py
Variables (fila t = LA h:00 del día d): L1 = [i == RD (h-1):30 mismo día], L3 = [i == RD (h-2):30 mismo día],
PF = log1p(# días hace 1-30 con RD (h'-1):30 = a -> LA h':00 = i), PR = log1p(# días hace 1-30 con LA h':00 = i -> RD h':30 = a),
a = RD (h-1):30. Solo RD anterior a la fila t (misma jornada, horas previas) y pares de jornadas anteriores.
"""
import csv, io, json, os, sys, time
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI); WT = os.path.dirname(MN)
sys.path.insert(0, MN); sys.path.insert(0, os.path.join(MN, "ag12_transiciones"))
sys.path.insert(0, os.path.join(MN, "ag02_residuo_boost")); sys.path.insert(0, os.path.join(WT, "herramientas"))
import arnes as A  # noqa: E402
import lotto_eval as LE  # noqa: E402
from rdint.datos import ANIMALES, sin_acentos, RD_CSV  # noqa: E402
import importlib.util as _iu  # noqa: E402
_sp = _iu.spec_from_file_location("exp_ag02", os.path.join(MN, "ag02_residuo_boost", "experimento.py"))
E2 = _iu.module_from_spec(_sp); _sp.loader.exec_module(E2)

LAM = 30.0
NOMBRES_RD = ["L1_rd_h1", "L3_rd_h2", "PF_par_rdla_1a30", "PR_par_lard_1a30"]
K = 38


def cargar_rd(fecha_max):
    """{(fecha, h): idx} de RD Int h:30 (h = 0 para 8:30). Mismo parseo que rdint.datos.cargar()."""
    rd = {}
    with io.open(RD_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cod = ANIMALES.get(sin_acentos(r["animal"]))
            h = int(r["hora"][:2]) - 8
            if cod is None or not r["hora"].endswith(":30") or not (0 <= h <= 11) or r["fecha"] > fecha_max:
                continue
            rd[(r["fecha"], h)] = LE.IDX[cod]
    return rd


def rasgos_rd(D, desde, rd):
    fecha = list(D.fecha); hora = np.asarray(D.hora); seq = np.asarray(D.seq)
    jor = np.array([(date.fromisoformat(f) - date(2020, 1, 1)).days for f in fecha])
    la = {(f, int(h)): int(s) for f, h, s in zip(fecha, hora, seq)}
    # historias de pares por día (se agregan al terminar cada día => sólo jornadas anteriores)
    fwd = {}   # (a_rd, i_la) -> lista de jornadas con RD (h'-1):30 = a -> LA h':00 = i
    rev = {}   # (a_rd, i_la) -> lista de jornadas con LA h':00 = i -> RD h':30 = a
    n = len(seq)
    X = np.zeros((n - desde, K, 4), np.float32)
    dias = sorted(set(fecha))
    idx_por_dia = {}
    for t, f in enumerate(fecha):
        idx_por_dia.setdefault(f, []).append(t)
    for f in dias:
        jd = (date.fromisoformat(f) - date(2020, 1, 1)).days
        for t in idx_por_dia[f]:
            if t < desde:
                continue
            h = int(hora[t]); x = X[t - desde]
            a = rd.get((f, h - 1)) if h >= 1 else None
            if a is not None:
                x[a, 0] = 1
                for i in range(K):
                    c = sum(1 for d0 in fwd.get((a, i), ()) if 1 <= jd - d0 <= 30)
                    if c: x[i, 2] = np.log1p(c)
                    c = sum(1 for d0 in rev.get((a, i), ()) if 1 <= jd - d0 <= 30)
                    if c: x[i, 3] = np.log1p(c)
            b = rd.get((f, h - 2)) if h >= 2 else None
            if b is not None:
                x[b, 1] = 1
        # al cierre del día: registrar pares de este día
        for h in range(12):
            a = rd.get((f, h - 1)) if h >= 1 else None
            i = la.get((f, h))
            if a is not None and i is not None:
                fwd.setdefault((a, i), []).append(jd)
            j = la.get((f, h)); a2 = rd.get((f, h))
            if j is not None and a2 is not None:
                rev.setdefault((a2, j), []).append(jd)
    return X


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)                       # nada >= 9357
    Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
    Pv1 = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy")); Pv1 = Pv1 / Pv1.sum(1, keepdims=True)
    LV1 = np.log(np.clip(Pv1, 1e-12, None)); LPE = np.log(np.clip(Pens, 1e-12, None))
    rd = cargar_rd(D.fecha[-1])
    Xr = rasgos_rd(D, A.W, rd).astype(np.float64)
    dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
    fechas = np.asarray(D.fecha[A.W:A.CORTE])
    print(f"filas {len(y)} · con RD (h-1):30: {int((Xr[:, :, 0].sum(1) > 0).sum())} · con RD (h-2):30: "
          f"{int((Xr[:, :, 1].sum(1) > 0).sum())}", flush=True)
    res, out = {}, []

    def rep(nombre, P):
        r = A.evaluar(P, P_ref=Pv1, y=y); res[nombre] = r
        f = lambda q: f"{q[0]:+.2f} [{q[1]:+.2f}, {q[2]:+.2f}]"
        s = "\n".join([f"== {nombre} (frente a ag12 V1, n={r['n']}) ==",
                       f"mbits: cand {r['mbits_cand']:+.2f} · ag12V1 {r['mbits_ens']:+.2f}",
                       f"Delta {f(r['delta_mbits'])} · mitad1 {f(r['delta_mitad1'])} · mitad2 {f(r['delta_mitad2'])}",
                       f"Top-3 {r['top3_cand']*100:.2f}% vs {r['top3_ens']*100:.2f}% · Top-5 {r['top5_cand']*100:.2f}% vs "
                       f"{r['top5_ens']*100:.2f}% · Top-15 {r['top15_cand']*100:.2f}% vs {r['top15_ens']*100:.2f}%",
                       f"Top-5 escalonado/ficha {r['ret_t5_cand']*100:+.2f}% vs {r['ret_t5_ens']*100:+.2f}% · delta {f(r['delta_ret_t5'])}",
                       f"PASA BARRA DEV: {r['pasa_barra_dev']}"])
        print(s, flush=True); out.append(s)

    def cf(X, off):
        P, pars = E2.cross_fit(lambda tr: E2.ajustar_lineal(X[tr], off[tr], y[tr], LAM),
                               lambda w, te: E2.predecir_lineal(w, X[te], off[te]), blo)
        return P, np.array(pars)

    def fw(X, off, Pbase):
        P = E2.forward(lambda tr: E2.ajustar_lineal(X[tr], off[tr], y[tr], LAM),
                       lambda w, te: E2.predecir_lineal(w, X[te], off[te]), blo)
        P[blo == 0] = Pbase[blo == 0]
        return P

    # control
    rep("control_ag12V1_contra_si_mismo", Pv1)
    # VA primaria
    PA, wA = cf(Xr, LV1); rep("VA_offsetV1_L1_L3_PF_PR", PA)
    res["VA_pesos"] = {nm: [float(v) for v in wA[:, i]] for i, nm in enumerate(NOMBRES_RD)}
    for i, nm in enumerate(NOMBRES_RD):
        print(f"  {nm:20s} {wA[:, i].mean():+.3f} [{wA[:, i].min():+.3f}, {wA[:, i].max():+.3f}]")
    PAf = fw(Xr, LV1, Pv1); rep("VA_forward_informativo", PAf)
    np.save(os.path.join(AQUI, "P_VA.npy"), PA)
    # VB
    PB, wB = cf(Xr[:, :, :2], LV1); rep("VB_offsetV1_L1_L3", PB)
    res["VB_pesos"] = {nm: [float(v) for v in wB[:, i]] for i, nm in enumerate(NOMBRES_RD[:2])}
    PBf = fw(Xr[:, :, :2], LV1, Pv1); rep("VB_forward_informativo", PBf)
    # VC: reajuste conjunto 33 + 4 desde el ensamble
    import rasgos12 as R12
    X12, _ = R12.construir(D, A.W)
    XC = np.concatenate([X12.astype(np.float64), Xr], axis=2); del X12
    PC, wC = cf(XC, LPE); rep("VC_conjunto_37var_desde_ensamble", PC)
    res["VC_pesos_rd"] = {nm: [float(v) for v in wC[:, 33 + i]] for i, nm in enumerate(NOMBRES_RD)}
    PCf = fw(XC, LPE, Pens); rep("VC_forward_informativo_(bloque0=ensamble)", PCf)
    # comparación justa del forward de VC: contra el forward de ag12 (33 var, mismo procedimiento)
    P12f = fw(XC[:, :, :33], LPE, Pens)
    d = A.mbits_fila(PCf, y) - A.mbits_fila(P12f, y); h = len(d) // 2
    res["VC_forward_menos_ag12_forward"] = {"todo": A.ic_bloques(d, dia), "mitad1": A.ic_bloques(d[:h], dia[:h]),
                                            "mitad2": A.ic_bloques(d[h:], dia[h:]),
                                            "sin_bloque0": A.ic_bloques(d[blo > 0], dia[blo > 0])}
    print("VC forward - ag12 forward:", res["VC_forward_menos_ag12_forward"], flush=True)
    del XC
    # diagnósticos: O/E de cada rasgo indicador frente a ag12 V1, antes/después de 2025-07-01
    diag = {}
    for nm, col in [("L1", 0), ("L3", 1)]:
        m = Xr[:, :, col] > 0
        for tramo, sel in [("antes_2025-07-01", fechas < "2025-07-01"), ("desde_2025-07-01", fechas >= "2025-07-01"),
                           ("todo", np.ones(len(y), bool))]:
            o = int(m[np.arange(len(y)), y][sel].sum()); e = float((Pv1 * m)[sel].sum())
            diag[f"{nm}_{tramo}"] = {"obs": o, "esp": round(e, 1), "OE": round(o / e, 3), "z": round((o - e) / np.sqrt(e), 2)}
            print(f"diag {nm} {tramo:18s} obs {o:4d} esp {e:6.1f} O/E {o/e:.3f} z {(o-e)/np.sqrt(e):+.2f}")
    for nm, col in [("PF", 2), ("PR", 3)]:
        m = Xr[:, :, col] > 0
        o = int(m[np.arange(len(y)), y].sum()); e = float((Pv1 * m).sum())
        diag[f"{nm}_todo"] = {"obs": o, "esp": round(e, 1), "OE": round(o / e, 3), "z": round((o - e) / np.sqrt(e), 2)}
        print(f"diag {nm} todo               obs {o:4d} esp {e:6.1f} O/E {o/e:.3f} z {(o-e)/np.sqrt(e):+.2f}")
    # delta de VA por tramo H4
    d = A.mbits_fila(PA, y) - A.mbits_fila(Pv1, y)
    for tramo, sel in [("antes_2025-07-01", fechas < "2025-07-01"), ("desde_2025-07-01", fechas >= "2025-07-01")]:
        diag[f"VA_delta_{tramo}"] = A.ic_bloques(d[sel], dia[sel])
        print(f"VA delta {tramo}: {diag[f'VA_delta_{tramo}']}")
    res["diagnostico"] = diag
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1)
    open(os.path.join(AQUI, "consola.txt"), "w", encoding="utf-8").write("\n\n".join(out) + "\n")
    print(f"[{time.time()-t0:.0f} s]")


if __name__ == "__main__":
    main()
