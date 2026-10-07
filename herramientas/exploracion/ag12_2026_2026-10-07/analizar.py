# -*- coding: utf-8 -*-
"""Replica de estabilidad de ag12 en 2026 + tramo fresco (PREREGISTRO.md de esta carpeta). Solo lee; escribe en esta carpeta.
Requiere: P_ens_fresco.npy, P_ag12_V1_fresco.npy, P_ag12_V0_fresco.npy (calcular_fresco.py, filas 9357..12759), fresco_rd.csv.
Uso: python analizar.py  ->  resultados.json + salida_analizar.txt"""
import csv, io, json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
WT = os.path.join(os.path.dirname(RAIZ), "lotto-activo-motor")
MN = os.path.join(WT, "motor_nuevo")
HERR = os.path.join(RAIZ, "herramientas")
sys.path.insert(0, HERR); sys.path.insert(0, os.path.join(HERR, "rdint"))
import lotto_eval as LE
from datos import ANIMALES, sin_acentos

K, PAGO, D0 = 38, 30, 9357
SEED = 20261007
F_T5 = np.zeros(40); F_T5[1:6] = [2, 2, 2, 1, 1]
F_POND = np.zeros(40); F_POND[1:6] = [3, 3, 3, 2, 2]; F_POND[6:16] = 1
F_PLANO = np.zeros(40); F_PLANO[1:16] = 1
SAL = io.open(os.path.join(AQUI, "salida_analizar.txt"), "w", encoding="utf-8")


def pr(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); SAL.write(s + "\n"); SAL.flush()


# ------------------------------------------------------------------ datos
EXT = os.path.join(AQUI, "hist_ext.txt")
cambios = {c["antes"]: c["despues"] for c in
           json.load(open(os.path.join(HERR, "correccion_historial_2026-09-29.json"), encoding="utf-8"))["cambios"]}
tocados = {k.split()[0] for k in cambios} | {v.split()[0] for v in cambios.values()}
filas = []
for ln in open(EXT, encoding="utf-8"):
    p = ln.split()
    if len(p) == 3 and p[2] in LE.IDX:
        filas.append((p[0], int(p[1]), LE.IDX[p[2]], cambios.get(" ".join(p), " ".join(p)).split()[0]))
filas.sort(key=lambda r: (r[0], r[1]))
D = LE.cargar(EXT)
assert len(filas) == len(D) == 12760 and all(a[2] == b for a, b in zip(filas, D.seq))
fecha_all = np.array([r[3] for r in filas]); hora_all = np.asarray(D.hora); y_all = np.asarray(D.seq)
old_fecha = np.array(D.fecha)
excl_all = np.array([(f in tocados) or (g in tocados) for f, g in zip(fecha_all, old_fecha)])
sl = slice(D0, len(D))
y = y_all[sl]; fe = fecha_all[sl]; ho = hora_all[sl]; ex = excl_all[sl]
glob = np.arange(D0, len(D))
dow = np.array([__import__("datetime").date.fromisoformat(f).weekday() for f in fe])

Pe = np.load(os.path.join(AQUI, "P_ens_fresco.npy")).astype(float)
Pa1 = np.load(os.path.join(AQUI, "P_ag12_V1_fresco.npy")).astype(float)
Pa0 = np.load(os.path.join(AQUI, "P_ag12_V0_fresco.npy")).astype(float)
assert len(Pe) == len(y) == len(Pa1) == len(Pa0)
# control contra la 2.a ciega guardada
rec = os.path.join(MN, "reciente")
for nom, P in (("ens", Pe), ("ag12V1", Pa1), ("ag12V0", Pa0)):
    g = {"ens": "P_ens_reciente.npy", "ag12V1": "P_ag12_V1.npy", "ag12V0": "P_ag12_V0.npy"}[nom]
    o = np.load(os.path.join(rec, g)); pr(f"control reproduccion {nom}: max|dif| contra reciente = {np.abs(P[:len(o)] - o).max():.2e}")

