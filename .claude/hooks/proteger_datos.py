#!/usr/bin/env python3
"""PreToolUse: impide que Claude modifique a mano los datos del marcador.

historial.txt y predicciones.json solo los debe escribir servidor.py.
Las copias dentro de respaldo/ no se protegen (sirven para pruebas).
Salida 2 = bloquear; el mensaje de stderr se le muestra a Claude.
"""
import json, os, re, sys

PROTEGIDOS = ("historial.txt", "predicciones.json")

def bloquear(motivo):
    sys.stderr.write(
        f"BLOQUEADO: {motivo}. Esos archivos son el registro del marcador y solo "
        "los escribe servidor.py. Para pruebas, trabaja sobre una copia fuera de la "
        "carpeta raíz (p. ej. en el scratchpad o en respaldo/).\n")
    sys.exit(2)

def es_protegido(ruta):
    if not ruta:
        return False
    r = ruta.replace("\\", "/")
    if "/respaldo/" in r or r.startswith("respaldo/"):
        return False
    return os.path.basename(r) in PROTEGIDOS

def main():
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return
    herramienta = datos.get("tool_name", "")
    entrada = datos.get("tool_input", {}) or {}

    if herramienta in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        ruta = entrada.get("file_path") or entrada.get("notebook_path")
        if es_protegido(ruta):
            bloquear(f"{herramienta} sobre {os.path.basename(ruta)}")
        return

    if herramienta in ("Bash", "PowerShell"):
        cmd = entrada.get("command", "")
        for nombre in PROTEGIDOS:
            n = re.escape(nombre)
            # Solo lectura (cat, head, grep, cp origen) está permitida.
            patrones = [
                rf">>?\s*[\"']?[^\s\"'|;&]*{n}",                 # redirección
                rf"\bsed\s+(-\w*i|--in-place)[^|;&]*{n}",          # sed -i
                rf"\b(rm|del|Remove-Item|truncate)\b[^|;&]*{n}",   # borrar
                rf"\bmv\b[^|;&]*{n}",                              # mover/renombrar
                rf"\b(cp|copy|Copy-Item)\b[^|;&]*\s[\"']?(\./)?{n}[\"']?\s*($|[|;&])",  # sobrescribir destino
                rf"\b(Set-Content|Add-Content|Out-File|Clear-Content)\b[^|;&]*{n}",
                rf"\btee\b[^|;&]*{n}",
            ]
            for p in patrones:
                m = re.search(p, cmd, re.IGNORECASE)
                if m and "respaldo/" not in m.group(0).replace("\\", "/"):
                    bloquear(f"comando que escribe en {nombre}")

if __name__ == "__main__":
    main()
