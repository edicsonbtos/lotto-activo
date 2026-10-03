"""ag04 — relaciones numéricas/geométricas en la transición nocturna (primer sorteo).
Uso: python analisis.py dev        -> exploración/selección en dev (+ cal crudo)
     python analisis.py prueba     -> evalúa los candidatos fijados en CANDIDATOS (una sola vez)
"""
import sys, json, datetime as dt
import numpy as np
from scipy import stats

BASE = '/tmp/claude-0/-home-user-lotto-activo/fffc39ca-02e7-4d69-b0fe-674a608a5e21/scratchpad/base8'
d = np.load(f'{BASE}/base8.npz', allow_pickle=True)
seq, hora, fecha, tramo, PA, prim = d['seq'], d['hora'], d['fecha'], d['tramo'], d['P_aj'], d['es_primero']
K = 38
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
val = np.array([0, 37] + list(range(1, 37)))           # círculo de 38
num = np.array([0, -1] + list(range(1, 37)))           # -1 = 00 (sin dígitos)

WHEEL = ["0","28","9","26","30","11","7","20","32","17","5","22","34","15","3","24","36","13","1","00",
         "27","10","25","29","12","8","19","31","18","6","21","33","16","4","23","35","14","2"]
wpos = np.zeros(K, int)
for j, s in enumerate(WHEEL): wpos[IDX[s]] = j

def rel(f):
    R = np.zeros((K, K), bool)
    for o in range(K):
        for x in range(K):
            if o == x: continue
            vo, vx, no, nx = val[o], val[x], num[o], num[x]
            dv = (vx - vo) % K; dw = (wpos[x] - wpos[o]) % K
            dig = no >= 0 and nx >= 0
            if f == 'val±1': r = dv in (1, K-1)
            elif f == 'val±2': r = dv in (2, K-2)
            elif f == 'espejo': r = vx == 37 - vo
            elif f == 'invertido':
                r = dig and int(str(no).zfill(2)[::-1]) == nx
            elif f == 'terminacion': r = dig and no % 10 == nx % 10
            elif f == 'decena': r = dig and no // 10 == nx // 10
            elif f == 'sumadig': r = dig and sum(map(int, str(no))) == sum(map(int, str(nx)))
            elif f == 'rueda±1': r = dw in (1, K-1)
            elif f == 'rueda±2': r = dw in (2, K-2)
            elif f == 'tablero':
                def nb(n):
                    if n == 0: return {1, 2, -1}
                    if n == -1: return {2, 3, 0}
                    s = set()
                    if (n-1) % 3 > 0: s.add(n-1)
                    if (n-1) % 3 < 2: s.add(n+1)
                    if n-3 >= 1: s.add(n-3)
                    if n+3 <= 36: s.add(n+3)
                    if n in (1, 2): s.add(0)
                    if n in (2, 3): s.add(-1)
                    return s
                r = nx in nb(no)
            R[o, x] = r
    return R

FAM = ['val±1', 'val±2', 'espejo', 'invertido', 'terminacion', 'decena', 'sumadig', 'rueda±1', 'rueda±2', 'tablero']
REL = {f: rel(f) for f in FAM}
# simetría (sanity)
for f in FAM: assert (REL[f] == REL[f].T).all(), f

# --- orígenes para cada primer sorteo ---
dates = np.array([dt.date.fromisoformat(s) for s in fecha])
rows = np.where(prim)[0]
first_of = {fecha[t]: t for t in rows}
last_of = {}
for t in range(len(seq)): last_of[fecha[t]] = t
Oa = np.full(len(seq), -1); Ob = np.full(len(seq), -1)
for t in rows:
    ay = (dates[t] - dt.timedelta(days=1)).isoformat()
    if ay in last_of and hora[last_of[ay]] == 11: Oa[t] = seq[last_of[ay]]
    if ay in first_of and hora[first_of[ay]] == hora[t]: Ob[t] = seq[first_of[ay]]  # misma era
ORIG = {'a_7pm': Oa, 'b_1ro': Ob}

def era_mask(tr, h=None):
    m = prim & (tramo == tr)
    if h is not None: m &= hora == h
    return m

def poi_p(O, E):
    lo = stats.poisson.cdf(O, E); hi = stats.poisson.sf(O - 1, E)
    return min(1.0, 2 * min(lo, hi)), lo, hi

def poi_ci(O, E):
    a = 0.05
    l = stats.chi2.ppf(a/2, 2*O)/2 if O > 0 else 0.0
    u = stats.chi2.ppf(1-a/2, 2*O+2)/2
    return l/E, u/E

def oe(mask, orig, R):
    t = np.where(mask & (orig >= 0))[0]
    S = R[orig[t]]                                   # (n,38)
    O = int(S[np.arange(len(t)), seq[t]].sum())
    E = float((PA[t] * S).sum())
    return len(t), O, E

