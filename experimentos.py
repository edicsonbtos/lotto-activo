# -*- coding: utf-8 -*-
"""Experimentos en vivo de Lotto Activo, aparte del pronóstico principal.

  * Regla de cambio por RD (PREREGISTRO_cambio_rd_top5.md): solo cambia lo que se MUESTRA.
  * Pronósticos en sombra (motor_nuevo/RETOMAR.md): ag12, ag12+RD y la corrección por exposición
    se guardan y se miden, pero NO entran en el marcador principal.

No importa servidor.py (evita el ciclo): recibe los sorteos resueltos y las fichas por parámetro.
servidor.py conserva los mismos nombres como envoltorios finos (tests/test_experimentos.py).
"""
import math
import os
import sys
from datetime import datetime

from comun import IDX, K, PAGO, POS

HERR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "herramientas")


def _ahora():
    return datetime.now().isoformat(timespec="seconds")


def _rd_por_slot():
    """{(fecha, h): código} de RD Internacional. Falla si rdint_vivo no carga; cada llamador decide qué hacer."""
    import rdint_vivo
    return {(f, h): c for f, h, c in rdint_vivo.cargar_rd()}


# ------------------------------------------------------------ regla de cambio por RD
CAMBIO_RD_DESDE = "2026-09-23"
# Marcador en vivo de la regla: cuenta desde el día en que se adoptó, que la prueba (hasta
# 2026-09-22) nunca vio. RD de las (h−1):30 siempre sale antes de LA h:00, así que aplicarla
# al congelado después no usa nada del futuro.


def cambiar(orden, cod):
    """Igual que herramientas/rdint/cambio_top5.py (lo validado): se quita del
    Top-5 el animal `cod`, los de abajo suben un puesto y el 6º entra 5º; `cod`
    pasa al 6º. Devuelve el MISMO objeto `orden` si no hay cambio."""
    r = IDX[cod]
    if len(orden) < 6 or r not in orden[:5]:
        return orden
    return [x for x in orden[:5] if x != r] + [orden[5], r] + list(orden[6:])


def cambio_rd(orden, pf, ph):
    """Regla de cambio (PREREGISTRO_cambio_rd_top5.md, adoptada sin confirmar el 2026-09-23).

    Si el animal que salió en RD Internacional a las (h−1):30 está en el Top-5 de LA h:00, se
    intercambia con el 6º. Solo cambia lo que se MUESTRA para jugar: el congelado que se puntúa
    no se toca. Devuelve (orden, info); info es None en el sorteo de 8:00 o si falla RD."""
    if ph <= 0 or len(orden) < 6:
        return orden, None
    try:
        import rdint_vivo
        cod = next((c for f, h, c in rdint_vivo.cargar_rd() if f == pf and h == ph - 1), None)
        info = {"hora_rd": rdint_vivo.HORAS_RD[ph - 1], "rd": cod}
    except Exception:  # noqa: BLE001 — RD no debe tumbar la jugada de LA
        return orden, None
    nuevo = cambiar(orden, cod) if cod is not None else orden
    if nuevo is orden:
        return orden, info
    info.update(sale=cod, entra=POS[orden[5]], puesto=orden.index(IDX[cod]) + 1)
    return nuevo, info


def marcador_cambio_rd(res, fichas):
    """Top-5 escalonado con y sin la regla de cambio, sobre el mismo congelado.
    `res` son los sorteos resueltos del modelo en uso; `fichas`, las fichas por puesto del Top-5."""
    try:
        rd = _rd_por_slot()
    except Exception:  # noqa: BLE001
        return None
    m = dict(desde=CAMBIO_RD_DESDE, n=0, cambios=0, gano_rd=0, gano_6=0, sin=0, con=0)
    for r in res:
        orden = r.get("orden_completo")
        if not orden or r["fecha"] < CAMBIO_RD_DESDE or r["hora"] <= 0 or r["salio"] not in orden:
            continue
        cod = rd_de_registro(r, rd).get((r["fecha"], r["hora"] - 1))
        if cod is None:
            continue
        m["n"] += 1
        p = orden.index(r["salio"]) + 1
        m["sin"] += PAGO * fichas[p] - sum(fichas)
        nuevo = cambiar(orden, cod)
        if nuevo is not orden:
            m["cambios"] += 1
            m["gano_rd"] += r["salio"] == IDX[cod]
            m["gano_6"] += r["salio"] == orden[5]
        m["con"] += PAGO * fichas[nuevo.index(r["salio"]) + 1] - sum(fichas)
    m["dif"] = m["con"] - m["sin"]
    return m


