import numpy as np, sys
from scipy.stats import poisson
sys.path.insert(0,'/home/user/lotto-activo/herramientas'); import lotto_eval as LE
z=np.load(sys.argv[1]); S=z['seq'];H=z['hora'];F=z['fecha'];P=z['P_aj'];EP=z['es_primero'];T=z['tramo']
def win(f):
    d=int(f[8:10]); return {LE.IDX[str(x)] for x in (d-1,d,d+1) if 0<x<=36}
def sem(f): return f[:4]+("a" if f[5:7]<="06" else "b")
rows={}
for t in range(len(S)):
    if T[t]=='cal' : 
        if EP[t]: k=('cal-1º',sem(F[t])); w=win(F[t]); r=rows.setdefault(k,[0,0,0]); r[0]+=S[t] in w; r[1]+=len(w)/38; r[2]+=1
        continue
    k=('1º' if EP[t] else 'resto', sem(F[t])); w=list(win(F[t]))
    r=rows.setdefault(k,[0,0.,0]); r[0]+=S[t] in w; r[1]+=P[t][w].sum(); r[2]+=1
for k in sorted(rows, key=lambda k:(k[0],k[1])):
    O,E,n=rows[k]; print(f"{k[0]:7s} {k[1]} n={n:5d} O={O:4d} E={E:6.1f} O/E={O/E:4.2f} p_low={poisson.cdf(O,E):.3f}")
