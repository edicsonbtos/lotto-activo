# A4 — Cronología y cambio de régimen del "día de la semana" (2026-10-06)
Pre-registro: `PREREGISTRO.md` (escrito antes de calcular). Scripts: `cronologia.py` (pre-registrado) → `salida.txt`;
`extra.py` (exploratorio, escrito después de ver `salida.txt`) → `salida_extra.txt`. Datos: `prod_0605.npz`, 2024-03-07..2026-10-05.
C1 = O/E Top-15 (contra el motor) de mié-vie − resto; C2 = domingo − resto; estratificados por hora.

## 1. Serie (trimestral; la mensual está en `salida.txt`)
| trim | C1 [IC95 por jornadas] | C2 [IC95] |
|---|---|---|
| 2024-T2 / T3 / T4 | +0,02 / −0,00 / +0,07 | −0,07 / **−0,24** / **−0,42** |
| 2025-T1 / T2 | +0,09 / +0,00 | **−0,39** / **−0,20** |
| 2025-T3 / T4 | +0,03 / +0,02 | −0,04 / −0,05 (semestre neutro: χ² 4,3, p 0,64) |
| 2026-T1 / T2 / T3 | **−0,16** [−0,26; −0,07] / **−0,14** [−0,25; −0,03] / **−0,22** [−0,32; −0,12] | +0,06 / +0,17 / +0,13 |
Meses con C1 < 0: 11 de 11 desde 2025-12; 6 de 21 antes. Meses con C2 < 0: 16 de 17 antes de 2025-08; 6 de 15 después.

## 2. Puntos de cambio (máx. |t| por cortes mensuales; p por permutación del orden de las semanas)
- **Domingo malo: termina en 2025-08** (|t| 6,0, p = 0,0005; rango 2025-05..2025-11). Como episodio de 2 cortes: 2024-07..2025-07
  (C2 −0,31 dentro, +0,03 fuera). Empieza cerca de 2024-T3, que es cuando la ventana de fecha cambió de signo. El 8:00 (2024-11-28) cae dentro del episodio y no lo marca.
- **Mié-vie malo: empieza en 2025-12** (|t| 5,6, p = 0,0005; rango 2025-10..2026-03). No hay segundo corte: sigue activo.
  Cae junto a 2025-T4, cuando el 8:00 dejó de esquivar lo de ayer, y junto al fin de dev (2025-12-19). Lo segundo es casualidad del calendario: el motor es walk-forward.
- **No coinciden** (4 meses de diferencia, más que el umbral de 2). Entre los dos hay un semestre neutro (2025-S2), así que no es un cambio único que mueve el día malo.
- Sin motor (reciclaje crudo "ayer o anteayer" contra uniforme sin repetir): en dev, mié-vie reciclaba MÁS que el resto (1,03-1,17 contra 0,91-1,03), y el domingo menos (0,77-0,93 hasta 2025-T2).
  En 2026 se invierte: mié-vie 0,90 / 1,01 / 0,91 contra resto 1,20 / 1,03 / 1,17, y domingo 1,13-1,20. El cambio
  lo hace el operador y no es un artefacto del motor. Sí afecta al motor, porque su rasgo "semana actual/anterior" (`intradia_v2`) y sus pesos se aprendieron con el patrón viejo:
  "ya salió esta semana", mié-vie, era 1,05 en dev y es 0,92 en 2026.
- Por hora: C1 2026 es negativo en 9 de 12 horas y C2 en el episodio en 12 de 12. Ninguno de los dos se explica por una hora suelta.

## 3. Controles (día del mes)
| | dev χ² p_perm | 2026 χ² p_perm | peor grupo 2026 (O/E relativo) |
|---|---|---|---|
| día de semana (7) | 0,0005 | 0,0005 | jue 0,87; bloque mié-vie −0,174, **p_perm = 5·10⁻⁵** (corrige los 7 bloques) |
| tercio del mes (3) | 0,37 | 0,92 | 1-10: 0,99 |
| semana del mes (5) | 0,66 | 0,99 | 8-14: 0,99 |
Los ciclos de mes son planos y no restan valor al hallazgo del día de la semana.

## 4. Conclusión
Criterios del pre-registro: (i) hay cambio, p 0,0005, y los trimestres de 2026 salen todos ≤ −0,14; (ii) no hay tendencia después
del corte (pendiente −0,14/año, p 0,19, que si acaso apunta a reforzarse); (iii) los controles salen planos; (iv) en dev, un solo semestre
(2024-S1, sábado 0,83; P0 = 0,41) tuvo un día malo que no era el domingo. **Según la regla escrita, el régimen es estable y el veredicto es REAL**:
el patrón de 2026 no es ruido, se ve sin el motor y aguanta la corrección por haber elegido el bloque.
**Salvedad adversarial:** la propia historia muestra que el "día malo" del operador ya cambió una vez. El domingo duró unos 13 meses
(2024-07..2025-07), después hubo ~4 meses neutros, y mié-vie lleva ~10 meses. Es un régimen de duración limitada y no
avisa cuándo termina: el anterior terminó sin señal previa. Si se usa, hay que vigilarlo mes a mes (C1 mensual
< 0) y apagarlo cuando dos meses seguidos salgan ≥ 0. El pre-registro en vivo del INFORME de reciclaje (2026-10-07..2027-01-06) sigue siendo el juez.
Además, el descubrimiento fue post-hoc (el enjambre probó muchas cosas). El p de 5·10⁻⁵ corrige el bloque, pero no todas las búsquedas.
