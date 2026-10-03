import numpy as np, sys
sys.path.insert(0,'/home/user/lotto-activo/herramientas'); sys.path.insert(0,'/home/user/lotto-activo/herramientas/modelos')
import lotto_eval as LE, exposicion as EX
z=np.load(sys.argv[1]); S=z['seq'];H=z['hora'];F=z['fecha'];DI=z['dia'];P=z['P'];PA=z['P_aj'];EP=z['es_primero'];T=z['tramo']
dias={}
for t in range(len(S)): dias.setdefault(int(DI[t]),[]).append(t)
def win(f):
    d=int(f[8:10]); return [LE.IDX[str(x)] for x in (d-1,d,d+1) if 1<=x<=36]
def rec(t):
    c=np.zeros(38); dd=int(DI[t])
    for k,j0 in ((1,1),(2,0)):
        for tt in dias.get(dd-k,[])[j0:]: c[S[tt]]=1
    return c
def norm(q): return q/q.sum()
M={
 "motor sin ajuste (P)": lambda t: P[t],
 "PRODUCCIÓN (P_aj)":    lambda t: PA[t],
 "+ventana fecha x0,486": lambda t: norm(PA[t]*np.where(np.isin(np.arange(38),win(F[t])),0.486,1)),
 "+exposición+ventana x0,59": lambda t: norm(np.array(EX.aplicar(PA[t],F[t],int(H[t])))*np.where(np.isin(np.arange(38),win(F[t])),0.59,1)),
 "+salió ayer/anteayer x1,378": lambda t: norm(PA[t]*np.where(rec(t)>0,1.378,1)),
 "+ventana +ayer/anteayer": lambda t: norm(PA[t]*np.where(np.isin(np.arange(38),win(F[t])),0.486,1)*np.where(rec(t)>0,1.378,1)),
}
F5=[0,2,2,2,1,1]+[0]*33; F15=[0,3,3,3,2,2]+[1]*10+[0]*23
def bloque(nombre, filas):
    print(f"\n### {nombre}: {len(filas)} primeros sorteos")
    print(f"{'modelo':30s} {'mbits vs PROD [IC95 días]':>28s} {'Top5':>5s} {'Top15':>6s} {'neto T5esc':>10s} {'neto T15p':>10s}")
    rng=np.random.default_rng(1)
    for k,f in M.items():
        mb=[];t5=t15=0;n5=n15=0.
        for t in filas:
            q=f(t); y=S[t]; mb.append(1000*np.log2(q[y]/PA[t][y]))
            pos=1+int((q>q[y]).sum())
            t5+=pos<=5; t15+=pos<=15
            n5+=30*F5[pos]-8; n15+=30*F15[pos]-23
        mb=np.array(mb); bs=[mb[rng.integers(0,len(mb),len(mb))].mean() for _ in range(2000)]
        ic=f"{mb.mean():+6.1f} [{np.percentile(bs,2.5):+6.1f};{np.percentile(bs,97.5):+6.1f}]"
        print(f"{k:30s} {ic:>28s} {t5:5d} {t15:6d} {n5:+10.0f} {n15:+10.0f}")
f26=[t for t in range(len(S)) if EP[t] and T[t]=='prueba' and F[t]>='2026-01-01']
viv=[t for t in range(len(S)) if EP[t] and T[t]=='vivo']
bloque("2026 (01-01 a 09-14; dentro del tramo de prueba)", f26)
bloque("VIVO (09-15 a 09-29; pronósticos reconstruidos = congelados)", viv)
bloque("2026 completo (ene-sep)", f26+viv)
print("\nFichas: Top-5 escalonado 2-2-2-1-1 = 8 fichas/sorteo; Top-15 ponderado 3-3-3-2-2-1x10 = 23 fichas/sorteo; pago 30.")
