#!/usr/bin/env python3
"""PostToolUse: tras editar un .py, compila; si es servidor.py, además
renderiza la página contra COPIAS temporales de los datos (nunca los reales).
Salida 2 = avisar a Claude del error para que lo corrija.
"""
import json, os, py_compile, shutil, sys, tempfile, importlib.util, traceback

def main():
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return
    ruta = (datos.get("tool_input") or {}).get("file_path") or ""
    if not ruta.endswith(".py") or not os.path.exists(ruta):
        return
    try:
        py_compile.compile(ruta, doraise=True)
    except py_compile.PyCompileError as e:
        sys.stderr.write(f"Error de sintaxis en {ruta}:\n{e.msg}\n")
        sys.exit(2)

    if os.path.basename(ruta) not in ("servidor.py", "modelo.py"):
        return
    raiz = os.path.dirname(os.path.abspath(ruta))
    if not os.path.exists(os.path.join(raiz, "historial.txt")):
        return
    tmp = tempfile.mkdtemp(prefix="lotto_smoke_")
    try:
        for f in ("servidor.py", "modelo.py", "historial.txt", "predicciones.json"):
            src = os.path.join(raiz, f)
            if os.path.exists(src):
                shutil.copy2(src, tmp)
        sys.path.insert(0, tmp)
        spec = importlib.util.spec_from_file_location("servidor_smoke", os.path.join(tmp, "servidor.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        html = mod.render()
        if "<html" not in html or "Próximo" not in html:
            sys.stderr.write("render() no devolvió la página esperada.\n")
            sys.exit(2)
    except SystemExit:
        raise
    except Exception:
        sys.stderr.write("render() falló con copias de los datos:\n" + traceback.format_exc()[-2500:])
        sys.exit(2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
