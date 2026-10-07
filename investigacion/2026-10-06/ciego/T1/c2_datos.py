"""C2: datos RD Int (rdint_historial.txt, h 0..11 = 8:30..19:30; SOLO LECTURA) alineados con Lotto Activo
(A.D = copia hist_0605.txt del scratchpad). Guarda <SP>/T1_rd_datos.npz: seq, hora, dia, dow, fecha, la_h, la_h1,
la_hoy (LA de h:00 y antes del MISMO día; sale 30 min antes que RD h:30)."""
import sys, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A
LE = A.LE
rd = LE.cargar("/home/user/lotto-activo/rdint_historial.txt")
la = {}
for f, h, s in zip(A.D.fecha, A.D.hora, A.D.seq):
    la.setdefault(f, {})[int(h)] = int(s)
n = len(rd); la_h = np.full(n, -1); la_h1 = np.full(n, -1); la_hoy = np.zeros((n, 38), np.int8)
for t, (f, h) in enumerate(zip(rd.fecha, rd.hora)):
    d = la.get(f, {}); h = int(h)
    la_h[t] = d.get(h, -1); la_h1[t] = d.get(h - 1, -1) if h > 0 else -1
    for hh, s in d.items():
        if hh <= h:
            la_hoy[t, s] += 1
np.savez_compressed(A.SP + "/T1_rd_datos.npz", seq=rd.seq, hora=rd.hora, dia=rd.dia, dow=rd.dow,
                    fecha=np.array(rd.fecha), la_h=la_h, la_h1=la_h1, la_hoy=la_hoy)
F = np.array(rd.fecha)
print("RD", n, rd.fecha[0], "..", rd.fecha[-1], "| sin LA h:", int((la_h < 0).sum()),
      "| en 2025-07..: sin LA h", int((la_h[F >= "2025-07-01"] < 0).sum()), "de", int((F >= "2025-07-01").sum()))
print("primera fila 2025-07:", int(np.argmax(F >= "2025-07-01")))