# ------------------------------------------------ regla RD extendida al Top-15
# PREREGISTRO enjambre_2026-09-30/ag12_top15: PASA dev +0,97 pp/ficha, réplica 2026 +2,47 [+1,59; +3,36]
# (herramientas/exploracion/ag12_2026_2026-10-07: fresco +1,57, frágil). Adoptada el 2026-10-07 con OK del
# usuario y medida en vivo aparte. El Top-5 sale IDÉNTICO al de cambiar(): solo cambia del 6º al 16º.
CAMBIO_RD15_DESDE = "2026-10-07"


def cambiar15(orden, cod):
    """Si `cod` está en el Top-15 se quita, los de abajo suben un puesto, el 16º entra 15º y `cod` pasa al 16º."""
    r = IDX[cod]
    if len(orden) < 16 or r not in orden[:15]:
        return orden
    return [x for x in orden[:15] if x != r] + [orden[15], r] + list(orden[16:])


def cambio_rd15(orden, pf, ph):
    """Como cambio_rd pero con la regla en el Top-15. info trae tope=5 o 15 según dónde estaba `cod`."""
    nuevo, info = cambio_rd(orden, pf, ph)
    if info is None or info["rd"] is None or len(orden) < 16:
        return nuevo, info
    cod = info["rd"]
    n15 = cambiar15(orden, cod)
    if n15 is orden:
        return nuevo, info
    puesto = orden.index(IDX[cod]) + 1
    info.update(sale=cod, puesto=puesto, tope=5 if puesto <= 5 else 15,
                entra=POS[orden[5] if puesto <= 5 else orden[15]])
    return n15, info


def marcador_cambio_rd15(res, fichas15):
    """Top-15 ponderado con y sin la regla, sobre el mismo congelado. `fichas15`: fichas por puesto del ponderado.
    Cuenta desde CAMBIO_RD15_DESDE; RD (h−1):30 sale antes de LA h:00, así que aplicarla al congelado no usa el futuro."""
    try:
        rd = _rd_por_slot()
    except Exception:  # noqa: BLE001
        return None
    m = dict(desde=CAMBIO_RD15_DESDE, n=0, cambios=0, gano_rd=0, gano_16=0, sin=0, con=0)
    for r in res:
        orden = r.get("orden_completo")
        if not orden or r["fecha"] < CAMBIO_RD15_DESDE or r["hora"] <= 0 or r["salio"] not in orden:
            continue
        cod = rd_de_registro(r, rd).get((r["fecha"], r["hora"] - 1))
        if cod is None:
            continue
        m["n"] += 1
        m["sin"] += PAGO * fichas15[orden.index(r["salio"]) + 1] - sum(fichas15)
        nuevo = cambiar15(orden, cod)
        if nuevo is not orden:
            m["cambios"] += 1
            m["gano_rd"] += r["salio"] == IDX[cod]
            m["gano_16"] += r["salio"] == orden[15]
        m["con"] += PAGO * fichas15[nuevo.index(r["salio"]) + 1] - sum(fichas15)
    m["dif"] = m["con"] - m["sin"]
    return m


# ------------------------------------------------ pronósticos en sombra (motor_nuevo)
# ag12 (pares consecutivos recientes) se guarda junto al congelado del ensamble,
# pero NO se muestra ni se puntúa en el marcador principal: solo sirve para medirlo
# con sorteos futuros (motor_nuevo/RETOMAR.md). ag12_rd NO se congela: RD (h−1):30
# sale ~25 min después del congelado, así que la regla de RD se aplica al PUNTUAR
# sobre la sombra ag12, igual que marcador_cambio_rd (RD (h−1):30 y (h−2):30 salen antes de LA h:00).
SOMBRA_DESDE = "2026-09-26"
SOMBRA_RD_MULT = {1: 0.50, 2: 0.75}     # r2_a03_rd_produccion (VB)
_RUTA_AG12 = os.path.join(HERR, "modelos", "ag12")

SOMBRA_EXP_DESDE = "2026-10-02"         # exposición (fecha/hora): PREREGISTRO_sombra_exposicion.md
SOMBRA_EXP_N_PRIMERA = 930              # primera mirada (solo para apagar); la decisión de encender es con SOMBRA_EXP_N_FINAL
SOMBRA_EXP_N_FINAL = 6000               # ~1,5 años: n con potencia ~75-80 % para ~+2,3 mbits (ver el pre-registro)
_EXPOSICION = []                        # módulo cargado una vez (evita tocar sys.path en cada consulta)
SOMBRA_8AM_DESDE = "2026-10-04"         # ventana de fecha a las 8:00: investigacion/2026-10-03/enjambre_8am/
SOMBRA_8AM_N_FRENO = 180                # desde aquí, apagar si O/E de la ventana >= 1,0
SOMBRA_8AM_N_FINAL = 730                # decisión única (≈ 2 años de primeros sorteos)


def sc_sombra(info, sc):
    """Probabilidades sobre las que se calculan las sombras: sin la corrección de las 8:00 ya encendida."""
    return info.get("scores_sin_8am") or sc


