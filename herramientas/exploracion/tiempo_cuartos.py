import sys; sys.path.insert(0,'.')
import numpy as np
from lotto_eval import cargar, particion, cargar_modelo
d=cargar(); n=len(d); w,corte=particion(n)
m=cargar_modelo('modelos/tiempo_v3.py', lambdas=(1.0,0.9999,0.9995,0.999), ventanas=[12,24,38,76,152,380,760,1520], devolver_todo=True)
P=m.predecir(d,w); y=d.seq[w:corte]; T=m.todo[:corte-w]
lp=np.log2(T[np.arange(len(y)),:,y]*38)*1000  # (N,L)
for i,q in enumerate(np.array_split(np.arange(len(y)),4)):
    print('cuarto',i,d.fecha[w+q[0]],'mbits por lambda', np.round(lp[q].mean(0),1), 'ventaja 0.9995-1.0', round(lp[q,2].mean()-lp[q,0].mean(),1),'+-',round((lp[q,2]-lp[q,0]).std()/np.sqrt(len(q)),1))
# distinct/day by quarter-year (12-draw days), only < corte
seq=d.seq; dia=d.dia
from collections import defaultdict
agg=defaultdict(list)
for k in np.unique(dia[:corte]):
    ix=np.flatnonzero(dia[:corte]==k)
    if len(ix)==12: agg[d.fecha[ix[0]][:7]].append(len(set(seq[ix])))
for mth in sorted(agg): print(mth, round(np.mean(agg[mth]),2), len(agg[mth]))
