# -*- coding: utf-8 -*-
"""r2_a08_comodin: ¿la lista negra de pares del operador es COMPARTIDA entre LA y RD Internacional?

LA h:00 evita s1->i si ese par salió consecutivo DENTRO de RD (RD h':30 -> RD (h'+1):30) en jornadas recientes.
Reajuste completo (offset log P_ens + 33 variables de ag12 V1 + nuevas), lambda=30, los mismos 5 bloques de jornada.
Delta frente a ag12 V1 (P_V1.npy) en desarrollo [2000, 9357). Nada >= 9357, nada del sellado.

Uso (desde la raíz del worktree lotto-activo-motor):
  PowerShell: $env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a08_comodin/experimento.py
"""
import csv, io, json, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI); WT = os.path.dirname(MN)
sys.path.insert(0, MN); sys.path.insert(0, os.path.join(MN, "ag12_transiciones"))
sys.path.insert(0, os.path.join(MN, "ag02_residuo_boost")); sys.path.insert(0, os.path.join(WT, "herramientas"))
import arnes as A  # noqa: E402
import lotto_eval as LE  # noqa: E402
from rdint.datos import ANIMALES, sin_acentos, RD_CSV  # noqa: E402
import rasgos12 as R12  # noqa: E402
import importlib.util as _iu  # noqa: E402
_sp = _iu.spec_from_file_location("exp_ag02", os.path.join(MN, "ag02_residuo_boost", "experimento.py"))
E2 = _iu.module_from_spec(_sp); _sp.loader.exec_module(E2)

LAM = 30.0
K = 38
VENT = [(1, 1), (2, 7), (8, 30), (31, 90)]   # la 4.ª solo es placebo del diagnóstico
NOMBRES_RD = ["RF1_rd_s1i_1d", "RF2_rd_s1i_2a7", "RF3_rd_s1i_8a30", "RR1_rd_is1_1d", "RR2_rd_is1_2a7", "RR3_rd_is1_8a30"]