def chi_dif(mask, orig, kind):
    t = np.where(mask & (orig >= 0))[0]
    pos = val if kind == 'val' else wpos
    D = (pos[None, :] - pos[orig[t]][:, None]) % K   # (n,38) clase de cada destino
    Oc = np.bincount(D[np.arange(len(t)), seq[t]], minlength=K).astype(float)
    Ec = np.zeros(K)
    for k in range(K): Ec[k] = (PA[t] * (D == k)).sum()
    # clase 0 = identidad: se excluye (la cubre producción/motor) -> 36 gl
    Oc2, Ec2 = Oc[1:], Ec[1:] * Oc[1:].sum() / Ec[1:].sum()
    chi = ((Oc2 - Ec2) ** 2 / Ec2).sum()
    return len(t), chi, stats.chi2.sf(chi, K - 2), Oc, Ec

def cal_crudo(orig, R):
    t = np.where(era_mask('cal') & (orig >= 0))[0]
    S = R[orig[t]]
    O = int(S[np.arange(len(t)), seq[t]].sum()); E = S.sum() / K
    return len(t), O, E

def apply_mult(q, orig, R, m):
    q = q.copy()
    t = np.where(orig >= 0)[0]
    S = R[orig[t]]
    q[t] = np.where(S, q[t] * m, q[t]); q[t] /= q[t].sum(1, keepdims=True)
    return q

def mbits(mask, q):
    t = np.where(mask)[0]
    g = 1000 * np.log2(q[t, seq[t]] / PA[t, seq[t]])
    rng = np.random.default_rng(4)
    bs = np.array([g[rng.integers(0, len(g), len(g))].mean() for _ in range(5000)])
    return g.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), (bs <= 0).mean()

def topk(mask, q, k):
    t = np.where(mask)[0]
    rk = np.argsort(-q[t], 1)[:, :k]
    return int((rk == seq[t][:, None]).any(1).sum()), len(t)

if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    out = {}
    if modo == 'dev':
        print(f"{'origen':7s} {'familia':12s} | {'9:00 n O E O/E':22s} | {'8:00 n O E O/E':22s} | conj O/E [IC] p2 | cal O/E_azar")
        res = []
        for on, orig in ORIG.items():
            for f in FAM:
                R = REL[f]
                r9 = oe(era_mask('dev', 1), orig, R); r8 = oe(era_mask('dev', 0), orig, R)
                n, O, E = oe(era_mask('dev'), orig, R)
                p2, lo, hi = poi_p(O, E); ci = poi_ci(O, E)
                nc, Oc, Ec = cal_crudo(orig, R)
                mismo = np.sign(r9[1]/r9[2]-1) == np.sign(r8[1]/r8[2]-1)
                res.append(dict(origen=on, fam=f, n9=r9[0], O9=r9[1], E9=r9[2], n8=r8[0], O8=r8[1], E8=r8[2],
                                n=n, O=O, E=E, p2=p2, ci=ci, cal=(nc, Oc, Ec), mismo=bool(mismo)))
                print(f"{on:7s} {f:12s} | {r9[0]:3d} {r9[1]:3d} {r9[2]:5.1f} {r9[1]/r9[2]:4.2f} | "
                      f"{r8[0]:3d} {r8[1]:3d} {r8[2]:5.1f} {r8[1]/r8[2]:4.2f} | {O/E:4.2f} [{ci[0]:.2f};{ci[1]:.2f}] "
                      f"p={p2:.3f} {'=' if mismo else 'x'} | cal {nc} {Oc}/{Ec:.1f}={Oc/Ec:.2f}")
        print("\nDistribución de la diferencia (D−O) mod 38, sin clase 0, chi² 36 gl:")
        for on, orig in ORIG.items():
            for kind in ('val', 'rueda'):
                n, chi, p, Oc, Ec = chi_dif(era_mask('dev'), orig, kind)
                _, c9, p9, O9, E9 = chi_dif(era_mask('dev', 1), orig, kind)
                _, c8, p8, O8, E8 = chi_dif(era_mask('dev', 0), orig, kind)
                z = (Oc - Ec) / np.sqrt(Ec)
                top = np.argsort(-np.abs(z[1:]))[:3] + 1
                print(f"{on:7s} dif_{kind:5s} n={n} chi={chi:.1f} p={p:.3f} | 9:00 p={p9:.3f} | 8:00 p={p8:.3f} | "
                      + ", ".join(f"k={k}: {Oc[k]:.0f}/{Ec[k]:.1f} (9:{O9[k]:.0f}/{E9[k]:.1f} 8:{O8[k]:.0f}/{E8[k]:.1f})" for k in top))
                res.append(dict(origen=on, fam=f'dif_{kind}', p2=p, chi=chi))
        ntest = len(res)
        print(f"\nContrastes en dev: {ntest}; Bonferroni 0,05/{ntest} = {0.05/ntest:.4f}")
        cand = sorted([r for r in res if 'O' in r and r['p2'] < 0.05 and r['mismo']], key=lambda r: r['p2'])[:3]
        print("Candidatos según regla pre-registrada:", [(r['origen'], r['fam'], round(r['O']/r['E'], 2), round(r['p2'], 4)) for r in cand])
        json.dump([{k: (v if not isinstance(v, (np.floating, np.integer)) else float(v)) for k, v in r.items() if k in ('origen','fam','O','E','p2','mismo')} for r in res],
                  open(f'{BASE}/ag04/dev_resultados.json', 'w'), indent=1, default=float)
