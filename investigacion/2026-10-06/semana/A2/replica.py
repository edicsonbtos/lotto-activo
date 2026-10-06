"""A2: reciclaje sin modelo (ganador ∈ animales de d-1 y d-2) por día de semana, en varios juegos.
Uso: python3 replica.py <SP>   (SP = carpeta con hist_0605.txt).  Ver PREREGISTRO.md."""
import sys, csv, math, unicodedata, collections as C
from datetime import date, timedelta
import numpy as np

SP = sys.argv[1]
DM = "/home/user/lotto-activo/datos_multiloteria/"
RNG = np.random.default_rng(20261006)
NAMES = ["Delfin", "Ballena", "Carnero", "Toro", "Ciempies", "Alacran", "Leon", "Rana", "Perico", "Raton", "Aguila",
         "Tigre", "Gato", "Caballo", "Mono", "Paloma", "Zorro", "Oso", "Pavo", "Burro", "Chivo", "Cochino", "Gallo",
         "Camello", "Cebra", "Iguana", "Gallina", "Vaca", "Perro", "Zamuro", "Elefante", "Caiman", "Lapa", "Ardilla",
         "Pescado", "Venado", "Jirafa", "Culebra"]
CODES = ["0", "00"] + [str(i) for i in range(1, 37)]
nz = lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().strip().lower()
N2C = {nz(n): c for n, c in zip(NAMES, CODES)}


def leer(juego):
    """dict fecha -> dict hora(str) -> código; y conjunto de horas estándar por fecha (función)."""
    G = C.defaultdict(dict)
    if juego == "LA":
        for ln in open(SP + "/hist_0605.txt"):
            p = ln.split()
            if len(p) == 3: G[p[0]][f"{8 + int(p[1]):02d}:00"] = p[2]
        std = lambda f: [f"{h:02d}:00" for h in (range(9, 20) if f < "2024-12-01" else range(8, 20))]
        # ojo: el cambio 11→12 sorteos ocurre a fines de 2024-11; los días de 12 antes de dic. también valen
        std0 = std
        std = lambda f: std0(f) if not (f < "2024-12-01" and "08:00" in G[f]) else [f"{h:02d}:00" for h in range(8, 20)]
    elif juego == "RD":
        for r in csv.DictReader(open(DM + "rdint_hist.csv", encoding="utf-8")):
            if r["fecha"] < "2025-07-01": G[r["fecha"]][r["hora"]] = N2C[nz(r["animal"])]
        for r in csv.DictReader(open(DM + "oficial_multi.csv")):
            if r["juego"] == "2": G[r["fecha"]][r["hora"]] = r["codigo"]
        std = lambda f: [f"{h:02d}:30" for h in range(8, 20)]
    elif juego == "LARD":
        for r in csv.DictReader(open(DM + "oficial_multi.csv")):
            if r["juego"] == "3": G[r["fecha"]][r["hora"]] = r["codigo"]
        std = lambda f: [f"{h:02d}:00" for h in range(8, 22)]
    else:
        arch, hh = {"GRANJITA": ("lagranjita.csv", ":00"), "SELVA": ("selvaplus.csv", ":15"),
                    "GUACHARO": ("guacharoactivo.csv", ":00")}[juego]
        for r in csv.DictReader(open(DM + arch, encoding="utf-8")):
            if r["hora"] <= "19:59": G[r["fecha"]][r["hora"]] = r["numero"]
        std = lambda f, hh=hh: [f"{h:02d}{hh}" for h in range(8, 20)]
    return G, std


