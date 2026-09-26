# -*- coding: utf-8 -*-
"""ag04_no_estacionario: ensamble adaptativo (Kalman / olvido corto / submodelos rápidos) frente al ensamble_v2.

Uso: PYTHONIOENCODING=utf-8 python motor_nuevo/ag04_no_estacionario/experimento.py
Requiere cache_sub_*.npy (python cache_sub.py base; python cache_sub.py rapidos).
Solo usa filas < 9357. Determinista (no hay azar salvo el desempate fijo del arnés).
"""
import json, os, sys, importlib.util
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import nucleo as N  # noqa: E402

A0 = 1000                     # arranque de los submodelos (como ensamble.py)
NBLOQ = 5
QS = [1e-7, 1e-6, 1e-5, 1e-4]
TAUS = [300, 1000, 3000]


def cargar_L(tags):
    Ps = [np.load(os.path.join(AQUI, f"cache_sub_{t}.npy")) for t in tags]
    L = np.stack([np.log(np.clip(P, 1e-9, None)) for P in Ps], axis=1)
    return L - np.log(np.exp(L).sum(2, keepdims=True))


def bloques(dia_dev):
    """5 bloques contiguos de jornadas sobre las filas de desarrollo."""
    ud = np.unique(dia_dev)
    cortes = np.array_split(ud, NBLOQ)
    b = np.empty(len(dia_dev), int)
    for i, c in enumerate(cortes):
        b[np.isin(dia_dev, c)] = i
    return b


def crossfit(Ps, y, blq):
    """Ps: lista de (n_dev, K) por valor de hiperparámetro. Fila del bloque b usa el hp con mejor
    log-verosimilitud media en los otros bloques. Devuelve P y la elección por bloque."""
    ll = np.stack([np.log(np.clip(P[np.arange(len(y)), y], 1e-12, None)) for P in Ps])  # (H, n)
    out = np.empty_like(Ps[0]); elig = []
    for b in range(NBLOQ):
        fuera = blq != b
        h = int(np.argmax(ll[:, fuera].mean(1)))
        elig.append(h)
        out[blq == b] = Ps[h][blq == b]
    return out, elig


def main():
    D = A.datos().prefijo(A.CORTE)
    seq = np.asarray(D.seq)
    P_ens, y = A.base()
    dia_dev = D.dia[A.W:A.CORTE]
    blq = bloques(dia_dev)
    yl = seq[A0:A.CORTE]
    res = {}; lineas = []

    def reg(nombre, P, extra=None):
        r = A.evaluar(P); r.update(extra or {})
        res[nombre] = r
        s = A.informe(P, nombre); print(s, flush=True); lineas.append(s)
        if extra:
            print("  ", extra, flush=True); lineas.append("   " + json.dumps(extra))

    # Control: ensamble_v2 reconstruido
    L = cargar_L(["intradia_v2", "secuencia_v3", "haz_v1"])
    Pc, _ = N.ensamble_refit(L, yl, A.W - A0, R=250, tau=3000.0, lam=5.0)
    dif = float(np.abs(Pc - P_ens).max())
    print("control ensamble reconstruido: max|dif| con la caché =", dif, flush=True)
    lineas.append(f"control ensamble reconstruido: max|dif| = {dif}")

    # V1 Kalman
    Pk = []; W_tray = {}
    for q in QS:
        P, Wt = N.kalman(L, yl, q=q, s0=0.1)
        Pk.append(P[A.W - A0:]); W_tray[q] = Wt
        print(f"  V1 q={q:g}: mbits {A.mbits_fila(P[A.W - A0:], y).mean():+.2f}", flush=True)
    P1, e1 = crossfit(Pk, y, blq)
    reg("V1_kalman_crossfit", P1, {"q_por_bloque": [QS[i] for i in e1]})
    Wt = W_tray[QS[e1[0]]]
    idx = np.arange(A.W - A0, len(yl), 500)
    print("  trayectoria w (q del bloque 0):", [(int(i + A0), np.round(Wt[i], 3).tolist()) for i in idx], flush=True)

    # V2 olvido corto, R=50
    Pv = []
    for tau in TAUS:
        P, _ = N.ensamble_refit(L, yl, A.W - A0, R=50, tau=float(tau), lam=5.0)
        Pv.append(P)
        print(f"  V2 tau={tau}: mbits {A.mbits_fila(P, y).mean():+.2f}", flush=True)
    P2, e2 = crossfit(Pv, y, blq)
    reg("V2_olvido_corto_crossfit", P2, {"tau_por_bloque": [TAUS[i] for i in e2]})

    # V3 submodelos rápidos
    rap = ["intradia_v2_tau400_ventana1500", "haz_v1_cada250_ventana2000_vida_media800"]
    if all(os.path.exists(os.path.join(AQUI, f"cache_sub_{t}.npy")) for t in rap):
        L5 = cargar_L(["intradia_v2", "secuencia_v3", "haz_v1"] + rap)
        P3, ws = N.ensamble_refit(L5, yl, A.W - A0, R=250, tau=3000.0, lam=5.0)
        reg("V3_submodelos_rapidos", P3, {"w_final": np.round(ws[-1][1], 3).tolist()})
    else:
        print("V3: faltan caches de submodelos rápidos", flush=True)

    # Δ por trimestre (informativo) de V1
    d = A.mbits_fila(P1, y) - A.mbits_fila(P_ens, y)
    tri = (dia_dev - dia_dev[0]) // 91
    print("  V1 Δ por trimestre:", [round(float(d[tri == k].mean()), 1) for k in np.unique(tri)], flush=True)

    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1)
    open(os.path.join(AQUI, "salida_experimento.txt"), "w", encoding="utf-8").write("\n".join(lineas) + "\n")


if __name__ == "__main__":
    main()
