# -*- coding: utf-8 -*-
"""
GESTION DE BANCA — Lotto Activo
================================
Decide CUANTO apostar en cada sorteo, CUANDO no apostar, y CUANDO parar.

NO toca historial.txt ni predicciones.json: solo los lee.
No necesita numpy ni scipy. Corre con Python puro.

Uso:
    python gestion_banca.py --banca 1000
    python gestion_banca.py --banca 1000 --p3 0.134     (prob. top-3 del sorteo actual)
    python gestion_banca.py --config                     (ver/ajustar parametros)
"""
import json, os, math, argparse, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI) if os.path.basename(AQUI) == "gestion" else AQUI
ESTADO = os.path.join(AQUI, "estado_banca.json")

# ---------------------------------------------------------------- parametros
PAGO          = 30      # paga 30x sobre lo apostado a UN animal
N_JUGADAS     = 3       # apostamos el Top-3 completo, monto igual en cada uno
P3_MEDIDA     = 0.12268 # acierto Top-3 en prueba ciega (final.txt, n=3122)
P3_IC_BAJO    = 0.1120  # limite inferior IC95 -> el que usamos para Kelly (conservador)
FRAC_KELLY    = 0.25    # 1/4 de Kelly. NO subir sin leer la seccion RIESGO del informe.
UMBRAL_ABST   = 0.1100  # si la suma de prob. del Top-3 baja de esto, NO se apuesta
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

BE = N_JUGADAS / PAGO   # punto de equilibrio = 3/30 = 10%
B  = (PAGO - N_JUGADAS) / N_JUGADAS   # odds netas por unidad apostada = 9


# ---------------------------------------------------------------- nucleo
def kelly(p, b=B, frac=FRAC_KELLY):
    """Fraccion de banca a arriesgar por sorteo. 0 si no hay ventaja."""
    q = 1.0 - p
    f = (b * p - q) / b
    return max(0.0, f * frac)


def plan_sorteo(banca, p3=None, banca_inicio_dia=None, perdido_hoy=0.0, maximo=None):
    """Devuelve el plan de apuesta para UN sorteo."""
    # TOPE DE CALIBRACION: la probabilidad que el modelo dice de si mismo no
    # esta calibrada; si se sobreestima, Kelly sobreapuesta. Se permite que
    # BAJE el tamano (p3 bajo -> abstencion) pero nunca que lo suba por encima
    # de la tasa medida en prueba ciega (limite inferior del IC95).
    p_ref = min(p3, P3_IC_BAJO) if p3 is not None else P3_IC_BAJO
    maximo = maximo or banca
    r = {"apostar": False, "motivo": "", "p3": p_ref, "por_animal": 0.0,
         "total": 0.0, "ganancia_si_acierta": 0.0, "ev": 0.0}

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
    if p_ref < UMBRAL_ABST:
        r["motivo"] = ("ABSTENERSE: el modelo da %.2f%% al Top-3 y el punto de equilibrio "
                       "es %.2f%%. Sin margen suficiente." % (p_ref * 100, BE * 100))
        return r

    f = kelly(p_ref)
    if f <= 0:
        r["motivo"] = "ABSTENERSE: sin ventaja a este precio."
        return r

    total = banca * f
    por = math.floor(total / N_JUGADAS / MIN_APUESTA) * MIN_APUESTA
    if por < MIN_APUESTA:
        r["motivo"] = ("Banca insuficiente: Kelly pide %.2f por animal y tu minimo es %.2f. "
                       "No apuestes por debajo del minimo, rompe el dimensionamiento."
                       % (total / N_JUGADAS, MIN_APUESTA))
        return r

    total = por * N_JUGADAS
    r.update(apostar=True, por_animal=por, total=total,
             ganancia_si_acierta=por * PAGO - total,
             ev=(p_ref * por * PAGO) - total,
             motivo="Apostar %.2f a CADA uno de los 3 animales (%.2f en total, %.2f%% de la banca)."
                    % (por, total, total / banca * 100))
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

    p = plan_sorteo(banca, p3, e["banca_inicio_dia"], e["perdido_hoy"], e["maximo"])
    L.append(" >> " + p["motivo"])
    if p["apostar"]:
        L.append("")
        L.append("    Por animal ......... %10.2f" % p["por_animal"])
        L.append("    Total en riesgo .... %10.2f" % p["total"])
        L.append("    Si acierta gana .... %10.2f  (neto)" % p["ganancia_si_acierta"])
        L.append("    Valor esperado ..... %+10.2f  (%+.1f%% de lo apostado)"
                 % (p["ev"], p["ev"] / p["total"] * 100))
        L.append("    Prob. de acertar ... %9.2f%%   -> fallaras %.0f de cada 10 sorteos"
                 % (p["p3"] * 100, (1 - p["p3"]) * 10))
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
