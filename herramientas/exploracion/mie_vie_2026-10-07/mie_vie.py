# -*- coding: utf-8 -*-
"""Hipotesis mie-vie mas flojo (2026-10-07). Ver PREREGISTRO.md. Solo desarrollo [2000,9357). Solo lectura.
   python mie_vie.py"""
import os, sys, math
from datetime import date, timedelta
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI))) if False else os.path.dirname(os.path.dirname(AQUI)))
import lotto_eval as LE  # noqa

DIAS = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
rng = np.random.default_rng(2026)

D = LE.cargar(); c = np.load(os.path.join(os.path.dirname(AQUI), "calor_cache.npz"))
P = c["P"] / c["P"].sum(1, keepdims=True); y = c["y"]; n = len(y)
sl = slice(LE.W, LE.W + n)
assert (np.asarray(D.seq)[sl] == y).all() and LE.W + n == LE.CORTE_FIJO
dow = np.asarray(D.dow)[sl]; hora = np.asarray(D.hora)[sl]; dia = np.asarray(D.dia)[sl]
fecha = np.array(D.fecha)[sl]
bits = np.log2(38 * P[np.arange(n), y]) * 1000          # mbits por sorteo
orden = LE.rankings(P); pos = np.argmax(orden == y[:, None], axis=1)
h5 = (pos < 5).astype(float); h15 = (pos < 15).astype(float)
m5 = np.take_along_axis(P, orden[:, :5], 1).sum(1)      # masa del Top-5 segun el modelo
m15 = np.take_along_axis(P, orden[:, :15], 1).sum(1)
print(f"Desarrollo: n={n}, {fecha[0]} .. {fecha[-1]}, dias={len(set(dia))}")

# --- bloques de dia
ud, inv = np.unique(dia, return_inverse=True); nd = len(ud)
dow_d = np.zeros(nd, int); dow_d[inv] = dow
def suma_dia(v): return np.bincount(inv, weights=v, minlength=nd)
cnt_d = np.bincount(inv, minlength=nd).astype(float)

def ratio_boot(num_d, den_d, mask_d, B=4000):
    """media = sum num / sum den dentro de mask dias, IC bootstrap por dia."""
    idx = np.where(mask_d)[0]; m = len(idx)
    est = num_d[idx].sum() / den_d[idx].sum()
    I = rng.integers(0, m, (B, m)); b = num_d[idx][I].sum(1) / den_d[idx][I].sum(1)
    return est, np.percentile(b, 2.5), np.percentile(b, 97.5)

print("\n== 1. Por dia de la semana (ensamble, desarrollo) ==")
print("dia   n_sort  mbits [IC95]            Top5 [IC]  (azar 13.16)      Top15 [IC] (azar 39.47)  Top5 mas-que-masa")
bits_d, h5_d, h15_d = suma_dia(bits), suma_dia(h5), suma_dia(h15)
cal5 = suma_dia(m5)
filas = {}
for k in range(7):
    md = dow_d == k
    a = ratio_boot(bits_d, cnt_d, md); b5 = ratio_boot(h5_d, cnt_d, md); b15 = ratio_boot(h15_d, cnt_d, md)
    filas[k] = (a, b5, b15)
    print(f"{DIAS[k]}  {int(cnt_d[md].sum()):5d}  {a[0]:6.1f} [{a[1]:6.1f};{a[2]:6.1f}]   "
          f"{100*b5[0]:5.2f} [{100*b5[1]:5.2f};{100*b5[2]:5.2f}]   {100*b15[0]:5.2f} [{100*b15[1]:5.2f};{100*b15[2]:5.2f}]   "
          f"O/E5 {h5_d[md].sum()/cal5[md].sum():.3f}")

# --- composicion horaria por dia
print("\n== Confusor hora: sorteos por hora y dia (hora 0..11) ==")
for k in range(7):
    cnts = np.bincount(hora[dow == k], minlength=12)
    print(DIAS[k], (cnts / cnts.sum()).round(3).tolist())
print("(si las filas son iguales, la hora no confunde por composicion)")

# --- prueba unica preregistrada: mie-vie vs resto, estratificada por hora
G = np.isin(dow, [2, 3, 4])
def dif_estratificada(v, G):
    """diferencia media G - resto, ponderada por n de G en cada hora (estratificada por hora)."""
    num = 0.0; w = 0.0
    for h in range(12):
        a = G & (hora == h); b = (~G) & (hora == h)
        if a.sum() and b.sum():
            num += a.sum() * (v[a].mean() - v[b].mean()); w += a.sum()
    return num / w
GM = np.isin(dow_d, [2, 3, 4])

