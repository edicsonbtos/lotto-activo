# hazard por celdas (g exacto, S, D) con conteos ponderados exp. y suavizado
import sys, json, numpy as np
sys.path.insert(0, r"C:/Users/edics/Downloads/lotto-activo/lotto-activo/herramientas")
from lotto_eval import cargar, particion, metricas
from haz_feat import feats
K=38
d=cargar(); W,C=particion(len(d)); N=C
G,D,S=feats(d,N); y=d.seq[:N]
def show(name,m):
    print(f"{name:50s} T1 {m['top1']['tasa']*100:.2f} T3 {m['top3']['tasa']*100:.2f} {m['logver']['bits_por_sorteo']*1000:+.1f}mb q{[round(x*100,1) for x in m['top3_por_cuarto']]}",flush=True)
def run(cfg):
    GM=cfg["gmax"]; hl=cfg.get("hl"); bw=cfg.get("bw",0); a=cfg.get("a",20)
    g=np.minimum(G,GM)-1
    s=np.minimum(S,1) if cfg.get("s") else np.zeros_like(S)
    cell=g + GM*s
    nc=2*GM
    hit=np.zeros(nc); tot=np.zeros(nc); P=np.zeros((N-W,K))
    dec=1.0 if hl is None else 0.5**(1/hl)
    # kernel matrix over g within each s block
    if bw>0:
        idx=np.arange(GM); Kg=np.exp(-0.5*((idx[:,None]-idx[None,:])/bw)**2)
        Km=np.zeros((nc,nc)); Km[:GM,:GM]=Kg; Km[GM:,GM:]=Kg
    for t in range(N):
        if t>=W:
            if bw>0: h=Km@hit; n=Km@tot
            else: h=hit; n=tot
            # beta-binomial shrinkage toward global rate
            r0=hit.sum()/max(tot.sum(),1)
            hz=(h+a*r0)/(n+a)
            p=hz[cell[t]]; P[t-W]=p/p.sum()
        if t>=300:
            if dec<1: hit*=dec; tot*=dec
            np.add.at(tot,cell[t],1); hit[cell[t,y[t]]]+=1
    return metricas(P,y[W:])
for cfg in json.loads(sys.argv[1]):
    show(json.dumps(cfg),run(cfg))
