import numpy as np, json
from candidatos import *
dev = [t for t in FIRST if TR[t] == "dev"]
dev9 = [t for t in dev if H[t] == 1]; dev8 = [t for t in dev if H[t] == 0]
rng = np.random.default_rng(1)
out = {}
for c in CANDS:
    lm = ajustar(dev, c); m = float(np.exp(lm))
    s = {}
    for nom, fl in (("dev", dev), ("9:00", dev9), ("8:00", dev8)):
        O, E = stats_cand(fl, c); s[nom] = (O, E)
    # mbits in-sample dev
    g = np.array([1000*np.log2(aplicar(t, lm, c)[S[t]] / PAJ[t, S[t]]) for t in dev])
    # separate-era fits for stability
    m9 = np.exp(ajustar(dev9, c)); m8 = np.exp(ajustar(dev8, c))
    # mitades temporales de dev
    h1, h2 = dev[:len(dev)//2], dev[len(dev)//2:]
    O1, E1 = stats_cand(h1, c); O2, E2 = stats_cand(h2, c)
    print(f"{c}: m={m:.3f} (9:00 {m9:.2f}, 8:00 {m8:.2f})  " + "  ".join(f"{k} O={o:.0f} E={e:.1f} O/E={o/e:.2f} p={poisson_p2(int(o),e):.4f}" for k, (o, e) in s.items())
          + f"  mitad1 {O1/E1:.2f} mitad2 {O2/E2:.2f}  mbits dev in-sample {g.mean():+.1f}")
    out[c] = dict(m=m, logm=float(lm), O_dev=float(s["dev"][0]), E_dev=float(s["dev"][1]),
                  signo=1 if s["dev"][0] > s["dev"][1] else -1,
                  mismo_signo=bool((s["9:00"][0]-s["9:00"][1])*(s["8:00"][0]-s["8:00"][1]) > 0))
json.dump(out, open("candidatos_dev.json", "w"), indent=1)
print(out)
