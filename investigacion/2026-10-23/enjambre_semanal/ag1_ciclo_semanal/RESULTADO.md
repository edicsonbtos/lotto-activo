# RESULTADO ag1 — ciclo semanal en todas las horas (LA dev, filas 2000-9356; Bonferroni 6 pruebas, |z| >= 2,64)
Preregistro: `PREREGISTRO.md`. Código: `semanal.py` (`dev` / `rd`), `s5_control.py`. Salidas: `salida_dev.txt`, `salida_rd.txt`, `salida_s5_control.txt`, `salida_*.json`.

| Hip. | O/E total [IC95] | z dev-A | z dev-B | z total | Veredicto | Réplica RD |
|---|---|---|---|---|---|---|
| S1 misma hora −7 d | 0,898 [0,78; 1,03] (182 obs / 203 esp) | −0,26 | −1,78 | −1,48 | NO PASA | no aplica (RD 1,02, z +0,3) |
| S2 misma hora −14 d | 0,946 [0,81; 1,09] | +0,38 | −1,42 | −0,77 | NO PASA | no aplica |
| S3 salió el mismo día de la semana pasada (cualquier hora) | 0,934 [0,90; 0,97] | −1,08 | −4,11 | −3,74 | NO PASA (dev-A no llega a 2) | no aplica (RD 0,99, z −0,7) |
| S4a bolsa semanal, inicio lunes: tendencia | O/E "no salido" 0,970; tercios 1,00 / 0,94 / 0,93 | −0,30 | −1,89 | −1,59 | NO PASA | no aplica |
| S4b bolsa semanal, inicio domingo: tendencia | 0,999; tercios 1,01 / 1,01 / 0,89 | +1,36 | −4,48 | −2,26 | NO PASA (signos opuestos) | no aplica |
| S5 cobertura semanal (48 semanas) | 33,04 animales/semana vs 35,16 simulado | −6,2 | −8,6 | −10,4 | PASA la regla, pero es ARTEFACTO | NO replica (A −0,04; B −5,3) |

Lectura en llano:
- S1 y S2 (misma hora hace 7 o 14 días): nada. Ni siquiera hay exceso ni defecto fiable; el rezago es lo que el ensamble ya espera.
- S3: leve defecto (los animales de ese día de la semana pasada salen ~7 % menos) pero solo en la segunda mitad; la primera mitad es 0,97 (z −1,1). Sin réplica en RD (0,99). No es señal.
- S4 (bolsa semanal): si la casa barajara una bolsa semanal, los animales no salidos saldrían de MÁS al avanzar la semana. Sale lo contrario o nada: O/E 1,00 → 0,94 → 0,93 (lunes) y 1,01 → 1,01 → 0,89 (domingo), tendencias de signo inestable entre mitades. La hipótesis de "empieza la semana debiendo" no se sostiene.
- S5: la regla formal dice PASA (z −10), pero el control `s5_control.py` (post-hoc, fuera de la familia) da el mismo déficit para ventanas de 7 días que empiezan en cualquier día (z −8,5 a −10,4; lunes −10,4). No es nada del ciclo semanal: la simulación fila a fila (que ignora el reciclaje entre días) rinde más animales distintos que la realidad. Además RD no replica (dev-A del RD z −0,04). Descartada; es un nulo mal especificado, no una señal.

Veredicto global: ninguna hipótesis del ciclo semanal pasa y se replica. Sin ciclo semanal ni reinicio semanal detectable en LA con este ensamble.
Qué haría falta para confirmarlo en vivo: nada que valga la pena (no hay señal). Si alguien insiste con S3, haría falta una sombra en vivo con n grande: el efecto es ~−7 % en una máscara de ~3 animales por sorteo, ~0,1 mbit; inmedible.
