# ag07: regla del primer sorteo cruzada entre juegos. Uso: python analizar.py dev | prueba
import sys, os, csv, re, unicodedata, datetime as dt, numpy as np
from scipy import stats
AQUI = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.dirname(AQUI)
ML = "/home/user/lotto-activo/datos_multiloteria"
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); import lotto_eval as LE
FASE = sys.argv[1] if len(sys.argv) > 1 else "dev"
ANIM = {"DELFIN":"0","BALLENA":"00","CARNERO":"1","TORO":"2","CIEMPIES":"3","ALACRAN":"4","LEON":"5","RANA":"6",
 "PERICO":"7","RATON":"8","AGUILA":"9","TIGRE":"10","GATO":"11","CABALLO":"12","MONO":"13","PALOMA":"14","ZORRO":"15",
 "OSO":"16","PAVO":"17","BURRO":"18","CHIVO":"19","COCHINO":"20","GALLO":"21","CAMELLO":"22","CEBRA":"23","IGUANA":"24",
 "GALLINA":"25","VACA":"26","PERRO":"27","ZAMURO":"28","ELEFANTE":"29","CAIMAN":"30","LAPA":"31","ARDILLA":"32",
 "PESCADO":"33","VENADO":"34","JIRAFA":"35","CULEBRA":"36"}
na = lambda s: re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", (s or "").upper()))
def idx_nombre(s):
    c = ANIM.get(na(s)); return None if c is None else LE.IDX[c]
# primer sorteo por fecha de cada juego: {fecha: idx o -1 si animal fuera de los 38}
def primeros_por_nombre(path, col="animal"):
    d = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        f, h = r["fecha"], r["hora"]
        if f not in d or h < d[f][0]:
            i = idx_nombre(r[col]); d[f] = (h, -1 if i is None else i)
    return {f: v[1] for f, v in d.items()}
def primeros_oficial(juego):
    d = {}
    for r in csv.DictReader(open(f"{ML}/oficial_multi.csv")):
        if r["juego"] != juego: continue
        f, h = r["fecha"], r["hora"]
        if f not in d or h < d[f][0]: d[f] = (h, LE.IDX[r["codigo"]])
    return {f: v[1] for f, v in d.items()}
RD = primeros_por_nombre(f"{ML}/rdint_hist.csv"); RDo = primeros_oficial("2")
for f, v in RDo.items(): RD.setdefault(f, v)
nd = sum(1 for f in RDo if f in RD and RD[f] != RDo[f])
LARD = primeros_oficial("3"); LAo = primeros_oficial("1")
GR = primeros_por_nombre(f"{ML}/lagranjita.csv"); SP = primeros_por_nombre(f"{ML}/selvaplus.csv")
GU = primeros_por_nombre(f"{ML}/guacharoactivo.csv"); RDw = primeros_por_nombre(f"{ML}/lottoactivordint.csv")
for f, v in RDw.items(): RD.setdefault(f, v)

z = np.load(f"{BASE}/base8.npz")
S, H, F, P, PA, EP, TR = z["seq"], z["hora"], z["fecha"], z["P"], z["P_aj"], z["es_primero"], z["tramo"]
LAp = {F[t]: int(S[t]) for t in np.where(EP)[0]}   # primer sorteo LA por fecha (con su hora real)
LAh = {F[t]: int(H[t]) for t in np.where(EP)[0]}
menos = lambda f, k: (dt.date.fromisoformat(f) - dt.timedelta(days=k)).isoformat()

def filas(tramos, era=None):
    m = EP & np.isin(TR, tramos)
    if era == 9: m &= (H == 1)
    if era == 8: m &= (H == 0)
    return np.where(m)[0]
def feat(fuente, k, ts):
    a = np.array([fuente.get(menos(F[t], k), -1) for t in ts]); return a
def oe(ts, a, Pm=PA):
    ok = a >= 0; ts, a = ts[ok], a[ok]
    O = int((S[ts] == a).sum()); E = float(Pm[ts, a].sum()) if len(ts) else 0.0
    lo = stats.chi2.ppf(.025, 2*O)/2 if O else 0.0; hi = stats.chi2.ppf(.975, 2*O+2)/2
    pb = stats.poisson.cdf(O, E) if E else np.nan; pa = stats.poisson.sf(O-1, E) if E else np.nan
    return dict(n=len(ts), O=O, E=E, oe=O/E if E else np.nan, ic=(lo/E if E else 0, hi/E if E else 0), p_baja=pb, p_alta=pa)
def fmt(r): return f"n={r['n']:4d} O={r['O']:3d} E={r['E']:6.2f} O/E={r['oe']:.2f} [{r['ic'][0]:.2f};{r['ic'][1]:.2f}] p(baja)={r['p_baja']:.4f} p(alta)={r['p_alta']:.4f}"
def mbits(ts, a, m, B=2000, seed=7):
    ok = a >= 0
    q = PA[ts].copy(); rows = np.where(ok)[0]
    q[rows, a[ok]] *= m; q /= q.sum(1, keepdims=True)
    g = 1000*np.log2(q[np.arange(len(ts)), S[ts]]/PA[ts, S[ts]])
    rng = np.random.default_rng(seed); bs = [g[rng.integers(0, len(g), len(g))].mean() for _ in range(B)]
    return g.mean(), np.percentile(bs, [2.5, 97.5]), (np.array(bs) <= 0).mean(), q
def topk(ts, Q, k):
    r = np.argsort(-Q, 1)[:, :k]; return int((r == S[ts][:, None]).any(1).sum())
