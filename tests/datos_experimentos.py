"""Datos sintéticos deterministas para fijar el comportamiento de los experimentos (cambio RD, sombra)."""
import random

POS = ["0", "00"] + [str(i) for i in range(1, 37)]


def log_sintetico():
    """(d, rd): un registro por sorteo del 2026-09-27 al 2026-10-04, horas 0..5, y el mapa RD {(fecha, h): código}."""
    rnd = random.Random(20261006)
    registros, rd = [], {}
    for dia in range(27, 38):
        fecha = "2026-09-%02d" % dia if dia <= 30 else "2026-10-%02d" % (dia - 30)
        for h in range(0, 6):
            def probs():
                v = [rnd.random() + 0.05 for _ in range(38)]
                t = sum(v)
                return [x / t for x in v]
            sc, ag = probs(), probs()
            orden = sorted(range(38), key=lambda i: (-sc[i], i))
            registros.append({
                "fecha": fecha, "hora": h, "modelo": "ensamble_v2", "salio": rnd.randrange(38),
                "scores": sc, "orden_completo": orden, "top3": orden[:3],
                "sombra": {"ag12": ag},
            })
            rd[(fecha, h)] = POS[rnd.randrange(38)]
    registros.append({"fecha": "2026-10-04", "hora": 6, "modelo": "ensamble_v2", "salio": 3,   # anulado: no cuenta
                      "scores": [1 / 38] * 38, "orden_completo": list(range(38)), "top3": [0, 1, 2],
                      "anulado": {"motivo": "prueba"}})
    registros.append({"fecha": "2026-10-04", "hora": 7, "modelo": "hazard_actual", "salio": 3})  # otro modelo
    return {"registros": registros}, rd


def rd_como_lista(rd):
    return [(f, h, c) for (f, h), c in sorted(rd.items())]
