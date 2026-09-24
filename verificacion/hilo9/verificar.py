# -*- coding: utf-8 -*-
"""Verificación independiente del hilo 9 (¿se pueden subir los porcentajes?).

1. Comprueba las huellas SHA-256 de los datos congelados (verificacion/hilo9/datos).
2. Corre los 3 análisis contra ESA copia (no contra los datos vivos del proyecto).
3. Compara cada número con verificacion/hilo9/esperado/*.md.

Uso (desde la raíz del repo, Python 3.10+ con numpy y scipy):
    python verificacion/hilo9/verificar.py            # los 3 (techo.py tarda 10-20 min)
    python verificacion/hilo9/verificar.py --rapido   # sólo residuos y paso2 (~2 min)
"""
import hashlib, os, re, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
DATOS = os.path.join(AQUI, "datos")
TOL = 0.6            # techo.py usa L-BFGS: otras CPU/BLAS pueden mover décimas


def huellas():
    ok = True
    for ln in open(os.path.join(AQUI, "SHA256SUMS.txt"), encoding="utf-8"):
        h, nombre = ln.split()
        nombre = nombre.lstrip("*")
        real = hashlib.sha256(open(os.path.join(DATOS, nombre), "rb").read()).hexdigest()
        print("%-22s %s" % (nombre, "OK" if real == h else "DISTINTO"))
        ok &= real == h
    return ok


def numeros(txt):
    return [float(x) for x in re.findall(r"[-+]?\d+\.\d+", txt)]


def main():
    print("== Huellas de los datos congelados")
    if not huellas():
        sys.exit("Los datos no coinciden con SHA256SUMS.txt: la verificación no vale.")
    env = dict(os.environ, HILO9_DATOS=DATOS, RAILWAY_VOLUME_MOUNT_PATH=DATOS, PYTHONIOENCODING="utf-8")
    scripts = ["residuos", "paso2"] + ([] if "--rapido" in sys.argv else ["techo"])
    fallos = 0
    for s in scripts:
        print("\n== %s.py" % s, flush=True)
        subprocess.run([sys.executable, os.path.join(RAIZ, "herramientas", "hilo9", s + ".py")],
                       env=env, cwd=RAIZ, check=True, stdout=subprocess.DEVNULL)
        nombre = {"residuos": "hilo9_residuos.md", "paso2": "hilo9_paso2.md", "techo": "hilo9_techo.md"}[s]
        nuevo = numeros(open(os.path.join(RAIZ, "herramientas", "resultados", nombre), encoding="utf-8").read())
        viejo = numeros(open(os.path.join(AQUI, "esperado", nombre), encoding="utf-8").read())
        tol = TOL if s == "techo" else 0.011
        malos = [(a, b) for a, b in zip(viejo, nuevo) if abs(a - b) > tol]
        if len(nuevo) != len(viejo) or malos:
            fallos += 1
            print("  DIFERENTE: %d números fuera de tolerancia %s" % (len(malos), malos[:10]))
        else:
            print("  IGUAL: %d números dentro de ±%g" % (len(viejo), tol))
    print("\nRESULTADO: %s" % ("TODO REPRODUCIDO" if not fallos else "%d análisis no coinciden" % fallos))


if __name__ == "__main__":
    main()
