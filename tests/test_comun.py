"""Helpers compartidos por servidor.py (Lotto Activo) y rdint_vivo.py (RD Internacional).

oro_vistas.json son las salidas que ambos módulos daban ANTES de unificar el código:
la unificación no puede cambiar ni un byte de HTML.
"""
import json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import comun
import rdint_vivo
import servidor

with open(os.path.join(AQUI, "oro_vistas.json"), encoding="utf-8") as f:
    ORO = json.load(f)


def test_comun_reproduce_el_html_de_antes():
    assert comun.fx(0, "a") == ORO["fx_0"]
    assert comun.fx(1, "a") == ORO["fx_1"]
    assert comun.fx(3, "b") == ORO["fx_3"]
    assert comun.COLS == ORO["cols"]
    assert comun.nav("la", 0, 5) == ORO["nav_la_0"]
    assert comun.nav("la", 2, 5) == ORO["nav_la_2"]
    assert comun.nav("la", 5, 5) == ORO["nav_la_5"]
    assert comun.nav("rd", 1, 3) == ORO["nav_rd_1"]
    assert comun.fila(3, "7", "Perico", "12,34 % · hace 5 sorteos", 2, 1) == ORO["fila_la"]
    assert comun.sec("x", "Tit", "m<eta>", "<p>c</p>") == ORO["sec"]
    assert comun.sec("x", "Tit", "m", "c", abierto=True) == ORO["sec_abierta"]
    assert comun.esc("<a&'\">") == ORO["esc"]


def test_comun_compartir_con_y_sin_fecha():
    assert comun.compartir('Lotto "X"', ["1 A", "2 B"], ["3 C"], cuando="hoy") == ORO["compartir_la"]
    assert comun.compartir("L", ["1 A"], cuando="hoy") == ORO["compartir_la_sin"]
    # RD no lleva data-f
    assert comun.compartir('RD "X"', ["1 A", "2 B"], ["3 C"]) == ORO["compartir_rd"]
    assert comun.compartir("R", ["1 A"]) == ORO["compartir_rd_sin"]


def test_comun_compartir_recorta_el_top_a_15():
    animales = [str(i) for i in range(20)]
    h = comun.compartir("L", animales, cuando="hoy")
    assert 'data-a="%s"' % "|".join(animales[:15]) in h


def test_servidor_y_rdint_siguen_dando_lo_mismo():
    assert servidor._fx(3, "b") == ORO["fx_3"]
    assert servidor.COLS_JUGADA == ORO["cols"]
    assert servidor.html_nav_hist("rd", 1, 3) == ORO["nav_rd_1"]
    assert servidor.fila_jugada(3, "7", "Perico", "12,34 % · hace 5 sorteos", 2, 1) == ORO["fila_la"]
    assert servidor.sec("x", "Tit", "m<eta>", "<p>c</p>") == ORO["sec"]
    assert servidor.html_compartir('Lotto "X"', "hoy", ["1 A", "2 B"], ["3 C"]) == ORO["compartir_la"]
    assert rdint_vivo._fila(3, "7", 12.3456) == ORO["fila_rd"]
    assert rdint_vivo._sec("x", "Tit", "m<eta>", "<p>c</p>") == ORO["sec_rd"]      # RD escapa la meta
    assert rdint_vivo._compartir('RD "X"', ["1 A", "2 B"], ["3 C"]) == ORO["compartir_rd"]
    assert rdint_vivo._e("<a&'\">") == ORO["esc_rd"]


def test_guardar_json_es_atomico_y_respeta_indent(tmp_path):
    ruta = str(tmp_path / "x.json")
    comun.guardar_json(ruta, {"a": "ñ", "b": [1, 2]})
    assert json.load(open(ruta, encoding="utf-8")) == {"a": "ñ", "b": [1, 2]}
    assert "\n" not in open(ruta, encoding="utf-8").read().strip()      # sin indent: una línea
    comun.guardar_json(ruta, {"a": 1}, indent=1)
    assert open(ruta, encoding="utf-8").read().startswith('{\n "a"')
    assert os.listdir(tmp_path) == ["x.json"]                           # sin .tmp huérfano


def test_respaldo_zip_solo_incluye_lo_que_existe(tmp_path):
    import io, zipfile
    (tmp_path / "a.txt").write_text("hola", encoding="utf-8")
    z = zipfile.ZipFile(io.BytesIO(comun.respaldo_zip(str(tmp_path), ["a.txt", "no_existe.json"])))
    assert z.namelist() == ["a.txt"] and z.read("a.txt") == b"hola"
