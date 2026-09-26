# -*- coding: utf-8 -*-
"""ag06_objetivo_dinero: reordenador sobre el logit del ensamble entrenado con pérdida de DINERO
(Top-5 escalonado 2-2-2-1-1, rango suave) frente a control log-loss. Cross-fitting en 5 bloques
contiguos de jornadas del desarrollo [2000, 9357). Determinista (L-BFGS desde w=0, sin azar)."""
import json, os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A
import rasgos as R
import nucleo as N

t0 = time.time()
D = A.datos()
P_ens, y = A.base()
Dd = D.prefijo(A.CORTE)                            # nada >= 9357
X = R.construir(Dd, A.W).astype(np.float64)        # (7357, 38, F)
assert X.shape[0] == len(y)
Pn = np.clip(P_ens, 1e-12, None); Pn /= Pn.sum(1, keepdims=True)
L = np.log(Pn)
dia = np.asarray(Dd.dia[A.W:A.CORTE])
ud = np.unique(dia)
bloque_dia = np.minimum((np.arange(len(ud)) * 5) // len(ud), 4)
blq = bloque_dia[np.searchsorted(ud, dia)]
print(f"filas {len(y)}, días {len(ud)}, filas por bloque {np.bincount(blq).tolist()}")

VARIANTES = [("V_dinero", "dinero", {"tau": 0.25}),
             ("V_logloss", "log", {}),
             ("V_dinero_tau0.1", "dinero", {"tau": 0.10})]
res, pesos = {}, {}
for nombre, tipo, kw in VARIANTES:
    Pc = np.zeros_like(Pn); ws, cs = [], []
    for b in range(5):
        tr, te = blq != b, blq == b
        w = N.ajustar(L[tr], X[tr], y[tr], tipo, **kw)
        s_tr = L[tr] + X[tr] @ w
        c = N.ajustar_c(s_tr, y[tr]) if tipo == "dinero" else 1.0
        Pc[te] = N.softmax(c * (L[te] + X[te] @ w))
        ws.append(w.tolist()); cs.append(c)
    r = A.evaluar(Pc)
    res[nombre] = r; pesos[nombre] = {"w_por_bloque": ws, "c_por_bloque": cs}
    print(A.informe(Pc, nombre))
    print("  w medio:", dict(zip(R.NOMBRES, np.round(np.mean(ws, 0), 3).tolist())), " c:", np.round(cs, 3).tolist())
    # dinero suave en test (diagnóstico): retorno ~ ganancia
    np.save(os.path.join(AQUI, f"P_{nombre}.npy"), Pc.astype(np.float32))
    print(f"  ({time.time()-t0:.0f} s)")

# Congelar V_dinero (primaria) con todo el desarrollo [2000, 9357)
w = N.ajustar(L, X, y, "dinero", tau=0.25)
c = N.ajustar_c(L + X @ w, y)
json.dump({"variante": "V_dinero", "tau": 0.25, "sigma": N.SIG, "lam": N.LAM, "nombres": R.NOMBRES,
           "w": w.tolist(), "c": c, "ajustado_con_filas": [A.W, A.CORTE]},
          open(os.path.join(AQUI, "parametros.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("congelado V_dinero:", dict(zip(R.NOMBRES, np.round(w, 3).tolist())), "c", round(c, 3))
json.dump({"primaria": "V_dinero", "resultados": res, "pesos": pesos},
          open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"total {time.time()-t0:.0f} s")
