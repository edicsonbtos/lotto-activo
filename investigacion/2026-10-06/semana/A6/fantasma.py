# A6: look-elsewhere + métricas + segunda reconstrucción + potencia. Uso: python fantasma.py <SP>
import sys, numpy as np
from datetime import date
SP = sys.argv[1]
NPERM = 10000
FICH = np.array([2, 2, 2, 1, 1])

def residuos(P, y):
    """Devuelve dict métrica -> (r, v) por sorteo, contra lo que espera el motor."""
    n = len(y); o = np.argsort(-P, 1, kind="stable"); rk = np.argmax(o == y[:, None], 1)
    Ps = np.take_along_axis(P, o, 1); out = {}
    for k in (15, 5, 3):
        m = Ps[:, :k].sum(1); out[f"Top-{k}"] = ((rk < k) - m, m * (1 - m))
    L = np.log2(38 * np.clip(P, 1e-12, 1)); el = (P * L).sum(1)
    out["mbits"] = ((L[np.arange(n), y] - el) * 1000, ((P * L ** 2).sum(1) - el ** 2) * 1e6)
    g = 30 * FICH / 8                       # ganancia bruta por ficha si cae en el puesto k
    eg = (Ps[:, :5] * g).sum(1); eg2 = (Ps[:, :5] * g ** 2).sum(1)
    act = np.where(rk < 5, g[np.minimum(rk, 4)], 0.0)
    out["ret_T5"] = (act - eg, eg2 - eg ** 2)
    return out, rk

def calendario(f):
    dd = [date.fromisoformat(x) for x in f]
    return (np.array([d.weekday() for d in dd]), np.array([d.day for d in dd]), np.array([d.month for d in dd]))

