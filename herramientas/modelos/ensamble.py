"""Ensamble log-lineal de modelos auditados.

P(i) ∝ exp( sum_m w_m · log p_m(i) )

Los pesos w se ajustan por máxima verosimilitud (L-BFGS con L2 hacia pesos
iguales) sobre las predicciones walk-forward PASADAS de cada submodelo y se
reajustan cada R sorteos: el bloque [T, T+R) usa w ajustado con filas < T.
Los submodelos predicen desde `arranque` (antes de `desde`) para que haya
historial con el que ajustar los pesos desde la primera fila evaluada.
"""
import importlib.util, os
import numpy as np
from scipy.optimize import minimize

AQUI = os.path.dirname(os.path.abspath(__file__))
K = 38
BASE = ["intradia_v2", "logit_final", "haz_v1"]


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(AQUI, nombre + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Modelo()


def ajustar_pesos(L, y, w0, lam=5.0, peso=None):
    """L: (N, M, K) log-probabilidades; y: (N,). Devuelve w (M,)."""
    N, M, _ = L.shape
    filas = np.arange(N)
    peso = np.ones(N) if peso is None else peso
    Ly = L[filas, :, y]                      # (N, M)
    prior = np.full(M, 1.0 / M)

    def f(w):
        z = np.einsum("nmk,m->nk", L, w)
        zm = z.max(1, keepdims=True)
        e = np.exp(z - zm); S = e.sum(1)
        p = e / S[:, None]
        nll = -(peso * (Ly @ w - np.log(S) - zm[:, 0])).sum() + 0.5 * lam * np.sum((w - prior) ** 2)
        esp = np.einsum("nk,nmk->nm", p, L)  # E_p[log p_m]
        g = -(peso[:, None] * (Ly - esp)).sum(0) + lam * (w - prior)
        return nll, g

    r = minimize(f, w0, jac=True, method="L-BFGS-B", bounds=[(-0.5, 2.0)] * M, options={"maxiter": 200})
    return r.x


class Modelo:
    nombre = "ensamble"

    def __init__(self, base=None, R=250, arranque=1000, tau=3000.0, lam=5.0):
        self.base = list(base or BASE)
        self.R, self.arranque, self.tau, self.lam = R, arranque, tau, lam
        self.nombre = "ensamble(" + "+".join(self.base) + ")"

    def predecir(self, datos, desde):
        n = len(datos)
        a = min(self.arranque, desde)
        modelos = [_cargar(b) for b in self.base]
        L = np.stack([np.log(np.clip(m.predecir(datos, a), 1e-9, None)) for m in modelos], axis=1)  # (n-a, M, K)
        L -= np.log(np.exp(L).sum(2, keepdims=True))
        y = np.asarray(datos.seq)[a:]
        M = len(modelos)
        w = np.full(M, 1.0 / M)
        out = np.empty((n - desde, K))
        self.historial_pesos = []
        for T in range(desde, n, self.R):
            j = T - a                            # filas de L anteriores a T
            if j >= 200:
                pesos_t = np.exp(-(j - 1 - np.arange(j)) / self.tau) if self.tau else None
                w = ajustar_pesos(L[:j], y[:j], w, self.lam, pesos_t)
            self.historial_pesos.append((T, w.copy()))
            b = min(T + self.R, n)
            z = np.einsum("nmk,m->nk", L[T - a:b - a], w)
            z -= z.max(1, keepdims=True)
            p = np.exp(z)
            out[T - desde:b - desde] = p / p.sum(1, keepdims=True)
        self.pesos = w
        return out