# RD Int
rd = {}
with io.open(os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        c = ANIMALES.get(sin_acentos(r["animal"]))
        if c is not None:
            rd[(r["fecha"], int(r["hora"][:2]) - 8)] = LE.IDX[c]
n_hist = len(rd)
with io.open(os.path.join(AQUI, "fresco_rd.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        k = (r["fecha"], int(r["hora"]))
        if k in rd and rd[k] != LE.IDX[r["codigo"]]:
            pr("DISCREPANCIA RD", k)
        rd[k] = LE.IDX[r["codigo"]]
pr("RD: sorteos del archivo", n_hist, "-> con fresco", len(rd))
rd1 = np.array([rd.get((f, h - 1), -1) if h > 0 else -1 for f, h in zip(fe, ho)])   # animal RD (h-1):30
rd2 = np.array([rd.get((f, h - 2), -1) if h > 1 else -1 for f, h in zip(fe, ho)])   # animal RD (h-2):30
pr("filas con RD (h-1):30:", int((rd1 >= 0).sum()), "de", len(y))

# ------------------------------------------------------------------ subconjuntos
valido = ~ex
S = {}
rep = valido & (glob < 12511) & (fe >= "2026-01-01")
fres = glob >= 12511
S["REPLICA_2026 (ene-16sep)"] = rep
S["FRESCO (16sep-7oct)"] = fres
S["2026_TODO (replica+fresco)"] = rep | fres
for q, (a, b) in {"T1 ene-mar": ("2026-01-01", "2026-03-31"), "T2 abr-jun": ("2026-04-01", "2026-06-30"),
                  "T3 jul-sep16": ("2026-07-01", "2026-09-16")}.items():
    S["TRIM " + q] = rep & (fe >= a) & (fe <= b)
for m in range(1, 10):
    S[f"MES 2026-{m:02d}"] = rep & (fe >= f"2026-{m:02d}-01") & (fe <= f"2026-{m:02d}-31")
S["MES 2026-09 (16-7oct fresco aparte)"] = fres
nombres_dia = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
for i, nd in enumerate(nombres_dia):
    S["DIA " + nd] = (rep | fres) & (dow == i)
S["DIA mie-vie"] = (rep | fres) & (dow >= 2) & (dow <= 4)
S["DIA resto"] = (rep | fres) & ~((dow >= 2) & (dow <= 4))
S["DIA mie-vie (solo replica)"] = rep & (dow >= 2) & (dow <= 4)
S["DIA resto (solo replica)"] = rep & ~((dow >= 2) & (dow <= 4))

_, jor = np.unique(fe, return_inverse=True)   # id de jornada (fecha corregida)


# ------------------------------------------------------------------ metricas por fila
def norm(P):
    P = np.clip(P, 1e-9, None); return P / P.sum(1, keepdims=True)


def mbits(P): return 1000 * np.log2(norm(P)[np.arange(len(y)), y] * K)


def rank_matrix(P):
    orden = LE.rankings(norm(P))        # misma semilla de desempate que el banco
    R = np.empty_like(orden); rows = np.arange(len(P))[:, None]
    R[rows, orden] = np.arange(1, K + 1)[None, :]
    return R                              # R[t, a] = puesto (1=primero) del animal a


def con_mult(P):
    M = np.ones_like(P); r = np.arange(len(P))
    for arr, mult in ((rd1, 0.50), (rd2, 0.75)):
        ok = arr >= 0; M[r[ok], arr[ok]] *= mult
    return norm(P * M)


def serie(P, nombre):
    R = rank_matrix(P); pos = R[np.arange(len(y)), y]
    rp = np.where(rd1 >= 0, R[np.arange(len(y)), np.where(rd1 >= 0, rd1, 0)], 99)
    s = {}
    s["mbits"] = mbits(P)
    for k in (3, 5, 15):
        s[f"top{k}"] = (pos <= k).astype(float) * 100
    ret = lambda f, p: (PAGO * f[np.minimum(p, 39)] - f.sum()) / f.sum() * 100
    s["t5"] = ret(F_T5, pos)
    s["p15"] = ret(F_POND, pos); s["pl15"] = ret(F_PLANO, pos)
    # reglas de cambio por RD (h-1):30: el de RD sale si esta en el Top-N y los de abajo suben
    for N, key in ((5, "t5r"), (15, "p15r"), (15, "pl15r")):
        f = {"t5r": F_T5, "p15r": F_POND, "pl15r": F_PLANO}[key]
        sube = (rp <= N) & (rp < pos)
        pn = np.where(sube, pos - 1, pos); pn = np.where((rp <= N) & (rp == pos), 99, pn)
        s[key] = ret(f, pn)
    if nombre in ("ens", "ag12V1"):
        s["_pos"] = pos
    return s, R


# ------------------------------------------------------------------ inferencia
def ic(x, sel, reps=4000, semilla=SEED):
    """media, IC95, IC90, error tipico por bootstrap de bloques de jornada (fecha)."""
    xs = x[sel]; j = jor[sel]
    u, inv = np.unique(j, return_inverse=True)
    s = np.bincount(inv, weights=xs); c = np.bincount(inv).astype(float)
    rng = np.random.default_rng(semilla)
    B = rng.integers(0, len(s), size=(reps, len(s)))
    m = s[B].sum(1) / c[B].sum(1)
    return dict(n=int(sel.sum()), jornadas=int(len(s)), media=float(xs.mean()),
                ic95=[float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))],
                ic90=[float(np.percentile(m, 5)), float(np.percentile(m, 95))], se=float(m.std()))


def flip(x, sel, reps=10000, semilla=SEED):
    xs = x[sel]; u, inv = np.unique(jor[sel], return_inverse=True)
    s = np.bincount(inv, weights=xs); c = np.bincount(inv).sum()
    rng = np.random.default_rng(semilla)
    sg = rng.choice([-1.0, 1.0], size=(reps, len(s)))
    m = (sg * s).sum(1) / c
    obs = s.sum() / c
    return dict(p_dos_colas=float((np.abs(m) >= abs(obs) - 1e-12).mean()), p_uni_pos=float((m >= obs - 1e-12).mean()))


SER = {}
SER["ens"], R_e = serie(Pe, "ens")
SER["ag12V1"], R_a1 = serie(Pa1, "ag12V1")
SER["ag12V0"], _ = serie(Pa0, "ag12V0")
Pe_rd, Pa1_rd = con_mult(Pe), con_mult(Pa1)
SER["ens_rd"], _ = serie(Pe_rd, "ens_rd")
SER["ag12V1_rd"], _ = serie(Pa1_rd, "ag12V1_rd")

PARES = {
    "ag12V1 - ensamble": ("ag12V1", "ens"),
    "ag12V0 - ensamble": ("ag12V0", "ens"),
    "ag12V1_rd(mult) - ensamble [como la sombra]": ("ag12V1_rd", "ens"),
    "ag12V1_rd(mult) - ensamble_rd(mult) [base justa]": ("ag12V1_rd", "ens_rd"),
}
CLAVES = ["mbits", "top3", "top5", "top15", "t5", "p15", "pl15", "t5r", "p15r"]


def resumen(sel, pares=("ag12V1 - ensamble",), todo=True):
    out = {"n": int(sel.sum()), "jornadas": int(len(np.unique(jor[sel])))}
    for nm in ("ens", "ag12V1"):
        out["nivel_" + nm] = {k: float(SER[nm][k][sel].mean()) for k in CLAVES}
    for pn in pares:
        a, b = PARES[pn]
        out[pn] = {k: ic(SER[a][k] - SER[b][k], sel) for k in (CLAVES if todo else ["mbits"])}
    return out


R = {}
pr("\n=== 1. DESGLOSE ag12 V1 - ensamble congelado (mbits; Top-3/5/15 en pp; Top-5 escalonado en pp/ficha) ===")
for nm, sel in S.items():
    r = resumen(sel, todo=True); R[nm] = r
    d = r["ag12V1 - ensamble"]
    f = lambda t: f"{t['media']:+.2f} [{t['ic95'][0]:+.2f};{t['ic95'][1]:+.2f}] (IC90 [{t['ic90'][0]:+.2f};{t['ic90'][1]:+.2f}])"
    pr(f"{nm:38s} n={r['n']:5d} j={r['jornadas']:3d} | dMbits {f(d['mbits'])}")
    pr(f"{'':38s}   top3 {d['top3']['media']:+.2f}pp top5 {d['top5']['media']:+.2f}pp top15 {d['top15']['media']:+.2f}pp [{d['top15']['ic95'][0]:+.2f};{d['top15']['ic95'][1]:+.2f}] | "
       f"T5esc {d['t5']['media']:+.2f} pp/ficha [{d['t5']['ic95'][0]:+.2f};{d['t5']['ic95'][1]:+.2f}] | T5esc+regla RD {d['t5r']['media']:+.2f} [{d['t5r']['ic95'][0]:+.2f};{d['t5r']['ic95'][1]:+.2f}]")
    pr(f"{'':38s}   niveles: ens top3/5/15 {r['nivel_ens']['top3']:.2f}/{r['nivel_ens']['top5']:.2f}/{r['nivel_ens']['top15']:.2f}  ag12 {r['nivel_ag12V1']['top3']:.2f}/{r['nivel_ag12V1']['top5']:.2f}/{r['nivel_ag12V1']['top15']:.2f}")

# contraste mie-vie vs resto (hipotesis declarada)
pr("\n=== 1b. Hipotesis declarada: mie-vie vs resto (dMbits ag12V1 - ens) ===")
dm = SER["ag12V1"]["mbits"] - SER["ens"]["mbits"]
for etiqueta, universo in (("replica+fresco", rep | fres), ("solo replica", rep)):
    mv = (dow >= 2) & (dow <= 4)
    A = universo & mv; B = universo & ~mv
    jA = np.unique(jor[A]); jB = np.unique(jor[B])

    def sums(sel_):
        u, inv = np.unique(jor[sel_], return_inverse=True)
        return np.bincount(inv, weights=dm[sel_]), np.bincount(inv).astype(float)
    sA, cA = sums(A); sB, cB = sums(B)
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(4000):
        ia = rng.integers(0, len(sA), len(sA)); ib = rng.integers(0, len(sB), len(sB))
        bs.append(sA[ia].sum() / cA[ia].sum() - sB[ib].sum() / cB[ib].sum())
    obs = sA.sum() / cA.sum() - sB.sum() / cB.sum()
    # permutacion de etiquetas por jornada (mismo numero de jornadas mie-vie)
    sj = np.concatenate([sA, sB]); cj = np.concatenate([cA, cB]); nA = len(sA); cnt = 0; reps = 5000
    for _ in range(reps):
        pm = rng.permutation(len(sj)); ia, ib = pm[:nA], pm[nA:]
        cnt += abs(sj[ia].sum() / cj[ia].sum() - sj[ib].sum() / cj[ib].sum()) >= abs(obs) - 1e-12
    r = dict(mie_vie=float(sA.sum() / cA.sum()), resto=float(sB.sum() / cB.sum()), n_mv=int(A.sum()), n_resto=int(B.sum()),
             contraste=float(obs), ic95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], p_perm=float((cnt + 1) / (reps + 1)))
    R["contraste_mie_vie " + etiqueta] = r
    pr(etiqueta, json.dumps(r))

