import sys, importlib.util
H=r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas"; sys.path.insert(0,H)
import numpy as np, lotto_eval as L
spec=importlib.util.spec_from_file_location("m", H+"/modelos/logit_s.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d=L.cargar(); w,c=L.particion(len(d)); dd=d.prefijo(c)
seq,ar,C,k,G,G2,DD,hoy=m._estado(dd)
Y=np.zeros((c,38)); Y[np.arange(c),seq]=1
kk=np.broadcast_to(k[:,None],(c,38))
cats={"hoy>0":hoy>0,"g1-3":G<=3,"g4-12 no hoy":(G>=4)&(G<=12)&(hoy==0),"g13-30":(G>=13)&(G<=30),"g31-60":(G>=31)&(G<=60),"g61-100":(G>=61)&(G<=100),"g>100":(G>100)&(G<10**5),
      "k0 & DD1":(kk==0)&(DD==1)}
edges=np.linspace(300,c,9).astype(int)
for nm,msk in cats.items():
    print(f"{nm:>14}", " ".join(f"{Y[a:b][msk[a:b]].mean()*38:.2f}" for a,b in zip(edges[:-1],edges[1:])))
print("filas", edges, "fechas", [dd.fecha[e] for e in edges[:-1]])
