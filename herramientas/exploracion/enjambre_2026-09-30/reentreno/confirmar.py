# -*- coding: utf-8 -*-
"""Confirmacion UNICA (PREREGISTRO.md): 2026-04-01..2026-09-29, variante elegida en desarrollo vs ensamble fijo.
Se niega a correr dos veces (registro_confirmacion.jsonl)."""
import hashlib, json, os, sys, time
import numpy as np
import comun as C
import sub
REG = os.path.join(C.AQUI, "registro_confirmacion.jsonl")
if os.path.exists(REG) and "--forzar-no" not in sys.argv:
    sys.exit("La confirmacion ya se corrio (registro_confirmacion.jsonl). No se repite.")
dev = json.load(open(os.path.join(C.AQUI, "dev_resultados.json"), encoding="utf-8"))
g = dev["elegida"]
D = sub.datos("todo"); y = np.asarray(D.seq); dias = np.asarray(D.dia); fe = np.array(D.fecha)
t0 = sub.fila_inicio_conf(D); n = len(y)
# control: walk-forward sin fuga -> las filas de desarrollo coinciden con la fase dev
for c in C.GRUPOS["base"]:
    a = np.load(os.path.join(C.AQUI, "cache", f"dev_{c}.npy")); b = np.load(os.path.join(C.AQUI, "cache", f"todo_{c}.npy"))[:len(a)]
    print("control", c, "max|dif| dev vs todo:", float(np.abs(a - b).max()))
Y = y[C.ARRANQUE:]
Pb = C.combinar(C.cargar_L("todo", C.GRUPOS["base"]), Y, t0, **C.COMB["base"])
Pv = C.combinar(C.cargar_L("todo", C.GRUPOS[g]), Y, t0, **C.COMB[g])
# informativo: ensamble congelado al 2026-03-31 (submodelos y pesos ajustados una vez, sin reentrenar)
Lb = C.cargar_L("todo", C.GRUPOS["base"]); j = t0 - C.ARRANQUE
wc = C.ENS.ajustar_pesos(Lb[:j], Y[:j], np.full(3, 1 / 3), 5.0, np.exp(-(j - 1 - np.arange(j)) / 3000.0))
Lc = np.stack([np.log(np.clip(np.load(os.path.join(C.AQUI, "cache", f"todo_congelado_{c}.npy")).astype(np.float64), 1e-9, None)) for c in "ISH"], 1)
Lc -= np.log(np.exp(Lc).sum(2, keepdims=True))
z = np.einsum("nmk,m->nk", Lc, wc); z -= z.max(1, keepdims=True); Pc = np.exp(z); Pc /= Pc.sum(1, keepdims=True)
yy = y[t0:]; dd = dias[t0:]; mes = np.array([f[:7] for f in fe[t0:]])
M = {"ensamble": C.por_sorteo(Pb, yy), g: C.por_sorteo(Pv, yy), "congelado": C.por_sorteo(Pc, yy)}
def resumen(sel):
    out = {}
    for k, m in M.items():
        r = {"n": int(sel.sum()), "mbits": round(float(m["mb"][sel].mean()), 1)}
        for q in ("t5", "t15", "r5", "r15", "r15p"):
            r[q] = round(float(m[q][sel].mean()) * 100, 2)
        if k != "ensamble":
            r["delta_mbits"] = [round(x, 2) for x in C.boot_dif(m["mb"][sel] - M["ensamble"]["mb"][sel], dd[sel])]
            r["delta_t5_pp"] = [round(100 * x, 2) for x in C.boot_dif(m["t5"][sel] - M["ensamble"]["t5"][sel], dd[sel])]
            r["delta_t15_pp"] = [round(100 * x, 2) for x in C.boot_dif(m["t15"][sel] - M["ensamble"]["t15"][sel], dd[sel])]
            r["delta_r5_pp"] = [round(100 * x, 2) for x in C.boot_dif(m["r5"][sel] - M["ensamble"]["r5"][sel], dd[sel])]
            r["delta_r15_pp"] = [round(100 * x, 2) for x in C.boot_dif(m["r15"][sel] - M["ensamble"]["r15"][sel], dd[sel])]
        out[k] = r
    return out
todo = np.ones(len(yy), bool)
res = {"elegida": g, "pasa_barra_dev": dev[g]["pasa_barra"], "ventana": [str(fe[t0]), str(fe[-1])], "total": resumen(todo),
       "por_mes": {m_: resumen(mes == m_) for m_ in sorted(set(mes))},
       "ic_ensamble_ret5": [round(100 * x, 2) for x in C.boot_dif(M["ensamble"]["r5"], dd)],
       "ic_ensamble_ret15": [round(100 * x, 2) for x in C.boot_dif(M["ensamble"]["r15"], dd)]}
dl = res["total"][g]["delta_mbits"]
res["veredicto"] = "PASA" if (res["pasa_barra_dev"] and dl[1] > 0) else "NO PASA"
json.dump(res, open(os.path.join(C.AQUI, "confirmacion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(REG, "a", encoding="utf-8") as f:
    f.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "elegida": g, "delta_mbits": dl,
                        "veredicto": res["veredicto"], "sha1_hist": hashlib.sha1(open(os.path.join(C.AQUI, "historial_la.txt"), "rb").read()).hexdigest()}) + "\n")
print(json.dumps(res["total"], ensure_ascii=False, indent=1))
print("ventana", res["ventana"], "IC ret T5 ensamble", res["ic_ensamble_ret5"], "IC ret T15", res["ic_ensamble_ret15"])
for m_, r in res["por_mes"].items():
    print(m_, " | ".join(f'{k}: {v["mbits"]} mb T5 {v["t5"]} T15 {v["t15"]} r5 {v["r5"]} r15 {v["r15"]}' for k, v in r.items()))
print("VEREDICTO:", res["veredicto"])