# ------------------------------------------------------------------ 3. ag12_rd y regla RD
pr("\n=== 3. ag12_rd y reglas RD ===")
for pn in ("ag12V1_rd(mult) - ensamble [como la sombra]", "ag12V1_rd(mult) - ensamble_rd(mult) [base justa]"):
    for nm in ("REPLICA_2026 (ene-16sep)", "FRESCO (16sep-7oct)", "2026_TODO (replica+fresco)"):
        r = resumen(S[nm], pares=(pn,), todo=False); R[f"{nm} :: {pn}"] = r
        t = r[pn]["mbits"]
        pr(f"{pn} | {nm}: dMbits {t['media']:+.2f} IC95 [{t['ic95'][0]:+.2f};{t['ic95'][1]:+.2f}] IC90 [{t['ic90'][0]:+.2f};{t['ic90'][1]:+.2f}]")

pr("\n-- Top-5 escalonado con regla cambio_rd (la jugada real): ag12 vs ensamble, pp/ficha")
for nm in ("REPLICA_2026 (ene-16sep)", "FRESCO (16sep-7oct)", "2026_TODO (replica+fresco)", "TRIM T1 ene-mar", "TRIM T2 abr-jun", "TRIM T3 jul-sep16"):
    sel = S[nm]
    base = ic(SER["ens"]["t5r"], sel); ag = ic(SER["ag12V1"]["t5r"], sel); dd = ic(SER["ag12V1"]["t5r"] - SER["ens"]["t5r"], sel)
    sinr = ic(SER["ens"]["t5r"] - SER["ens"]["t5"], sel)
    R[f"t5_regla :: {nm}"] = dict(ens_con_regla=base["media"], ag12_con_regla=ag["media"], delta=dd, efecto_regla_en_ens=sinr)
    pr(f"{nm:28s} n={dd['n']} ens+regla {base['media']:+.2f} | ag12+regla {ag['media']:+.2f} | delta {dd['media']:+.2f} [{dd['ic95'][0]:+.2f};{dd['ic95'][1]:+.2f}] IC90 [{dd['ic90'][0]:+.2f};{dd['ic90'][1]:+.2f}] | efecto de la regla sobre ens {sinr['media']:+.2f} [{sinr['ic95'][0]:+.2f};{sinr['ic95'][1]:+.2f}]")

