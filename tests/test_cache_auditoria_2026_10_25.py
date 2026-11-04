"""Cachés de rendimiento de la auditoría 2026-10-25: mismo resultado, menos trabajo."""
import os
import rdint_vivo
import servidor


def test_hazard_memoizado_igual_y_sin_recalcular(monkeypatch):
    seq = [(i * 7 + i // 3) % 38 for i in range(600)]
    esperado = servidor._hazard_calcular(seq)
    servidor._HZ_CACHE.clear()
    assert servidor.hazard(seq) == esperado
    llamadas = []
    monkeypatch.setattr(servidor, "_hazard_calcular", lambda s: llamadas.append(1) or esperado)
    assert servidor.hazard(seq) == esperado
    assert not llamadas
    seq2 = seq + [5]
    servidor.hazard(seq2)
    assert llamadas


def test_hazard_devuelve_copia():
    seq = [i % 38 for i in range(300)]
    a = servidor.hazard(seq); a[0] = -1
    assert servidor.hazard(seq)[0] != -1


def test_cargar_rd_cache_por_mtime(tmp_path, monkeypatch):
    p = tmp_path / "rd.txt"
    p.write_text("2026-10-01 0 5\n", encoding="utf-8")
    monkeypatch.setattr(rdint_vivo, "RD_HIST", str(p))
    monkeypatch.setattr(rdint_vivo, "_sembrar", lambda: None)
    rdint_vivo._RD_CACHE.clear()
    a = rdint_vivo.cargar_rd()
    assert a == [("2026-10-01", 0, "5")]
    a.append("x")
    assert rdint_vivo.cargar_rd() == [("2026-10-01", 0, "5")]
    with open(p, "a", encoding="utf-8") as f:
        f.write("2026-10-01 1 7\n")
    assert len(rdint_vivo.cargar_rd()) == 2


def test_cargar_cache_por_mtime(tmp_path, monkeypatch):
    p = tmp_path / "h.txt"
    p.write_text("2026-10-01 0 5\n", encoding="utf-8")
    monkeypatch.setattr(servidor, "HIST", str(p))
    servidor._CARGAR_CACHE.clear()
    a = servidor.cargar()
    a.append("x")
    assert len(servidor.cargar()) == 1
    with open(p, "a", encoding="utf-8") as f:
        f.write("2026-10-01 1 7\n")
    assert len(servidor.cargar()) == 2


def test_tope_global_de_herramientas(monkeypatch):
    class P:
        def poll(self):
            return None
    monkeypatch.setattr(servidor, "TAREAS", {"a": {"proc": P()}})
    lanzados = []
    monkeypatch.setattr(servidor.subprocess, "Popen", lambda *a, **k: lanzados.append(1))
    clave = next(k for k in servidor.HERRAMIENTAS if k != "a")
    servidor.iniciar_tarea(clave)
    assert not lanzados


def test_regla_rd_mueve_el_animal_correcto():
    """La cadena RD -> orden no debe apagarse en silencio (int vs código)."""
    import experimentos as ex
    p = [1.0 / 38] * 38
    rd = {("2026-10-20", 5): "31"}
    q, usado = ex.con_rd(p, rd, "2026-10-20", 6)      # h-1 -> x0,50
    assert usado and q[ex.IDX["31"]] == p[0] * 0.5
    rd_int = {("2026-10-20", 5): ex.IDX["31"]}         # índice entero: la regla se apaga
    q2, usado2 = ex.con_rd(p, rd_int, "2026-10-20", 6)
    assert not usado2
