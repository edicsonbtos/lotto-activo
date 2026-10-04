import numpy as np
z=np.load("vivo_rk.npz",allow_pickle=True); rk=z["rk"]; t=z["t"]; f=z["f"]
pr=(t>=9357)&(f<"2026-09-15")
def plan(*w): a=np.zeros(38); a[:len(w)]=w; return a/ a.sum()
E={"Top-5 escalonado (actual)":plan(2,2,2,1,1),"Top-2":plan(1,1),"2-1":plan(2,1),"Top-1":plan(1)}
dias=sorted(set(f[pr])); rng=np.random.default_rng(5)
porDia={nom:[ (30*w[rk[pr&(f==d)]]-1) for d in dias] for nom,w in E.items()}   # ganancia neta por sorteo, apuesta = 1 unidad/sorteo
print("Banca inicial = 100 apuestas (p. ej. apuesta 1 $/sorteo con 100 $). 90 días de 12 sorteos, 4000 simulaciones con días reales de prueba")
for nom,L in porDia.items():
    fin=[];quiebra=0;bajo50=0
    for _ in range(4000):
        b=100.0; mn=b
        for j in rng.integers(0,len(dias),90):
            for g in L[j]:
                b+=g; mn=min(mn,b)
                if b<=0: break
            if b<=0: break
        quiebra+=b<=0; bajo50+=mn<=50; fin.append(b)
    fin=np.array(fin)
    print(f"  {nom:26s} quiebra {quiebra/40:4.1f}%   llega a perder la mitad {bajo50/40:4.1f}%   banca final mediana {np.median(fin):6.0f}   termina en pérdida {np.mean(fin<100)*100:4.1f}%")
