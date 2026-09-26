# -*- coding: utf-8 -*-
"""Pruebas ciegas 3 (RD Internacional) y 4 (LARD) de ag12 V0 con pesos congelados. Ver PREREGISTRO_CIEGAS34.md.
Una sola corrida: queda en registro_ciegas34.jsonl. Bonferroni k=2.
  python prueba_ciegas34.py --ensayo   -> mecánica sobre secuencias al azar (no toca datos reales ni registra)"""
import csv, hashlib, io, json, os, subprocess, sys
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
MN = os.path.dirname(AQUI); WT = os.path.dirname(MN)
sys.path.insert(0, os.path.join(WT, "herramientas")); sys.path.insert(0, os.path.join(MN, "ag12_transiciones"))
import lotto_eval as LE  # noqa: E402
import rasgos12 as R  # noqa: E402

KBONF, NBOOT, SEMILLA = 2, 4000, 20260926
RAZON_HOY = 0.38
DESDE_RD, JORNADA_LARD = 2000, 31
REG = os.path.join(AQUI, "registro_ciegas34.jsonl")
OFICIAL = os.path.join(WT, "datos_multiloteria", "oficial_multi.csv")


def pesos_v0():
    cfg = json.load(open(os.path.join(MN, "ag12_transiciones", "parametros_V0.json"), encoding="utf-8"))
    w = np.array(cfg["w"], float)
    assert cfg["nombres"][-6:] == R.NUEVOS and np.all(w[:-6] == 0)
    return w[-6:]


def datos_de(filas):
    filas = sorted(set(filas), key=lambda r: (r[0], r[1]))
    d0 = date.fromisoformat(filas[0][0]); f = [r[0] for r in filas]
    return LE.Datos(np.array([r[2] for r in filas]), np.array([r[1] for r in filas]),
                    np.array([date.fromisoformat(x).weekday() for x in f]),
                    np.array([(date.fromisoformat(x) - d0).days for x in f]), f)


def cargar_rd():
    from rdint import datos as DT
    return DT.cargar()[0]


def cargar_lard():
    filas = []
    with io.open(OFICIAL, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["juego"] == "3" and r["codigo"] in LE.IDX:
                filas.append((r["fecha"], int(r["hora"][:2]) - 8, LE.IDX[r["codigo"]]))
    return datos_de(filas)


def base_regla(D, desde):
    """P ∝ 0,38 si el animal ya salió hoy, 1 si no (sin ajuste)."""
    seq = np.asarray(D.seq); dia = np.asarray(D.dia)
    P = np.ones((len(seq) - desde, LE.K))
    hoy = np.zeros(LE.K, int)
    for t in range(len(seq)):
        if t == 0 or dia[t] != dia[t - 1]:
            hoy[:] = 0
        if t >= desde:
            P[t - desde] = np.where(hoy > 0, RAZON_HOY, 1.0)
        hoy[seq[t]] += 1
    return P / P.sum(1, keepdims=True)


def base_secuencia(D, desde):
    m = LE.cargar_modelo(os.path.join(WT, "herramientas", "modelos", "secuencia_v3.py"))
    return LE.normalizar(m.predecir(D, desde))


def evaluar(nombre, D, desde, Pb, w):
    X = R.transiciones(D, desde).astype(float)          # (n-desde, 38, 6), fila t usa solo seq[:t]
    z = np.log(np.clip(Pb, 1e-12, None)) + X @ w
    z -= z.max(1, keepdims=True); Q = np.exp(z); Q /= Q.sum(1, keepdims=True)
    y = np.asarray(D.seq[desde:]); dia = np.asarray(D.dia[desde:]); r = np.arange(len(y))
    d = 1000 * (np.log2(Q[r, y]) - np.log2(Pb[r, y]))
    _, g = np.unique(dia, return_inverse=True); G = g.max() + 1
    suma = np.bincount(g, d, G); cuenta = np.bincount(g, None, G)
    rng = np.random.default_rng(SEMILLA); boots = np.empty(NBOOT)
    for b in range(NBOOT):
        c = np.bincount(rng.integers(0, G, G), minlength=G)
        boots[b] = (c * suma).sum() / (c * cuenta).sum()
    a = 0.05 / KBONF
    lo, hi = np.quantile(boots, [a / 2, 1 - a / 2])
    # O/E del par s1→i de hace 2-7 jornadas (rasgo T2 > 0) frente a la base
    I = X[:, :, 1] > 0
    masa = (I * Pb).sum(1)
    obs = I[r, y].sum(); esp = masa.sum(); var = (masa * (1 - masa)).sum()

    def topn(P, n):
        return float(np.mean((np.argsort(-P, 1)[:, :n] == y[:, None]).any(1)))
    res = dict(prueba=nombre, n=int(len(y)), dias=int(G), desde_fecha=D.fecha[desde], hasta_fecha=D.fecha[-1],
               mbits_base=float(1000 * np.mean(np.log2(Pb[r, y] * LE.K))),
               delta_mbits=float(d.mean()), ic=[float(lo), float(hi)], pasa=bool(lo > 0),
               oe_s1i_2a7=float(obs / esp), z_s1i_2a7=float((obs - esp) / np.sqrt(var)), obs=int(obs), esp=float(esp),
               top5_base=topn(Pb, 5), top5_ag12=topn(Q, 5), top15_base=topn(Pb, 15), top15_ag12=topn(Q, 15))
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)
    return res


def sha(ruta):
    return hashlib.sha256(open(ruta, "rb").read()).hexdigest()


def main():
    w = pesos_v0()
    if "--ensayo" in sys.argv:
        rng = np.random.default_rng(1)
        for nombre, por_dia, dias in [("ensayo_rd", 12, 400), ("ensayo_lard", 14, 200)]:
            filas = [(str(date.fromordinal(date(2024, 1, 1).toordinal() + k)), h, int(rng.integers(0, 38)))
                     for k in range(dias) for h in range(por_dia)]
            D = datos_de(filas); desde = 30 * por_dia
            evaluar(nombre, D, desde, base_regla(D, desde), w)
        return
    if os.path.exists(REG):
        sys.exit("registro_ciegas34.jsonl ya existe: la prueba ya se corrió una vez. No se repite.")
    commit = subprocess.run(["git", "-C", WT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    sucio = subprocess.run(["git", "-C", WT, "status", "--porcelain", "motor_nuevo/ciegas34", "motor_nuevo/ag12_transiciones"],
                           capture_output=True, text=True).stdout.strip()
    assert not sucio, "hay cambios sin commit en el prerregistro o en ag12:\n" + sucio
    out = []
    rd = cargar_rd()
    out.append(evaluar("3_RD_Internacional", rd, DESDE_RD, base_secuencia(rd, DESDE_RD), w))
    lard = cargar_lard()
    _, dn = np.unique(lard.dia, return_inverse=True)
    desde = int(np.flatnonzero(dn == JORNADA_LARD - 1)[0])
    out.append(evaluar("4_LARD", lard, desde, base_regla(lard, desde), w))
    reg = dict(commit=commit, sha_rd=sha(os.path.join(WT, "datos_multiloteria", "rdint_hist.csv")), sha_oficial=sha(OFICIAL),
               resultados=out)
    with open(REG, "w", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    print("VEREDICTO:", {r["prueba"]: ("PASA" if r["pasa"] else "NO PASA") for r in out})


if __name__ == "__main__":
    main()
