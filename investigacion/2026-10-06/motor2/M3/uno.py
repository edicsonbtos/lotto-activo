import sys, time, os, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M3")
import m3
SP="/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
X=np.load(SP+"/m3_X.npy", mmap_mode="r"); M=np.load(SP+"/m3_meta.npz")
vm=float(sys.argv[1]); lam=float(sys.argv[2]); iters=int(sys.argv[3]) if len(sys.argv)>3 else 2
t0=time.time()
P,B,db=m3.walk_forward(np.ascontiguousarray(X), M["y"], M["dia"], int(M["nb"]), vm, lam, iters=iters)
np.savez(SP+f"/m3_cfg_{int(vm)}_{sys.argv[2]}_{iters}.npz", P=P, B=B, db=db)
print(vm, lam, iters, "seg", round(time.time()-t0,1), flush=True)
