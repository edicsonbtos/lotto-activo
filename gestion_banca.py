# -*- coding: utf-8 -*-
"""
GESTION DE BANCA — Lotto Activo
================================
Decide CUANTO apostar en cada sorteo, CUANDO no apostar, y CUANDO parar.

NO toca historial.txt ni predicciones.json: solo los lee.
No necesita numpy ni scipy. Corre con Python puro.

Uso:
    python gestion_banca.py --banca 1000
    python gestion_banca.py --banca 985 --perdi 15       (anotar lo perdido hoy)

La jugada es el TOP-5 ESCALONADO: 2 fichas a cada uno de los puestos 1-3 y
1 ficha a los puestos 4-5 (8 fichas). Ver herramientas/resultados/estrategia_top5.md.
"""
import json, os, math, argparse, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI) if os.path.basename(AQUI) == "gestion" else AQUI
ESTADO = os.path.join(AQUI, "estado_banca.json")

# ---------------------------------------------------------------- parametros
PAGO          = 30      # paga 30x sobre lo apostado a UN animal
FICHAS        = [2, 2, 2, 1, 1]   # fichas por puesto 1..5 (Top-5 escalonado)
# Los puestos 1-3 son la BASE PROBADA (IC95 entero por encima del equilibrio).
# Los puestos 4-5 son un REFUERZO no probado: 3,6 % c/u en prueba ciega y en
# desarrollo (equilibrio 3,33 %), pero z=1,27. Van a media ficha porque eso es
# lo que da Kelly con la tasa medida; si quieres jugar solo lo probado, pon
# FICHAS = [1, 1, 1, 0, 0].
P3_MEDIDA     = 0.12268 # acierto Top-3 en prueba ciega (n=3154)
P3_IC_BAJO    = 0.1117  # limite inferior IC95 del Top-3 -> Kelly conservador
FRAC_KELLY    = 0.25    # 1/4 de Kelly. NO subir sin leer la seccion RIESGO del informe.
# Ya NO hay umbral de abstencion por la probabilidad del Top-3: elegir sorteos
# por lo "caliente" de la lista FALLO en prueba ciega (hilo 6, 2026-09-22:
# los sorteos calientes acertaron 10,9 % y los frios 13,0 %). Se juegan todos.
TOPE_DIARIO   = 0.06    # se para el dia tras perder este % de la banca inicial del dia
TOPE_TOTAL    = 0.25    # se para TODO tras caer este % desde el maximo historico
MIN_APUESTA   = 1.0     # unidad minima que acepta tu banca (redondeo)
MODELO_MARCADOR = "ensamble_v2"   # el SPRT solo cuenta el modelo EN USO,
                                  # no mezcla con las predicciones del hazard viejo

# ----------------------------------------------------- REGLA PRE-COMPROMETIDA
# Decidida el 2026-09-15, ANTES de ver los datos futuros. Existe para que un
# mal mes no dispare cambios al modelo (eso es sobreajuste con otro nombre).
#
#   Si el modelo `hazard` supera a `ensamble_v2` en Top-3 durante TRES MESES
#   CONSECUTIVOS en la carrera walk-forward mensual
#   (herramientas/resultados/carrera_1ano.txt), se abre revision de la
#   ponderacion del ensamble. ANTES DE ESO NO SE TOCA NADA: ni pesos, ni
#   features, ni umbrales.
#
# Dato que motiva la regla: en 2026-09 hazard hizo 12.1% de Top-3 contra 11.6%
# del ensamble. Es UN mes y no es significativo; por eso la regla exige 3.
VIGILANCIA = {
    "regla": "hazard > ensamble_v2 en Top-3 durante 3 meses consecutivos -> revisar pesos",
    "decidida": "2026-09-15",
    "fuente": "herramientas/resultados/carrera_1ano.txt",
    "meses_en_contra": ["2026-09"],   # anadir un mes SOLO cuando la carrera lo confirme
    "umbral_meses": 3,
}

BE = 3 / PAGO           # equilibrio del Top-3 (para el monitor SPRT) = 10%
TOTAL_FICHAS = sum(FICHAS)          # 8


# ---------------------------------------------------------------- nucleo
def kelly(p=P3_IC_BAJO, frac=FRAC_KELLY):
    """Fraccion de banca para la BASE (Top-3, apuesta plana). 0 si no hay ventaja.

    El tamano se decide solo con lo probado (limite bajo del IC del Top-3); el
    refuerzo 4-5 va encima, en la proporcion de FICHAS."""
    b = (PAGO - 3) / 3
    return max(0.0, (b * p - (1 - p)) / b * frac)


