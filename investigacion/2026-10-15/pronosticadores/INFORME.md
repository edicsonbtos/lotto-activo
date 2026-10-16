# ¿El operador esquiva los "datos" de los pronosticadores? (2026-10-15)

Protocolo: `PREREGISTRO.md`, escrito antes de bajar el histórico. Scripts: `descargar.py` (archivo de las webs),
`bajar_mesa.py` (motor congelado en vivo), `analizar.py` (prueba preregistrada → `salida.txt`, `resultados.json`),
`explorar.py` y `explorar2.py` (controles hechos DESPUÉS → `salida_explorar.txt`, `salida_explorar2.txt`). No se tocó producción.

## 1. Qué datos hay
- **Railway** (`/api/datos_publicados`): 13 días (02-10 a 14-10), las 6 fuentes bien. La API solo dice si se bajó; el HTML
  no está expuesto (`/respaldo.zip` no lo incluye y pide clave). No sirve todavía.
- **Archivo público por fecha** (lo que da potencia): `lotoven.com/datos/` y `loteriadehoy.com/datos/animalitos/` aceptan
  `POST fecha=AAAA-MM-DD` y devuelven los datos de ese día, con archivo desde 2022. Se bajaron 2024-03-01..2025-12-14
  y 2026-09-15..10-14, sin errores. LA: lotoven 652 días (3,2 animales/día), loteriadehoy 669 días (5,5/día). RD Int igual.
- **Pirámide de juegoactivo** (S3): es determinista (sumas de las filas de la pirámide de la fecha), así que se reconstruye
  para cualquier día. Comprobada contra la página del 14-10.
- Sin archivo: la pirámide de tuazar (5 animales, regla desconocida; solo ayer, hoy y mañana), el Top-10 de juegoactivo
  (son frecuencias = "calientes/fríos", ya cerrado) y el foro Sortario (texto libre).

## 2. Resultado preregistrado (U = lotoven ∪ loteriadehoy, Lotto Activo, O/E contra el motor walk-forward)
| tramo | sorteos | obs | esp | O/E [IC95 por jornadas] |
|---|---|---|---|---|
| Desarrollo 2024-03-07..2025-02-03 | 3.653 | 681 | 681,6 | **1,00** [0,93; 1,07] |
| Confirmación 1 2025-02-04..2025-12-05 | 3.564 | 684 | 793,2 | **0,86** [0,80; 0,92] |
| Confirmación 2, en vivo 2026-09-18..10-14 | 310 | 47 | 66,7 | **0,70** [0,51; 0,92] |
| Réplica RD dev 2024-03..2025-06 | 5.712 | 1.063 | 1.097 | 0,97 [0,92; 1,02] |

Por fuente (conf. 1): lotoven 0,71 [0,62; 0,81], loteriadehoy 0,92 [0,85; 0,99], pirámide S3 0,73 [0,67; 0,79].
**Veredicto formal: PASA.** Pero hay que decirlo claro: pasa por la letra. En desarrollo el O/E fue 0,999, que es nulo.
El "misma dirección" se cumple por una milésima. La explotación preregistrada (x = 0,999 del desarrollo) da **+0,04 mbits**: nada.

## 3. Controles exploratorios (hechos después de ver el resultado; no confirman nada)
- **Placebo con los datos de otro día** (d±7, d±14): en conf. 1 da 0,99-1,05. El efecto es del día y no viene de que
  el motor esté mal calibrado para este tipo de animales. En desarrollo, U(d+7) da 1,24: los datos de una semana
  después contienen los ganadores de hoy, o sea que los pronosticadores arman sus datos con resultados pasados.
- **Una parte del efecto es la fecha, que ya se conoce.** Quitando día−1..día+2, mes, hora en 12 h y los números de la
  pirámide (sumas y pares), lo que queda de U da: desarrollo 1,02 [0,92; 1,12], conf. 1 **0,92 [0,84; 1,02]**,
  vivo 0,64 [0,35; 0,95]. La parte de U que coincide con la fecha da 0,80 en conf. 1.
