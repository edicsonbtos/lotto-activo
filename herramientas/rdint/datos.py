# -*- coding: utf-8 -*-
"""Hilo 7: datos alineados de RD Internacional (h:30) con Lotto Activo (h:00).

cargar() -> (rd, la_h, la_h1, la_hoy, tramo)
  rd      : lotto_eval.Datos de RD Int (seq en el indice de lotto_eval.POS, hora 0..11)
  la_h    : (n,) indice del ganador de Lotto Activo a las h:00 del MISMO dia (-1 si falta)
  la_h1   : (n,) idem a las (h-1):00 (-1 si h=0 o falta)
  la_hoy  : (n, 38) veces que cada animal salio en Lotto Activo HOY hasta h:00 INCLUSIVE
  tramo   : (n,) 'cal' | 'dev' | 'test' | 'desc' | 'vivo'  (PREREGISTRO_rdint_cruzado.md)

Todo lo de Lotto Activo usado para el sorteo RD de h:30 es de h:00 o antes: sale 30 min antes.
"""
import csv, io, os, re, sys, unicodedata
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(AQUI))
import lotto_eval as LE

RD_CSV = os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv")
LA_CSV = os.path.join(RAIZ, "datos_multiloteria", "lottoactivo.csv")   # cola posterior a historial.txt
# En Railway el historial vivo está en el volumen, no en /app
LA_HIST = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or RAIZ, "historial.txt")

ANIMALES = {
    "DELFIN": "0", "BALLENA": "00", "CARNERO": "1", "TORO": "2", "CIEMPIES": "3",
    "ALACRAN": "4", "LEON": "5", "RANA": "6", "PERICO": "7", "RATON": "8",
    "AGUILA": "9", "TIGRE": "10", "GATO": "11", "CABALLO": "12", "MONO": "13",
    "PALOMA": "14", "ZORRO": "15", "OSO": "16", "PAVO": "17", "BURRO": "18",
    "CHIVO": "19", "COCHINO": "20", "GALLO": "21", "CAMELLO": "22", "CEBRA": "23",
    "IGUANA": "24", "GALLINA": "25", "VACA": "26", "PERRO": "27", "ZAMURO": "28",
    "ELEFANTE": "29", "CAIMAN": "30", "LAPA": "31", "ARDILLA": "32", "PESCADO": "33",
    "VENADO": "34", "JIRAFA": "35", "CULEBRA": "36",
}

TRAMOS = [("cal", "2023-09-04"), ("dev", "2024-03-01"), ("test", "2025-07-01"),
          ("desc", "2026-04-13"), ("vivo", "2026-09-14")]


def sin_acentos(txt):
    return re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", (txt or "").upper()))


def tramo_de(f):
    t = None
    for nombre, desde in TRAMOS:
        if f >= desde:
            t = nombre
    return t


def _la_por_fecha():
    """{fecha: {h: idx}} de Lotto Activo: historial.txt + cola de lottoactivo.csv."""
    d = {}
    la = LE.cargar(LA_HIST)
    for f, h, s in zip(la.fecha, la.hora, la.seq):
        d.setdefault(f, {})[int(h)] = int(s)
    if os.path.exists(LA_CSV):
        with io.open(LA_CSV, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["fecha"] in d:
                    continue
                cod = ANIMALES.get(sin_acentos(r["animal"]))
                if cod is None:
                    continue
                d.setdefault(r["fecha"], {})[int(r["hora"][:2]) - 8] = LE.IDX[cod]
    return d


def cargar():
    filas, desconocidos = [], {}
    with io.open(RD_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cod = ANIMALES.get(sin_acentos(r["animal"]))
            if cod is None:
                desconocidos[r["animal"]] = desconocidos.get(r["animal"], 0) + 1
                continue
            h = int(r["hora"][:2]) - 8
            if not (r["hora"].endswith(":30") and 0 <= h <= 11):
                desconocidos["hora " + r["hora"]] = desconocidos.get("hora " + r["hora"], 0) + 1
                continue
            filas.append((r["fecha"], h, LE.IDX[cod]))
    if desconocidos:
        sys.stderr.write("rdint: filas descartadas %s\n" % desconocidos)
    filas = sorted(set(filas), key=lambda r: (r[0], r[1]))
    d0 = date.fromisoformat(filas[0][0])
    fechas = [r[0] for r in filas]
    rd = LE.Datos(np.array([r[2] for r in filas]), np.array([r[1] for r in filas]),
                  np.array([date.fromisoformat(f).weekday() for f in fechas]),
                  np.array([(date.fromisoformat(f) - d0).days for f in fechas]), fechas)
    la = _la_por_fecha()
    n = len(filas)
    la_h = np.full(n, -1); la_h1 = np.full(n, -1); la_hoy = np.zeros((n, LE.K), np.int8)
    for t, (f, h, _) in enumerate(filas):
        dia = la.get(f, {})
        la_h[t] = dia.get(h, -1)
        la_h1[t] = dia.get(h - 1, -1) if h > 0 else -1
        for hh, s in dia.items():
            if hh <= h:
                la_hoy[t, s] += 1
    tramo = np.array([tramo_de(f) for f in fechas])
    return rd, la_h, la_h1, la_hoy, tramo


if __name__ == "__main__":
    rd, la_h, la_h1, la_hoy, tramo = cargar()
    print("RD Int sorteos:", len(rd), rd.fecha[0], "..", rd.fecha[-1])
    print("por tramo:", {k: int((tramo == k).sum()) for k in np.unique(tramo)})
    print("sin LA h:", int((la_h < 0).sum()), " numeros RD distintos:", len(set(rd.seq.tolist())))
    print("uso de '00' (Ballena) en RD:", int((rd.seq == LE.IDX["00"]).sum()))
