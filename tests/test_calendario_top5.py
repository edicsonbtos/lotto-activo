import sys, os

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import servidor as s


def _registro(fecha, hora, ganador):
    return {"fecha": fecha, "hora": hora, "creado": f"{fecha}T07:50:00", "salio": ganador,
            "orden_completo": list(range(38)), "top3": [0, 1, 2]}


def test_calendario_marca_solo_el_top5_de_lotto_a_las_ocho():
    d = {"registros": [_registro("2026-10-23", 0, 0),
                        _registro("2026-10-24", 0, 10),
                        _registro("2026-10-25", 1, 0)]}
    html = s.html_calendario_8am(d, "2026-10")
    assert 'class="cal-dia cal-acierto"' in html
    assert 'class="cal-dia cal-fallo"' in html
    assert html.count("cal-acierto") == 1
    assert html.count("cal-fallo") == 1
    assert "8:00 AM" in html and "RD Internacional" not in html


def test_historial_muestra_mas_de_los_ultimos_cinco_dias():
    registros = [_registro("2026-10-23", 0, 0) for _ in range(361)]
    html = s.html_resultados({"registros": registros})
    assert "Se muestran los últimos 360 de 361." in html
    assert "de los últimos 360" in s.resumen_resultados({"registros": registros})
