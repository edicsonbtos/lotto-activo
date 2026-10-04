import numpy as np
z=np.load("vivo_rk.npz",allow_pickle=True); rk=z["rk"]; t=z["t"]; f=z["f"]; h=z["h"]; P=z["P"]
import sys; sys.path.insert(0,"/home/user/lotto-activo/herramientas"); import lotto_eval as LE
D=LE.cargar("hist_hoy.txt"); S=np.asarray(D.seq)
y=S[t]; n=len(t)
o=np.argsort(-P,1,kind="stable")
starts=[i for i in range(1,n) if f[i]!=f[i-1]]       # primer sorteo de cada día
def seg(i): return "dev" if t[i]<9357 else ("vivo" if f[i]>="2026-09-15" else "prueba")
print("Elegir k animales al abrir el día (Top-k del motor) y jugarlos 1 ficha c/u por sorteo hasta que salgan o se cumpla la ventana")
for W in (12,24):
    for k in (1,2,3):
        R={"dev":[0,0,0,0],"prueba":[0,0,0,0],"vivo":[0,0,0,0]}
        for s0 in starts:
            if s0+W>n and seg(s0)!="vivo": continue
            for a in o[s0,:k]:
                cost=gain=0; hit=0
                for j in range(s0,min(s0+W,n)):
                    cost+=1
                    if y[j]==a: gain=30; hit=1; break
                r=R[seg(s0)]; r[0]+=cost; r[1]+=gain; r[2]+=hit; r[3]+=1
        print(f"  ventana {W:2d} sorteos, k={k}: "+"   ".join(f"{s}: sale {r[2]/r[3]*100:4.1f}% retorno {(r[1]/r[0]-1)*100:+5.1f}%" for s,r in R.items()))
# comparar: Top-k renovado en cada sorteo
for k in (1,2,3):
    hit=rk<k
    print(f"  renovar Top-{k} en cada sorteo: "+"   ".join(f"{s}: {(30*hit[m].mean()/k-1)*100:+5.1f}%" for s,m in (("dev",t<9357),("prueba",(t>=9357)&(f<"2026-09-15")),("vivo",f>="2026-09-15"))))