pr("\n-- Regla RD en Top-15 (con - sin), Top-15 ponderado, pp/ficha")
for nm in ("REPLICA_2026 (ene-16sep)", "FRESCO (16sep-7oct)", "2026_TODO (replica+fresco)", "TRIM T1 ene-mar", "TRIM T2 abr-jun", "TRIM T3 jul-sep16"):
    sel = S[nm]
    out = {}
    for modelo in ("ens", "ag12V1"):
        e = ic(SER[modelo]["p15r"] - SER[modelo]["p15"], sel); out[modelo] = e
    out["ag12_con_regla_vs_ens_con_regla"] = ic(SER["ag12V1"]["p15r"] - SER["ens"]["p15r"], sel)
    R[f"regla_top15 :: {nm}"] = out
    pr(f"{nm:28s} regla en ens {out['ens']['media']:+.2f} [{out['ens']['ic95'][0]:+.2f};{out['ens']['ic95'][1]:+.2f}] IC90 [{out['ens']['ic90'][0]:+.2f};{out['ens']['ic90'][1]:+.2f}] | "
       f"regla en ag12 {out['ag12V1']['media']:+.2f} [{out['ag12V1']['ic95'][0]:+.2f};{out['ag12V1']['ic95'][1]:+.2f}] | ag12+regla vs ens+regla {out['ag12_con_regla_vs_ens_con_regla']['media']:+.2f} [{out['ag12_con_regla_vs_ens_con_regla']['ic95'][0]:+.2f};{out['ag12_con_regla_vs_ens_con_regla']['ic95'][1]:+.2f}]")

