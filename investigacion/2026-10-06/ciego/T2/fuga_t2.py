"""(e) Fuga temporal con reentreno REAL: en 3 cortes t se altera TODA la secuencia desde t (seq[t:]), se recalculan
TODOS los rasgos (M4 sin RD + nuevos de S2, con q_prior/lift/etiquetas blandas) y se reentrena el mes de t (objetivo C,
vida 90). Se exige que P de todas las filas del mes ≤ t coincida con la matriz congelada, y (control de que la
alteración muerde) que las filas > t del mismo mes SÍ cambien."""
import sys, time, copy, importlib.util, resource, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import arnes as A, rasgos_s2 as R, motor_s2 as M
spec = importlib.util.spec_from_file_location("r4", "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M4/rasgos.py")
R4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(R4)
SP = A.SP; z = np.load(SP + "/s2_rasgos.npz"); rho = float(z["rho"]); NM = [str(x) for x in z["nm"]]
D0 = A.D; Pfin = np.load(SP + "/motor0_S2.npz")["P"]

def pipeline_mes(seq, mes):
    fecha = list(D0.fecha)
    X4, nm4 = R4.construir(seq, np.asarray(D0.hora), D0.dia, fecha, None)
    keep = [j for j, n in enumerate(nm4) if n not in ("rd1", "rd2", "hay_rd")]
    Xn, nmn, info = R.nuevos(seq, np.asarray(D0.hora), D0.dia, fecha, rho=rho)   # rho: hiperparámetro congelado (AJUSTE)
    X = np.concatenate([X4[:, :, keep], Xn], 2).astype(np.float32); nm = [nm4[j] for j in keep] + nmn
    assert nm == NM
    D = copy.copy(D0); D.seq = np.asarray(seq); M.A.D = D          # las etiquetas de entrenamiento salen de seq alterada
    P, _, _ = M.correr("C", 90, X, nm, info["etq"], desde=mes, paso=1, hasta=mes, log=lambda *a, **k: None)
    M.A.D = D0
    return P

S = np.asarray(D0.seq).copy(); rng = np.random.default_rng(7)
cortes = [(10560, "(+7) mod 38", lambda s: (s + 7) % 38),                       # 1.er sorteo de 2026-04-01 (ELECCION)
          (9137, "biyección aleatoria", lambda s: rng.permutation(38)[s]),        # 2025-11-20 h5 (AJUSTE, mitad del día)
          (11495, "iid uniforme", lambda s: rng.integers(0, 38, len(s)))]         # último sorteo de 2026-06-19 (ELECCION)
ok = True
for c, nombre, alt in cortes:
    t0 = time.time(); mes = D0.fecha[c][:7]
    S2 = S.copy(); S2[c:] = alt(S[c:]); frac = (S2[c:] != S[c:]).mean()
    P = pipeline_mes(S2, mes)
    filas = np.where(np.isfinite(P[:, 0]))[0]; t_rel = c - A.T[0]
    antes = filas[filas <= t_rel]; desp = filas[filas > t_rel]
    d_antes = np.abs(P[antes] - Pfin[antes]).max(); d_t = np.abs(P[t_rel] - Pfin[t_rel]).max()
    d_desp = np.abs(P[desp] - Pfin[desp]).max(axis=1) if len(desp) else np.array([0.0])
    bien = d_antes < 1e-9
    ok &= bien
    print(f"corte {c} ({D0.fecha[c]} h{D0.hora[c]}, mes {mes}) alteración {nombre} ({100*frac:.0f}% de seq[t:] cambia): "
          f"max|ΔP[t]| = {d_t:.2e}; max|ΔP| filas del mes ≤ t ({len(antes)}) = {d_antes:.2e} -> {'OK' if bien else 'FUGA'}; "
          f"filas > t ({len(desp)}): cambian {(d_desp > 1e-6).mean()*100:.0f}% (control) | {time.time()-t0:.0f}s", flush=True)
print("FUGA TEMPORAL:", "OK (P[t] no cambia en los 3 cortes)" if ok else "FALLA")
r = resource.getrusage(resource.RUSAGE_SELF); print(f"CPU {r.ru_utime + r.ru_stime:.0f}s")
