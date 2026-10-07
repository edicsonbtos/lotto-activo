"""secuencia_v2_dow: secuencia_final con el balance por día de la semana (dowbal=8).
Versión histórica de la familia secuencia (bandas de conteo [38,200) y [200,700) + misma columna).

Era una copia de 337 líneas de secuencia_final.py que solo añadía dowbal=8 a la configuración;
ahora hereda su código y solo declara la diferencia. Lo fija tests/test_modelos_secuencia.py
(predicciones idénticas a las de la copia anterior)."""
import importlib.util, os

_spec = importlib.util.spec_from_file_location("secuencia_final", os.path.join(os.path.dirname(os.path.abspath(__file__)), "secuencia_final.py"))
_sf = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_sf)

CFG_FINAL = {**_sf.CFG_FINAL, "dowbal": 8}


class Modelo(_sf.Modelo):
    nombre = "secuencia_v2_dow (dowbal8 + logit_final + bandas de conteo [38,200)/[200,700) + misma columna tras anterior)"

    def __init__(self, R=250, lam=1.0, inicio=200, tau=3000, tau_r=None, rho=None, **cfg):
        self.R = R; self.lam = lam; self.inicio = inicio; self.tau = tau; self.cfg = {**CFG_FINAL, **cfg}
        self.tau_r = tau_r; self.rho = rho
