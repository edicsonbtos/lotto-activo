# ag06 — control: ¿el exceso de "hueco 0-1 días" es exclusivo del primer sorteo? (solo dev, horas != primer sorteo)
import numpy as np
import os; d = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "base8.npz"), allow_pickle=True)
S,H,DI,P,EP,TR=d["seq"],d["hora"],d["dia"],d["P"],d["es_primero"],d["tramo"]
n=len(S); ult=np.full(38,-1)
O={}; E={}
for t in range(n):
    if TR[t]=="dev" and not EP[t]:
        hd=np.array([DI[t]-DI[ult[a]]-1 if ult[a]>=0 else 99 for a in range(38)])
        # hueco en días calendario: -1 = hoy ya salió (excluir), 0 = ayer
        b=np.select([hd<0,hd<=1,hd<=3,hd<=6],[-1,0,2,4],7)
        for k in (0,2,4,7,-1):
            O[k]=O.get(k,0)+(b[S[t]]==k); E[k]=E.get(k,0)+P[t][b==k].sum()
    ult[S[t]]=t
for k in (-1,0,2,4,7): print("bin",k,"O",O[k],"E %.1f"%E[k],"O/E %.3f"%(O[k]/E[k]))
