"""Revisión de código del 2026-10-26 (commits 9fbd3e2..a8e38c6): los diez hallazgos, uno por prueba."""
import json, os, re, sys
from datetime import datetime, timedelta

import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
sys.path.insert(0, os.path.join(AQUI, "..", ".claude", "skills", "lotto-historial"))
import servidor as s
import topes
import historial_txt as ht
import bajar
from test_registro_marcador import datos  # noqa: F401  (fixture)


@pytest.fixture(autouse=True)
def auto_limpio(monkeypatch):
    monkeypatch.setitem(s.AUTO, "activo", True)
    monkeypatch.setitem(s.AUTO, "pausa_hasta", None)
    monkeypatch.setitem(s.AUTO, "corriendo", False)


# 1. topes.json dañado: no se pisa lo acumulado.
def test_topes_danado_no_se_sobrescribe(tmp_path):
    ruta = tmp_path / "topes.json"
    ruta.write_text('[{"fecha": "2026-10-23", "juego": "la"', encoding="utf-8")
    texto, clase = topes.anotar(str(ruta), "2026-10-23", "la", 3, "5")
    assert clase == "bad" and "dañado" in texto
    assert ruta.read_text(encoding="utf-8") == '[{"fecha": "2026-10-23", "juego": "la"'
    assert topes.cargar(str(ruta)) == []           # la página sigue sin caerse


# 2. Una pasada automática que esperaba el cerrojo no anota tras un «deshacer».
def test_pasada_en_espera_respeta_la_pausa(monkeypatch):
    from scraping import auto_resultado
    llamadas = []
    monkeypatch.setattr(auto_resultado, "una_pasada", lambda: llamadas.append(1) or 1)
    monkeypatch.setitem(s.AUTO, "pausa_hasta", datetime.now() + timedelta(minutes=30))
    assert s.auto_pasada() == 0 and llamadas == []
    assert not s.AUTO["corriendo"]


# 3. La fecha del tope es visible y editable (no la del próximo LA, que puede ser mañana).
def test_formulario_topes_con_fecha_editable(monkeypatch):
    monkeypatch.setattr(s, "topes_resumen", lambda *a: {"anotaciones": 0})
    h = s.html_topes({"pf": "2099-01-01", "ph": 0})
    assert 'type="date"' in h and 'name="fecha"' in h and "2099-01-01" not in h


# 4. El mismo animal en el mismo sorteo cuenta una vez.
def test_resumen_sin_duplicados():
    ent = [{"creado": "2026-10-23T08:00:00", "fecha": "2026-10-23", "juego": "la", "hora": 2, "animales": a,
            "agencia": g} for a, g in ((["5"], "A"), (["5", "7"], "B"))]
    hora = lambda j, f, h: datetime(2026, 10, 23, 8 + h)
    r = topes.resumen(ent, lambda j, f, h: "5", None, hora)
    assert (r["resueltas"], r["animal_sorteos"], r["salieron"]) == (1, 2, 1)
    assert abs(r["esperado"] - 2 / 38) < 0.01


# 5. El O/E de LA usa el motor que se mostró (ag12+RD+capas), no el ensamble.
def test_prob_jugada_usa_el_principal(monkeypatch):
    monkeypatch.setattr(s, "MOTOR_PRINCIPAL", "ag12_rd")
    ag12 = [1.0 / 38] * 38; ag12[3] = 0.5
    r = {"fecha": "2026-10-23", "hora": 0, "scores": [1.0 / 38] * 38, "sombra": {"ag12": ag12}}
    assert s._prob_jugada(r, {})[3] == 0.5
    monkeypatch.setattr(s, "MOTOR_PRINCIPAL", "ensamble")
    assert s._prob_jugada(r, {}) == r["scores"]


# 6. Disco lleno o de solo lectura: aviso, no excepción, y sin .tmp colgando.
def test_topes_error_de_disco(tmp_path, monkeypatch):
    ruta = str(tmp_path / "topes.json")
    def falla(r, d, indent=None):
        open(r + ".tmp", "w").close(); raise OSError("disco lleno")
    monkeypatch.setattr(topes, "guardar_json", falla)
    texto, clase = topes.anotar(ruta, "2026-10-23", "la", 3, "5")
    assert clase == "bad" and not os.path.exists(ruta + ".tmp")


# 7. Sin topes no se recargan historiales ni predicciones en cada render.
def test_sin_topes_no_relee_nada(tmp_path, monkeypatch):
    monkeypatch.setattr(s, "TOPES", str(tmp_path / "no_hay_topes.json"))
    monkeypatch.setattr(s, "log_cargar", lambda: pytest.fail("releyó predicciones"))
    monkeypatch.setattr(s, "cargar", lambda: pytest.fail("releyó el historial"))
    assert s.topes_resumen()["anotaciones"] == 0


# 8. El .txt quita los tres puntajes del ensamble y deja sombra; leer() y armar() equivalen a exportar().
def test_historial_txt_quita_puntajes_y_deja_sombra(tmp_path):
    log = tmp_path / "p.json"
    reg = {"fecha": "2026-10-20", "hora": 0, "scores": [0.1] * 38, "scores_base": [0.1] * 38,
           "scores_sin_8am": [0.1] * 38, "sombra": {"ag12": [0.1] * 38}}
    log.write_text(json.dumps({"registros": [reg]}), encoding="utf-8")
    rutas = (str(tmp_path / "h.txt"), str(log), str(tmp_path / "r.txt"), str(tmp_path / "rp.json"))
    texto = ht.armar(*ht.leer(*rutas))
    linea = json.loads(texto.split("===== predicciones.jsonl =====\n")[1].split("\n")[0])
    assert set(linea) == {"fecha", "hora", "sombra"}
    assert texto.split("\n", 2)[2] == ht.exportar(*rutas).split("\n", 2)[2]


# 9. El LEEME del respaldo cuenta los cuatro archivos sin depender del orden de una lista.
def test_respaldo_leeme(datos):
    import io, zipfile
    z = zipfile.ZipFile(io.BytesIO(s.respaldo_historial()))
    leeme = z.read("LEEME.txt").decode("utf-8")
    assert re.search(r"^historial\.txt: \d+ sorteos$", leeme, re.M) and "pesos_ensamble.json:" in leeme
    assert "meta.json" not in leeme.split("\n\n")[1]


# 10. bajar.py no escribe secciones con nombres inesperados.
def test_bajar_ignora_nombres_raros(tmp_path):
    texto = "cabecera\n===== historial.txt =====\nx\n===== ../fuera.txt =====\nmalo\n"
    bajar.separar(texto, str(tmp_path / "out"))
    assert (tmp_path / "out" / "historial.txt").read_text(encoding="utf-8") == "x\n"
    assert not (tmp_path / "fuera.txt").exists()