def sombra_de(filas, pf, ph, sc):
    """{"ag12": 38 probabilidades} o None. Nunca tumba el pronóstico principal."""
    try:
        if _RUTA_AG12 not in sys.path:
            sys.path.insert(0, _RUTA_AG12)
        import sombra
        return {"ag12": sombra.corregir(filas, pf, ph, sc)["ag12"]}
    except Exception as ex:  # noqa: BLE001
        print(f"[sombra] {_ahora()} fallo: {ex!r}", file=sys.stderr, flush=True)
        return None


def con_rd(p, rd, f, h):
    """ag12 × 0,50 al animal de RD (h−1):30 y × 0,75 al de (h−2):30, si ya salieron."""
    q = list(p); usado = False
    for k, mult in SOMBRA_RD_MULT.items():
        c = rd.get((f, h - k)) if h - k >= 0 else None
        if c in IDX:
            q[IDX[c]] *= mult; usado = True
    return q, usado


def hora_sorteo(f, h):
    """Hora de Caracas en que se juega LA (f, h): h=0 es las 8:00."""
    return datetime.fromisoformat(f).replace(hour=8 + int(h))


def congelar_rd(r, rd, ahora):
    """Guarda en r["sombra"]["rd"] el RD de (h−1):30 y (h−2):30 tal como se conocía ANTES de LA h:00.

    Mientras el sorteo no se juega se actualiza (un RD corregido entra); desde la hora del sorteo no se toca.
    Sin esto, ag12+RD se recalculaba al leer con el RD de hoy: un RD anotado tarde cambiaba hacia atrás el Top
    que se mostró para jugar. rd=None: RD no se pudo leer (la página tampoco aplicó nada); se congela vacío sin
    borrar lo ya congelado. Pasada la hora avisa UNA vez si el RD de (h−1):30 quedó vacío (RD atrasado), porque
    ese sorteo sale de los marcadores de la regla. Devuelve True si cambió algo."""
    s = r.get("sombra")
    if not s or "ag12" not in s or r.get("salio") is not None:
        return False
    f, h = r["fecha"], int(r["hora"])
    if ahora >= hora_sorteo(f, h):
        fijo = s.get("rd")
        if h < 1 or not isinstance(fijo, dict) or fijo.get("1") is not None or s.get("rd_vacio_avisado"):
            return False
        s["rd_vacio_avisado"] = True
        print(f"[rd] {_ahora()} LA {f} {8 + h}:00: el RD de las {8 + h - 1}:30 no estaba anotado antes del sorteo; "
              "ag12+RD se jugó sin esa regla", file=sys.stderr, flush=True)
        return True
    if rd is None:
        if "rd" in s:
            return False
        rd = {}
    nuevo = {str(k): (rd.get((f, h - k)) if h - k >= 0 else None) for k in SOMBRA_RD_MULT}
    if s.get("rd") == nuevo:
        return False
    s["rd"] = nuevo
    return True


def rd_de_registro(r, rd):
    """El RD con que se puntúa ag12+RD en r: el congelado si existe; si no (registros viejos), el anotado."""
    fijo = (r.get("sombra") or {}).get("rd")
    if not isinstance(fijo, dict):
        return rd
    f, h = r["fecha"], int(r["hora"])
    return {(f, h - int(k)): c for k, c in fijo.items() if c}


def exposicion(p, f, h, variante="aplicar"):
    """Multiplicadores congelados por fecha y hora (herramientas/modelos/exposicion.py); solo calendario."""
    if not _EXPOSICION:
        ruta = os.path.join(HERR, "modelos")
        if ruta not in sys.path:
            sys.path.append(ruta)
        import exposicion as modulo
        _EXPOSICION.append(modulo)
    return getattr(_EXPOSICION[0], variante)(p, f, h)


def ventana_8am(fecha):
    d = int(fecha[8:10])
    return [IDX[str(n)] for n in (d - 1, d, d + 1) if 1 <= n <= 36]


def ic90_jornadas(pares, escala=1):
    """Media de la diferencia por sorteo con IC 90 % agrupando por jornada (fecha). pares = [(fecha, dif)].

    escala multiplica ANTES de redondear (fracción 0/1 -> pp con escala=100): redondear la fracción a dos
    decimales y luego pasarla a pp convertía −0,45 pp en «−0,00»."""
    if escala != 1:
        pares = [(f, v * escala) for f, v in pares]
    por = {}
    for f, v in pares:
        a = por.setdefault(f, [0.0, 0]); a[0] += v; a[1] += 1
    n = sum(a[1] for a in por.values())
    if n == 0:
        return None
    media = sum(a[0] for a in por.values()) / n
    J = len(por)
    if J < 2:
        return dict(n=n, jornadas=J, media=round(media, 2), ic90=None)
    se = math.sqrt(sum((a[0] - media * a[1]) ** 2 for a in por.values()) * J / (J - 1)) / n
    return dict(n=n, jornadas=J, media=round(media, 2),
                ic90=[round(media - 1.645 * se, 2), round(media + 1.645 * se, 2)])


