"""Ensamble log-lineal: intradia_v2 + secuencia_v3 + haz_v1 (secuencia_v3 ya contiene a logit_final)."""
import importlib.util, os
_spec = importlib.util.spec_from_file_location("ensamble", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensamble.py"))
_e = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_e)

class Modelo(_e.Modelo):
    def __init__(self, **kw):
        kw.setdefault("base", ["intradia_v2", "secuencia_v3", "haz_v1"])
        super().__init__(**kw)
