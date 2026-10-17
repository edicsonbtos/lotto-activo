# Retomar — enjambre 2026-10-15

Punto de partida: `investigacion/2026-10-14/REAUDITORIA.md`. Los días buenos y malos del Top-15 son azar: no hay régimen que se pueda replicar. El Top-15 pierde plata.

Se lanzaron 4 agentes con el protocolo `lotto-nueva-idea`:

| Carpeta | Pregunta | Resultado |
|---|---|---|
| `mas_jugado/` | Otros indicadores de lo más jugado (invertido, terminal, quincena, festivos…) | **No pasa nada (0/10).** M5, el invertido del último ganador, y M6, su terminal, valen ≈ +1 mbit: solo vigilancia o réplica en RD. |
| `rd_senales/` | Portar a RD el "primero de ayer" y el esquive de fecha y hora | **No pasa.** Confirmación −1,3 mbits [−4,6; +2,0]. La confirmación 2026-04-13..09-13 quedó gastada para esta idea. |
| `sombras/` | ¿Se puede promover ag12 o la exposición? | **Todavía no.** ag12: +16,9 mbits, z = 1,14; la mirada preregistrada es el 14-dic (P(pasa) 0,33–0,65). En plata, ag12 haría Top-15 ponderado +12,5 % y Top-5 +27,8 %, pero se concentra del 3 al 14 de octubre. La regla RD en el Top-15 se mantiene: sus −30 u son un solo sorteo. |
| `pronosticadores/` | ¿El operador esquiva los animales que publican los pronosticadores? | **Lo único prometedor.** Hay archivo histórico en lotoven y loteriadehoy (desde 2022). O/E: desarrollo 1,00; confirmación 1 (2025) 0,86 [0,80; 0,92]; vivo 0,70 [0,51; 0,92]; RD 0,97. Más de la mitad es la fecha, ya conocida; lo propio de los pronosticadores queda en 0,92 en confirmación y 0,64 en vivo. Corrección p×0,86 = +11 mbits [+1; +21] en vivo (exploratorio). Riesgo: que el archivo haya sido rehecho después de los sorteos. |

## Pendientes concretos
1. Subir (commit y push) el cambio local de `servidor.py` y `static/`, que expone ag12 sorteo por sorteo (`/api/mesa?modelo=sombra`). Hoy está sin desplegar.
2. Guardar las 38 probabilidades del pronóstico congelado de RD (hoy solo guarda el Top-15), para poder medir RD en mbits en vivo.
3. Registrar el motivo cuando falla `sombra_de` (el 2-oct a las 8:00 quedó sin sombra).
4. Definir `RESPALDO_CLAVE` en Railway y revisar la facturación.
5. El 14-dic-2026: decisión de ag12 con la regla preregistrada. Ojo: el plan de dos miradas tiene un error de tipo I real ≈ 8,2 %.
6. Revisar 11 resultados de RD de marzo de 2026 que no coinciden entre el archivo oficial y el histórico local.
7. **Pronosticadores (decisión del usuario):** (a) auditar el archivo comparándolo con los HTML que Railway guarda de 6:00 a 7:55 desde el 2-oct (hace falta exponerlos: toca servidor.py); (b) si coinciden, poner p×0,86 en sombra junto con la exposición y decidir a unos 140 días.

## Cierre 2026-10-16
- Hecho: ag13 en sombra desplegado (9e5cf66). **ag12 + RD es el motor principal** de la pestaña Lotto Activo (6075aae); el ensamble sigue en «Modelo anterior» y en el marcador. Volver atrás: `MOTOR_PRINCIPAL=ensamble` en Railway.
- Hecho: pendiente 1 (`/api/mesa?modelo=sombra` desplegado) y pendiente 2 (RD guarda las 38 probabilidades, 47377f2).
- 10/12 en el Top-15 del ensamble el 16-oct: azar (≈1 de cada 56 días).
- RD: ninguna pieza de ag13 pasa allí; sigue con rdint_b1.
- Siguen abiertos: 3, 4, 5 (ag12 el 14-dic), 6 y 7 (auditar el archivo de pronosticadores, necesario para confiar en ag13).
