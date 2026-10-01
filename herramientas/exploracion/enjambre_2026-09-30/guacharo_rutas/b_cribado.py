# Parte B del PREREGISTRO: cribado de B1 (dupleta 1000x) y B2 (fuerza de no-repeticion en linea).
# Uso:  python b_cribado.py dev          -> solo desarrollo (filas [2000, 9357))
#       python b_cribado.py confirmar B1 -> UNA mirada a 2026-04-01..09-16 (solo si B1 paso en dev)
import sys, os, json
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
PROD = r"C:\Users\edics\Downloads\lotto-activo\lotto-activo"
MOTOR = r"C:\Users\edics\Downloads\lotto-activo\lotto-activo-motor"
modo = sys.argv[1]

if modo == "dev":
    sys.path.insert(0, os.path.join(PROD, "herramientas")); import lotto_eval as LE
    D = LE.cargar(os.path.join(PROD, "historial.txt"))
    c = np.load(os.path.join(PROD, "herramientas", "exploracion", "calor_cache.npz"))
    P = c["P"].astype(np.float32); y = c["y"].astype(int); a, b = 2000, 9357
    assert (D.seq[a:b] == y).all()
    mask_eval = np.ones(len(y), bool)
else:
    reg = os.path.join(AQUI, "registro.jsonl")
    if any('"confirmacion"' in l and sys.argv[2] in l for l in open(reg)):
        sys.exit("La confirmacion ya se corrio: no se repite.")
    sys.path.insert(0, os.path.join(MOTOR, "herramientas")); import lotto_eval as LE
    D = LE.cargar(os.path.join(MOTOR, "historial.txt"))
    P = np.load(os.path.join(MOTOR, "motor_nuevo", "reciente", "P_ens_reciente.npy")).astype(np.float32)
    a, b = 9357, 12511; y = np.asarray(D.seq[a:b]).astype(int)
    mask_eval = np.array([f >= "2026-04-01" for f in D.fecha[a:b]])
P = P / P.sum(1, keepdims=True)
hora = np.asarray(D.hora[a:b]); dia = np.asarray(D.dia[a:b]); fecha = np.array(D.fecha[a:b])
seq_all = np.asarray(D.seq); dia_all = np.asarray(D.dia)
n = len(y); r = np.arange(n)

def boot(v, grp):
    u, idx = np.unique(grp, return_inverse=True); Dn = len(u)
    s = np.bincount(idx, v, Dn); cnt = np.bincount(idx, None, Dn)
    g = np.random.default_rng(7); bb = np.empty(2000)
    for i in range(2000):
        k = g.integers(0, Dn, Dn); bb[i] = s[k].sum() / cnt[k].sum()
    return [round(float(v.mean()), 4), round(float(np.percentile(bb, 2.5)), 4), round(float(np.percentile(bb, 97.5)), 4), int(len(v))]

def mitades(v):
    h = len(v) // 2; return [round(float(v[:h].mean()), 4), round(float(v[h:].mean()), 4)]

rng = np.random.default_rng(12345)
orden = np.argsort(-(P + rng.random(P.shape).astype(np.float32) * 1e-9), axis=1)
out = {"modo": " ".join(sys.argv[1:]), "filas": f"{a}..{b}", "desde": fecha[mask_eval][0], "hasta": fecha[mask_eval][-1]}

# ---------- referencia: animal suelto 30x ----------
t15 = (orden[:, :15] == y[:, None]).any(1).astype(float)
st = np.array([2, 2, 2, 1, 1], float); g5 = ((orden[:, :5] == y[:, None]) * st).sum(1)
m = mask_eval
out["suelto_top15_acierto"] = boot(t15[m], dia[m])
out["suelto_top15_ret_30x"] = boot((t15 * 30 / 15 - 1)[m], dia[m])
out["suelto_top5esc_ret_30x"] = boot((g5 * 30 / 8 - 1)[m], dia[m])

# ---------- B1: dupleta (h, h+1) con la lista Top-k de P_h ----------
par = np.where((dia[:-1] == dia[1:]) & (hora[1:] == hora[:-1] + 1))[0]
par = par[mask_eval[par] & mask_eval[par + 1]]
B1 = {"pares": int(len(par))}
for k in (5, 10, 15):
    T = orden[par, :k]
    hit = ((T == y[par, None]).any(1) & (T == y[par + 1, None]).any(1) & (y[par] != y[par + 1])).astype(float)
    fichas = k * (k - 1)
    B1[f"k{k}"] = {"fichas": fichas, "acierto_par": boot(hit, dia[par]),
                   "ret_1000x": boot(hit * 1000 / fichas - 1, dia[par]),
                   "ret_100x": boot(hit * 100 / fichas - 1, dia[par]),
                   "mitades_ret_1000x": mitades(hit * 1000 / fichas - 1),
                   "pago_equilibrio": round(fichas / max(hit.mean(), 1e-9), 1),
                   "azar_acierto_par": round(k * (k - 1) / (38 * 37), 4)}
    # por hora de la primera pata
    B1[f"k{k}"]["ret_1000x_por_hora"] = {int(h): round(float((hit * 1000 / fichas - 1)[hora[par] == h].mean()), 3) for h in np.unique(hora[par])}
