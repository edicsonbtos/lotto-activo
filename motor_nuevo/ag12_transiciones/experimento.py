# -*- coding: utf-8 -*-
"""ag12: ensamble + corrección lineal con 33 variables (ag02 + transiciones). Cross-fit 5 bloques + forward."""
import json, os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, os.path.join(MN, "ag02_residuo_boost")); sys.path.insert(0, AQUI)
import arnes as A  # noqa
import importlib.util as _iu
_sp = _iu.spec_from_file_location('exp_ag02', os.path.join(MN, 'ag02_residuo_boost', 'experimento.py'))
E2 = _iu.module_from_spec(_sp); _sp.loader.exec_module(E2)  # ag02: ajustar_lineal, cross_fit, forward, bloques_jornada
import rasgos12 as R  # noqa
LAM = 30.0
t0 = time.time()
D = A.datos().prefijo(A.CORTE)
Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
LPE = np.log(np.clip(Pens, 1e-12, None))
X, _ = R.construir(D, A.W); X = X.astype(np.float64)
dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
res, out = {}, []
def rep(nombre, Pc):
    s = A.informe(Pc, nombre); print(s, flush=True); out.append(s); res[nombre] = A.evaluar(Pc)
def cf(cols):
    Xc = X[:, :, cols]
    return E2.cross_fit(lambda tr: E2.ajustar_lineal(Xc[tr], LPE[tr], y[tr], LAM),
                        lambda w, te: E2.predecir_lineal(w, Xc[te], LPE[te]), blo), Xc
todas = list(range(R.F)); nuevas = list(range(27, 33)); viejas = list(range(27))
(P1, pars), Xc = cf(todas); rep("V1_33var_crossfit", P1); np.save(os.path.join(AQUI, "P_V1.npy"), P1)
Wb = np.array(pars)
for i, nm in enumerate(R.NOMBRES):
    print(f"  {nm:22s} {Wb[:, i].mean():+.3f} [{Wb[:, i].min():+.3f}, {Wb[:, i].max():+.3f}]")
Pf = E2.forward(lambda tr: E2.ajustar_lineal(X[tr], LPE[tr], y[tr], LAM),
                lambda w, te: E2.predecir_lineal(w, X[te], LPE[te]), blo)
Pf[blo == 0] = Pens[blo == 0]; rep("V1_forward_informativo", Pf)
(P0, _), _ = cf(nuevas); rep("V0_solo_6_transiciones", P0)
(P2, _), _ = cf(viejas); rep("ag02_27var_referencia", P2)
# V1 frente a ag02 (¿aportan las nuevas?)
d = A.mbits_fila(P1, y) - A.mbits_fila(P2, y)
res["V1_menos_ag02"] = A.ic_bloques(d, dia); print("V1 - ag02 mbits:", res["V1_menos_ag02"])
json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1)
open(os.path.join(AQUI, "salida_experimento.txt"), "w", encoding="utf-8").write("\n\n".join(out) + f"\nV1 - ag02: {res['V1_menos_ag02']}\n")
print(f"[{time.time()-t0:.0f} s]")