def cargar_rd(fecha_max):
    """{(fecha, h): idx} de RD Int h:30 (h = 0 para 8:30), solo fechas <= fecha_max."""
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
    """Conteos CRUDOS (n-desde, 38, 8): [s1->i en RD por 4 ventanas, i->s1 en RD por 4 ventanas].
    Solo pares RD de jornadas anteriores (edad >= 1). s1 = LA anterior del mismo día."""
    seq = np.asarray(D.seq); fecha = list(D.fecha)
    _, dn = np.unique(np.asarray(D.dia), return_inverse=True)
    f2d = {}
    for f, d in zip(fecha, dn):
        f2d[f] = int(d)
    # pares consecutivos internos de RD, con la jornada LA de su fecha
    fwd, bwd = {}, {}
    npares = 0
    for (f, h), a in sorted(rd.items()):
        b = rd.get((f, h + 1))
        if b is None or f not in f2d:
            continue
        jd = f2d[f]
        fwd.setdefault(a, []).append((jd, b)); bwd.setdefault(b, []).append((jd, a)); npares += 1
    n = len(seq)
    X = np.zeros((n - desde, K, 2 * len(VENT)), np.float32)
    for t in range(max(desde, 1), n):
        if dn[t - 1] != dn[t]:
            continue
        s1 = int(seq[t - 1]); d = int(dn[t]); x = X[t - desde]
        for (jd, b) in fwd.get(s1, ()):
            age = d - jd
            for v, (lo, hi) in enumerate(VENT):
                if lo <= age <= hi: x[b, v] += 1
        for (jd, a) in bwd.get(s1, ()):
            age = d - jd
            for v, (lo, hi) in enumerate(VENT):
                if lo <= age <= hi: x[a, len(VENT) + v] += 1
    return X, npares


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)          # nada >= 9357 entra en memoria
    fecha_max = D.fecha[-1]
    Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
    LPE = np.log(np.clip(Pens, 1e-12, None))
    P_V1 = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy"))
    dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
    n = len(y); h = n // 2
    out, res = [], {"fecha_max_rd": fecha_max}

    def pr(s=""):
        print(s, flush=True); out.append(s)

    X33, _ = R12.construir(D, A.W); X33 = X33.astype(np.float64)
    rd = cargar_rd(fecha_max)
    XR, npares = rasgos_rd(D, A.W, rd)
    pr(f"RD: {len(rd)} sorteos h:30 hasta {fecha_max}; {npares} pares consecutivos internos RD")
    RAW = XR.astype(np.float64)                       # crudos, 8 columnas
    RD6 = np.log1p(RAW[:, :, [0, 1, 2, 4, 5, 6]])

    # ---------- diagnóstico descriptivo (O/E crudo) ----------
    pr("\n== Diagnóstico: O/E de las máscaras RD (obs = ganador en la máscara; esp = suma de P) ==")
    diag = {}
    for nom, c in [("RD s1->i", 0), ("RD i->s1", len(VENT))]:
        for v, (lo, hi) in enumerate(VENT):
            M = RAW[:, :, c + v] > 0
            fila = {}
            for base_nom, P in [("ens", Pens), ("V1", P_V1)]:
                for parte, sl in [("m1", slice(0, h)), ("m2", slice(h, n)), ("tot", slice(0, n))]:
                    Ms = M[sl]; o = int(Ms[np.arange(Ms.shape[0]), y[sl]].sum()); e = float((P[sl] * Ms).sum())
                    fila[f"{base_nom}_{parte}"] = (o, e, o / e if e else float("nan"), (o - e) / np.sqrt(e) if e else 0.0)
            diag[f"{nom} {lo}-{hi}"] = fila
            f = fila
            pr(f"{nom} hace {lo:>2}-{hi:<2} | vs ens tot {f['ens_tot'][0]:4d}/{f['ens_tot'][1]:7.1f} O/E {f['ens_tot'][2]:.3f} z {f['ens_tot'][3]:+.2f}"
               f" | vs V1 tot {f['V1_tot'][0]:4d}/{f['V1_tot'][1]:7.1f} O/E {f['V1_tot'][2]:.3f} z {f['V1_tot'][3]:+.2f}"
               f" · m1 {f['V1_m1'][2]:.3f} ({f['V1_m1'][3]:+.2f}) · m2 {f['V1_m2'][2]:.3f} ({f['V1_m2'][3]:+.2f})")
    res["diagnostico"] = diag

    # ---------- modelos ----------
    def cf(X):
        return E2.cross_fit(lambda tr: E2.ajustar_lineal(X[tr], LPE[tr], y[tr], LAM),
                            lambda w, te: E2.predecir_lineal(w, X[te], LPE[te]), blo)

    def fw(X):
        P = E2.forward(lambda tr: E2.ajustar_lineal(X[tr], LPE[tr], y[tr], LAM),
                       lambda w, te: E2.predecir_lineal(w, X[te], LPE[te]), blo)
        return P

    fmt = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f} ; {t[2]:+.2f}]"

    # control: reproducir P_V1
    Pc, _ = cf(X33)
    dif = float(np.abs(Pc - P_V1).max()); res["control_repro_P_V1_difmax"] = dif
    pr(f"\nControl: 33 variables reproducen P_V1, dif. máx. = {dif:.2e}")
    assert dif < 1e-6, "no se reproduce P_V1"
    Pf_V1 = fw(X33)
    m_fw = blo >= 1

    LA_raw = np.expm1(X33[:, :, 27:33])
    variantes = {
        "V1_primaria_33+6RD": np.concatenate([X33, RD6], axis=2),
        "V2_lista_unica_27+6agrupadas": np.concatenate([X33[:, :, :27], np.log1p(LA_raw + RAW[:, :, [0, 1, 2, 4, 5, 6]])], axis=2),
        "V3_parsimoniosa_33+2": np.concatenate([X33, np.log1p(RAW[:, :, 0:3].sum(2, keepdims=True)),
                                                np.log1p(RAW[:, :, 4:6].sum(2, keepdims=True))], axis=2),
    }
    nombres_extra = {"V1_primaria_33+6RD": NOMBRES_RD,
                     "V2_lista_unica_27+6agrupadas": ["G_s1i_1d", "G_s1i_2a7", "G_s1i_8a30", "G_is1_1d", "G_is1_2a7", "G_is1_8a30"],
                     "V3_parsimoniosa_33+2": ["RF_1a30", "RR_1a7"]}
    for nom, X in variantes.items():
        P, pars = cf(X)
        r = A.evaluar(P, P_ref=P_V1, y=y)
        Wb = np.array(pars)
        ncols = X.shape[2]
        nm_all = (R12.NOMBRES[:27] + nombres_extra[nom]) if nom.startswith("V2") else (R12.NOMBRES + nombres_extra[nom])
        pesos = {nm_all[i]: [float(Wb[:, i].mean()), float(Wb[:, i].min()), float(Wb[:, i].max())] for i in range(ncols)}
        Pf = fw(X)
        dfw = A.mbits_fila(Pf[m_fw], y[m_fw]) - A.mbits_fila(Pf_V1[m_fw], y[m_fw])
        fw_vs_fw = A.ic_bloques(dfw, dia[m_fw])
        hh = int(m_fw.sum()) // 2
        fw_m = (A.ic_bloques(dfw[:hh], dia[m_fw][:hh])[0], A.ic_bloques(dfw[hh:], dia[m_fw][hh:])[0])
        Pf2 = Pf.copy(); Pf2[blo == 0] = P_V1[blo == 0]
        r_fw = A.evaluar(Pf2, P_ref=P_V1, y=y)
        r["forward_vs_V1forward_b1a4"] = fw_vs_fw; r["forward_vs_V1forward_mitades"] = fw_m
        r["forward_vs_PV1_bloque0=PV1"] = r_fw["delta_mbits"]
        r["pesos"] = pesos
        r["pasa_barra_completa"] = bool(r["pasa_barra_dev"] and fw_vs_fw[0] > 0)
        res[nom] = r
        pr(f"\n== {nom} (Δ frente a ag12 V1; n={r['n']}) ==")
        pr(f"mbits cand {r['mbits_cand']:+.2f} · ag12 V1 {r['mbits_ens']:+.2f}")
        pr(f"Δ mbits {fmt(r['delta_mbits'])} · mitad1 {fmt(r['delta_mitad1'])} · mitad2 {fmt(r['delta_mitad2'])}")
        pr(f"Top-3 {r['top3_cand']*100:.2f}% vs {r['top3_ens']*100:.2f}% · Top-5 {r['top5_cand']*100:.2f}% vs {r['top5_ens']*100:.2f}%"
           f" · Top-15 {r['top15_cand']*100:.2f}% vs {r['top15_ens']*100:.2f}%")
        pr(f"Top-5 escalonado/ficha {r['ret_t5_cand']*100:+.2f}% vs {r['ret_t5_ens']*100:+.2f}% · Δ {fmt(r['delta_ret_t5'])}")
        pr(f"Forward (b1-4) frente a V1 forward: {fmt(fw_vs_fw)} · mitades {fw_m[0]:+.2f} / {fw_m[1]:+.2f}")
        pr(f"Forward frente a P_V1 (bloque 0 = P_V1): {fmt(r_fw['delta_mbits'])}")
        for k2 in nombres_extra[nom]:
            p = pesos[k2]; pr(f"  peso {k2:18s} {p[0]:+.3f} [{p[1]:+.3f} ; {p[2]:+.3f}]")
        if nom.startswith("V1"):
            for k2 in R12.NUEVOS:
                p = pesos[k2]; pr(f"  peso {k2:18s} {p[0]:+.3f} [{p[1]:+.3f} ; {p[2]:+.3f}]  (LA, ag12)")
        pr(f"PASA BARRA (dev + forward): {r['pasa_barra_completa']}")

    res["segundos"] = time.time() - t0
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    pr(f"\n[{res['segundos']:.0f} s]")
    open(os.path.join(AQUI, "consola.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
