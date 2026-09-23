# -*- coding: utf-8 -*-
"""La jugada del próximo sorteo, en plata, leída de la web en vivo (Railway).

Uso: python jugada.py [banca]
Solo lee /api/mesa (el pronóstico congelado que se puntúa). No escribe nada.
Usa curl porque el Python del PC del usuario falla verificando certificados.
"""
import json, subprocess, sys

URL = "https://lotto-activo-production.up.railway.app"
PAGO = 30
ESCALONADO = [2, 2, 2, 1, 1]                          # puestos 1..5
PONDERADO = [3, 3, 3, 2, 2] + [1] * 10                # puestos 1..15


def leer(ruta):
    out = subprocess.run(["curl", "-s", "--max-time", "60", URL + ruta],
                         capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out)


def main():
    banca = float(sys.argv[1]) if len(sys.argv) > 1 else None
    m = leer("/api/mesa?offset=0")
    if m.get("vista") != "prob" or not any(a["rank"] for a in m["animales"]):
        print("La web todavía está calculando el pronóstico (pasa 1-2 min tras cada despliegue). "
              "Vuelve a intentarlo en un minuto.")
        return
    orden = sorted((a for a in m["animales"] if a["rank"]), key=lambda a: a["rank"])
    print(f"Sorteo: {m['fecha_txt']} {m['hora_txt']} · modelo {m['modelo']}")
    if str(m["modelo"]).endswith("_sin_pesos"):
        print("AVISO: pronóstico hecho SIN pesos del ensamble: no es el modelo medido. Mejor no jugar este.")
    # ficha: base Top-3 con 1/4 de Kelly sobre el límite bajo (0,33 % de la banca en el Top-3)
    ficha = None
    if banca:
        f3 = 0.25 * (9 * 0.1117 - 0.8883) / 9
        ficha = max(0.0, int(banca * f3 / 6))
    print("\nTop-5 escalonado (recomendada, ≈ +19 % en prueba ciega):")
    for a in orden[:5]:
        fx = ESCALONADO[a["rank"] - 1]
        plata = f" -> {fx * ficha:g} $" if ficha else ""
        print(f"  {a['rank']}. {a['num']:>2} {a['nombre']:<12} {a['prob']*100:5.2f} %  {fx} ficha(s){plata}")
    print("  Cobra ~1 de cada 5 sorteos: 60 fichas si sale 1-3, 30 si sale 4-5. Cuesta 8 fichas.")
    print("\nTop-15 ponderado (alternativa, ≈ +6 %, cobra ~1 de cada 2):")
    print("  " + ", ".join(f"{a['num']} {a['nombre']}({PONDERADO[a['rank']-1]})" for a in orden[:15]))
    print("  23 fichas: si sale 1-3 +67, 4-5 +37, 6-15 +7; si no sale ninguno −23.")
    if banca is not None:
        if ficha and ficha >= 1:
            print(f"\nCon banca {banca:g} $: ficha de {ficha} $ -> {8*ficha} $ por sorteo en el Top-5 escalonado.")
        else:
            print(f"\nCon banca {banca:g} $ la ficha prudente (1/4 de Kelly) queda por debajo de 1 $. Opciones:\n"
                  "  - Prudente: solo el Top-3, 1 $ a cada uno (3 $ por sorteo).\n"
                  "  - Para intentar doblar la banca: Top-3 con 3 $ a cada uno (9 $ por sorteo), hasta\n"
                  "    llegar al doble o quedarte sin la banca. Más riesgo: ~2 de cada 10 veces se pierde entera.\n"
                  "  - El Top-5 escalonado con fichas de 1 $ pide ~1.850 $ de banca para ser prudente.")


if __name__ == "__main__":
    main()