# ------------------------------------------------ ag13 en sombra (PREREGISTRO_ag13.md)
# ag12 -> regla RD -> exposición (todas las horas) -> pronosticadores ×0,862. NO entra en el marcador principal.
AG13_DESDE = "2026-10-15"
AG13_N_DECIDE = 931          # mirada única, sobre los PRIMEROS 931 sorteos con pron válido
AG13_N_FRENO = 600           # con n >= 600 y Δ mbits < AG13_FRENO_MBITS se apaga
AG13_FRENO_MBITS = -10.0
AG13_E_PRON = 350.0          # aciertos esperados de U a los que se juzga el componente pronosticadores
AG13_T5_MIN = -3.0           # Top-5 pp/ficha: ag13 no peor que esto contra el ensamble
_AG13 = []
_FIN_VENTANA_PRON = "T07:56"    # datos_publicados.pasada solo descarga de 6:00 a 7:55
_ANTES_DEL_PRIMER_SORTEO = "T08:00:00"


def _modulo_ag13():
    if not _AG13:
        ruta = os.path.join(HERR, "modelos")
        if ruta not in sys.path:
            sys.path.append(ruta)
        import ag13 as modulo
        _AG13.append(modulo)
    return _AG13[0]


def pron_del_dia(base, fecha, ahora=None):
    """Lo que publicaron los pronosticadores el día `fecha`, leído de las páginas que guarda datos_publicados.
    None si todavía puede llegar (la ventana de descarga sigue abierta); si no, {"u": [...], "fuentes": {...}}
    o {"falta": motivo}. Una página solo vale si se bajó ANTES de las 8:00 del día: así nada de esto puede depender
    de un resultado. Hacen falta las dos fuentes."""
    import json
    ahora = (ahora or datetime.now()).isoformat(timespec="seconds")
    carpeta = os.path.join(base, "datos_publicados", fecha)
    try:
        with open(os.path.join(carpeta, "meta.json"), encoding="utf-8") as f:
            meta = json.load(f)
        meta = meta if isinstance(meta, dict) else {}
    except (OSError, ValueError):
        meta = {}
    ok = {}
    for f in _modulo_ag13().FUENTES:
        v = meta.get(f + "_datos") or {}
        if v.get("ok") and str(v.get("cuando", "")) < fecha + _ANTES_DEL_PRIMER_SORTEO:
            ok[f] = True
    if len(ok) < len(_modulo_ag13().FUENTES) and ahora < fecha + _FIN_VENTANA_PRON:
        return None
    if len(ok) < len(_modulo_ag13().FUENTES):
        return {"falta": "páginas no guardadas antes de las 8:00: " + ", ".join(
            f for f in _modulo_ag13().FUENTES if f not in ok)}
    return _modulo_ag13().conjunto_del_dia(carpeta, fecha)


def completar_pron(registros, base, ahora=None):
    """Pone `pron` en los registros que aún no lo tienen (también al del 8:00, que se congela la noche anterior).
    Es solo un insumo de la sombra: no toca scores ni orden. Devuelve True si cambió algo."""
    cambio, cache = False, {}
    for r in registros:
        if r.get("anulado") or "pron" in r or r.get("fecha", "") < AG13_DESDE or not r.get("sombra"):
            continue
        try:
            if r["fecha"] not in cache:
                cache[r["fecha"]] = pron_del_dia(base, r["fecha"], ahora)
            v = cache[r["fecha"]]
        except Exception as ex:  # noqa: BLE001  (nunca tumba el pronóstico principal)
            print(f"[ag13] {_ahora()} pron {r['fecha']}: {ex!r}", file=sys.stderr, flush=True)
            continue
        if v is not None:
            r["pron"] = v
            cambio = True
    return cambio


def _oe_jornadas(cols):
    """O/E de U con IC 95 % por jornadas (razón de sumas; varianza por conglomerados)."""
    por = {}
    for x in cols:
        a = por.setdefault(x["f"], [0.0, 0.0]); a[0] += x["o"]; a[1] += x["e"]
    O = sum(a[0] for a in por.values()); E = sum(a[1] for a in por.values())
    if E <= 0:
        return None
    R = O / E; J = len(por)
    out = dict(O=int(O), E=round(E, 1), oe=round(R, 3), jornadas=J, ic95=None)
    if J >= 2:
        se = math.sqrt(sum((a[0] - R * a[1]) ** 2 for a in por.values()) * J / (J - 1)) / E
        out["ic95"] = [round(R - 1.96 * se, 3), round(R + 1.96 * se, 3)]
    return out


