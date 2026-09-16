import sys,os,time,json; H=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,H)
import numpy as np, lotto_eval as e
d=e.cargar(); n=len(d); W,CORTE=e.particion(n)
mod=sys.argv[1]; variantes=json.loads(sys.argv[2])
for kw in variantes:
    m=e.cargar_modelo(os.path.join(H,'modelos',mod),**kw); t0=time.time()
    P=m.predecir(d.prefijo(CORTE),W)   # solo desarrollo
    r=e.metricas(P,d.seq[W:CORTE])
    print(f"{json.dumps(kw):70s} T1 {r['top1']['tasa']*100:5.2f} T3 {r['top3']['tasa']*100:5.2f} {r['logver']['bits_por_sorteo']*1000:+6.2f}mb q{[round(x*100,1) for x in r['top3_por_cuarto']]} {time.time()-t0:.0f}s",flush=True)
