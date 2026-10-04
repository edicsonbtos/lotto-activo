import sys, numpy as np
sys.path.insert(0,"/home/user/lotto-activo/herramientas"); import lotto_eval as LE
D=LE.cargar("hist.txt"); S=np.asarray(D.seq); H=np.asarray(D.hora); F=np.array(D.fecha)
z=np.load("vers.npz"); d0=int(np.load("wf.npz")["desde"]); n=len(S); t=np.arange(d0,n); y=S[t]; f=F[t]; h=H[t]
def plan(tr):
    a=np.zeros(38)
    for i,j,k in tr: a[i-1:j]=k
    return a
E={"Top-15 ponderado 3-2-1":plan([(1,3,3),(4,5,2),(6,15,1)]),"Top-5 escalonado":plan([(1,3,2),(4,5,1)]),"Top-15 plano":plan([(1,15,1)]),"Top-3":plan([(1,3,1)])}
for V in "BC":
  M=z[V]; o=np.argsort(-M,1,kind="stable"); r=np.argmax(o==y[:,None],1)
  print("versión",V)
  for nom,a in E.items():
    g=a[r]*30-a.sum()
    def s(m): return f"{g[m].sum():+5.0f} fichas ({g[m].sum()/(a.sum()*m.sum())*100:+.0f}%)"
    print(f"  {nom:24} ayer {s(f=='2026-10-03')}  hoy {s(f=='2026-10-04')}  vivo15sep {s(f>='2026-09-15')}  8am vivo {s((f>='2026-09-15')&(h==0))}")