def marcador_ag13(res, fichas, rd=None):
    """Marcador de ag13 y de sus componentes sobre los MISMOS sorteos (los que tienen pron válido). Solo lectura."""
    try:
        return _marcador_ag13(res, fichas, rd or {})
    except Exception as ex:  # noqa: BLE001  (la sombra nunca tumba la web)
        print(f"[ag13] {_ahora()} marcador falló: {ex!r}", file=sys.stderr, flush=True)
        return {"error": repr(ex)[:200]}


# ------------------------------------------------ ag14 prospectivo en sombra
AG14_DESDE = "2026-10-17"
AG14_N_DECIDE = 931          # mirada única: primeros 931 sorteos válidos desde el inicio prospectivo
AG14_T5_MIN = -3.0           # tolerancia congelada en pp/ficha frente al ensamble
_AG14 = []


def _modulo_ag14():
    if not _AG14:
        ruta = os.path.join(HERR, "modelos")
        if ruta not in sys.path:
            sys.path.append(ruta)
        import ag14 as modulo
        _AG14.append(modulo)
    return _AG14[0]


def marcador_ag14(res, fichas, rd=None):
    """Evalúa ag12 -> RD disponible -> exposición en sorteos prospectivos, sin requerir pron."""
    try:
        return _marcador_ag14(res, fichas, rd or {})
    except Exception as ex:  # noqa: BLE001; un fallo en sombra no interrumpe el motor
        print(f"[ag14] {_ahora()} marcador falló: {ex!r}", file=sys.stderr, flush=True)
        return {"error": repr(ex)[:200]}


def _marcador_ag14(res, fichas, rd):
    """rd (el historial RD de HOY) no se usa: puntuar con él hacía que un RD anotado tarde cambiara hacia atrás
    el marcador. Cada sorteo se puntúa solo con el RD congelado en su registro. Entran a la cohorte que decide
    los de las 8:00 (no usan RD) y los intradía con RD congelado; los intradía sin RD congelado (17–19 oct, antes
    de congelarlo) quedan en «historico_sin_rd_posterior», puntuados sin RD, y NO deciden. La elegibilidad es por
    procedencia, nunca por aciertos."""
    m = _modulo_ag14()
    filas, todas, sin_ag12, rd_no_congelado = [], [], 0, 0
    for r in sorted(res, key=lambda x: (x["fecha"], x["hora"])):
        if r.get("anulado") or r["fecha"] < AG14_DESDE:
            continue
        s = r.get("sombra") or {}
        sc = r.get("scores_sin_8am") or r.get("scores")
        if "ag12" not in s or not sc or r.get("salio") is None:
            sin_ag12 += 1
            continue
        f, h, w = r["fecha"], int(r["hora"]), int(r["salio"])
        elegible = h == 0 or isinstance(s.get("rd"), dict)
        rd_no_congelado += not elegible
        rr = rd_de_registro(r, {})
        q, _ = con_rd(s["ag12"], rr, f, h)
        p14 = m.cadena(q, f, h)
        mb = lambda p: 1000 * math.log2(max(p[w] / sum(p), 1e-12) * K)
        orden = sorted(range(K), key=lambda i: (-p14[i], i))
        orden_base = sorted(range(K), key=lambda i: (-sc[i], i))
        cod = rr.get((f, h - 1)) if h > 0 else None
        if cod in IDX:
            orden = cambiar15(orden, cod)
            orden_base = cambiar15(orden_base, cod)
        neto = lambda o: 100.0 * (PAGO * fichas[o.index(w) + 1] - sum(fichas)) / sum(fichas)
        fila = {"f": f, "mb": mb(p14) - mb(sc), "t5": neto(orden) - neto(orden_base),
                "top3": orden.index(w) < 3, "top5": orden.index(w) < 5, "top15": orden.index(w) < 15}
        todas.append(fila)
        if elegible:
            filas.append(fila)

    n = len(filas)
    dm = ic90_jornadas([(x["f"], x["mb"]) for x in filas])
    dt = ic90_jornadas([(x["f"], x["t5"]) for x in filas])
    base = {"version": m.VERSION, "desde": AG14_DESDE, "n": n, "sin_ag12": sin_ag12,
            "rd_no_congelado": rd_no_congelado, "decide_con": AG14_N_DECIDE,
            "elegibilidad": "8:00, o intradía con RD congelado antes del sorteo",
            "historico_sin_rd_posterior": {
                "n": len(todas), "top3": sum(x["top3"] for x in todas), "top5": sum(x["top5"] for x in todas),
                "top15": sum(x["top15"] for x in todas),
                "delta_mbits": ic90_jornadas([(x["f"], x["mb"]) for x in todas]),
                "nota": "todos los sorteos desde AG14_DESDE, solo con RD congelado; diagnóstico, no decide"}}
    if not n:
        return dict(base, estado="esperando sorteos prospectivos")
    estado, decision = f"acumulando ({n} de {AG14_N_DECIDE})", None
    if n >= AG14_N_DECIDE:
        cols = filas[:AG14_N_DECIDE]
        d1 = ic90_jornadas([(x["f"], x["mb"]) for x in cols])
        d2 = ic90_jornadas([(x["f"], x["t5"]) for x in cols])
        pasa = bool(d1 and d1["ic90"] and d1["ic90"][0] > 0 and d2 and d2["media"] >= AG14_T5_MIN)
        decision = {"n": AG14_N_DECIDE, "mbits": d1, "top5_pp_ficha": d2, "pasa": pasa}
        estado = "PASA (sombra; requiere revisión antes de producción)" if pasa else "NO PASA"
    return dict(base, estado=estado, decision=decision,
                top3=sum(x["top3"] for x in filas), top5=sum(x["top5"] for x in filas),
                top15=sum(x["top15"] for x in filas), delta_mbits=dm, top5_pp_ficha=dt)


