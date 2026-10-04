"""salud_modelo(): ventanas, retorno por jugada y estado contra la referencia de prueba."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import servidor as s

ORDEN = list(range(38))


def _regs(puestos, desde="2026-09-01"):
    from datetime import date, timedelta
    d0 = date.fromisoformat(desde); out = []
    for i, p in enumerate(puestos):
        out.append({"fecha": (d0 + timedelta(days=i // 12)).isoformat(), "hora": i % 12,
                    "orden_completo": ORDEN, "salio": ORDEN[p - 1], "top3": ORDEN[:3],
                    "modelo": s.MODELO_MARCADOR})
    return {"registros": out}


def test_cuenta_aciertos_y_retorno():
    d = _regs([1, 2, 3, 16] * 12)                     # 48 sorteos, 4 días
    v = s.salud_modelo(d)["ventanas"][-1]
    top2, top5, top15 = v["jugadas"]
    assert (top2["aciertos"], top5["aciertos"], top15["aciertos"]) == (24, 36, 36)
    assert abs(top2["retorno"] - (30 * 24 / (48 * 2) - 1)) < 1e-9
    assert abs(top5["retorno"] - (30 * (12 * 2 * 3) / (48 * 8) - 1)) < 1e-9
    assert v["estado"] == "normal"


def test_alarma_si_el_top15_se_hunde():
    d = _regs([20] * 100 + [1] * 20)                  # 20/120 en Top-15 contra 49,5 % de referencia
    assert s.salud_modelo(d)["ventanas"][-1]["estado"] == "alarma"


def test_pocos_datos_y_ventana_de_7_dias():
    d = _regs([1] * 12 * 10)                          # 10 días
    w = s.salud_modelo(d)["ventanas"]
    assert w[0]["n"] == 84 and w[2]["n"] == 120
    assert s.salud_modelo(_regs([1] * 10))["ventanas"][0]["estado"] == "pocos datos"
    assert "Salud del modelo" in s.html_salud(d)
