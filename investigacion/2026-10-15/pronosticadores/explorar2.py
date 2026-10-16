# -*- coding: utf-8 -*-
"""EXPLORATORIO 2: la pirámide por sumas (S3) separada de los números de la fecha/hora ya conocidos."""
import contextlib, io, os, runpy
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    E = runpy.run_path(os.path.join(AQUI, "explorar.py"))
LE, V, correr, SEL, mostrar = E["LE"], E["VARIANTES"], E["correr"], E["SEL"], E["mostrar"]
pir, conf, orig, pp = E["piramide"], E["confusores"], E["orig"], E["pares_piramide"]
def dia_win(f):
    d = int(f[8:10]); return {LE.IDX[str(x)] for x in (d - 1, d, d + 1, d + 2) if 0 <= x <= 36}
V["S3 pirámide sumas"] = lambda j, f, h: pir(f)
V["S3 sin día-1..día+2 ni hora12"] = lambda j, f, h: pir(f) - dia_win(f) - conf(f, h) or None
V["S3 sin fecha/hora ni pares"] = lambda j, f, h: pir(f) - dia_win(f) - conf(f, h) - pp(f) or None
V["U fuera de S3 y de fecha"] = lambda j, f, h: (orig(j, f, "U") or set()) - pir(f) - dia_win(f) - conf(f, h) or None
V["S3 placebo (pirámide de d+7)"] = lambda j, f, h: pir(E["corr"](f, 7))
for tramo, s in SEL.items():
    print("==", tramo)
    for n in ("S3 pirámide sumas", "S3 sin día-1..día+2 ni hora12", "S3 sin fecha/hora ni pares", "U fuera de S3 y de fecha", "S3 placebo (pirámide de d+7)"):
        mostrar(n, correr(n, E["P"][s], E["Y"][s], E["H"][s], E["F"][s], E["DIA"][s]))
print("== vivo")
for n in ("S3 pirámide sumas", "S3 sin día-1..día+2 ni hora12", "U fuera de S3 y de fecha"):
    mostrar(n, correr(n, E["PM"], E["YM"], E["HM"], E["FM"], E["DM"]))
c = np.load(os.path.join(E["G"]["RAIZ"], "verificacion", "hilo9", "datos", "cache_todo.npz")); s = c["tramo"] == "dev"
P1 = c["P1"][s].astype(float); P1 /= P1.sum(1, keepdims=True)
print("== RD dev")
for n in ("S3 sin día-1..día+2 ni hora12",):
    mostrar(n, correr(n, P1, c["y"][s], c["hora"][s], c["fecha"][s], c["dia"][s], juego="RD"))