def _marcador_ag13(res, fichas, rd):
    m = _modulo_ag13()
    sf = sum(fichas)
    filas, faltas, sin_pron = [], {}, 0
    for r in sorted(res, key=lambda r: (r["fecha"], r["hora"])):
        s, pr = r.get("sombra"), r.get("pron")
        sc = r.get("scores_sin_8am") or r.get("scores")
        if r["fecha"] < AG13_DESDE or not s or "ag12" not in s or not sc:
            continue
        if pr is None:
            sin_pron += 1
            continue
        if "u" not in pr:
            faltas[r["fecha"]] = pr.get("falta", "?")
            continue
        f, h, w = r["fecha"], int(r["hora"]), r["salio"]
        rr = rd_de_registro(r, rd)
        q, _ = con_rd(s["ag12"], rr, f, h)
        q_exp, p13, p13nd = m.cadena(q, f, h, pr["u"])
        pm = {"ensamble": sc, "ag12_rd": q, "ag12_rd_exp": q_exp, "ag13": p13, "ag13_nd": p13nd}
        mb = {k: 1000 * math.log2(max(p[w] / sum(p), 1e-12) * K) for k, p in pm.items()}
        cod = rr.get((f, h - 1)) if h > 0 else None

        def neto(p):
            orden = sorted(range(K), key=lambda i: (-p[i], i))
            if cod is not None:
                orden = cambiar15(orden, cod)
            return 100.0 * (PAGO * fichas[orden.index(w) + 1] - sf) / sf
        filas.append(dict(f=f, mb=mb, t5={"ensamble": neto(sc), "ag13": neto(p13)},
                          o=int(w in pr["u"]), e=sum(q_exp[i] for i in pr["u"])))

    def dif(a, b, cols):
        return ic90_jornadas([(x["f"], x["mb"][a] - x["mb"][b]) for x in cols])

    n = len(filas)
    p1 = dif("ag13", "ensamble", filas)
    base = {"desde": AG13_DESDE, "n": n, "decide_con": AG13_N_DECIDE, "freno_n": AG13_N_FRENO,
            "sin_pron_aun": sin_pron, "dias_sin_pron": faltas}
    if not n:
        return dict(base, estado="esperando los primeros sorteos con pronosticadores")
    medias = {k: round(sum(x["mb"][k] for x in filas) / n, 1) for k in filas[0]["mb"]}
    estado = "acumulando (%d de %d)" % (n, AG13_N_DECIDE)
    decision = None
    if n >= AG13_N_FRENO and p1 and p1["media"] < AG13_FRENO_MBITS:
        estado = "APAGADO por freno (Δ < %g con n ≥ %d)" % (AG13_FRENO_MBITS, AG13_N_FRENO)
    elif n >= AG13_N_DECIDE:
        cols = filas[:AG13_N_DECIDE]                    # mirada única: los primeros 931, no la cola que crece
        d1 = dif("ag13", "ensamble", cols)
        d2 = ic90_jornadas([(x["f"], x["t5"]["ag13"] - x["t5"]["ensamble"]) for x in cols])
        pasa = bool(d1 and d1["ic90"] and d1["ic90"][0] > 0 and d2 and d2["media"] >= AG13_T5_MIN)
        decision = {"n": AG13_N_DECIDE, "mbits": d1, "top5_pp_ficha": d2, "pasa": pasa}
        estado = "PASA (solo con tu OK entra a producción)" if pasa else "NO PASA"
    oe = _oe_jornadas(filas)
    pron = {"oe_U": oe, "decide_con_E": AG13_E_PRON,
            "estado": ("esperando E=%g" % AG13_E_PRON) if not oe or oe["E"] < AG13_E_PRON else
            ("conservar" if oe["ic95"] and oe["ic95"][1] < 1 and dif("ag13", "ag12_rd_exp", filas)["media"] > 0
             else "quitar pronosticadores")}
    return dict(base, estado=estado, decision=decision, mbits_medios=medias,
                p1_ag13_menos_ensamble=p1,
                ag13_menos_ag12_rd_exp=dif("ag13", "ag12_rd_exp", filas),
                exposicion_menos_ag12_rd=dif("ag12_rd_exp", "ag12_rd", filas),
                ag12_rd_menos_ensamble=dif("ag12_rd", "ensamble", filas),
                ag13_nd_menos_ag12_rd_exp=dif("ag13_nd", "ag12_rd_exp", filas),
                componente_pronosticadores=pron)