def dif_boot(v, B=3000):
    est = dif_estratificada(v, G)
    out = []
    for _ in range(B):
        sel_d = rng.integers(0, nd, nd)               # remuestreo de dias (bloques)
        cnt = np.bincount(sel_d, minlength=nd)
        w = cnt[inv]
        # media ponderada por hora
        num = 0.0; ww = 0.0
        for h in range(12):
            a = G & (hora == h); b = (~G) & (hora == h)
            wa, wb = w[a].sum(), w[b].sum()
            if wa and wb:
                na = a.sum()
                num += na * ((v[a] * w[a]).sum() / wa - (v[b] * w[b]).sum() / wb); ww += na
        out.append(num / ww)
    return est, np.percentile(out, 2.5), np.percentile(out, 97.5)

# permutacion: etiquetas de dow permutadas dentro de cada semana (conserva tendencia)
d0 = date.fromisoformat(fecha[0])
fe_d = {}
for f, dd in zip(fecha, dia): fe_d[dd] = f
sem_d = np.array([(date.fromisoformat(fe_d[d]) - date.fromisoformat(fe_d[ud[0]])).days // 7 for d in ud])
# alinear semana por lunes:
sem_d = np.array([(date.fromisoformat(fe_d[d]) - timedelta(days=date.fromisoformat(fe_d[d]).weekday())).toordinal() for d in ud])
def permuta(B=20000, nombre=""):
    return None
def perm_p(v, B=5000):
    est = dif_estratificada(v, G)
    grupos = {}
    for i, s in enumerate(sem_d): grupos.setdefault(s, []).append(i)
    glist = [np.array(g) for g in grupos.values()]
    ge = 0; vals = []
    # dif estratificada cuesta; usamos version rapida por hora pre-indexada
    for _ in range(B):
        lab = GM.copy()
        for g in glist:
            lab[g] = lab[rng.permutation(g)]
        Gp = lab[inv]
        vals.append(dif_estratificada(v, Gp))
    vals = np.array(vals)
    return est, float((np.abs(vals) >= abs(est)).mean()), float((vals <= est).mean()), vals

print("\n== 2. PRUEBA UNICA: mie-vie vs resto, mbits, estratificada por hora ==")
est, lo, hi = dif_boot(bits)
print(f"dif mbits (mie-vie menos resto) = {est:+.1f}  IC95 bloques-dia [{lo:+.1f}; {hi:+.1f}]")
e2, p2, p1, vals = perm_p(bits)
print(f"permutacion (etiquetas dentro de semana, 5000): p dos colas={p2:.3f}  p una cola(<)={p1:.3f}  sd nula={vals.std():.1f}")
for nom, v in (("Top5", h5), ("Top15", h15)):
    e, l, h = dif_boot(v, 1500)
    print(f"dif {nom} = {100*e:+.2f} pp  IC95 [{100*l:+.2f}; {100*h:+.2f}]")

# --- placebo: 7 contrastes "dia k vs resto" con permutacion, mbits
print("\n== 3. Cada dia vs resto (mbits, estratificado), Bonferroni x7 (alfa=0.00714) ==")
for k in range(7):
    Gk = dow == k
    est_k = dif_estratificada(bits, Gk)
    # bootstrap rapido sobre dias para el IC
    out = []
    for _ in range(1500):
        sd = rng.integers(0, nd, nd); w = np.bincount(sd, minlength=nd)[inv]
        num = 0; ww = 0
        for h in range(12):
            a = Gk & (hora == h); b = (~Gk) & (hora == h)
            wa, wb = w[a].sum(), w[b].sum()
            if wa and wb:
                num += a.sum() * ((bits[a] * w[a]).sum() / wa - (bits[b] * w[b]).sum() / wb); ww += a.sum()
        out.append(num / ww)
    out = np.array(out)
    se = out.std(); z = est_k / se
    p = math.erfc(abs(z) / math.sqrt(2))
    print(f"{DIAS[k]}: {est_k:+6.1f} mbits  IC95 [{np.percentile(out,2.5):+.1f};{np.percentile(out,97.5):+.1f}]  z={z:+.2f}  p={p:.3f}  {'*' if p<0.05/7 else ''}")

# --- feriados
def pascua(a):
    A = a % 19; B = a // 100; C = a % 100; Dd = B // 4; E = B % 4; F = (B + 8) // 25; Gg = (B - F + 1) // 3
    H = (19 * A + B - Dd - Gg + 15) % 30; I = C // 4; K = C % 4; L = (32 + 2 * E + 2 * I - H - K) % 7
    M = (A + 11 * H + 22 * L) // 451; mes = (H + L - 7 * M + 114) // 31; dd = (H + L - 7 * M + 114) % 31 + 1
    return date(a, mes, dd)
fer = set()
for a in range(2023, 2027):
    for m, dd in ((1, 1), (4, 19), (5, 1), (6, 24), (7, 5), (7, 24), (10, 12), (12, 24), (12, 25), (12, 31)):
        fer.add(date(a, m, dd))
    e = pascua(a)
    for off in (-48, -47, -3, -2):  # carnaval lun-mar, jueves y viernes santo
        fer.add(e + timedelta(days=off))
esf = np.array([date.fromisoformat(f) in fer for f in fecha])
print(f"\n== 4. Feriados: {esf.sum()} sorteos en {len(set(dia[esf]))} dias feriados (lista fija VE aprox.)")
keep = ~esf
G_all = G.copy()
def dif_sin(v, mask):
    num = 0; w = 0
    for h in range(12):
        a = G & (hora == h) & mask; b = (~G) & (hora == h) & mask
        if a.sum() and b.sum():
            num += a.sum() * (v[a].mean() - v[b].mean()); w += a.sum()
    return num / w
print(f"mbits mie-vie menos resto sin feriados: {dif_sin(bits, keep):+.1f}  (con feriados {est:+.1f})")
print(f"feriados: mbits medios {bits[esf].mean():.1f}  vs resto {bits[keep].mean():.1f}")

# --- modelo u operador
print("\n== 5. Modelo u operador (mie-vie vs resto) ==")
hoy_vis = np.zeros(n)   # nº de animales distintos ya salidos hoy antes del sorteo y si el ganador es uno de ellos
salio_hoy = np.zeros(n); masa_hoy = np.zeros(n); entrop = np.zeros(n)
seq = np.asarray(D.seq)[sl]
cur = None; vistos = set()
for t in range(n):
    if dia[t] != cur: cur = dia[t]; vistos = set()
    idx = list(vistos)
    salio_hoy[t] = float(y[t] in vistos); masa_hoy[t] = P[t, idx].sum() if idx else 0.0
    vistos.add(int(y[t]))
    entrop[t] = -(P[t] * np.log2(P[t])).sum()
for nom, g in (("mie-vie", G), ("resto", ~G)):
    print(f"{nom:8s} mbits {bits[g].mean():6.1f} | Top5 obs {100*h5[g].mean():.2f}% vs masa prometida {100*m5[g].mean():.2f}% | "
          f"Top15 obs {100*h15[g].mean():.2f}% vs masa {100*m15[g].mean():.2f}% | ganador ya salido hoy obs {100*salio_hoy[g].mean():.2f}% vs P {100*masa_hoy[g].mean():.2f}% | entropia P {entrop[g].mean():.4f} (max {math.log2(38):.4f})")
# calibracion O/E por bloque de dia
for nom, v, m in (("Top5", h5_d, suma_dia(m5)), ("Top15", h15_d, suma_dia(m15))):
    r = ratio_boot(v, m, GM); s = ratio_boot(v, m, ~GM)
    print(f"O/E {nom}: mie-vie {r[0]:.3f} [{r[1]:.3f};{r[2]:.3f}]  resto {s[0]:.3f} [{s[1]:.3f};{s[2]:.3f}]")

# --- aplanado hacia delante
print("\n== 6. Aplanar P^a solo en mie-vie, validacion hacia delante (a elegido con el pasado) ==")
anio = np.array([int(f[:4]) for f in fecha])
grid = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
def mb(a, rows):
    Q = P[rows] ** a; Q /= Q.sum(1, keepdims=True)
    return np.log2(38 * Q[np.arange(rows.sum()), y[rows]]) * 1000
tot_a = []; tot_1 = []; dias_eval = []
for Y in sorted(set(anio))[1:]:
    pas = G & (anio < Y); fut = G & (anio == Y)
    if pas.sum() < 300 or fut.sum() == 0: continue
    sc = {a: mb(a, pas).mean() for a in grid}; aopt = max(sc, key=sc.get)
    ma = mb(aopt, fut); m1 = mb(1.0, fut)
    print(f"{Y}: a elegido {aopt} (pasado mie-vie: {sc[aopt]:.1f} vs a=1 {sc[1.0]:.1f}); en {Y}: {ma.mean():.1f} vs {m1.mean():.1f} (dif {ma.mean()-m1.mean():+.2f})")
    tot_a.append(ma); tot_1.append(m1); dias_eval.append(inv[fut])
da = np.concatenate(tot_a) - np.concatenate(tot_1); di = np.concatenate(dias_eval)
u, ii = np.unique(di, return_inverse=True); sd = np.bincount(ii, weights=da); cn = np.bincount(ii).astype(float)
I = rng.integers(0, len(u), (4000, len(u))); b = sd[I].sum(1) / cn[I].sum(1)
print(f"AJUSTE hacia delante, mie-vie: {sd.sum()/cn.sum():+.2f} mbits/sorteo  IC95 bloques-dia [{np.percentile(b,2.5):+.2f}; {np.percentile(b,97.5):+.2f}]")
sc_all = {a: mb(a, G).mean() for a in grid}
print("optimo in-sample mie-vie (solo informativo):", {a: round(v, 1) for a, v in sc_all.items()})
sc_r = {a: mb(a, ~G).mean() for a in grid}
print("mismo grid en el resto:", {a: round(v, 1) for a, v in sc_r.items()})
