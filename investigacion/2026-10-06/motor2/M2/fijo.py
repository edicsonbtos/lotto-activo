import numpy as np, comun as C, correccion as R
A = C.A; aj = np.where(A.TRAMOS["AJUSTE"])[0]
for var in ("V1", "V2", "V3", "V4"):
    X, nom, tau = R.diseno(var); th = R.ajustar(X, tau, aj, np.ones(len(aj)))
    P = C.PROD.copy(); m = A.TRAMOS["AJUSTE"] | A.TRAMOS["ELECCION"]; ii = np.where(m)[0]; P[ii] = R.predecir(th, X, tau, ii)
    print(var, dict(zip(nom + (["tau_lm", "tau_mvf", "tau_sd"] if tau else []), np.round(np.r_[np.exp(th[:len(nom)]), th[len(nom):]], 3))))
    A.evaluar(P, f"fijo_{var}")
