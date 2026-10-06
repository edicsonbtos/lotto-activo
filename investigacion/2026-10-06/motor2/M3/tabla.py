import sys, numpy as np, glob, os
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
Y=A.Y; i0=np.arange(len(Y))
def mb(P,m): return 1000*np.log2(P[m,Y[m]]*38).mean()
mA=A.TRAMOS["AJUSTE"]; mE=A.TRAMOS["ELECCION"]; mO=A.TRAMOS["ANTIGUO"]; mAE=mA|mE
print("prod: ANT %.1f AJ %.1f EL %.1f AJ+EL %.1f"%(mb(A.PROD,mO),mb(A.PROD,mA),mb(A.PROD,mE),mb(A.PROD,mAE)))
for f in sorted(glob.glob(A.SP+"/m3_cfg_*.npz")):
    P=np.load(f)["P"]; nm=os.path.basename(f)[7:-4]
    print(f"{nm:12} ANT {mb(P,mO):+6.1f} AJ {mb(P,mA):+6.1f} EL {mb(P,mE):+6.1f} AJ+EL {mb(P,mAE):+6.1f}")
z1=np.load(A.SP+"/m3_cfg_60_inf_2.npz")["P"]; z2=np.load(A.SP+"/m3_cfg_60_inf_5.npz")["P"]
print("conv max|logP2-logP5|", np.abs(np.log(z1)-np.log(z2)).max(), "mbits diff", (1000*np.log2(z1[i0,Y]/z2[i0,Y])).mean())
