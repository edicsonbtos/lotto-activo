"""Regresión de la función Compartir y del Anti Top-15 (servidor.py y rdint_vivo.py)."""
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import rdint_vivo
import servidor

ANIMALES = ["%s %s" % (c, n) for c, n in rdint_vivo.NOMBRE.items()]
CODIGOS = list(rdint_vivo.NOMBRE)


@pytest.mark.skipif(shutil.which("node") is None, reason="node no está instalado")
def test_js_compartir_es_sintaxis_valida():
    """Caso del bug 65e7b3c: saltos de línea reales dentro de cadenas JS."""
    js = re.sub(r"</?script>", "", servidor.JS.replace("%CALC%", "false"))
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf8") as f:
        f.write(js)
    try:
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
    finally:
        os.unlink(f.name)
    assert r.returncode == 0, r.stderr


def test_js_compartir_usa_escapes_no_saltos_dentro_de_cadenas():
    # solo el tramo de Compartir (el resto del JS usa comillas dentro de regex/HTML)
    js = servidor.JS[servidor.JS.rindex("<script>"):]  # último bloque = Compartir
    for linea in js.splitlines():
        assert linea.count("'") % 2 == 0, "cadena JS partida en varias líneas: %r" % linea


def test_html_compartir_sin_anti_no_ofrece_opciones_anti():
    h = servidor.html_compartir("Lotto Activo", "hoy", ANIMALES)
    assert 'value="anti"' not in h and 'value="ambos"' not in h
    assert 'data-x=""' in h


def test_html_compartir_con_anti_las_ofrece_y_escapa():
    h = servidor.html_compartir('Lotto "X"', "hoy", ANIMALES, ["1 <b>"])
    assert 'value="anti"' in h and 'value="ambos"' in h
    assert "&lt;b&gt;" in h and "<b>" not in h
    assert "&quot;X&quot;" in h


def test_html_compartir_recorta_top_a_15():
    h = servidor.html_compartir("LA", "hoy", ANIMALES)
    data_a = re.search(r'data-a="([^"]*)"', h).group(1)
    assert len(data_a.split("|")) == 15


def test_rd_compartir_con_y_sin_anti():
    assert 'value="anti"' not in rdint_vivo._compartir("RD", ANIMALES[:15])
    h = rdint_vivo._compartir("RD", ANIMALES[:15], ANIMALES[-15:])
    assert 'value="ambos"' in h and "data-x=" in h


def test_anti_vacio_si_hay_menos_de_30_animales():
    assert rdint_vivo._anti(CODIGOS[:29], {}) == ""


def test_anti_lista_los_15_ultimos_el_menos_probable_primero():
    pr = {c: 0.01 for c in CODIGOS}
    h = rdint_vivo._anti(CODIGOS, pr)
    assert h.count("<li>") == 15
    # el último del orden aparece antes que el penúltimo
    assert h.index(rdint_vivo._e(CODIGOS[-1])) < h.index(rdint_vivo._e(CODIGOS[-2]) + "</span>")
    assert "Anti Top-15" in h


def test_anti_no_divide_por_cero_con_masa_nula():
    h = rdint_vivo._anti(CODIGOS, {})
    assert "—" in h