def crudo(fa, fb, k, desde="0000", hasta="9999"):
    """# días con primero(fa, f) == primero(fb, f-k), vs n/38."""
    n = o = 0
    for f, v in fa.items():
        if not (desde <= f <= hasta): continue
        w = fb.get(menos(f, k), -1)
        if v < 0 or w < 0: continue
        n += 1; o += (v == w)
    return n, o, n/38

print(f"RD primeros: {len(RD)} días; discrepancias rdint_hist vs oficial juego 2: {nd}; LARD {len(LARD)}; GR {len(GR)} SP {len(SP)} GU {len(GU)}")
# chequeo: LA de base8 vs oficial juego 1
nd1 = sum(1 for f, v in LAo.items() if f in LAp and LAh[f] == 0 and LAp[f] != v); print("discrepancias LA base8 vs oficial:", nd1)

FEATS = [("RD", RD, 1), ("RD", RD, 2), ("RD", RD, 3), ("LARD", LARD, 1), ("LARD", LARD, 2), ("LARD", LARD, 3)]
if FASE == "dev":
    print("\n=== DEV: LA primer sorteo vs primer sorteo de otro juego hace k días (contra P_aj) ===")
    for nom, fu, k in FEATS:
        for era in (9, 8, None):
            ts = filas(["dev"], era); a = feat(fu, k, ts)
            if (a >= 0).sum() == 0: continue
            print(f"{nom} k={k} era={era or 'todo'}: {fmt(oe(ts, a))}")
        # contra el motor sin ajuste y crudo en cal (solo RD)
        ts = filas(["dev"]); a = feat(fu, k, ts); print(f"   (contra P sin ajuste: {fmt(oe(ts, a, P))})")
        if nom == "RD":
            tc = filas(["cal"]); ac = feat(fu, k, tc); ok = ac >= 0
            print(f"   cal crudo: n={ok.sum()} O={(S[tc][ok]==ac[ok]).sum()} E(1/38)={ok.sum()/38:.2f}")
    print("\n=== Contexto crudo (descriptivo): cada juego vs SU primer sorteo de ayer (todo el rango) ===")
    for nom, fu in [("LA", LAp), ("RD", RD), ("LARD", LARD), ("Granjita", GR), ("SelvaPlus", SP), ("Guacharo", GU)]:
        for k in (1, 3):
            n, o, e = crudo(fu, fu, k); print(f"{nom} propio k={k}: n={n} O={o} E={e:.1f} O/E={o/e if e else float('nan'):.2f}")
    print("\n=== Reverso (descriptivo): RD 8:30 de hoy == LA primer sorteo de hace k días (crudo vs 1/38) ===")
    for k in (1, 3):
        for nom, d, h in [("cal+dev era 9:00", "0000", "2024-11-27"), ("era 8:00", "2024-11-28", "9999"), ("RD-dev 2024-03..2025-06", "2024-03-01", "2025-06-30")]:
            n, o, e = crudo(RD, LAp, k, d, h); print(f"k={k} {nom}: n={n} O={o} E={e:.1f} O/E={o/e:.2f} p(baja)={stats.poisson.cdf(o,e):.3f}")
    sys.exit()

if FASE == "desc":
    # Descriptivo (NO candidatos): juegos con muestra solo desde 2026-04-13, contra P_aj, todas las filas disponibles
    print("=== Descriptivo: LA primer sorteo vs primer sorteo de Granjita / SelvaPlus / Guacharo hace k días ===")
    for nom, fu in [("Granjita", GR), ("SelvaPlus", SP), ("Guacharo", GU)]:
        for k in (1, 3):
            ts = filas(["prueba", "vivo"]); a = feat(fu, k, ts); print(f"{nom} k={k}: {fmt(oe(ts, a))}")
    print("=== Descriptivo: RD propio k=1 por tramo (crudo vs 1/38) ===")
    for nom, d, h in [("cal 2023-09..2024-02", "0000", "2024-02-29"), ("RD-dev 2024-03..2025-06", "2024-03-01", "2025-06-30"),
                      ("RD-test 2025-07..2026-04-12", "2025-07-01", "2026-04-12"), ("2026-04-13..", "2026-04-13", "9999")]:
        n, o, e = crudo(RD, RD, 1, d, h); print(f"{nom}: n={n} O={o} E={e:.1f} O/E={o/e:.2f} p(baja)={stats.poisson.cdf(o,e):.2g}")
    for nom, d, h in [("LARD 2025-07..12-19", "0000", "2025-12-19"), ("LARD 2025-12-20..", "2025-12-20", "9999")]:
        n, o, e = crudo(LARD, LARD, 1, d, h); print(f"LARD propio {nom}: n={n} O={o} E={e:.1f} O/E={o/e:.2f}")

if FASE == "escala":
    # Escala del efecto (DENTRO de dev, optimista por estar ajustado en la misma muestra): mbits y Top-5/15
    for nom, fu, k in FEATS:
        ts = filas(["dev"]); a = feat(fu, k, ts); r = oe(ts, a); m = (r["O"]+.5)/(r["E"]+.5)
        g, ic, p0, Q = mbits(ts, a, m)
        print(f"{nom} k={k}: m={m:.3f} mbits dev (in-sample)={g:+.2f} [{ic[0]:+.2f};{ic[1]:+.2f}] Top5 {topk(ts,PA[ts],5)}->{topk(ts,Q,5)} Top15 {topk(ts,PA[ts],15)}->{topk(ts,Q,15)}")