- **Por trimestre**, U crece con el tiempo: 2024-T1/T2 1,1; T3 0,89; T4 0,99; 2025-T1 0,97; T2 0,94; T3 0,86; T4 0,76.
  Va en la misma dirección que la ventana de fecha de las 8:00 (desde 2024-T3) y que lo que se ve en vivo.
- **Pirámide por sumas (S3):** se queda baja aunque se le quiten el día y la hora: desarrollo 0,93 [0,86; 1,00],
  conf. 1 0,76 [0,70; 0,82]. Pero en vivo da 0,96 [0,74; 1,17] y en RD 0,96. Es una variante más de la pirámide, que ya
  estaba cerrada en la ronda 4 (pares 0,84 en dev-B, RD 1,01), y repite su patrón: fuerte en LA 2025, nula en RD.
- **Explotación ajustando x en conf. 1 y aplicándolo al vivo** (el único tramo que no se usó para ajustar):
  p × 0,862 sobre U → **+11 mbits/sorteo [+1; +21]** en vivo (+3,8 [+1,1; +6,5] dentro de la muestra de conf. 1).
  Si se usa solo U sin lo de la fecha (x = 0,924) → +4 [+0,2; +8]. El motor en vivo (ensamble_v2) no tiene la
  corrección de exposición a la fecha, así que parte de esos +11 se solapan con ella (+6 mbits, en sombra).

## 4. Potencia
SE(ln O/E) ≈ 1/√E. U suma unos 2,1-2,7 aciertos esperados por día. Esto es lo que se puede detectar con 80 % de potencia:
O/E ≈ 0,90 con 330 días, ≈ 0,71 con 27 días (es el vivo actual: el 0,70 está justo en el borde).
- Confirmar x ≈ 0,86 en vivo exige E ≈ 350, o sea **~140 días** de sorteos con el motor congelado.
- Lo propio de los pronosticadores, sin la fecha (O/E ≈ 0,92-0,94), exige E ≈ 1.500-2.000, unos 2-4 años: no es viable.
- Los 13 días de Railway no dan potencia. Sirven, en cambio, para auditar el archivo (ver 5).

## 5. Límites
- **No se puede comprobar que el archivo sea lo que se publicó esa mañana.** Si alguna web rehízo días pasados quitando
  los ganadores, saldría justo un O/E < 1 falso. La contaminación típica (meter ganadores) daría > 1, y lo que se ve es
  < 1, que es lo preocupante. Revisión: comparar el HTML que Railway guardó a las 6:00-7:55 (02-10 en adelante) con
  el archivo de esas fechas. Si coinciden, el resultado gana mucho. Hay que exponer o descargar esos HTML; eso toca
  servidor.py y necesita tu OK.
- El desarrollo da nulo. Todo el efecto está en 2025-T3 en adelante. Puede ser que el operador haya cambiado de
  conducta (encaja con la ventana de las 8:00) o puede ser azar con un tramo largo; la réplica en RD no lo apoya (0,97).
- La fecha y los datos se confunden, porque los pronosticadores también usan la fecha.

## 6. Conclusión
El preregistro pasa por la letra, pero la explotación preregistrada vale 0. Lo que sobrevive es esto: **desde mediados de
2025, los animales que publican lotoven y loteriadehoy salen ~14 % menos de lo que da el motor (vivo: ~30 % menos,
con IC ancho)**. Algo más de la mitad se explica por los números de la fecha, que ya se conocían. No hay que meterlo en
producción todavía. Lo que sigue: (1) auditar el archivo contra los HTML de Railway; (2) ponerlo en sombra con p × 0,86
sobre U y decidir a ~140 días de vivo (unos 1.700 sorteos), junto con la sombra de exposición, para no contar dos veces la fecha.
