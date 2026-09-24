# -*- coding: utf-8 -*-
"""Hilo 8: baja de la API oficial (lottoactivo.com) los resultados de los juegos 1 (Lotto Activo),
2 (RD Internacional) y 3 (Lotto Activo República Dominicana), día por día. La API tiene historia
desde 2025-07-01. Reanuda: los días ya guardados no se vuelven a pedir. Python puro (sin numpy).

Uso: python herramientas/lard/descargar.py [hasta=AAAA-MM-DD]
Salida: datos_multiloteria/oficial_multi.csv  (fecha,juego,hora,codigo)  hora en 24 h "HH:MM"
"""
import csv, io, os, re, sys, time
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scraping"))
import fuente_oficial as F

INICIO = date(2025, 7, 1)
JUEGOS = ("1", "2", "3")
SALIDA = os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv")


def hora24(txt):
    m = re.match(r"\s*(\d{1,2}):(\d{2})\s*([AP]M)", str(txt), re.I)
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3).upper() == "PM" else 0)
    return "%02d:%s" % (h, m.group(2))


def filas_dia(js, fecha):
    out = []
    for juego in (js or {}).get("datos") or []:
        jid = str(juego.get("id"))
        if jid not in JUEGOS:
            continue
        for r in juego.get("resultados") or []:
            h = hora24(r.get("time_s"))
            cod, _ = F.codigo_de(r.get("number_animal"), r.get("name_animal"))
            if h and cod:
                out.append((fecha, jid, h, cod))
    return out


def main():
    hasta = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today() - timedelta(days=1)
    hechos = set()
    if os.path.exists(SALIDA):
        with io.open(SALIDA, encoding="utf-8") as fh:
            hechos = {r["fecha"] for r in csv.DictReader(fh)}
    nuevo = not os.path.exists(SALIDA)
    fh = io.open(SALIDA, "a", encoding="utf-8", newline="")
    w = csv.writer(fh)
    if nuevo:
        w.writerow(["fecha", "juego", "hora", "codigo"])
    d, n, vacios = INICIO, 0, []
    while d <= hasta:
        f = d.isoformat()
        if f not in hechos:
            filas = None
            for i in range(3):
                try:
                    filas = filas_dia(F._pedir(f, F.token(refrescar=i > 0)), f)
                    break
                except Exception as e:  # noqa: BLE001
                    sys.stderr.write("%s: fallo %r, reintento\n" % (f, e))
                    time.sleep(3)
            if filas:
                w.writerows(filas); fh.flush(); n += 1
            else:
                vacios.append(f)
            time.sleep(0.3)
            if n and n % 30 == 0:
                print("%s  %d días nuevos" % (f, n), flush=True)
        d += timedelta(days=1)
    fh.close()
    print("listo: %d días nuevos; sin datos: %d %s" % (n, len(vacios), vacios[:20]), flush=True)


if __name__ == "__main__":
    main()