def plan_sorteo(banca, banca_inicio_dia=None, perdido_hoy=0.0, maximo=None):
    """Devuelve el plan de apuesta para UN sorteo."""
    maximo = maximo or banca
    r = {"apostar": False, "motivo": "", "ficha": 0.0, "total": 0.0,
         "gana_top3": 0.0, "gana_45": 0.0, "ev": 0.0}

    # --- cortacircuitos, en orden de gravedad
    caida = (maximo - banca) / maximo if maximo > 0 else 0.0
    if caida >= TOPE_TOTAL:
        r["motivo"] = ("PARADA TOTAL: caida de %.1f%% desde el maximo (%.2f -> %.2f). "
                       "Revisa el modelo antes de volver a jugar." % (caida * 100, maximo, banca))
        return r
    if banca_inicio_dia and perdido_hoy >= TOPE_DIARIO * banca_inicio_dia:
        r["motivo"] = ("PARADA DEL DIA: llevas perdido %.2f de %.2f permitidos hoy. "
                       "Vuelve manana." % (perdido_hoy, TOPE_DIARIO * banca_inicio_dia))
        return r

    f = kelly()
    if f <= 0:
        r["motivo"] = "ABSTENERSE: sin ventaja a este precio."
        return r

    fichas_base = sum(FICHAS[:3])
    ficha = math.floor(banca * f / fichas_base / MIN_APUESTA) * MIN_APUESTA
    if ficha < MIN_APUESTA:
        # Banca chica: el Top-3 plano solo necesita 3 fichas en vez de 8.
        por = math.floor(banca * f / 3 / MIN_APUESTA) * MIN_APUESTA
        if por >= MIN_APUESTA:
            r.update(apostar=True, ficha=0.0, total=3 * por, solo_top3=por,
                     gana_top3=por * PAGO - 3 * por, gana_45=0.0,
                     ev=(P3_MEDIDA * PAGO - 3) * por,
                     motivo=("Banca chica para el Top-5 (necesitaria ~%.0f). Apostar %.2f a CADA uno "
                             "de los puestos 1, 2 y 3, nada al 4 y 5." % (MIN_APUESTA * fichas_base / f, por)))
            return r
        r["motivo"] = ("Banca insuficiente: Kelly pide una ficha de %.2f y tu minimo es %.2f. "
                       "No apuestes por debajo del minimo, rompe el dimensionamiento."
                       % (banca * f / fichas_base, MIN_APUESTA))
        return r

    total = ficha * TOTAL_FICHAS
    ev_ficha = (P3_MEDIDA * FICHAS[0] * PAGO + 0.0723 * FICHAS[3] * PAGO) / TOTAL_FICHAS - 1   # prueba ciega
    r.update(apostar=True, ficha=ficha, total=total,
             gana_top3=FICHAS[0] * ficha * PAGO - total, gana_45=FICHAS[3] * ficha * PAGO - total,
             ev=ev_ficha * total,
             motivo=("Apostar %.2f a CADA uno de los puestos 1, 2 y 3 (base probada) y %.2f al 4 y "
                     "al 5 (refuerzo no probado). %.2f en total, %.2f%% de la banca."
                     % (FICHAS[0] * ficha, FICHAS[3] * ficha, total, total / banca * 100)))
    return r


# ---------------------------------------------------------------- monitor
def sprt(aciertos, n, p1=P3_MEDIDA, p0=BE, alfa=0.05, beta=0.05):
    """Prueba secuencial: la ventaja sigue viva (p=p1) o se murio (p=p0)?"""
    if n == 0:
        return {"llr": 0.0, "veredicto": "sin datos", "n": 0, "tasa": None}
    fallos = n - aciertos
    llr = aciertos * math.log(p1 / p0) + fallos * math.log((1 - p1) / (1 - p0))
    A = math.log((1 - beta) / alfa)
    B_ = math.log(beta / (1 - alfa))
    if llr >= A:
        v = "VENTAJA CONFIRMADA en vivo"
    elif llr <= B_:
        v = "VENTAJA NO CONFIRMADA — parar y revisar el modelo"
    else:
        v = "sin conclusion todavia (sigue acumulando)"
    return {"llr": llr, "cota_alta": A, "cota_baja": B_, "veredicto": v,
            "n": n, "aciertos": aciertos, "tasa": aciertos / n}


def leer_marcador(ruta=None):
    ruta = ruta or os.path.join(RAIZ, "predicciones.json")
    if not os.path.exists(ruta):
        return None
    d = json.load(open(ruta, encoding="utf-8"))
    res = [r for r in d.get("registros", [])
           if not r.get("anulado") and r.get("salio") is not None and r.get("top3")
           and r.get("modelo") == MODELO_MARCADOR]
    ac = sum(1 for r in res if r["salio"] in r["top3"])
    return {"n": len(res), "aciertos": ac}


