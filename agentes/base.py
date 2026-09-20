# -*- coding: utf-8 -*-
"""Contrato común de los agentes de predicción.

Un agente es una estrategia determinista que, dado el historial COMPLETO de
sorteos anteriores, asigna un puntaje (no necesariamente una probabilidad) a
cada uno de los 38 animales. El orquestador normaliza y ordena.

REGLAS DE HONESTIDAD (obligatorias):
  * Usar SOLO sorteos estrictamente anteriores al que se va a predecir.
    Las listas que se reciben ya cumplen eso: son el pasado completo.
  * Ninguna aleatoriedad: mismo historial -> misma salida, siempre.
  * predecir() debe tardar < 2 s con ~12.500 sorteos.

Orden de animales (idéntico a servidor.py):
  POS = ["0", "00", "1", "2", ..., "36"]  -> indice 0..37
"""
import math

K = 38
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}

# Nombre de animal por indice (para depuracion)
ANIM = {"0": "DELFIN", "00": "BALLENA", "1": "CARNERO", "2": "TORO", "3": "CIEMPIES",
        "4": "ALACRAN", "5": "LEON", "6": "RANA", "7": "PERICO", "8": "RATON",
        "9": "AGUILA", "10": "TIGRE", "11": "GATO", "12": "CABALLO", "13": "MONO",
        "14": "PALOMA", "15": "ZORRO", "16": "OSO", "17": "PAVO", "18": "BURRO",
        "19": "CHIVO", "20": "COCHINO", "21": "GALLO", "22": "CAMELLO", "23": "CEBRA",
        "24": "IGUANA", "25": "GALLINA", "26": "VACA", "27": "PERRO", "28": "ZAMURO",
        "29": "ELEFANTE", "30": "CAIMAN", "31": "LAPA", "32": "ARDILLA", "33": "PESCADO",
        "34": "VENADO", "35": "JIRAFA", "36": "CULEBRA"}


class Agente:
    """Interfaz: subclass e implementar predecir()."""

    nombre = "base"           # identificador corto, sin espacios
    descripcion = ""          # una linea, se muestra en la web

    def predecir(self, seq, horas, dweek):
        """Devuelve una lista de K=38 puntajes (float). A mayor puntaje, mas
        probable segun este agente.

        seq    : list[int]   indices de animales de TODOS los sorteos pasados,
                             en orden cronologico.
        horas  : list[int]   hora de sorteo 0..11 (8AM=0 ... 7PM=11) de cada uno.
        dweek  : list[int]   dia de la semana 0=lun..6=dom de cada sorteo.
        """
        raise NotImplementedError

    # ---------------------------------------------------------------- utilidades
    def softmax(self, scores, temp=1.0):
        m = max(scores)
        e = [math.exp((s - m) / temp) for s in scores]
        t = sum(e)
        return [x / t for x in e]


def cargar_historial(ruta):
    """Lee historial.txt ('YYYY-MM-DD H NUM') -> (seq, horas, dweek, fechas)."""
    from datetime import date
    seq, horas, dweek, fechas = [], [], [], []
    with open(ruta, encoding="utf-8") as f:
        for ln in f:
            p = ln.split()
            if len(p) == 3 and p[2] in IDX:
                fechas.append(p[0])
                horas.append(int(p[1]))
                seq.append(IDX[p[2]])
                dweek.append(date.fromisoformat(p[0]).weekday())
    return seq, horas, dweek, fechas
