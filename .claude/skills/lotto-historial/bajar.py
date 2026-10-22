"""Baja /historial.txt de la web de Railway y lo separa en sus cuatro archivos. Uso: python bajar.py [carpeta]"""
import os, sys, tempfile, urllib.request

URL = os.environ.get("LOTTO_URL", "https://lotto-activo-production.up.railway.app") + "/historial.txt"


def separar(texto, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, "lotto_historial.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    for trozo in texto.split("\n===== ")[1:]:
        nombre, _, cuerpo = trozo.partition(" =====\n")
        with open(os.path.join(carpeta, nombre), "w", encoding="utf-8") as f:
            f.write(cuerpo.strip("\n") + "\n" if cuerpo.strip() != "(vacío)" else "")
    print(texto.split("\n=====")[0])
    print(f"\nGuardado en {carpeta}")


if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "lotto_historial")
    try:
        with urllib.request.urlopen(URL, timeout=120) as r:
            texto = r.read().decode("utf-8")
    except Exception as ex:  # noqa: BLE001
        sys.exit(f"No se pudo bajar {URL}: {ex!r}\n"
                 "Si es un 403/connect_rejected del proxy, la red del entorno bloquea Railway: ver SKILL.md paso 3.")
    separar(texto, destino)
