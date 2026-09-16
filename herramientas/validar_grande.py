# -*- coding: utf-8 -*-
"""Valida el ensamble con mucha muestra (todo el tramo de DESARROLLO: ~7.357
sorteos) en vez de mirar rachas cortas de 10-12 sorteos, que no alcanzan para
concluir nada.

Importante: usa SOLO el tramo de desarrollo [calentamiento, CORTE_FIJO). NO
toca el tramo de prueba (>= CORTE_FIJO) porque ese ya se miró una vez
(2026-09-14, registrado en registro_final.jsonl) y volver a mirarlo para
"validar" contaminaría esa prueba: dejaría de ser una sorpresa para el
modelo. Este script es seguro de correr las veces que quieras, siempre
sobre la misma franja de desarrollo.

Da, además de Top-1/3/5/10 con intervalos de confianza (igual que
lotto_eval.py), el puesto (1-38) que el modelo le dio a cada resultado real,
para ver la forma completa de la distribución y no solo si entró o no en el
Top-3.

Uso:
    python validar_grande.py
"""
import os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import lotto_eval as LE

HIST = os.path.join(os.path.dirname(AQUI), "historial.txt")
MOD_NUEVO = os.path.join(AQUI, "modelos", "ensamble_v2.py")
MOD_VIEJO = os.path.join(AQUI, "modelos", "hazard_actual.py")


def evaluar_desarrollo(ruta_modelo, datos, w, corte):
    modelo = LE.cargar_modelo(ruta_modelo)
    t0 = time.time()
    P = LE.normalizar(modelo.predecir(datos, w))
    seg = time.time() - t0
    P_dev = P[: corte - w]
    y_dev = datos.seq[w:corte]
    m = LE.metricas(P_dev, y_dev)
    orden = LE.rankings(P_dev)
    puestos = np.argmax(orden == y_dev[:, None], axis=1) + 1  # 1..38
    return modelo.nombre, m, puestos, seg


def resumen(nombre, m, puestos, seg):
    t1, t3, t5 = m["top1"], m["top3"], m["top5"]
    print(f"\n== {nombre}  ({seg:.0f} s, n={m['n']})")
    print(f"  Top1  {t1['tasa']*100:5.2f}%  IC95 [{t1['ic95'][0]*100:.2f}-{t1['ic95'][1]*100:.2f}]  "
          f"p={t1['p_valor']:.4f}  (azar 2,63%, umbral 30x 3,33%)")
    print(f"  Top3  {t3['tasa']*100:5.2f}%  IC95 [{t3['ic95'][0]*100:.2f}-{t3['ic95'][1]*100:.2f}]  "
          f"p={t3['p_valor']:.4f}  (azar 7,89%)")
    print(f"  Top5  {t5['tasa']*100:5.2f}%  IC95 [{t5['ic95'][0]*100:.2f}-{t5['ic95'][1]*100:.2f}]  "
          f"(azar 13,16%)")
    print(f"  bits/sorteo: {m['logver']['bits_por_sorteo']*1000:+.2f} mbits  z={m['logver']['z']:+.2f}")
    print(f"  puesto medio: {puestos.mean():.2f}  (azar = 19.5)   mediana: {int(np.median(puestos))}")
    print(f"  estabilidad por cuartos (Top3 %): {[round(x*100,1) for x in m['top3_por_cuarto']]}")
    # histograma simple por deciles de puesto
    bordes = [1, 4, 8, 13, 19, 26, 39]
    etiquetas = ["1-3", "4-7", "8-12", "13-18", "19-25", "26-38"]
    print("  distribución de puestos:")
    for lo, hi, et in zip(bordes[:-1], bordes[1:], etiquetas):
        pct = np.mean((puestos >= lo) & (puestos < hi)) * 100
        barra = "#" * int(pct / 2)
        print(f"    {et:>7}: {pct:5.1f}%  {barra}")


def main():
    datos = LE.cargar(HIST)
    w, corte = LE.particion(len(datos))
    print(f"historial total: {len(datos)} sorteos")
    print(f"desarrollo (lo que se valida aquí): filas {w}-{corte}  =>  n={corte - w} sorteos")
    print(f"prueba (NO se toca): filas {corte}-{len(datos)}  =>  n={len(datos) - corte} sorteos, "
          f"ya evaluada el 2026-09-14")

    for ruta in (MOD_VIEJO, MOD_NUEVO):
        nombre, m, puestos, seg = evaluar_desarrollo(ruta, datos, w, corte)
        resumen(nombre, m, puestos, seg)

    print("\nCon miles de sorteos estos intervalos de confianza son mucho más angostos que los de una "
          "racha de 12: si el Top1/Top3 del ensamble_v2 aquí sigue por encima del modelo viejo y del azar, "
          "es evidencia real y estable, no un espejismo de una buena racha.")


if __name__ == "__main__":
    main()
