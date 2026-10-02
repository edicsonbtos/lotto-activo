import runpy,os,sys,io,contextlib
src=open("ronda5.py",encoding="utf-8").read().split("d = np.array")[0]
exec(src)
d = np.array([int(f[8:10]) for f in FECHA])
ds = np.array([sum(map(int, str(x))) for x in d])
a=np.array([LE.IDX[str(x)] for x in ds]); o=(Y==a).astype(float); e=PE[np.arange(len(Y)),a]
for nom,msk in (("dia>=10 (suma != dia)",d>=10),("dia<=9 (suma==dia)",d<=9)):
    for t,I in (("A",IA),("B",IB)):
        k=I&msk; print(nom,t,k.sum(),boot_oe(o[k],e[k],DIA[k],2.5))
