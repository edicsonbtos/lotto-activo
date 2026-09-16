# Compara variantes (kwargs de cfg) contra la base, diferencia pareada de log-verosimilitud en desarrollo.
import sys,os,json,time; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
SCR="C:/Users/edics/AppData/Local/Temp/claude/C--Users-edics-Downloads-lotto-activo-lotto-activo/a04420f8-b46c-44c9-bcc9-37398d9fed49/scratchpad"
d=e.cargar(); N=len(d); W,CORTE=e.particion(N); dd=d.prefijo(CORTE); y=dd.seq[W:]
ruta=sys.argv[1]; variantes=json.loads(sys.argv[2])
base=np.load(f"{SCR}/base_logit_final.npy"); lb=np.log2(base[np.arange(len(y)),y]*38)
for nm,kw in variantes.items():
    t0=time.time(); m=e.cargar_modelo(ruta,**kw); P=e.normalizar(m.predecir(dd,W)); np.save(f"{SCR}/var_{nm}.npy",P)
    l=np.log2(P[np.arange(len(y)),y]*38); df=l-lb
    q=[1000*x.mean() for x in np.array_split(df,4)]
    met=e.metricas(P,y)
    print(f"{nm:<14} {1000*l.mean():+7.2f} mbits  diff {1000*df.mean():+5.2f} ± {1000*df.std()/np.sqrt(len(df)):.2f}  cuartos {np.round(q,2)}  top1 {met['top1']['tasa']*100:.2f} top3 {met['top3']['tasa']*100:.2f} {[round(x*100,1) for x in met['top3_por_cuarto']]} ({time.time()-t0:.0f}s)",flush=True)