# mbits del par (P_h(a)*P_h(b)/(1-P_h(a))) contra azar sin repeticion
pa = P[par, y[par]]; pb = P[par, y[par + 1]]
q = np.where(y[par] != y[par + 1], pa * pb / np.maximum(1 - pa, 1e-9), 1e-9)
B1["mbits_par_vs_azar"] = boot(1000 * np.log2(q * 38 * 37), dia[par])
v = B1["k15"]["ret_1000x"]
B1["PASA_DEV"] = bool(v[0] > 0 and v[1] > 0 and min(B1["k15"]["mitades_ret_1000x"]) > 0)
out["B1_dupleta"] = B1

# ---------- B2: fuerza de no-repeticion estimada en linea ----------
if modo == "dev" or (len(sys.argv) > 2 and sys.argv[2] == "B2"):
    # R_t: animales ya salidos hoy antes de t (con la historia completa, no solo el tramo)
    R = np.zeros((n, 38), bool)
    for t in range(n):
        g = a + t; j = g - 1
        while j >= 0 and dia_all[j] == dia_all[g]:
            R[t, seq_all[j]] = True; j -= 1
    obs = R[r, y].astype(float); esp = (P * R).sum(1)
    udias = np.unique(dia); th = np.ones(n, np.float32)
    # acumulados por dia (solo dentro del tramo; los primeros 30 dias quedan con theta ~ (O+2)/(E+2) sobre menos dias)
    Od = {d_: obs[dia == d_].sum() for d_ in udias}; Ed = {d_: esp[dia == d_].sum() for d_ in udias}
    for i_, d_ in enumerate(udias):
        prev = [x for x in udias[max(0, i_ - 60):i_] if d_ - 30 <= x < d_]
        O = sum(Od[x] for x in prev); E = sum(Ed[x] for x in prev)
        th[dia == d_] = np.clip((O + 2) / (E + 2), 0.25, 4)
    P2 = P * np.where(R, th[:, None], 1); P2 /= P2.sum(1, keepdims=True)
    dmb = 1000 * np.log2(P2[r, y] / P[r, y])
    o2 = np.argsort(-(P2 + rng.random(P2.shape).astype(np.float32) * 1e-9), axis=1)
    m = mask_eval
    B2 = {"theta_media": round(float(th[m].mean()), 3), "theta_p10_p90": [round(float(np.percentile(th[m], 10)), 3), round(float(np.percentile(th[m], 90)), 3)],
          "obs_vs_esp_repeticion": [int(obs[m].sum()), round(float(esp[m].sum()), 1)],
          "delta_mbits": boot(dmb[m], dia[m]), "mitades": mitades(dmb[m]),
          "por_hora": {int(h): round(float(dmb[m & (hora == h)].mean()), 2) for h in np.unique(hora)},
          "delta_top15_pp": round(100 * float(((o2[:, :15] == y[:, None]).any(1).astype(float) - (orden[:, :15] == y[:, None]).any(1))[m].mean()), 3),
          "delta_top5_pp": round(100 * float(((o2[:, :5] == y[:, None]).any(1).astype(float) - (orden[:, :5] == y[:, None]).any(1))[m].mean()), 3)}
    v = B2["delta_mbits"]
    B2["PASA_DEV"] = bool(v[0] >= 3 and v[1] > 0 and min(B2["mitades"]) > 0)
    out["B2_regimen"] = B2

print(json.dumps(out, indent=1, ensure_ascii=False))
nom = "resultado_b_dev.json" if modo == "dev" else f"resultado_b_confirmacion_{sys.argv[2]}.json"
json.dump(out, open(os.path.join(AQUI, nom), "w"), indent=1, ensure_ascii=False)
if modo != "dev":
    import hashlib, datetime
    with open(os.path.join(AQUI, "registro.jsonl"), "a") as fh:
        fh.write(json.dumps({"archivo": nom, "momento": "confirmacion", "ruta": sys.argv[2],
                             "sha256": hashlib.sha256(open(os.path.join(AQUI, nom), "rb").read()).hexdigest(),
                             "hora": datetime.datetime.now().isoformat(timespec="seconds")}) + "\n")
