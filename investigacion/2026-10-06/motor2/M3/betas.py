import sys, numpy as np
from datetime import date, timedelta
SP="/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
M=np.load(SP+"/m3_meta.npz"); nom=list(M["nombres"]); nb=int(M["nb"])
z=np.load(SP+"/m3_cfg_120_30_2.npz"); B=z["B"]; db=z["db"]
d0=date(2023,9,4); F=np.array([(d0+timedelta(days=int(x))).isoformat() for x in db])
DIAS=["lun","mar","mié","jue","vie","sáb","dom"]
def traj(fn):  # (días, 7): β común + δ_dow
    return B[:,nom.index(fn)][:,None]+B[:,[nom.index(f"{fn}@{w}") for w in range(7)]]
per=[("2024-07..2025-06","2024-07-01","2025-06-30"),("2025-07..2025-11","2025-07-01","2025-11-30"),("2025-12..2026-06","2025-12-01","2026-06-30"),("2026-07..2026-10","2026-07-01","2026-10-05")]
out=[]
for fn in ("hoy","d1","d2","d3"):
    T=traj(fn); out.append(f"\nβ_{fn} (común+δ) media por periodo | "+" ".join(f"{d:>6}" for d in DIAS)+" | común")
    for lab,a,b in per:
        m=(F>=a)&(F<=b); out.append(f"  {lab:18} | "+" ".join(f"{v:+6.2f}" for v in T[m].mean(0))+f" | {B[m,nom.index(fn)].mean():+6.2f}")
out.append("\nβ comunes (media 2026-03..06): "+", ".join(f"{n} {B[(F>='2026-03-01')&(F<='2026-06-30'),i].mean():+.2f}" for i,n in enumerate(nom[:nb])))
txt="\n".join(out); print(txt); open("betas.txt","w").write(txt)
