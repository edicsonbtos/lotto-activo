# Parte A del PREREGISTRO: re-precio de Guacharo M2 (predicciones ya congeladas y ya puntuadas en la ciega b07)
import numpy as np, json, os
AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = r"C:\Users\edics\Downloads\lotto-activo\lotto-activo-motor\motor_nuevo\ronda3\b07_guacharo\ciega\salida.npz"
d = np.load(SAL, allow_pickle=True)
f = d["fecha"].astype(str); y = d["y"].astype(int); anim = [str(a) for a in d["animales"]]
i75 = anim.index("75")
K = 77

def evalua(m, etiqueta):
    P2 = d["P_M2"][m].astype(np.float32); P0 = d["P_N0"][m].astype(np.float32)
    yy = y[m]; ff = f[m]; n = len(yy); r = np.arange(n)
    dias, idx = np.unique(ff, return_inverse=True); D = len(dias)
    rng = np.random.default_rng(12345)
    def orden(P):
        Q = P + rng.random(P.shape).astype(np.float32) * 1e-9
        return np.argsort(-Q, axis=1)
    o2, o0 = orden(P2), orden(P0)
    def boot(v):
        g = np.random.default_rng(7); s = np.bincount(idx, v, D); c = np.bincount(idx, None, D)
        b = np.empty(2000)
        for i in range(2000):
            k = g.integers(0, D, D); b[i] = s[k].sum() / c[k].sum()
        return [round(float(v.mean()), 4), round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]
    out = {"ventana": etiqueta, "sorteos": n, "dias": D, "desde": ff[0], "hasta": ff[-1]}
    mb = 1000 * np.log2(P2[r, yy] / P0[r, yy])
    out["mbits_M2_menos_N0"] = boot(mb)
    for nom, o in [("M2", o2), ("N0", o0)]:
        t15 = (o[:, :15] == yy[:, None]).any(1).astype(float)
        out[nom + "_top15"] = boot(t15)
        out[nom + "_top15_incluye_75_frac"] = round(float((o[:, :15] == i75).any(1).mean()), 4)
        for pago in (60, 55, 50):
            mult = np.where(yy == i75, 2 * pago, pago)  # el 75 paga el doble (120x con 60x)
            ret = t15 * mult / 15 - 1
            out[f"{nom}_ret_top15_pago{pago}"] = boot(ret)
            st = np.array([2, 2, 2, 1, 1], float)
            hit = (o[:, :5] == yy[:, None]); g5 = (hit * st).sum(1)
            out[f"{nom}_ret_top5esc_pago{pago}"] = boot(g5 * mult / st.sum() - 1)
        out[nom + "_pago_equilibrio_top15"] = round(15 / t15.mean(), 2)
    out["azar_top15"] = round(15 / 77, 4)
    out["frec_75_obs_vs_esperado"] = round(float((yy == i75).mean() * K), 3)
    # por mes
    mes = np.array([x[:7] for x in ff]); pm = {}
    t15 = (o2[:, :15] == yy[:, None]).any(1)
    for mm in np.unique(mes):
        s = mes == mm; pm[mm] = [int(s.sum()), round(float(t15[s].mean()), 4)]
    out["M2_top15_por_mes"] = pm
    return out

res = {"ultimos_6m": evalua(f >= "2026-04-01", "2026-04-01..2026-09-27 (YA mirado en la ciega b07)"),
       "sellado_completo": evalua(np.ones(len(f), bool), "2024-11-22..2026-09-27 (ciega b07)")}
print(json.dumps(res, indent=1, ensure_ascii=False))
json.dump(res, open(os.path.join(AQUI, "resultado_a_guacharo.json"), "w"), indent=1, ensure_ascii=False)