# ---------------------------------------------------------------- estado
def cargar_estado():
    if os.path.exists(ESTADO):
        return json.load(open(ESTADO, encoding="utf-8"))
    return {}


def guardar_estado(e):
    json.dump(e, open(ESTADO, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- informe
def informe(banca, p3=None):
    e = cargar_estado()
    hoy = datetime.date.today().isoformat()
    if e.get("dia") != hoy:
        e["dia"] = hoy
        e["banca_inicio_dia"] = banca
        e["perdido_hoy"] = 0.0
    e["maximo"] = max(e.get("maximo", banca), banca)
    guardar_estado(e)

    L = []
    L.append("=" * 62)
    L.append(" PLAN DE APUESTA — %s" % hoy)
    L.append("=" * 62)
    L.append(" Banca actual .......... %10.2f" % banca)
    L.append(" Maximo historico ...... %10.2f  (caida %.1f%%)"
             % (e["maximo"], (e["maximo"] - banca) / e["maximo"] * 100))
    L.append(" Perdido hoy ........... %10.2f  de %.2f permitidos"
             % (e["perdido_hoy"], TOPE_DIARIO * e["banca_inicio_dia"]))
    L.append("")

    p = plan_sorteo(banca, e["banca_inicio_dia"], e["perdido_hoy"], e["maximo"])
    L.append(" >> " + p["motivo"])
    if p3 is not None:
        L.append("    (--p3 ya no se usa: saltar sorteos por su porcentaje fallo en prueba ciega)")
    if p.get("solo_top3"):
        L.append("")
        L.append("    Puestos 1-2-3 ...... %10.2f  cada uno" % p["solo_top3"])
        L.append("    Si acierta gana .... %10.2f  (neto)" % p["gana_top3"])
        L.append("    Valor esperado ..... %+10.2f  (prueba ciega)" % p["ev"])
    elif p["apostar"]:
        L.append("")
        L.append("    Puestos 1-2-3 ...... %10.2f  cada uno" % (FICHAS[0] * p["ficha"]))
        L.append("    Puestos 4-5 ........ %10.2f  cada uno" % (FICHAS[3] * p["ficha"]))
        L.append("    Total en riesgo .... %10.2f" % p["total"])
        L.append("    Si sale 1-2-3 gana . %10.2f  (neto)" % p["gana_top3"])
        L.append("    Si sale 4-5 gana ... %10.2f  (neto)" % p["gana_45"])
        L.append("    Valor esperado ..... %+10.2f  (%+.1f%% de lo apostado; IC95 aprox. +10%% a +28%%)"
                 % (p["ev"], p["ev"] / p["total"] * 100))
        L.append("    Cobras en ~1 de cada 5 sorteos (19,5%); fallar 10 seguidos es normal.")
    L.append("")

    m = leer_marcador()
    if m:
        s = sprt(m["aciertos"], m["n"])
        L.append("-" * 62)
        L.append(" MARCADOR EN VIVO")
        L.append("  %d sorteos registrados, %d aciertos Top-3 (%.1f%%)"
                 % (s["n"], s["aciertos"], (s["tasa"] or 0) * 100))
        L.append("  Esperado por el banco de pruebas: %.1f%% | equilibrio: %.1f%%"
                 % (P3_MEDIDA * 100, BE * 100))
        L.append("  Prueba secuencial: %+.2f  (confirma en %+.2f / corta en %+.2f)"
                 % (s["llr"], s["cota_alta"], s["cota_baja"]))
        L.append("  -> %s" % s["veredicto"])
        falta = max(0, int((s["cota_alta"] - s["llr"]) / 0.00268)) if s["llr"] < s["cota_alta"] else 0
        if falta:
            L.append("  Faltan ~%d sorteos (~%d dias) para poder concluir algo."
                     % (falta, falta // 12))
    L.append("=" * 62)
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--banca", type=float, required=True, help="banca actual")
    ap.add_argument("--p3", type=float, default=None,
                    help="prob. Top-3 que da el modelo para este sorteo (0-1)")
    ap.add_argument("--perdi", type=float, default=None, help="registrar perdida de hoy")
    a = ap.parse_args()
    if a.perdi is not None:
        e = cargar_estado(); e["perdido_hoy"] = e.get("perdido_hoy", 0) + a.perdi; guardar_estado(e)
    print(informe(a.banca, a.p3))