def filas(juego, lo, hi, Nover=None):
    G, std = leer(juego)
    N = Nover or len({c for d in G.values() for c in d.values()})
    comp = {f for f in G if all(h in G[f] for h in std(f))}
    R = []  # (dia_id, dow, hora_idx, O, E1, E0, Orep, Erep)
    for f in sorted(G):
        if not (lo <= f <= hi) or f not in comp: continue
        d = date.fromisoformat(f)
        p1, p2 = (d - timedelta(1)).isoformat(), (d - timedelta(2)).isoformat()
        if p1 not in comp or p2 not in comp: continue
        S = set(G[p1].values()) | set(G[p2].values())
        T = set()
        for k, h in enumerate(std(f)):
            y = G[f][h]
            R.append((f, d.weekday(), int(h[:2]), y in S, len(S - T) / (N - len(T)), len(S) / N,
                      y in T, len(T) / N))
            T.add(y)
    return N, R


def rr_mh(day, hor, O, E, A):
    num = den = 0.0
    for h in np.unique(hor):
        m = hor == h
        a, b = m & A, m & ~A
        Oa, Ob, Ea, Eb = O[a].sum(), O[b].sum(), E[a].sum(), E[b].sum()
        if Ea + Eb == 0: continue
        num += Oa * Eb / (Ea + Eb); den += Ob * Ea / (Ea + Eb)
    return num / den if den > 0 else float("nan")


def analizar(nom, juego, lo, hi, out, nperm=5000, nboot=2000, Nover=None):
    N, R = filas(juego, lo, hi, Nover)
    f = np.array([r[0] for r in R]); dw = np.array([r[1] for r in R]); hr = np.array([r[2] for r in R])
    O = np.array([r[3] for r in R], float); E1 = np.array([r[4] for r in R]); E0 = np.array([r[5] for r in R])
    Orp = np.array([r[6] for r in R], float); Erp = np.array([r[7] for r in R])
    dias, di = np.unique(f, return_inverse=True)
    ddow = np.array([date.fromisoformat(x).weekday() for x in dias]); dA = np.isin(ddow, [2, 3, 4])
    A = dA[di]
    rr = rr_mh(di, hr, O, E1, A); rr0 = rr_mh(di, hr, O, E0, A); rrc = rr_mh(di, hr, Orp, Erp, A)
    # permutación de etiquetas entre jornadas
    cnt = 0; cntc = 0
    for _ in range(nperm):
        pa = RNG.permutation(dA)[di]
        cnt += rr_mh(di, hr, O, E1, pa) <= rr
    p = (cnt + 1) / (nperm + 1)
    # bootstrap por jornadas (estratificado por grupo A/B)
    idxd = [np.where(di == k)[0] for k in range(len(dias))]
    iA, iB = np.where(dA)[0], np.where(~dA)[0]
    bs = []
    for _ in range(nboot):
        sel = np.concatenate([RNG.choice(iA, len(iA)), RNG.choice(iB, len(iB))])
        ix = np.concatenate([idxd[k] for k in sel])
        bs.append(rr_mh(None, hr[ix], O[ix], E1[ix], A[ix]))
    bs = np.log(np.array(bs)); se = bs.std(ddof=1)
    lo95, hi95 = np.exp(np.percentile(bs, [2.5, 97.5]))
    oeA, oeB = O[A].sum() / E1[A].sum(), O[~A].sum() / E1[~A].sum()
    dn = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    pdow = "  ".join(f"{dn[k]} {O[dw == k].sum() / E1[dw == k].sum():.2f}" if (dw == k).any() else f"{dn[k]} —"
                     for k in range(7))
    cdow = "  ".join(f"{dn[k]} {Orp[dw == k].sum() / max(Erp[dw == k].sum(), 1e-9):.2f}" if (dw == k).any() else
                     f"{dn[k]} —" for k in range(7))
    s = (f"\n== {nom}  [{lo}..{hi}]  N={N}  jornadas {len(dias)} (mié-vie {dA.sum()})  sorteos {len(O)}\n"
         f"  reciclaje real {O.mean() * 100:.1f}%  azar E1 {E1.mean() * 100:.1f}%  E0 {E0.mean() * 100:.1f}%  O/E1 global {O.sum() / E1.sum():.3f}\n"
         f"  O/E1 mié-vie {oeA:.3f} | resto {oeB:.3f}   RR_MH {rr:.3f} IC95 [{lo95:.3f}; {hi95:.3f}]  p_unil {p:.4f}"
         f"   (RR con E0 {rr0:.3f})\n"
         f"  por día O/E1: {pdow}\n"
         f"  control repetición mismo día: O/E mié-vie {Orp[A].sum() / Erp[A].sum():.3f} | resto {Orp[~A].sum() / Erp[~A].sum():.3f}  RR_MH {rrc:.3f}\n"
         f"  control por día: {cdow}")
    print(s); out.write(s + "\n")
    return dict(nom=nom, rr=rr, se=se, p=p, lo=lo95, hi=hi95)


