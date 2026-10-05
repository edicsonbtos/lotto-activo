# Sorteo de las 8:00: "ayer como hoy", sombras y más pruebas (2026-10-05)

Pre-registro: `PREREGISTRO.md`, escrito antes de ver resultados. Historial hasta el 2026-09-29 7 PM. Del 30-sep
al 5-oct faltan horas anotadas a mano y la red de la sesión no llega a Railway ni a las fuentes de resultados.
Motor B = `ensamble_v2` walk-forward + `ajuste_primer_sorteo` (producción). 8:00 desde 2024-11-28.
Scripts: `0_walkforward.py` (~50 s), `1_analisis.py` (pre-registrado) y `2_tiempo.py` (exploratorio, escrito después
de ver resultados). Salidas: `salida_*.txt`. Auditoría `revisor-sesgo`: sin fugas. B coincide con producción
(máx. 1,7e-18) y el walk-forward no ve el futuro. Sus correcciones a la redacción están aplicadas aquí.

## Motor B a las 8:00
| tramo | n | Top-1 | Top-3 | Top-5 | Top-15 | mbits |
|---|---|---|---|---|---|---|
| dev | 372 | 5,9 % | 16,4 % | 24,2 % | 62,4 % | +197 |
| prueba | 261 | 3,8 % | 10,3 % | 21,1 % | 50,6 % | +59 |
| vivo (al 29-sep) | 15 | 6,7 % | 20,0 % | 26,7 % | 80,0 % | +311 |

## H1. ¿Las 8:00 tratan lo que salió ayer como si hubiera salido hoy? **RECHAZADA (regla pre-registrada)**
O/E crudo de que el ganador de las 8:00 esté entre los animales que salieron ayer (azar = |Y|/38):
dev 0,49 [0,37; 0,64]; **prueba 1,05 [0,84; 1,31]**; vivo 0,89 (n = 15). Dentro del día, repetir lo de hoy: 0,41-0,46.

Exploratorio (`2_tiempo.py`, cortes por trimestre elegidos después de ver los datos):
- Crudo: 2025-T1 0,20 [0,06; 0,46] y 2025-T2 0,23 [0,08; 0,49]. En esos meses las 8:00 sí esquivaban lo de ayer,
  casi como si fuera de hoy. Desde 2025-T4 queda cerca de 1 (1,15; 1,28; 1,02; 0,85).
- Contra el motor: 2025-T4 2,28 [1,51; 3,32], 2026-T1 1,72 [1,18; 2,41], 2026-T2 1,12 [0,73; 1,66] y
  2026-T3 0,92 [0,58; 1,38]. Desde 2025-T4, juntos: 1,38 [1,13; 1,66]. El motor siguió esquivando lo de ayer cuando
  el operador ya no lo hacía. En 2026-T2/T3 no hay evidencia de que lo siga subestimando, pero el IC es ancho y admite
  hasta un +34 %.
- **Conclusión práctica:** hoy no hay base para sacar de la jugada los animales de ayer a las 8:00. Salen a su ritmo
  normal, o incluso por encima de lo que dice el motor.
- Lo de anteayer sale de más en crudo (dev 1,38, prueba 1,51). El motor ya lo captura casi todo (1,09 y 1,09).
  "Ni ayer ni anteayer" contra el motor: 0,90 y 0,84 (z −2,0 y −2,1). No llega al umbral. Sigue la vigilancia ya abierta.
- Por posición de ayer (8:00 ... 7 PM) contra el motor: ninguna con |z| ≥ 3 en dev.

## H3 (primer sorteo de hace k = 1..10 días) y H4 (retraso): sin candidatas
El máximo |z| en dev es 1,9 (H3) y 1,6 (H4). Hay poca potencia: con E ≈ 10 por k solo se detectaría un O/E ≈ 2.
H4 "retraso 1-12" es el mismo conjunto que "salió ayer" en las 639 mañanas, así que su z = +2,4 en prueba NO es una
señal aparte. H3 k = 1 es lo mismo que "ayer hora 0". Que k = 1 y k = 3 salgan calibrados en dev es tautológico:
ahí se ajustaron. En prueba hay poca información (1/1,5 y 12/12,2).

## H2. Sombras a las 8:00 — **una sola señal, ya mirada en prueba, no es ciega**
| tramo | n | C − B (mbits, **IC 90 %**) | C8 − C (IC 90 %) | ventana O / E(C) |
|---|---|---|---|---|
| dev | 372 | +12,6 [+7,4; +17,8] | +15,7 [+4,2; +27,3] (0,59 ajustado aquí) | 12 / 25,0 |
| prueba | 261 | +11,3 [+5,0; +17,7] | +13,1 [−1,1; +27,3]; al 95 %: [−3,8; +30,1] | 9 / 17,1 = 0,53 [0,24; 1,00] |

- El 94 % de C − B a las 8:00 viene de los multiplicadores día−1, día y día+1, es decir, de la misma ventana
  (+10,6 de +11,3 en prueba). Día+2, hora y mes aportan +0,7 [−2,2; +3,3]. "C" y "C8" NO son dos confirmaciones:
  son la ventana dos veces, sobre los mismos 9 aciertos que el enjambre ya contó el 2026-10-03 (+24,6 mbits).
- p unilateral de la ventana en prueba ≈ 0,024 sin corregir. La auditoría del enjambre dio un p honesto ≈ 0,1, porque
  la ventana iba al revés antes de 2024-T3 (O/E 1,4-1,7). Que esté por debajo de 1 "en todos los trimestres desde
  2025" no es evidencia nueva: esos trimestres son dev, donde se eligió, o la prueba ya mirada.
- C − B a las 8:00 (+11,3 ± 7,6) no se distingue del de otras horas en prueba (+8 a +10 ± 8).
- En vivo (n = 15) hay 0 aciertos en la ventana. La ganancia que sale ahí es solo renormalización: no informa nada.
- Las dos miradas a prueba quedan anotadas en `herramientas/registro_final.jsonl`.

## Qué queda para subir las 8:00
- La única palanca con algo de respaldo es la ventana de fecha (C8) a las 8:00. Si lo de prueba se mantuviera, daría
  unos +24 mbits por mañana y ~+2 pp de Top-5, y el Top-15 casi no se movería. Pero no es significativa al 95 % y
  ya no hay tramo ciego para confirmarla. Su sombra en vivo corre desde el 2026-10-04. **Encenderla antes de tiempo
  rompe el pre-registro y le toca decidirlo al usuario.** No se cambió nada en producción.
- Excluir lo de ayer, perfiles de k días y retraso: nada, o peor.
