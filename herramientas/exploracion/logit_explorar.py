import sys, os, time, json, importlib.util
AQUI = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(AQUI)
sys.path.insert(0, H)
import numpy as np, lotto_eval as L
def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(H, "modelos", nombre + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
datos = L.cargar(); n = len(datos); w, corte = L.particion(n)
# SOLO desarrollo: se trunca el histórico en el corte (nunca se toca la prueba)
dd = datos.prefijo(corte)
def run(mod, **kw):
    M = cargar(mod).Modelo(**kw); t0 = time.time()
    P = M.predecir(dd, w); m = L.metricas(P, dd.seq[w:])
    print(f"{mod} {kw} | Top1 {m['top1']['tasa']*100:.2f} Top3 {m['top3']['tasa']*100:.2f} "
          f"{m['logver']['bits_por_sorteo']*1000:+.1f} mbits | q {[round(x*100,1) for x in m['top3_por_cuarto']]} | {time.time()-t0:.0f}s", flush=True)
    return M
if __name__ == "__main__":
    variantes = eval(sys.argv[2]) if len(sys.argv) > 2 else [{}]
    for kw in variantes:
        M = run(sys.argv[1], **kw)
    if hasattr(M, "beta"):
        for nm, b in zip(M.nombres, M.beta): print(f"  {nm:>14} {b:+.3f}")
