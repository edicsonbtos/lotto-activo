# Pre-registro: ¿el operador esquiva la fecha y la hora en 2026? (2026-10-01, antes de calcular)

La otra sesión (rama `claude/admiring-babbage-l07kfe`, `top15_70/INFORME.md`) midió esto solo en el
desarrollo (filas < 9357, hasta 2025-12-16). Aquí se replica en **2026**, que ella no tocó.

## Datos
`datos_multiloteria/oficial_multi.csv`, juego 1 (Lotto Activo, API oficial; coincide línea por línea con
`historial.txt` corregido). Primario: fechas >= 2026-01-01. Secundario (solo descripción): 2025-07-01..2025-12-31.

## Medida (sin modelo, con placebos del mismo año)
Para cada sorteo, el "animal objetivo" de cada familia es el animal cuyo código es:
- **D0**: el día del mes (1..31). **D1**: día del mes + 1. **H12**: la hora en reloj de 12 h (8,9,10,11,12,1..7).
- Placebos: los mismos códigos corridos s en {−10..−3} y {+3..+10} (se omiten los códigos fuera de 0..36).
- Tasa = sorteos en que el ganador es el animal objetivo / sorteos válidos. Referencia = tasa media de los
  placebos de esa familia. Razón R = tasa objetivo / tasa placebo. Esperado bajo "nada": R = 1.
- IC por bootstrap de jornadas (4.000 réplicas, semilla 20261001).

## Criterio
Cada familia **PASA** si R < 0,80 y p unilateral (bootstrap) < 0,0167 (Bonferroni 3). Si D0 y H12 pasan,
la señal queda confirmada fuera de muestra en LA. Si ninguna pasa, se considera NO replicada en 2026.
No se hace nada más con estos datos (no se elige ninguna otra variable).

## Lo que no hace
No toca el modelo, la web, el historial ni el marcador. Una replicación aquí NO basta para meter la señal en la
jugada: eso pasa por sombra en vivo y por la regla `gestion_banca.VIGILANCIA`.
