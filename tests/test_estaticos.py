"""CSS/JS viven en static/: deben ser byte a byte los que antes estaban embebidos en servidor.py."""
import hashlib, json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import servidor as s


def _sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _oro():
    with open(os.path.join(AQUI, "oro_css_js.json"), encoding="utf-8") as f:
        return json.load(f)


def test_css_identico_al_embebido():
    assert _sha(s.CSS) == _oro()["CSS"]


def test_js_identico_al_embebido():
    assert _sha(s.JS) == _oro()["JS"]


def test_render_incluye_css_y_js_de_static():
    html = s.render()
    assert s.CSS in html
    assert s.JS.replace("%CALC%", "true") in html or s.JS.replace("%CALC%", "false") in html
