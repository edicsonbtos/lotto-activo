import sys; sys.path.insert(0,'.')
import numpy as np
from lotto_eval import cargar, particion, cargar_modelo
d=cargar(); n=len(d); w,corte=particion(n)
V=[12,24,38,76,152,380,760,1520]
for t in [3000,4500,6000,7500,9357]:
    m=cargar_modelo('modelos/tiempo_v3.py', lambdas=(1.0,0.9995), ventanas=V)
    dp=d.prefijo(t); m.predecir(dp, t-1)
    W=m.w; Dc=m.Dc
    # gap block offsets: gap 0..46 ; hoy starts 47
    print(d.fecha[t-1], 'hoy(k=1,2,6,11 x1):', [np.round(W[:,47+1+(k-1)*2],2).tolist() for k in (1,6,11)],
          'gap g13-20 mean-g1..5:', np.round(W[:,12:20].mean(1)-W[:,0:5].mean(1),2), 'dens:', np.round(W[:,Dc:],2).tolist())