def preparar(P, y, f, h):
    R, rk = residuos(P, y)
    dias = np.array(sorted(set(f))); di = {d: i for i, d in enumerate(dias)}; dix = np.array([di[x] for x in f])
    dw, dm, mo = calendario(dias)
    # particiones de calendario a nivel de jornada: lista (nombre, etiquetas por día, nombres de celda)
    parts = []
    nm = "lun mar mié jue vie sáb dom".split()
    parts.append(("día semana", [dw == k for k in range(7)], nm))
    parts.append(("par días consec.", [np.isin(dw, [k, (k + 1) % 7]) for k in range(7)], [f"{nm[k]}-{nm[(k+1)%7]}" for k in range(7)]))
    parts.append(("trío días consec.", [np.isin(dw, [k, (k + 1) % 7, (k + 2) % 7]) for k in range(7)], [f"{nm[k]}-{nm[(k+2)%7]}" for k in range(7)]))
    parts.append(("laborable/finde", [dw < 5, dw >= 5], ["lun-vie", "sáb-dom"]))
    parts.append(("día del mes", [dm == k for k in range(1, 32)], [f"día {k}" for k in range(1, 32)]))
    parts.append(("decena", [dm <= 10, (dm > 10) & (dm <= 20), dm > 20], ["1-10", "11-20", "21-31"]))
    parts.append(("semana del mes", [(dm - 1) // 7 == k for k in range(5)], [f"sem {k+1}" for k in range(5)]))
    meses = sorted(set(mo)); parts.append(("mes", [mo == k for k in meses], [f"mes {k}" for k in meses]))
    parts.append(("quincena", [dm <= 15, dm > 15], ["1-15", "16-31"]))
    parts.append(("par/impar", [dm % 2 == 0, dm % 2 == 1], ["par", "impar"]))
    cal = []
    for pn, masks, cn in parts:
        for m, c in zip(masks, cn): cal.append((pn, c, m))
    Mcal = np.array([m for _, _, m in cal]).T.astype(float)           # días × celdas
    fin = (dw >= 5).astype(int)
    data = {}
    for met, (r, v) in R.items():
        hm = np.array([r[h == k].mean() for k in range(12)])
        rc = r - hm[h]; rg = r - r.mean()
        Sd = np.bincount(dix, rc, len(dias)); Vd = np.bincount(dix, v, len(dias)); Nd = np.bincount(dix, None, len(dias))
        Sdh = np.zeros((len(dias), 12)); Vdh = np.zeros((len(dias), 12)); Ndh = np.zeros((len(dias), 12))
        np.add.at(Sdh, (dix, h), rc); np.add.at(Vdh, (dix, h), v); np.add.at(Ndh, (dix, h), 1)
        # hora (invariante a la permutación de jornadas)
        Sh = np.bincount(h, rg, 12); Vh = np.bincount(h, v, 12); Nh = np.bincount(h, None, 12)
        zh = Sh / np.sqrt(Vh * (1 - Nh / len(r)))
        data[met] = dict(r=r, v=v, rc=rc, Sd=Sd, Vd=Vd, Nd=Nd, Sdh=Sdh, Vdh=Vdh, Ndh=Ndh, zh=zh, n=len(r))
    return dict(dias=dias, dix=dix, dw=dw, dm=dm, mo=mo, cal=cal, Mcal=Mcal, fin=fin, data=data, rk=rk)

def zfam(Q, met, perm=None):
    """z de todas las celdas (calendario + hora×finde) con las etiquetas de día permutadas por perm."""
    d = Q["data"][met]; M = Q["Mcal"] if perm is None else Q["Mcal"][perm]
    fin = Q["fin"] if perm is None else Q["fin"][perm]
    S = M.T @ d["Sd"]; V = M.T @ d["Vd"]; N = M.T @ d["Nd"]
    zc = S / np.sqrt(V * (1 - N / d["n"]))
    F = np.stack([fin == 0, fin == 1]).astype(float)               # 2 × días
    S2 = F @ d["Sdh"]; V2 = F @ d["Vdh"]; N2 = F @ d["Ndh"]; Nh = d["Ndh"].sum(0)
    zhf = (S2 / np.sqrt(V2 * (1 - N2 / Nh))).ravel()
    return zc, zhf

def informe_familia(Q, met, rng, nperm=NPERM, titulo=""):
    zc, zhf = zfam(Q, met); zh = Q["data"][met]["zh"]
    allz = np.concatenate([zc, zh, zhf]); zmax = np.nanmax(np.abs(allz))
    print(f"\n=== {titulo} — {met}: max |z| por partición (contraste estratificado por hora) ===")
    names = [c for _, c, _ in Q["cal"]]; pn = [p for p, _, _ in Q["cal"]]
    for p in dict.fromkeys(pn):
        idx = [i for i, q in enumerate(pn) if q == p]; j = idx[int(np.nanargmax(np.abs(zc[idx])))]
        print(f"  {p:18} max|z| {abs(zc[j]):4.2f}  ({names[j]}, z {zc[j]:+.2f})")
    j = int(np.argmax(np.abs(zh))); print(f"  {'hora':18} max|z| {abs(zh[j]):4.2f}  (hora {j+8}:00, z {zh[j]:+.2f})")
    j = int(np.nanargmax(np.abs(zhf))); print(f"  {'hora×finde':18} max|z| {abs(zhf[j]):4.2f}  ({'finde' if j>=12 else 'lab'} {j%12+8}:00, z {zhf[j]:+.2f})")
    # nulo
    nd = len(Q["dias"]); mx = np.empty(nperm); mxcal = np.empty(nperm); mvf_null = np.empty(nperm); d1 = np.empty(nperm)
    i_mvf = [i for i, (p, c, _) in enumerate(Q["cal"]) if p == "trío días consec." and c == "mié-vie"][0]
    i_dw = [i for i, (p, _, _) in enumerate(Q["cal"]) if p == "día semana"]
    perms = []
    for b in range(nperm):
        pm = rng.permutation(nd); perms.append(pm)
        a, c = zfam(Q, met, pm)
        mx[b] = max(np.nanmax(np.abs(a)), np.nanmax(np.abs(c)), np.max(np.abs(zh))); mxcal[b] = np.nanmax(np.abs(a))
        mvf_null[b] = a[i_mvf]; d1[b] = np.nanmax(np.abs(a[i_dw]))
    zobs_mvf = zc[i_mvf]; zobs_dw = np.nanmax(np.abs(zc[i_dw]))
    print(f"  OBS: max|z| familia {zmax:.2f};  mié-vie vs resto z {zobs_mvf:+.2f};  max|z| un día suelto {zobs_dw:.2f}")
    print(f"  NULO max|z| familia: mediana {np.median(mx):.2f}, p95 {np.percentile(mx,95):.2f}, p99 {np.percentile(mx,99):.2f}")
    print(f"  p familiar (max|z|perm ≥ obs) = {np.mean(mx >= zmax - 1e-9):.4f}   |  p familiar solo calendario = {np.mean(mxcal >= np.nanmax(np.abs(zc)) - 1e-9):.4f}")
    print(f"  p(max|z| familia nula ≥ |z| del mejor día suelto {zobs_dw:.2f}) = {np.mean(mx >= zobs_dw):.4f}")
    print(f"  p contraste PRE-FIJADO mié-vie (bilateral, permutación) = {np.mean(np.abs(mvf_null) >= abs(zobs_mvf)):.4f}")
    return dict(mx=mx, zmax=zmax, zmvf=zobs_mvf, perms=perms)

def ic_mvf(Q, met, rng, B=4000):
    d = Q["data"][met]; dix = Q["dix"]; mvf_d = np.isin(Q["dw"], [2, 3, 4])
    Sd = d["Sd"]; Nd = d["Nd"]
    # diferencia de residuo medio (centrado por hora) mié-vie − resto
    def dif(idx):
        a = mvf_d[idx]; return Sd[idx][a].sum() / Nd[idx][a].sum() - Sd[idx][~a].sum() / Nd[idx][~a].sum()
    nd = len(Sd); obs = dif(np.arange(nd)); bs = [dif(rng.integers(0, nd, nd)) for _ in range(B)]
    return obs, np.percentile(bs, 2.5), np.percentile(bs, 97.5)

def main():
    rng = np.random.default_rng(20261006)
    z = np.load(SP + "/prod_0605.npz", allow_pickle=True); P, t, y, f, h = z["P"], z["t"], z["y"], z["f"], z["h"]
    m26 = f >= "2026-01-01"; mdev = t < 9357
    Q = preparar(P[m26], y[m26], f[m26], h[m26]); Qd = preparar(P[mdev], y[mdev], f[mdev], h[mdev])
    print(f"2026: {m26.sum()} sorteos, {len(Q['dias'])} jornadas.  dev: {mdev.sum()} sorteos, {len(Qd['dias'])} jornadas.")
    # sobredispersión por jornada: Var(suma diaria de residuos)/Σv
    for lab, QQ in (("2026", Q), ("dev", Qd)):
        for met in ("Top-15", "Top-5", "mbits"):
            d = QQ["data"][met]; full = d["Nd"] == 12
            print(f"  sobredispersión diaria {lab} {met}: Var(Σr día)/E(Σv día) = {np.var(d['Sd'][full]) / d['Vd'][full].mean():.2f}")
    res = {}
    for met in ("Top-15", "Top-5", "Top-3", "mbits", "ret_T5"):
        res[met] = informe_familia(Q, met, rng, NPERM if met == "Top-15" else 3000, "2026")
        o, lo, hi = ic_mvf(Q, met, rng)
        u = {"Top-15": 100, "Top-5": 100, "Top-3": 100, "mbits": 1, "ret_T5": 100}[met]
        print(f"  mié-vie − resto (residuo medio por sorteo, centrado por hora): {o*u:+.2f} [IC95 jornadas {lo*u:+.2f}; {hi*u:+.2f}] {'pp' if met.startswith('Top') else ('mbits' if met=='mbits' else '% por ficha')}")
    # trimestres bajo el nulo, Top-15
    d = Q["data"]["Top-15"]; dix = Q["dix"]; r = d["r"]
    rk = Q["rk"]; hit = (rk < 15).astype(float); E = hit - r
    Od = np.bincount(dix, hit, len(Q["dias"])); Ed = np.bincount(dix, E, len(Q["dias"]))
    tri = np.where(Q["mo"] <= 3, 0, np.where(Q["mo"] <= 6, 1, 2))
    i_mvf = [i for i, (p, c, _) in enumerate(Q["cal"]) if p == "trío días consec." and c == "mié-vie"][0]
    def oe_tri(mask): return [Od[mask & (tri == k)].sum() / Ed[mask & (tri == k)].sum() for k in range(3)]
    mvf_d = np.isin(Q["dw"], [2, 3, 4]); print(f"\nTop-15 O/E crudo mié-vie por trimestre (obs): {np.round(oe_tri(mvf_d),2)}; resto {np.round(oe_tri(~mvf_d),2)}")
    # nulo: en cada permutación, la celda de calendario con max|z| (solo particiones de calendario); ¿estable en 3 trim?
    cnt = 0; cnt_strong = 0; nb = 3000
    for b in range(nb):
        pm = res["Top-15"]["perms"][b]; a, _ = zfam(Q, "Top-15", pm); j = int(np.nanargmax(np.abs(a)))
        mask = Q["Mcal"][pm][:, j] > 0; sgn = np.sign(a[j])
        ot = np.array(oe_tri(mask)); rt = np.array(oe_tri(~mask))
        if np.all(np.sign(ot - rt) == sgn): cnt += 1
        if np.all(sgn * (ot - rt) >= 0.10): cnt_strong += 1
    print(f"Nulo (Top-15): la mejor celda va en el mismo sentido en los 3 trimestres en {cnt/nb*100:.0f}% de las permutaciones; con diferencia ≥ 0,10 de O/E en cada trimestre en {cnt_strong/nb*100:.0f}%")
    # dev
    rd = informe_familia(Qd, "Top-15", rng, 3000, "dev 2024-25")
    # potencia
    full = d["Nd"] == 12; sd_dia = np.sqrt(np.var(d["Sd"][full]))   # sd de la suma diaria de residuos centrados
    o, lo, hi = ic_mvf(Q, "Top-15", rng, 10)
    for frac in (1.0, 0.5):
        delta = abs(o) * frac   # diferencia de tasa por sorteo
        for za, lab in ((1.96, "bilateral"), (1.645, "unilateral")):
            # Var(diff) ≈ sd_dia²/12² · (1/n1 + 1/n2) por jornadas; n1 = 3/7 N, n2 = 4/7 N
            Nd_need = (sd_dia / 12) ** 2 * (7 / 3 + 7 / 4) * ((za + 0.8416) / delta) ** 2
            print(f"Potencia 80% ({lab}, α=0,05), efecto {frac:.0%} del observado (Δ={delta*100:.1f} pp): {Nd_need:.0f} jornadas = {Nd_need*12:.0f} sorteos ({Nd_need/30.4:.1f} meses)")
    from scipy.stats import norm
    for frac in (1.0, 0.5):
        delta = abs(o) * frac; Nd_plan = 92; se = (sd_dia / 12) * np.sqrt((7 / 3 + 7 / 4) / Nd_plan)
        print(f"Plan en vivo (92 jornadas, 7-oct..6-ene), efecto {frac:.0%}: potencia unilateral 5% = {norm.sf(1.645 - delta/se):.2f}; con IC90 (equiv.) igual")
    # segunda reconstrucción
    zv = np.load(SP + "/vivo_rk.npz", allow_pickle=True)
    Pv, tv, fv, hv = zv["P"], zv["t"], zv["f"], zv["h"]
    # hist_hoy y hist_0605 difieren en 1 fila (2026-06-24 11): se alinea por (fecha, hora)
    from_fh = {(a, int(b)): i for i, (a, b) in enumerate(zip(f, h))}; ii = np.array([from_fh[(a, int(b))] for a, b in zip(fv, hv)]); yv = y[ii]
    assert np.all(f[ii] == fv) and np.all(h[ii] == hv)
    rkv_chk = np.argmax(np.argsort(-Pv, 1, kind="stable") == yv[:, None], 1); print(f"  rk guardado == rk recalculado con y de hist_0605: {np.mean(rkv_chk == zv['rk'])*100:.2f}%")
    print(f"\nvivo_rk.npz: claves {zv.files}; {len(tv)} sorteos {fv[0]}..{fv[-1]} (ensamble_v2 walk-forward sobre hist_hoy, SIN ajustes de producción).")
    cor = np.corrcoef(np.log(Pv).ravel(), np.log(P[ii]).ravel())[0, 1]; agree = np.mean(np.argmax(Pv, 1) == np.argmax(P[ii], 1))
    rkv = zv["rk"]; rk_prod = np.argmax(np.argsort(-P,1,kind="stable") == y[:, None], 1); print(f"  correlación log P con prod_0605: {cor:.3f}; mismo #1: {agree*100:.0f}%; ganador en Top-15 en una y no en otra: {np.mean((rkv<15)!=(rk_prod[ii]<15))*100:.1f}%")
    m = fv >= "2026-01-01"; Qv = preparar(Pv[m], yv[m], fv[m], hv[m])
    for met in ("Top-15", "Top-5", "mbits"):
        dwv = Qv["dw"]; d = Qv["data"][met]
        zc, _ = zfam(Qv, met); i_mvf = [i for i, (p, c, _) in enumerate(Qv["cal"]) if p == "trío días consec." and c == "mié-vie"][0]
        idw = [i for i, (p, _, _) in enumerate(Qv["cal"]) if p == "día semana"]
        print(f"  [2ª reconstr. 2026] {met}: z por día " + " ".join(f"{c}{zc[i]:+.1f}" for i, c in zip(idw, "LMXJVSD")) + f" | mié-vie vs resto z {zc[i_mvf]:+.2f}")
    # vivo desde 2026-09-15 (ambas reconstrucciones)
    for lab, PP, ff, yy, hh in (("prod_0605", P, f, y, h), ("vivo_rk", Pv, fv, yv, hv)):
        m = ff >= "2026-09-15"; R, rk2 = residuos(PP[m], yy[m]); dw2 = calendario(ff[m])[0]; a = np.isin(dw2, [2, 3, 4])
        hit = rk2 < 15; E = hit - R["Top-15"][0]
        for k, c in zip(range(7), "LMXJVSD"):
            b = dw2 == k
            if b.sum(): print(f"     {c}: O/E {hit[b].sum()/E[b].sum():.2f} ({hit[b].sum()}/{b.sum()})", end="")
        print()
        print(f"  VIVO {lab} (desde 15-sep, {m.sum()} sorteos, {len(set(ff[m][a]))} jornadas mié-vie): Top-15 O/E mié-vie {hit[a].sum()/E[a].sum():.2f} ({hit[a].sum()}/{a.sum()}), resto {hit[~a].sum()/E[~a].sum():.2f} ({hit[~a].sum()}/{(~a).sum()})")

def cronologia(SP):
    z = np.load(SP + "/prod_0605.npz", allow_pickle=True); P, t, y, f, h = z["P"], z["t"], z["y"], z["f"], z["h"]
    R, rk = residuos(P, y); r = R["Top-15"][0]; hit = rk < 15; E = hit - r
    dw = calendario(f)[0]; a = np.isin(dw, [2, 3, 4]); dom = dw == 6
    print("\nCronología por semestre (Top-15 O/E crudo): mié-vie | resto(sin dom) | domingo")
    for lo, hi in (("2024-03-01","2024-08-31"),("2024-09-01","2024-12-31"),("2025-01-01","2025-04-30"),("2025-05-01","2025-08-31"),("2025-09-01","2025-12-31"),
                   ("2026-01-01","2026-03-31"),("2026-04-01","2026-06-30"),("2026-07-01","2026-10-05")):
        m = (f >= lo) & (f <= hi); b = m & ~a & ~dom
        print(f"  {lo}..{hi}: {hit[m&a].sum()/E[m&a].sum():.2f} | {hit[b].sum()/E[b].sum():.2f} | {hit[m&dom].sum()/E[m&dom].sum():.2f}")

if __name__ == "__main__":
    cronologia(SP)
    main()
