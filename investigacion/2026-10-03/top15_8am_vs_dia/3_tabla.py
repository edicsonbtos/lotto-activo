import sys, numpy as np, math
sys.path.insert(0,"/home/user/lotto-activo/herramientas"); import lotto_eval as LE
D=LE.cargar("hist_full.txt"); H=np.asarray(D.hora); F=np.array(D.fecha)
V=np.load("sim15.npy",allow_pickle=True).item()
t=V["A"][:,0].astype(int); h=H[t]; f=F[t]
era8 = f>="2024-11-28"
seg={"dev (nov24-dic25)":(t<9357)&era8,"prueba (dic25-sep26)":(t>=9357)&(f<"2026-09-15"),"vivo (15sep-3oct)":f>="2026-09-15","todo desde nov-24":era8}
names={"A":"motor actual","B":"+ ajuste 1er sorteo","C":"B + fecha/hora (sombra)","D":"B + ventana 8am (sombra)"}
def ci(k,n):
    p=k/n; z=1.96; d=1+z*z/n; c=(p+z*z/(2*n))/d; w=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return (c-w)*100,(c+w)*100
for sn,m in seg.items():
    print(f"\n=== {sn} ===   azar Top-15 = 39,5 %")
    print(f"{'version':26s} {'8:00':>22s} {'resto del día (9-19h)':>26s}   esperado por el motor 8:00/resto")
    for k in "ABCD":
        hit=V[k][:,1]<15; mass=V[k][:,2]
        a=m&(h==0); b=m&(h!=0)
        if a.sum()==0: continue
        l1,u1=ci(hit[a].sum(),a.sum()); l2,u2=ci(hit[b].sum(),b.sum())
        print(f"{names[k]:26s} {hit[a].mean()*100:5.1f}% [{l1:4.1f}-{u1:4.1f}] n={a.sum():3d}   {hit[b].mean()*100:5.1f}% [{l2:4.1f}-{u2:4.1f}] n={b.sum():4d}   {mass[a].mean()*100:4.1f}% / {mass[b].mean()*100:4.1f}%")
# por hora, todo desde nov-24, motor B
print("\nTop-15 por hora (desde nov-24), versión B:")
hit=V["B"][:,1]<15
print("  "+"  ".join(f"{['8a','9a','10a','11a','12p','1p','2p','3p','4p','5p','6p','7p'][j]} {hit[era8&(h==j)].mean()*100:.0f}%" for j in range(12)))
# diferencia pareada B-A y D-B a las 8:00 por tramo, bootstrap por día
rng=np.random.default_rng(1)
for sn,m in seg.items():
    a=m&(h==0)
    for x,y in (("B","A"),("D","B")):
        dlt=(V[x][a,1]<15).astype(int)-(V[y][a,1]<15).astype(int)
        bs=[rng.choice(dlt,len(dlt)).mean() for _ in range(4000)]
        print(f"  {sn:22s} {x}-{y} a las 8:00: {dlt.mean()*100:+.1f} pp  IC95 [{np.percentile(bs,2.5)*100:+.1f}, {np.percentile(bs,97.5)*100:+.1f}]  (gana {int((dlt>0).sum())}, pierde {int((dlt<0).sum())})")
