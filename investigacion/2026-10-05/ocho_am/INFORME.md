# Sorteo de las 8:00: "ayer como hoy", sombras y más pruebas (2026-10-05)

Pre-registro: `PREREGISTRO.md`, escrito antes de ver resultados. Historial hasta el 2026-09-29 7 PM. Del 30-sep
al 5-oct faltan horas anotadas a mano y la red de la sesión no llega a Railway ni a las fuentes de resultados.
Motor B = `ensamble_v2` walk-forward + `ajuste_primer_sorteo` (producción). 8:00 desde 2024-11-28.
Scripts: `0_walkforward.py` (~50 s), `1_analisis.py` y `2_tiempo.py` (~10 s). Salidas: `salida_*.txt`.

## Motor B a las 8:00
| tramo | n | Top-1 | Top-3 | Top-5 | Top-15 | mbits |
|---|---|---|---|---|---|---|
| dev | 372 | 5,9 % | 16,4 % | 24,2 % | 62,4 % | +197 |
| prueba | 261 | 3,8 % | 10,3 % | 21,1 % | 50,6 % | +59 |
| vivo (al 29-sep) | 15 | 6,7 % | 20,0 % | 26,7 % | 80,0 % | +311 |

## H1. ¿Las 8:00 tratan lo que salió ayer como si hubiera salido hoy? **RECHAZADA hoy (fue cierto hasta 2025-T3)**
O/E crudo de que el ganador de las 8:00 esté entre los animales que salieron ayer (azar = |Y|/38):
- dev 0,49 [0,37; 0,64]; **prueba 1,05 [0,84; 1,31]**; vivo 0,89. Dentro del día (9:00 a 7 PM, repetir lo de hoy): 0,41-0,46.
- Por trimestre: 2025-T1 0,20 y 2025-T2 0,23 (igual que "dentro del día") → 2025-T3 0,51 → **2025-T4 1,15, 2026-T1 1,28,
  2026-T2 1,02, 2026-T3 0,85**. El operador dejó de hacerlo hacia octubre de 2025.
- Contra el motor: 1,07 en dev y 1,24 en prueba. El motor tardó en adaptarse (2025-T4: 2,28), pero en los dos
  últimos trimestres ya va bien (1,12 y 0,92).
- **Conclusión: hoy las 8:00 NO ignoran ni esquivan lo de ayer.** Sacar de la jugada los animales de ayer
  quitaría ~28 % de los animales, que hoy salen a su ritmo normal. Eso empeoraría la jugada.
- Lo de anteayer sale de más en crudo, y en todos los trimestres (1,06-1,66; dev 1,38, prueba 1,51). El motor ya lo
  captura casi todo (O/E 1,09 y 1,09). "Ni ayer ni anteayer" contra el motor: 0,90 y 0,84 (z −2,0 y −2,1).
  No llega al umbral pre-registrado. Es la misma señal débil que ya estaba en vigilancia ("salió ayer o anteayer").
- Por posición de ayer (8:00 ... 7 PM) contra el motor: ninguna con |z| ≥ 3 en dev. Sin candidatas.

## H3. Primer sorteo de hace k días (k = 1..10): sin candidatas
Ninguna con |z| ≥ 3 en dev. Con B, k = 1 y k = 3 quedan bien calibrados (el ajuste en producción funciona).

## H4. Retraso del animal: sin candidatas
Ningún tramo con |z| ≥ 3 en dev.

## H2. Sombras a las 8:00 (el tramo de prueba YA se había mirado para la ventana; no es ciego)
| tramo | n | C − B (mbits, IC 90 %) | C8 − C | ventana O / E(C) | Top-5 B → C → C8 | Top-15 B → C → C8 |
|---|---|---|---|---|---|---|
| dev | 372 | +12,6 [+7,4; +17,8] | +15,7 [+4,2; +27,3] (ajustado aquí) | 12 / 25,0 | 24,2 → 25,0 → 25,5 % | 62,4 → 64,5 → 65,6 % |
| prueba | 261 | **+11,3 [+5,0; +17,7]** | +13,1 [−1,1; +27,3] | 9 / 17,1 | 21,1 → 21,8 → 23,4 % | 50,6 → 51,3 → 51,0 % |
| vivo | 15 | +28,3 | +39,1 | 0 / 1,0 | sin cambio | sin cambio |

La ventana {día−1, día, día+1} queda por debajo de lo esperado en los 7 trimestres desde 2025 (O/E 0,18-0,85).
Es la señal más estable a las 8:00, pero su tramo de prueba ya no es ciego. La única confirmación limpia es la sombra
en vivo desde el 2026-10-04 (pre-registro: decide con n = 730 mañanas, unos 2 años).

## Qué se puede hacer para subir las 8:00
- Encender **C8 solo a las 8:00** (corrección fecha/hora + ventana × 0,59). Lo esperado, si se mantiene lo de prueba:
  unos +25 mbits por mañana y ~+2 pp de Top-5. El Top-15 casi no se mueve. **Romper el pre-registro le toca al
  usuario.** No se cambió nada en producción.
- Lo demás (excluir lo de ayer, perfiles de k días, retraso) no da nada o empeora.
