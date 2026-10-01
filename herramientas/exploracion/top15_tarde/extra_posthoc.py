# -*- coding: utf-8 -*-
"""Descriptivo POST-HOC (no pre-registrado, después de la ciega): para el informe.
(a) LA: sacar del Top-15 el RD (h-1):30 (regla HERM), todas las horas, por año y por hora.
(b) Calibración del Top-15 actual por trimestre (masa que se da el modelo contra acierto real)."""
import os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import top15_tarde as T
rng = np.random.default_rng(7)
la, rd = T.juego_la(), T.juego_rd()
print("(a) LA: RD (h-1):30 fuera del Top-15, todas las horas")
for nom, sel in [("2024", la["fecha"] < "2025-01-01"), ("2025", (la["fecha"] >= "2025-01-01") & (la["fecha"] < "2026-01-01")),
                 ("2026", la["fecha"] >= "2026-01-01")]:
    P, y, fe = la["P"][sel], la["y"][sel], la["fecha"][sel]
    sub = {k: v[sel] for k, v in la.items() if isinstance(v, np.ndarray) and len(v) == len(la["y"])}
    X = T.mascara(sub, ("HERM",), None)
    b = T.medidas(P, y, np.zeros_like(X)); m = T.medidas(P, y, X)
    top = np.zeros_like(X); np.put_along_axis(top, b["orden"][:, :15], True, 1)
    dv, (_, ic) = T.boot(m["t15"] - b["t15"], fe, rng)
    d5, (_, ic5) = T.boot(m["r15p"] - b["r15p"], fe, rng)
    print(f"  {nom}: n {len(y)}  actual {b['t15'].mean()*100:.2f} %  con regla {m['t15'].mean()*100:.2f} %  "
          f"Δ {dv*100:+.2f} pp [{ic[0]*100:+.2f}; {ic[1]*100:+.2f}]  Δ ret. ponderado {d5*100:+.2f} pp [{ic5[0]*100:+.2f}; {ic5[1]*100:+.2f}]"
          f"  | RD dentro del Top-15 en {(top & X).any(1).mean()*100:.0f} % de los sorteos; ese animal ganó {(top & X)[np.arange(len(y)), y].sum()}"
          f" veces (el modelo esperaba {(P * (top & X)).sum():.1f})")
print("(b) Calibración del Top-15 actual por trimestre: acierto real / lo que se da el modelo")
for j, d in [("LA", la), ("RD", rd)]:
    sel = d["fecha"] >= "2024-03-01"
    P, y, fe = d["P"][sel], d["y"][sel], d["fecha"][sel]
    o = T.LE.rankings(P); pos = np.argmax(o == y[:, None], 1); masa = np.take_along_axis(P, o[:, :15], 1).sum(1)
    tri = np.array([f[:4] + "T" + str((int(f[5:7]) - 1) // 3 + 1) for f in fe])
    print("  " + j + ": " + "  ".join(f"{t} {100*(pos[tri==t]<15).mean():.1f}/{100*masa[tri==t].mean():.1f}" for t in sorted(set(tri))))
