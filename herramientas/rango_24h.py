# -*- coding: utf-8 -*-
"""Para los sorteos de las últimas 24 horas (o las N horas que pidas), recalcula
la lista completa de 38 animales que el ensamble generaba EN ESE MOMENTO
(walk-forward, sin fuga: solo usa datos anteriores a cada sorteo, igual que
lotto_eval.py) y muestra en qué puesto de esa lista quedó el animal que
realmente salió.

Sirve para ver si los aciertos/fallos de hoy están cerca del Top-3 (puesto
4, 5, 6...) o muy lejos (puesto 20+), lo que ayuda a distinguir "el modelo
casi acierta" de "el modelo no tiene información esta racha".

Uso:
    python rango_24h.py            (últimas 24 horas)
    python rango_24h.py 48         (últimas 48 horas)
    python rango_24h.py 2026-09-14 (un día completo, fecha exacta)

Tarda varios minutos: reajusta los pesos del ensamble sobre todo el
histórico, igual que la herramienta "Validar predicción por sorteo" del
panel.
"""
import os, sys, time
from datetime import datetime, timedelta, date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import lotto_eval as LE

HIST = os.path.join(RAIZ, "historial.txt")
MOD = os.path.join(AQUI, "modelos", "ensamble_v2.py")
POS = LE.POS
ANIM = {"0": "DELFÍN", "00": "BALLENA", "1": "CARNERO", "2": "TORO", "3": "CIEMPIÉS", "4": "ALACRÁN",
        "5": "LEÓN", "6": "RANA", "7": "PERICO", "8": "RATÓN", "9": "ÁGUILA", "10": "TIGRE", "11": "GATO",
        "12": "CABALLO", "13": "MONO", "14": "PALOMA", "15": "ZORRO", "16": "OSO", "17": "PAVO", "18": "BURRO",
        "19": "CHIVO", "20": "COCHINO", "21": "GALLO", "22": "CAMELLO", "23": "CEBRA", "24": "IGUANA",
        "25": "GALLINA", "26": "VACA", "27": "PERRO", "28": "ZAMURO", "29": "ELEFANTE", "30": "CAIMÁN",
        "31": "LAPA", "32": "ARDILLA", "33": "PESCADO", "34": "VENADO", "35": "JIRAFA", "36": "CULEBRA"}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "24"
    datos = LE.cargar(HIST)
    n = len(datos)

    if arg.count("-") == 2:  # fecha exacta YYYY-MM-DD
        objetivo = [i for i, f in enumerate(datos.fecha) if f == arg]
        etiqueta = f"día {arg}"
    else:
        horas = float(arg)
        # timestamp aproximado por fila: fecha + hora del sorteo (slot 0-11 -> 8:00..19:00)
        d0 = date.fromisoformat(datos.fecha[0])
        limite = datetime.now() - timedelta(hours=horas)
        objetivo = []
        for i in range(n):
            f = date.fromisoformat(datos.fecha[i])
            ts = datetime(f.year, f.month, f.day, 8 + int(datos.hora[i]))
            if ts >= limite:
                objetivo.append(i)
        etiqueta = f"últimas {horas:g} horas"

    if not objetivo:
        print(f"No hay sorteos en {etiqueta}."); return

    w = LE.W  # calentamiento mínimo del modelo (2000)
    desde = min(objetivo[0], w)
    if objetivo[0] < w:
        print(f"Aviso: el histórico tiene menos de {w} sorteos antes del primero pedido; "
              f"el modelo arranca en calentamiento y sus primeras filas serán poco fiables.")

    print(f"Recalculando el ensamble desde la fila {desde} hasta {n} para ver {etiqueta}...")
    t0 = time.time()
    modelo = LE.cargar_modelo(MOD)
    P = LE.normalizar(modelo.predecir(datos, desde))
    print(f"  listo en {time.time() - t0:.0f} s\n")

    print(f"{'fecha':<10} {'hora':>5} {'salió':>7} {'puesto':>7} {'prob':>7}  top-5 del momento")
    for i in objetivo:
        fila = P[i - desde]
        orden = np.argsort(-fila)
        real = datos.seq[i]
        puesto = int(np.where(orden == real)[0][0]) + 1
        hora_txt = f"{8 + int(datos.hora[i])}:00"
        top5 = " ".join(f"{POS[j]}" for j in orden[:5])
        print(f"{datos.fecha[i]:<10} {hora_txt:>5} {POS[real]+' '+ANIM[POS[real]]:>7} "
              f"{puesto:>7} {fila[real]*100:>6.2f}%  {top5}")

    puestos = [int(np.where(np.argsort(-P[i - desde]) == datos.seq[i])[0][0]) + 1 for i in objetivo]
    print(f"\nPromedio de puesto: {np.mean(puestos):.1f} (azar = 19.5; Top-3 perfecto = 2.0)")
    print(f"En Top-3: {sum(1 for p in puestos if p <= 3)}/{len(puestos)}   "
          f"En Top-5: {sum(1 for p in puestos if p <= 5)}/{len(puestos)}   "
          f"En Top-10: {sum(1 for p in puestos if p <= 10)}/{len(puestos)}")


if __name__ == "__main__":
    main()