# ------------------------------------------------------------------ potencia
pr("\n=== 2. POTENCIA del tramo fresco (y de la replica) ===")
z = 1.6449 + 0.8416
from math import erf, sqrt
Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
pot = {}
for nm in ("FRESCO (16sep-7oct)", "REPLICA_2026 (ene-16sep)", "2026_TODO (replica+fresco)"):
    t = R[nm]["ag12V1 - ensamble"]["mbits"]; se = t["se"]; n = t["n"]
    sd = se * sqrt(n)
    emd = z * se
    pot[nm] = dict(n=n, se=se, sd_efectiva_por_sorteo=sd, EMD_ic90_80pct=emd,
                   potencia={str(e): float(Phi(e / se - 1.6449)) for e in (5, 10, 19.4)})
    pr(f"{nm}: n={n} SE={se:.2f} sd_ef={sd:.0f} EMD(IC90, 80%)={emd:.1f} mbits; potencia +5:{pot[nm]['potencia']['5']:.2f} +10:{pot[nm]['potencia']['10']:.2f} +19,4:{pot[nm]['potencia']['19.4']:.2f}")
R["potencia"] = pot
sd = pot["2026_TODO (replica+fresco)"]["sd_efectiva_por_sorteo"]
req = {str(e): int(np.ceil((z * sd / e) ** 2)) for e in (5, 10, 15, 19.4)}
R["n_necesario_80pct_ic90"] = req
pr("n necesario (IC90 unilateral 5 %, 80 % potencia, sd efectiva", round(sd), "):", req)

