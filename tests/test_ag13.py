"""ag13 en sombra (herramientas/exploracion/PREREGISTRO_ag13.md): parseo, cadena y regla de decisión."""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas", "modelos"))
import ag13 as A
import experimentos as E
import exposicion as X

F = "2026-10-20"
LOTOVEN = ('<h3 class="text-center pb-3" title="Datos Lotto Activo">x</h3><div class="title three">martes, 20 de October de 2026</div>'
           '<span class="info">Numero</span><span class="result"> 7 </span>'
           '<span class="info">Numero</span><span class="result">00</span>'
           '<h3 class="text-center pb-3" title="Datos Lotto Activo RD Int">y</h3>'
           '<span class="info">Numero</span><span class="result">30</span>')
LDH = ('<input id="datepicker" value="2026-10-20"><div class="card"><h6 class="h7">Lotto Activo</h6><h6>12 Gallo</h6></div>'
       '<div class="card"><h6 class="h7">Lotto Activo Rd Int</h6><h6>33 Perro</h6></div>')


def _paginas(tmp, lotoven=LOTOVEN * 1, ldh=LDH, cuando="2026-10-20T06:10:00"):
    c = tmp / "datos_publicados" / F
    c.mkdir(parents=True)
    (c / "lotoven_datos.html").write_text(lotoven, encoding="utf-8")
    (c / "loteriadehoy_datos.html").write_text(ldh, encoding="utf-8")
    json.dump({"lotoven_datos": {"ok": True, "cuando": cuando}, "loteriadehoy_datos": {"ok": True, "cuando": cuando}},
              open(c / "meta.json", "w"))
    return c


def test_parseo_excluye_rd_y_exige_la_fecha_del_dia():
    s, _ = A.conjunto_fuente(LOTOVEN, "lotoven", F)
    assert s == {A.IDX["7"], A.IDX["00"]}                       # el 30 es de RD Int
    s, _ = A.conjunto_fuente(LDH, "loteriadehoy", F)
    assert s == {A.IDX["12"]}                                   # el 33 es de RD Int
    s, motivo = A.conjunto_fuente(LDH, "loteriadehoy", "2026-10-21")
    assert s is None and "no del 2026-10-21" in motivo


def test_conjunto_del_dia_une_las_dos_fuentes(tmp_path):
    c = _paginas(tmp_path)
    r = A.conjunto_del_dia(str(c), F)
    assert r["u"] == sorted({A.IDX["7"], A.IDX["00"], A.IDX["12"]})
    assert set(r["fuentes"]) == {"lotoven", "loteriadehoy"} and len(r["fuentes"]["lotoven"]["sha256"]) == 16


def test_con_una_sola_fuente_no_cuenta(tmp_path):
    c = _paginas(tmp_path, ldh="<html></html>")
    assert "falta" in A.conjunto_del_dia(str(c), F)


def test_cadena_ag13_baja_solo_a_los_de_u_y_suma_uno():
    p = [1 / 38] * 38
    q_exp, p13, nd = A.cadena(p, F, 3, [A.IDX["7"], A.IDX["12"]])
    assert abs(sum(p13) - 1) < 1e-12 and abs(sum(nd) - 1) < 1e-12
    r = [p13[i] / q_exp[i] for i in range(38)]
    assert all(r[A.IDX[c]] < r[A.IDX["1"]] for c in ("7", "12"))
    assert abs(r[A.IDX["7"]] / r[A.IDX["1"]] - A.PRON_X) < 1e-9


def test_nd_no_toca_lo_que_la_exposicion_ya_toco():
    # día 20, hora 3 -> a las 11 (12 h): números tocados = 19, 20, 21, 22, 11 y mes 10
    p = [1 / 38] * 38
    u = [A.IDX["20"], A.IDX["7"]]
    q_exp, _, nd = A.cadena(p, F, 3, u)
    r = [nd[i] / q_exp[i] for i in range(38)]
    assert abs(r[A.IDX["20"]] / r[A.IDX["1"]] - 1) < 1e-9       # el 20 ya lo bajó la exposición: no se repite
    assert abs(r[A.IDX["7"]] / r[A.IDX["1"]] - A.PRON_X_ND) < 1e-9


def test_pron_del_dia_espera_la_ventana_y_luego_marca_falta(tmp_path):
    ahora = datetime(2026, 10, 20, 7, 0)
    assert E.pron_del_dia(str(tmp_path), F, ahora) is None      # aún se puede bajar
    r = E.pron_del_dia(str(tmp_path), F, datetime(2026, 10, 20, 9, 0))
    assert "falta" in r and "lotoven" in r["falta"]