SOMBRA_AG12_N_DECIDE = 931              # PREREGISTRO ag12_top15, anexo 2026-09-30 (+ anexo 2026-10-07)
SOMBRA_AG12_N_MAX = 3500                # si a 931 no concluye: seguir hasta aquí (efecto esperado <= +10 mbits)


def decision_sombra(res, fichas):
    """Lo que pide el criterio de ag12 y el marcador no daba: IC 90 % por jornadas de Δ(ag12 − ensamble)
    en mbits y en Top-5 escalonado (pp por ficha), crudo y con la regla de cambio RD (lo que se juega).
    Solo lectura: no altera nada guardado."""
    try:
        rd = _rd_por_slot()
    except Exception:  # noqa: BLE001
        rd = {}
    sf = sum(fichas)
    dm, dt, dtr = [], [], []
    for r in res:
        s = r.get("sombra"); sc = r.get("scores_sin_8am") or r.get("scores")
        if not s or "ag12" not in s or r["fecha"] < SOMBRA_DESDE or not sc:
            continue
        w = r["salio"]; f = r["fecha"]; h = r["hora"]
        pe, pa = sc, s["ag12"]
        dm.append((f, 1000 * math.log2((pa[w] / sum(pa)) / (pe[w] / sum(pe)))))
        netos = []
        cod = rd_de_registro(r, rd).get((f, h - 1)) if h > 0 else None
        for p in (pe, pa):
            orden = sorted(range(K), key=lambda i: (-p[i], i))
            netos.append(100.0 * (PAGO * fichas[orden.index(w) + 1] - sf) / sf)
            if cod is not None:
                orden = cambiar15(orden, cod)
            netos.append(100.0 * (PAGO * fichas[orden.index(w) + 1] - sf) / sf)
        dt.append((f, netos[2] - netos[0]))             # ag12 − ensamble, sin regla
        dtr.append((f, netos[3] - netos[1]))            # ag12 − ensamble, ambos con la regla RD
    n = len(dm)
    return {"desde": SOMBRA_DESDE, "n": n, "decide_con": SOMBRA_AG12_N_DECIDE, "hasta_si_no_concluye": SOMBRA_AG12_N_MAX,
            "mbits_ag12_menos_ensamble": ic90_jornadas(dm),
            "top5_pp_ficha_sin_regla": ic90_jornadas(dt),
            "top5_pp_ficha_con_regla_rd": ic90_jornadas(dtr),
            "regla": "PASA si Δ mbits > 0 con límite inferior IC90 > 0 y Top-5 pp/ficha no peor en más de 3 puntos; "
                     "ver PREREGISTRO ag12_top15 (anexo 2026-10-07)"}


