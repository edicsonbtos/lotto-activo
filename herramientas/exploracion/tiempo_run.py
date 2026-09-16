import sys, time, importlib; sys.path.insert(0,'.')
import numpy as np
from lotto_eval import cargar, particion, metricas, cargar_modelo
d=cargar(); n=len(d); w,corte=particion(n)
ruta=sys.argv[1]; kw=eval(sys.argv[2]) if len(sys.argv)>2 else {}
m=cargar_modelo(ruta, devolver_todo=True, **kw)
t0=time.time(); P=m.predecir(d,w); print('seg',round(time.time()-t0,1))
y=d.seq[w:corte]
def show(name,Q):
    r=metricas(Q[:corte-w],y)
    print(f"{name:>14} T1 {r['top1']['tasa']*100:.2f} T3 {r['top3']['tasa']*100:.2f} mb {r['logver']['bits_por_sorteo']*1000:+.1f} q {[round(x*100,1) for x in r['top3_por_cuarto']]}")
show("mix",P); print("w dens", np.round(m.w[:, m.Dc:],3))
for i,l in enumerate(m.lambdas): show(f"l={l} k={m.kappas[i,0] if hasattr(m,"kappas") else 0}",m.todo[:,i])
