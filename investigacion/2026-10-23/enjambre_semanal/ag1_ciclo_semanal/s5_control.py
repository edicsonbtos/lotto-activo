# -*- coding: utf-8 -*-
"""Control post-hoc de S5 (descriptivo, fuera de la familia): ventanas de 7 dias que empiezan en cada dia de la semana.
Si el deficit de animales distintos es igual en todas, no es un efecto semanal sino de la simulacion."""
import sys; sys.argv = [sys.argv[0], "dev"]
exec(open(__file__.replace("s5_control.py", "semanal.py"), encoding="utf-8").read().split("# ----- S5 cobertura semanal")[0].replace("print(", "(lambda *a, **k: None)("))
devs = np.array(dev); m = len(dev)
X = np.zeros((R, m), np.int8); seen_d = np.zeros((R, 38), bool); cur = None
for j, t in enumerate(dev):
    if filas[t][0] != cur: cur = filas[t][0]; seen_d[:] = False
    p = pfun(t, vistos_dia[t]); pr = np.broadcast_to(p, (R, 38)).copy(); pr[seen_d] = 0
    cs = pr.cumsum(1); u = rng.random(R)[:, None] * cs[:, -1:]
    x = np.minimum((cs < u).sum(1), 37); seen_d[np.arange(R), x] = True; X[:, j] = x
fechas_dev = [fe[t] for t in dev]; d0 = fechas_dev[0]
yobs = np.array([filas[t][2] for t in dev])
nd = {}
for j, d in enumerate(fechas_dev): nd.setdefault(d, []).append(j)
dias_l = sorted(nd)
print("inicio_dia  ventanas  obs_medio  sim_medio  z")
for k in range(7):
    obs = []; sm = []
    for d in dias_l:
        if d.weekday() != k: continue
        js = []
        for q in range(7): js += nd.get(d + timedelta(days=q), [])
        if len(js) != 84: continue
        obs.append(len(set(yobs[js]))); 
        sm.append(np.array([len(set(X[r, js])) for r in range(300)]))
    sm = np.array(sm).mean(0); o = np.mean(obs)
    print(f"{['lun','mar','mie','jue','vie','sab','dom'][k]}  {len(obs)}  {o:.2f}  {sm.mean():.2f}  {(o-sm.mean())/sm.std():+.2f}")
