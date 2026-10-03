"""Variante en sombra de la ventana de fecha a las 8:00 (exposicion.aplicar_8am y /api/sombra)."""
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
