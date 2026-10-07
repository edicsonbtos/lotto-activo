"""secuencia_v1: logit_final + bloques secuenciales (columna del anterior x columna candidato,
diferencia circular respecto al anterior). Versión histórica de la familia secuencia.

Era una copia de 335 líneas de secuencia_final.py con otra configuración (colpar + dif_lags);
ahora hereda su código y solo declara la configuración. Lo fija tests/test_modelos_secuencia.py
(predicciones idénticas a las de la copia anterior)."""
import importlib.util, os

_spec = importlib.util.spec_from_file_location("secuencia_final", os.path.join(os.path.dirname(os.path.abspath(__file__)), "secuencia_final.py"))
_sf = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_sf)

CFG_FINAL = dict(colpar=True, dif_lags=[1], cuota=True, s_gap=15.0, s_hoy=15.0, s_dias=15.0, s_g2=150.0, s_cuota=15.0, ventanas=[12, 38])


class Modelo(_sf.Modelo):
    nombre = "secuencia_v1"

    def __init__(self, R=250, lam=1.0, inicio=200, tau=3000, tau_r=None, rho=None, **cfg):
        # NO se parte del CFG de secuencia_final: sus opciones (bandas, mismacol...) cambiarían este modelo.
        self.R = R; self.lam = lam; self.inicio = inicio; self.tau = tau; self.cfg = {**CFG_FINAL, **cfg}
        self.tau_r = tau_r; self.rho = rho