def marcador_sombra(res, fichas):
    """Ensamble, ag12 y ag12+RD sobre los MISMOS sorteos resueltos (desde SOMBRA_DESDE).
    Aparte, desde SOMBRA_EXP_DESDE: ensamble, ag12_rd y los dos con la corrección por exposición."""
    try:
        rd = _rd_por_slot()
    except Exception:  # noqa: BLE001
        rd = {}
    nombres = ("ensamble", "ag12", "ag12_rd")
    m = {k: dict(n=0, top3=0, top5=0, top15=0, mbits=0.0, t5_neto=0.0) for k in nombres}
    nexp = ("ensamble", "ag12_rd", "ensamble_exp", "ag12_rd_exp")
    mx = {k: dict(n=0, top3=0, top5=0, top15=0, mbits=0.0, t5_neto=0.0) for k in nexp}
    n_con_rd = 0
    n_rd_vacio = 0                          # RD (h−1):30 congelado vacío: RD iba atrasado al sorteo
    dif = {"ensamble": ([], []), "ag12_rd": ([], [])}      # (dif mbits, dif Top-5 en 0/1) por sorteo y jornada
    fallos_exp = 0
    v8 = dict(n=0, O=0, E=0.0, top5_exp=0, top5_exp8=0, mbits_dif=[])   # solo 8:00, exp8 contra exp
    for r in res:
        sc_base = r.get("scores_sin_8am") or r.get("scores")   # sin la corrección de las 8:00 ya encendida
        if r["fecha"] >= SOMBRA_8AM_DESDE and int(r["hora"]) == 0 and sc_base:
            try:
                pe = exposicion(sc_base, r["fecha"], 0)
                p8 = exposicion(sc_base, r["fecha"], 0, "aplicar_8am")
                w = r["salio"]; ven = ventana_8am(r["fecha"])
                v8["n"] += 1; v8["O"] += w in ven; v8["E"] += sum(pe[i] for i in ven)
                for k, p in (("top5_exp", pe), ("top5_exp8", p8)):
                    v8[k] += sum(1 for i in range(K) if (-p[i], i) < (-p[w], w)) < 5
                v8["mbits_dif"].append((r["fecha"], 1000 * math.log2(p8[w] / pe[w])))
            except Exception as ex:  # noqa: BLE001  (la sombra nunca tumba la web)
                print(f"[sombra] {_ahora()} ventana 8:00 falló: {ex!r}", file=sys.stderr, flush=True)
        s = r.get("sombra")
        if not s or "ag12" not in s or r["fecha"] < SOMBRA_DESDE or not sc_base:
            continue
        q, usado = con_rd(s["ag12"], rd_de_registro(r, rd), r["fecha"], r["hora"])
        n_con_rd += usado
        n_rd_vacio += isinstance(s.get("rd"), dict) and int(r["hora"]) >= 1 and s["rd"].get("1") is None
        filas = [(m, "ensamble", sc_base), (m, "ag12", s["ag12"]), (m, "ag12_rd", q)]
        if r["fecha"] >= SOMBRA_EXP_DESDE:
            try:
                filas += [(mx, "ensamble", sc_base), (mx, "ag12_rd", q),
                          (mx, "ensamble_exp", exposicion(sc_base, r["fecha"], r["hora"])),
                          (mx, "ag12_rd_exp", exposicion(q, r["fecha"], r["hora"]))]
            except Exception as ex:  # noqa: BLE001  (la sombra nunca tumba la web)
                fallos_exp += 1
                if fallos_exp == 1:                          # una línea por consulta, no una por sorteo
                    print(f"[sombra] {_ahora()} exposición falló: {ex!r}", file=sys.stderr, flush=True)
        este = {}
        for mm, k, p in filas:
            tot = sum(p)
            orden = sorted(range(K), key=lambda i: (-p[i], i))
            pos = orden.index(r["salio"]) + 1
            x = mm[k]; x["n"] += 1
            x["top3"] += pos <= 3; x["top5"] += pos <= 5; x["top15"] += pos <= 15
            mb = 1000 * math.log2(max(p[r["salio"]] / tot, 1e-12) * K)
            x["mbits"] += mb
            x["t5_neto"] += PAGO * fichas[pos] - sum(fichas)
            if mm is mx:
                este[k] = (mb, pos <= 5)
        if len(este) == 4:                                  # los 4 modelos del bloque, mismo sorteo
            for base in dif:
                dif[base][0].append((r["fecha"], este[base + "_exp"][0] - este[base][0]))
                dif[base][1].append((r["fecha"], float(este[base + "_exp"][1]) - float(este[base][1])))
    for x in list(m.values()) + list(mx.values()):
        if x["n"]:
            for c in ("top3", "top5", "top15"):
                x[c + "_pct"] = round(100 * x[c] / x["n"], 2)
            x["mbits"] = round(x["mbits"] / x["n"], 1)
    difs = {}
    for base, (dm, dt) in dif.items():
        difs[base + "_exp_vs_" + base] = dict(mbits=ic90_jornadas(dm), top5_pp=ic90_jornadas(dt, escala=100))
    return {"desde": SOMBRA_DESDE, "sorteos_con_rd": n_con_rd, "sorteos_rd_vacio": n_rd_vacio, "marcador": m,
            "ag13": marcador_ag13(res, fichas, rd),
            "ag14": marcador_ag14(res, fichas, rd),
            "exposicion": {"desde": SOMBRA_EXP_DESDE, "primera_mirada_n": SOMBRA_EXP_N_PRIMERA,
                           "decide_con": SOMBRA_EXP_N_FINAL, "primaria": "ensamble_exp_vs_ensamble",
                           "marcador": mx, "diferencias": difs, "fallos": fallos_exp},
            "ventana_8am": {"desde": SOMBRA_8AM_DESDE, "freno_n": SOMBRA_8AM_N_FRENO, "decide_con": SOMBRA_8AM_N_FINAL,
                            "n": v8["n"], "ventana_obs": v8["O"], "ventana_esp": round(v8["E"], 2),
                            "oe": round(v8["O"] / v8["E"], 3) if v8["E"] else None,
                            "top5_exp": v8["top5_exp"], "top5_exp8": v8["top5_exp8"],
                            "mbits_exp8_vs_exp": ic90_jornadas(v8["mbits_dif"])}}
