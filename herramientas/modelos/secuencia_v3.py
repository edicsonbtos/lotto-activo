"""secuencia_v3: secuencia_final SIN el efecto 'misma columna' (auditoría: ruido
elegido a posteriori, +2,7 ± 0,9 mbits tras buscar entre miles de clases).
Conserva las bandas de conteo [38,200) y [200,700), que sí sobreviven a la
corrección por búsqueda (max |z| 9,9 frente a p99 nulo 3,8)."""
import importlib.util, os

_spec = importlib.util.spec_from_file_location("secuencia_final", os.path.join(os.path.dirname(os.path.abspath(__file__)), "secuencia_final.py"))
_sf = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_sf)


class Modelo(_sf.Modelo):
    nombre = "secuencia_v3 (logit_final + bandas de conteo, sin columna)"

    def __init__(self, **kw):
        kw.setdefault("mismacol", False); kw.setdefault("mismacol2", False)
        super().__init__(**kw)
