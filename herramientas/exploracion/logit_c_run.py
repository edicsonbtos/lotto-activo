# Uso: python logit_c_run.py <modulo> "[{cfg1}, {cfg2}]" [coef]
# SOLO desarrollo: el histórico se trunca en el corte (la prueba nunca se toca).
import sys, os, time, importlib.util
AQUI = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(AQUI)
sys.path.insert(0, H)
import numpy as np, lotto_eval as L
def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(H, "modelos", nombre + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
datos = L.cargar(); n = len(datos); w, corte = L.particion(n)
dd = datos.prefijo(corte)
mod = cargar(sys.argv[1])
for kw in eval(sys.argv[2]):
    M = mod.Modelo(**kw); t0 = time.time()
    P = M.predecir(dd, w); m = L.metricas(P, dd.seq[w:])
    with open(os.path.join(AQUI, "logit_c_log.txt"), "a") as f:
        line = (f"{sys.argv[1]} {kw} | Top1 {m['top1']['tasa']*100:.2f} Top3 {m['top3']['tasa']*100:.2f} "
          f"{m['logver']['bits_por_sorteo']*1000:+.1f} mbits | q {[round(x*100,1) for x in m['top3_por_cuarto']]} | {time.time()-t0:.0f}s")
        f.write(line + "\n")
    print(line, flush=True)
    Pn = L.normalizar(P); lp = np.log(Pn[np.arange(len(Pn)), dd.seq[w:]] * 38) / np.log(2)
    np.save(os.path.join(AQUI, "logit_lp", f"{sys.argv[1]}_{abs(hash(repr(kw)))%10**8}.npy"), lp)
    import json; json.dump({"kw": repr(kw)}, open(os.path.join(AQUI, "logit_lp", f"{sys.argv[1]}_{abs(hash(repr(kw)))%10**8}.json"), "w"))
if len(sys.argv) > 3:
    for nm, b in zip(M.nombres, M.beta): print(f"  {nm:>16} {b:+.3f}")
