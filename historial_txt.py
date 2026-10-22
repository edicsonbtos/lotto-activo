"""Historial en un solo .txt: botón «Descargar historial» de la web y ruta /historial.txt.

Junta lo necesario para analizar fuera de la web: los dos historiales tal cual y los pronósticos congelados de
Lotto Activo y RD Internacional, un registro JSON por línea (sin la lista de 38 puntajes, que es lo que pesa).
"""
import json, os
from datetime import datetime


def _lineas(ruta):
    if not os.path.isfile(ruta):
        return None
    with open(ruta, encoding="utf-8", errors="replace") as f:
        return [x.rstrip("\n") for x in f if x.strip()]


def _registros(ruta):
    if not os.path.isfile(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            reg = json.load(f).get("registros")
    except (ValueError, AttributeError, OSError):
        return None
    return reg if isinstance(reg, list) else None


def exportar(hist, log, rd_hist, rd_log):
    """Texto plano con cabecera, conteos y cuatro secciones «===== nombre =====»."""
    hl, rl = _lineas(hist), _lineas(rd_hist)
    pl, pr = _registros(log), _registros(rd_log)

    def cuenta(x, que):
        return "no existe" if x is None else f"{len(x)} {que}"
    partes = ["LOTTO ACTIVO — HISTORIAL COMPLETO\n"
              f"generado {datetime.now().isoformat(timespec='seconds')} (hora de Caracas)\n\n"
              f"historial.txt (Lotto Activo, sorteos h:00): {cuenta(hl, 'sorteos')}\n"
              f"rdint_historial.txt (RD Internacional, sorteos h:30): {cuenta(rl, 'sorteos')}\n"
              f"predicciones (Lotto Activo): {cuenta(pl, 'pronósticos congelados')}\n"
              f"rdint_predicciones (RD Internacional): {cuenta(pr, 'pronósticos congelados')}\n\n"
              "Historiales: una línea por sorteo, igual que el archivo original.\n"
              "Predicciones: un registro JSON por línea con el orden congelado ANTES del sorteo (orden_completo, "
              "índices 0-37) y lo que salió (salio).\nSe omite «scores» (38 probabilidades) para que pese poco; "
              "el zip completo con los puntajes sigue en /historial.zip con la clave.\n"]
    for nombre, filas in (("historial.txt", hl), ("rdint_historial.txt", rl)):
        partes.append(f"===== {nombre} =====\n" + ("\n".join(filas) if filas else "(vacío)"))
    for nombre, regs in (("predicciones.jsonl", pl), ("rdint_predicciones.jsonl", pr)):
        cuerpo = "\n".join(json.dumps({k: v for k, v in r.items() if k not in ("scores", "scores_sin_8am")},
                                      ensure_ascii=False, separators=(",", ":"))
                           for r in regs or [] if isinstance(r, dict))
        partes.append(f"===== {nombre} =====\n" + (cuerpo or "(vacío)"))
    return "\n\n".join(partes) + "\n"
