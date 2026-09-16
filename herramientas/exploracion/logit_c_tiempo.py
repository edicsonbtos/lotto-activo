import sys, os, time, importlib.util
H=r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas"; sys.path.insert(0,H)
import numpy as np, lotto_eval as L
spec=importlib.util.spec_from_file_location("m", H+"/modelos/logit_c.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d=L.cargar(); w,c=L.particion(len(d)); dd=d.prefijo(c)
t0=time.time(); tb,D,_=m.construir(dd,{}); print("build",time.time()-t0)
T=c; sl=slice(200,T)
pr=m.Problema([(a,ix[sl],s) for a,ix,s in tb],D[sl],dd.seq[sl],np.ones(T-200))
b=np.zeros(pr.d); t0=time.time()
for _ in range(10): pr.f(b)
print("f eval", (time.time()-t0)/10)
from scipy.optimize import minimize
refs=[0,36,59]
for opts in [dict(maxiter=1000,gtol=1e-8,ftol=1e-12), dict(maxiter=1000,gtol=1e-6,ftol=1e-10), dict(maxiter=200)]:
    mask=np.ones(pr.d); mask[refs]=0
    def f(x):
        x=x*mask; v,g=pr.f(x); return v+0.5*3e-5*x@x,(g+3e-5*x)*mask
    t0=time.time(); r=minimize(f,np.zeros(pr.d),jac=True,method="L-BFGS-B",options=opts)
    print(opts, r.nit, r.fun, time.time()-t0)
