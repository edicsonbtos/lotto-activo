"""Variante en sombra de la ventana de fecha a las 8:00 (exposicion.aplicar_8am y /api/sombra)."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas", "modelos"))
import exposicion as X
import servidor as s

U = [1 / 38] * 38


def test_8am_castiga_solo_la_ventana_del_dia():
    a = X.aplicar(U, "2026-10-15", 0); b = X.aplicar_8am(U, "2026-10-15", 0)
    r = [b[i] / a[i] for i in range(38)]
    ven = {X.IDX[c] for c in ("14", "15", "16")}
    assert all(abs(r[i] / r[0] - X.VENTANA_8AM) < 1e-9 for i in ven)
    assert all(abs(r[i] / r[0] - 1) < 1e-9 for i in range(38) if i not in ven)
    assert abs(sum(b) - 1) < 1e-9


def test_otras_horas_igual_que_aplicar():
    assert X.aplicar_8am(U, "2026-10-15", 3) == X.aplicar(U, "2026-10-15", 3)


def test_dia_1_no_toca_el_cero():
    a = X.aplicar(U, "2026-11-01", 0); b = X.aplicar_8am(U, "2026-11-01", 0)
    assert abs(b[X.IDX["0"]] / a[X.IDX["0"]] - b[X.IDX["5"]] / a[X.IDX["5"]]) < 1e-9
    assert s._ventana_8am("2026-11-01") == [X.IDX["1"], X.IDX["2"]]


def test_marcador_cuenta_solo_8am_desde_la_fecha(monkeypatch):
    def reg(f, h, salio):
        return {"fecha": f, "hora": h, "salio": salio, "scores": U, "modelo": s.MODELO_MARCADOR}
    regs = [reg("2026-10-03", 0, X.IDX["3"]),     # antes de la fecha: fuera
            reg("2026-10-04", 0, X.IDX["4"]),     # 8:00, en la ventana (3, 4, 5)
            reg("2026-10-04", 1, X.IDX["4"]),     # 9:00: fuera
            reg("2026-10-05", 0, X.IDX["20"])]    # 8:00, fuera de la ventana
    v = s.marcador_sombra({"registros": regs})["ventana_8am"]
    assert v["n"] == 2 and v["ventana_obs"] == 1
    assert 0.1 < v["ventana_esp"] < 0.2              # ~3/38 por sorteo con exposición


# Auditoría 8:00 del 2026-10-31 (P2 metodológico): el IC90 de mbits solo ve lo observado; con 0 eventos no incluye
# la pérdida grande si sale un animal castigado. /api/sombra debe traer la prueba contra la base.
def _reg8(f, salio):
    return {"fecha": f, "hora": 0, "salio": salio, "scores": U, "modelo": s.MODELO_MARCADOR}


def _p_ventana(f):
    pe = X.aplicar(U, f, 0); t = sum(pe)
    return sum(pe[i] for i in s._ventana_8am(f)) / t


def test_prob_de_ver_tan_pocos_eventos_si_la_ventana_no_hiciera_nada():
    regs = [_reg8("2026-10-04", X.IDX["4"]), _reg8("2026-10-05", X.IDX["20"])]   # 1 de 2 en la ventana
    v = s.marcador_sombra({"registros": regs})["ventana_8am"]
    p1, p2 = _p_ventana("2026-10-04"), _p_ventana("2026-10-05")
    assert abs(v["p_obs_o_menos"] - (1 - p1 * p2)) < 1e-3
    cero = s.marcador_sombra({"registros": regs[1:]})["ventana_8am"]               # 0 de 1
    assert abs(cero["p_obs_o_menos"] - (1 - p2)) < 1e-3


def test_mbits_esperados_si_la_base_es_la_verdad_son_negativos():
    f = "2026-10-05"
    v = s.marcador_sombra({"registros": [_reg8(f, X.IDX["20"])]})["ventana_8am"]
    pe = X.aplicar(U, f, 0); p8 = X.aplicar_8am(U, f, 0)
    te, t8 = sum(pe), sum(p8)
    kl = sum(pe[i] / te * math.log2((p8[i] / t8) / (pe[i] / te)) for i in range(38))
    assert abs(v["mbits_esperado_si_base"] - 1000 * kl) < 0.1 and v["mbits_esperado_si_base"] < 0
    assert "730" in v["lectura"] and "IC90" in v["lectura"]