# ------------------------------------------------------------------ vive de verdad un mecanismo? test directo O/E
pr("\n=== 4. Prueba directa del mecanismo (O/E de repeticion de par, bajo las probabilidades del ENSAMBLE) ===")
sys.path.insert(0, os.path.join(MN, "ag12_transiciones")); sys.path.insert(0, os.path.join(MN, "ag02_residuo_boost"))
import rasgos12 as R12
Dl = LE.cargar(EXT)
Xp = R12.transiciones(Dl, D0)                 # (n, 38, 6) log1p(cuentas)
np.save(os.path.join(AQUI, "X_pares.npy"), Xp.astype(np.float32))
Bn = (Xp > 0).astype(float)
cols = R12.NUEVOS
mec = {}
for nm in ("REPLICA_2026 (ene-16sep)", "FRESCO (16sep-7oct)", "2026_TODO (replica+fresco)", "TRIM T1 ene-mar", "TRIM T2 abr-jun", "TRIM T3 jul-sep16"):
    sel = S[nm]; Pn = norm(Pe)
    mec[nm] = {}
    for c, col in enumerate(cols):
        I = Bn[np.arange(len(y)), y, c]; E = (Pn * Bn[:, :, c]).sum(1); V = E * (1 - E)
        O, Es, z_ = I[sel].sum(), E[sel].sum(), (I[sel].sum() - E[sel].sum()) / sqrt(V[sel].sum())
        mec[nm][col] = dict(O=float(O), E=float(Es), OE=float(O / Es), z=float(z_))
    pr(f"{nm:28s} " + " | ".join(f"{c.split('_')[0]} O/E {mec[nm][c]['OE']:.2f} (z {mec[nm][c]['z']:+.1f})" for c in cols))
R["mecanismo_OE"] = mec

# ------------------------------------------------------------------ placebos
pr("\n=== PLACEBOS ===")
w = json.load(open(os.path.join(MN, "ag12_transiciones", "parametros_V1.json")))["w"]
wp = np.array(w[-6:], float); pr("coeficientes de par T1..R3 (congelados):", np.round(wp, 3).tolist())
lin = Xp.astype(float) @ wp                    # (n, 38) aporte de los 6 rasgos de par en el log
def reconstruye(Q_extra_lin):
    return norm(Pa1 * np.exp(Q_extra_lin))
pl = {}
for nm in ("REPLICA_2026 (ene-16sep)", "FRESCO (16sep-7oct)", "2026_TODO (replica+fresco)"):
    sel = S[nm]; pl[nm] = {}
    f1 = flip(dm, sel); pl[nm]["volteo_signo_por_jornada"] = f1
    # 2) invertir el efecto de par
    P_inv = reconstruye(-2 * lin); d_inv = mbits(P_inv) - SER["ens"]["mbits"]
    pl[nm]["pares_invertidos"] = ic(d_inv, sel)
    # 3) pares barajados entre filas de la misma hora (otra jornada)
    rng = np.random.default_rng(SEED); ds = []
    for _ in range(30):
        perm = np.arange(len(y))
        for h in range(12):
            idx = np.where(ho == h)[0]; perm[idx] = rng.permutation(idx)
        lin_s = Xp[perm].astype(float) @ wp
        ds.append(float((mbits(reconstruye(lin_s - lin)) - SER["ens"]["mbits"])[sel].mean()))
    pl[nm]["pares_barajados_misma_hora"] = dict(media_30=float(np.mean(ds)), sd=float(np.std(ds)), max=float(np.max(ds)), min=float(np.min(ds)))
    pr(f"{nm}: volteo de signo p(2 colas)={f1['p_dos_colas']:.4f}, p(uni +)={f1['p_uni_pos']:.4f} | pares invertidos dMbits {pl[nm]['pares_invertidos']['media']:+.2f} "
       f"[{pl[nm]['pares_invertidos']['ic95'][0]:+.2f};{pl[nm]['pares_invertidos']['ic95'][1]:+.2f}] | pares barajados media {np.mean(ds):+.2f} (sd {np.std(ds):.2f}, max {np.max(ds):+.2f})")
