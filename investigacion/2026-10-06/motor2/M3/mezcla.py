import sys, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
Y=A.Y; mA=A.TRAMOS["AJUSTE"]; mE=A.TRAMOS["ELECCION"]
def mb(P,m): return 1000*np.log2(P[m,Y[m]]*38).mean()
for nm in ("120_30_2","120_3_2"):
    P=np.load(A.SP+f"/m3_cfg_{nm}.npz")["P"]; print(nm, "AJ+EL exacto", round(mb(P,mA|mE),3))
nm=sys.argv[1]; P=np.load(A.SP+f"/m3_cfg_{nm}.npz")["P"]
def mix(w):
    L=(1-w)*np.log(A.PROD)+w*np.log(P); L-=L.max(1,keepdims=True); Q=np.exp(L); return Q/Q.sum(1,keepdims=True)
for w in np.round(np.arange(0,1.01,0.1),1):
    Q=mix(w); print(f"w={w:.1f} Δ AJ {mb(Q,mA)-mb(A.PROD,mA):+6.2f}  Δ EL {mb(Q,mE)-mb(A.PROD,mE):+6.2f}")
for w in (0.05,0.15,0.25):
    Q=mix(w); print(f"w={w:.2f} Δ AJ {mb(Q,mA)-mb(A.PROD,mA):+6.2f}  Δ EL {mb(Q,mE)-mb(A.PROD,mE):+6.2f}")
