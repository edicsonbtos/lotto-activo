import sys, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
Y=A.Y; P=np.load(A.SP+"/m3_cfg_120_30_2.npz")["P"]; P0=np.load(A.SP+"/m3_cfg_120_inf_2.npz")["P"]
L=0.9*np.log(A.PROD)+0.1*np.log(P); L-=L.max(1,keepdims=True); Q=np.exp(L); Q/=Q.sum(1,keepdims=True)
A.evaluar(P,"M3 vm120 λ30"); A.evaluar(Q,"PROD^0.9·M3^0.1")
np.savez(A.SP+"/motor2_M3.npz", P=P, P_mezcla_w01=Q, t=A.T)
def d(a,b,m): return (1000*np.log2(a[m,Y[m]]/b[m,Y[m]])).mean()
mv=np.isin(A.DOW,[2,3,4]); dom=A.DOW==6
for tr in ("ANTIGUO","AJUSTE","ELECCION"):
    m=A.TRAMOS[tr]
    print(tr, "Δ(dow − sin dow) mié-vie %+.1f  dom %+.1f  resto %+.1f"%(d(P,P0,m&mv),d(P,P0,m&dom),d(P,P0,m&~mv&~dom)),
          "| mezcla−prod mié-vie %+.1f dom %+.1f resto %+.1f"%(d(Q,A.PROD,m&mv),d(Q,A.PROD,m&dom),d(Q,A.PROD,m&~mv&~dom)),
          "| M3−prod mié-vie %+.1f resto %+.1f"%(d(P,A.PROD,m&mv),d(P,A.PROD,m&~mv)))