def test_pagina_bajada_despues_de_las_8_no_vale(tmp_path):
    _paginas(tmp_path, cuando="2026-10-20T08:30:00")
    assert "falta" in E.pron_del_dia(str(tmp_path), F, datetime(2026, 10, 20, 12, 0))


def test_completar_pron_pone_el_conjunto_y_no_toca_scores(tmp_path):
    _paginas(tmp_path)
    reg = {"fecha": F, "hora": 3, "salio": None, "scores": [1 / 38] * 38, "sombra": {"ag12": [1 / 38] * 38}}
    antes = json.dumps(reg["scores"])
    assert E.completar_pron([reg], str(tmp_path), datetime(2026, 10, 20, 12, 0))
    assert "u" in reg["pron"] and json.dumps(reg["scores"]) == antes
    assert not E.completar_pron([reg], str(tmp_path), datetime(2026, 10, 20, 12, 1))   # ya está: no repite


def test_registros_viejos_o_sin_sombra_no_reciben_pron(tmp_path):
    viejo = {"fecha": "2026-10-01", "hora": 3, "sombra": {"ag12": [1 / 38] * 38}}
    sin = {"fecha": F, "hora": 3}
    assert not E.completar_pron([viejo, sin], str(tmp_path), datetime(2026, 10, 20, 12, 0))
    assert "pron" not in viejo and "pron" not in sin


def _res(n_jornadas, w_en_u, ganador_bien):
    """n_jornadas días de 12 sorteos; el ensamble es uniforme y ag12 también (el efecto sale solo de la cadena)."""
    out = []
    for j in range(n_jornadas):
        f = "2026-11-%02d" % (j % 28 + 1) if j < 28 else "2026-12-%02d" % (j - 27)
        for h in range(12):
            u = [A.IDX["7"], A.IDX["12"]]
            w = u[0] if w_en_u else A.IDX["30"]
            out.append({"fecha": f, "hora": h, "salio": w, "scores": [1 / 38] * 38, "modelo": "x",
                        "sombra": {"ag12": [1 / 38] * 38}, "pron": {"u": u}})
    return out


FICHAS = [0, 2, 2, 2, 1, 1] + [0] * 33


def test_marcador_vacio_y_con_faltas():
    m = E.marcador_ag13([], FICHAS, {})
    assert m["n"] == 0 and "esperando" in m["estado"]
    r = [{"fecha": F, "hora": 1, "salio": 3, "scores": [1 / 38] * 38, "sombra": {"ag12": [1 / 38] * 38},
          "pron": {"falta": "x"}}]
    m = E.marcador_ag13(r, FICHAS, {})
    assert m["n"] == 0 and m["dias_sin_pron"] == {F: "x"}


def test_si_ganan_los_de_u_ag13_pierde_y_si_no_ganan_gana():
    # ganan siempre los animales que ag13 baja (U): ag13 debe quedar peor que el ensamble
    m = E.marcador_ag13(_res(10, True, None), FICHAS, {})
    assert m["n"] == 120 and m["p1_ag13_menos_ensamble"]["media"] < 0
    m = E.marcador_ag13(_res(10, False, None), FICHAS, {})
    assert m["p1_ag13_menos_ensamble"]["media"] > 0 or m["ag13_menos_ag12_rd_exp"]["media"] > 0


def test_freno_apaga_con_600_y_delta_menor_a_menos_10():
    m = E.marcador_ag13(_res(52, True, None), FICHAS, {})       # 624 sorteos, todos contra ag13
    assert m["n"] == 624 and m["estado"].startswith("APAGADO")


def test_decision_usa_solo_los_primeros_931_y_no_pasa_si_el_ic_cruza_cero():
    m = E.marcador_ag13(_res(80, False, None), FICHAS, {})       # 960 sorteos
    d = m["decision"]
    assert d is not None and d["n"] == E.AG13_N_DECIDE
    assert (d["pasa"] is True) == (d["mbits"]["ic90"][0] > 0 and d["top5_pp_ficha"]["media"] >= E.AG13_T5_MIN)


def test_marcador_sombra_expone_ag13():
    import servidor as s
    m = s.marcador_sombra({"registros": []})
    assert "ag13" in m and m["ag13"]["n"] == 0
    assert "ag14" in m and m["ag14"]["n"] == 0
