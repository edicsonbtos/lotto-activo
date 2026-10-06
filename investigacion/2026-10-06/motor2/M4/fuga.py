# -*- coding: utf-8 -*-
"""M4: A.chequear_fuga con el reentrenamiento REAL (rasgos recalculados con la secuencia alterada, etiquetas de la
secuencia alterada, modelo entrenado con las filas de antes del mes, predicción de la fila i).
Para ahorrar CPU usa el nº de árboles que eligió V1 en ese mes (la parada temprana usa solo filas anteriores al mes)."""
import sys
from datetime import date
import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, sys.path[0] + "/M4")
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M4")
import arnes as A, rasgos as R, motor as M

RD = R.cargar_rd()
INFO = dict((m, b) for m, b in np.load(A.SP + "/m4_V1.npz", allow_pickle=True)["info"])
POS_T = {int(t): j for j, t in enumerate(A.T)}


def fn(S, hora, dow, fecha, i):
    X, nm = R.construir(S, hora, np.asarray(A.D.dia), fecha, RD)
    XT, nombres, LP = M.preparar(X, nm, True)
    Yoh = (np.arange(38)[None, :] == np.asarray(S)[A.T][:, None]).astype(np.float32)
    j = POS_T[i]; mes = A.F[j][:7]; ini = date.fromisoformat(mes + "-01")
    FD = np.array([date.fromisoformat(f) for f in A.F]); tr = np.where(FD < ini)[0]
    b = INFO.get(mes, 100); b = 100 if b == "PROD" else int(b)
    m = M.entrenar(XT, LP, Yoh, tr, np.ones(len(tr)), nombres, rondas=b)
    raw = m.predict(XT[j].reshape(-1, XT.shape[2]), raw_score=True)
    return M.softmax((raw + LP[j])[None])[0]


if __name__ == "__main__":
    # cortes dentro de AJUSTE, ELECCION y PRUEBA26 (índices de D)
    cortes = tuple(int(A.T[np.where(A.F >= f)[0][0]] + 5) for f in ("2025-09-10", "2026-04-15", "2026-08-20"))
    print("cortes", cortes)
    A.chequear_fuga(fn, cortes=cortes)