# 4) RD barajado: efecto de la regla Top-15 si el animal de RD viene de otra jornada de la misma hora
Rm = {"ens": R_e, "ag12V1": R_a1}
pos_e = SER["ens"]["_pos"]; pos_a = SER["ag12V1"]["_pos"]
tiene = rd1 >= 0
def efecto_regla_perm(modelo, sel, reps=1000):
    Rk = Rm[modelo]; pos = SER[modelo]["_pos"]; rng = np.random.default_rng(SEED); out = []
    ret = lambda f, p: (PAGO * f[np.minimum(p, 39)] - f.sum()) / f.sum() * 100
    base = ret(F_POND, pos)
    cand = {h: np.where(tiene & (ho == h))[0] for h in range(12)}
    for _ in range(reps):
        r = np.full(len(y), -1)
        for h in range(1, 12):
            idx = cand[h]; r[idx] = rd1[rng.permutation(idx)]
        rp = np.where(r >= 0, Rk[np.arange(len(y)), np.where(r >= 0, r, 0)], 99)
        sube = (rp <= 15) & (rp < pos); pn = np.where(sube, pos - 1, pos); pn = np.where((rp <= 15) & (rp == pos), 99, pn)
        out.append((ret(F_POND, pn) - base)[sel].mean())
    return np.array(out)
for nm in ("REPLICA_2026 (ene-16sep)", "FRESCO (16sep-7oct)"):
    sel = S[nm]
    for modelo in ("ens", "ag12V1"):
        pe_ = efecto_regla_perm(modelo, sel)
        real = (SER[modelo]["p15r"] - SER[modelo]["p15"])[sel].mean()
        pl.setdefault(nm, {})[f"rd_barajado_{modelo}"] = dict(real=float(real), perm_media=float(pe_.mean()), perm_sd=float(pe_.std()),
                                                             p_uni=float(((pe_ >= real).sum() + 1) / (len(pe_) + 1)))
        pr(f"{nm} regla RD Top-15 sobre {modelo}: real {real:+.2f} pp/ficha | RD barajado media {pe_.mean():+.2f} sd {pe_.std():.2f} p(uni) {pl[nm][f'rd_barajado_{modelo}']['p_uni']:.4f}")
R["placebos"] = pl

# ------------------------------------------------------------------ veredicto segun criterio preregistrado
pr("\n=== VEREDICTO segun PREREGISTRO.md ===")
fr = R["FRESCO (16sep-7oct)"]["ag12V1 - ensamble"]["mbits"]
rp_ = R["REPLICA_2026 (ene-16sep)"]["ag12V1 - ensamble"]["mbits"]
tr = {q: R["TRIM " + q]["ag12V1 - ensamble"]["mbits"]["media"] for q in ("T1 ene-mar", "T2 abr-jun", "T3 jul-sep16")}
a = fr["media"] > 0 and fr["ic90"][0] > 0
b = all(v > 0 for v in tr.values())
no_pasa = rp_["ic90"][0] <= 0 or fr["ic90"][1] < 0
ver = "PASA" if (a and b) else ("NO PASA" if no_pasa else "NO CONCLUYENTE")
pr(f"fresco: dMbits {fr['media']:+.2f} IC90 [{fr['ic90'][0]:+.2f};{fr['ic90'][1]:+.2f}] -> (a) {a}; trimestres {tr} -> (b) {b}; replica IC90 inferior {rp_['ic90'][0]:+.2f}")
pr("VEREDICTO ag12 V1:", ver)
R["veredicto_ag12V1"] = dict(a_fresco=bool(a), b_trimestres=bool(b), trimestres=tr, veredicto=ver)

json.dump(R, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