if __name__ == "__main__":
    out = open("/home/user/lotto-activo/investigacion/2026-10-06/semana/A2/salida.txt", "w")
    res = {}
    for nom, j, lo, hi in [("LA dev 2024-25", "LA", "2024-01-01", "2025-12-31"),
                           ("LA 2026", "LA", "2026-01-01", "2026-10-05"),
                           ("LA 2026 ventana abr-sep", "LA", "2026-04-13", "2026-09-13"),
                           ("RD 2024-25", "RD", "2024-01-01", "2025-12-31"),
                           ("RD 2026", "RD", "2026-01-01", "2026-09-22"),
                           ("LARD 2025-S2", "LARD", "2025-07-01", "2025-12-31"),
                           ("LARD 2026", "LARD", "2026-01-01", "2026-09-22"),
                           ("La Granjita 2026", "GRANJITA", "2026-04-13", "2026-09-13"),
                           ("Selva Plus 2026", "SELVA", "2026-04-13", "2026-09-13"),
                           ("Guácharo 2026", "GUACHARO", "2026-04-13", "2026-09-13")]:
        res[nom] = analizar(nom, j, lo, hi, out)
    analizar("Selva Plus 2026 (sensibilidad N=100)", "SELVA", "2026-04-13", "2026-09-13", out, 1000, 200, 100)
    ciegos = ["RD 2026", "LARD 2026", "La Granjita 2026", "Selva Plus 2026", "Guácharo 2026"]
    w = np.array([1 / res[k]["se"] ** 2 for k in ciegos]); l = np.array([math.log(res[k]["rr"]) for k in ciegos])
    lp = (w * l).sum() / w.sum(); sp = 1 / math.sqrt(w.sum()); z = lp / sp
    pz = 0.5 * math.erfc(-z / math.sqrt(2))
    npass = sum(res[k]["rr"] < 1 and res[k]["p"] < 0.05 for k in ciegos)
    s = (f"\n== COMBINADO réplica ciega (5 juegos 2026): RR {math.exp(lp):.3f} IC95 [{math.exp(lp - 1.96 * sp):.3f}; "
         f"{math.exp(lp + 1.96 * sp):.3f}]  z {z:+.2f}  p_unil {pz:.4f}   juegos que pasan (p<0,05): {npass}/5")
    w2 = [k for k in ciegos if k not in ("RD 2026", "LARD 2026")]
    w = np.array([1 / res[k]["se"] ** 2 for k in w2]); l = np.array([math.log(res[k]["rr"]) for k in w2])
    lp2 = (w * l).sum() / w.sum(); sp2 = 1 / math.sqrt(w.sum())
    s += f"\n   solo otros operadores (Granjita, Selva, Guácharo): RR {math.exp(lp2):.3f} z {lp2 / sp2:+.2f}"
    w = np.array([1 / res[k]["se"] ** 2 for k in ciegos[:2]]); l = np.array([math.log(res[k]["rr"]) for k in ciegos[:2]])
    lp3 = (w * l).sum() / w.sum(); sp3 = 1 / math.sqrt(w.sum())
    s += f"\n   solo familia Lotto Activo (RD, LARD): RR {math.exp(lp3):.3f} z {lp3 / sp3:+.2f}"
    print(s); out.write(s + "\n")
