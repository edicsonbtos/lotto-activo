# ag03 — PRE-REGISTRO (escrito antes de mirar prueba, 2026-10-03)

## Hipótesis
El primer sorteo del día tiene otra distribución marginal (arranque, pre-carga, revisión manual) que el motor `P_aj` no recoge.

## Lo explorado en dev/cal (≈ 95 contrastes; ver explorar_dev.out, dispersion_dev.py, ajuste_dev.out)
- Uniformidad por animal (crudo, cal+dev, n = 818; y por era), 0/00, par/impar, bajo/alto, docenas, columnas, rojo/negro,
  4 y 2 sectores del cilindro americano, 1-31 vs 32-36: contra 1/38, contra las demás horas y contra P_aj (por era).
  Cambio entre la era 9:00 y la 8:00. Dispersión por hora (23 franjas). Popularidad: número = día del mes, día±1, hora 12 h, mes.
- Resultado: NADA de la distribución marginal se separa (min p = 0,12 fuera de "popularidad"; chi² vs motor 25,3 / 37 gl).
  Lo único con p < 0,05 es el número de la FECHA (ya conocido, no exclusivo del primer sorteo; el motor no lo captura).
  Ningún dato de "datos publicados" está en local (solo se guardan en el volumen de Railway desde 2026-10-01).

## Candidatos a PRUEBA (3, una sola vez; filas = primer sorteo, tramo 'prueba', n = 261)
Multiplicadores ajustados SOLO en dev (suavizado +0,5), aplicados a P_aj y renormalizados; archivo `multiplicadores_dev.json`.
- **C1_fecha**: código = día del mes ×0,607 y código = día+1 ×0,661 (ajustados en todas las horas de dev).
  Contraste primario: O de esos 2 objetivos contra E = Σ P_aj; p unilateral P(O ≤ obs | Poisson E).
  Dev por era: 9:00 O/E 0,56, 8:00 O/E 0,39 (mismo signo).
- **C2_fecha_hora**: C1 + código = hora en reloj 12 h (8 o 9 en el primer sorteo) ×0,777. Mismo contraste con 3 objetivos.
  Dev por era: 9:00 0,60, 8:00 0,54.
- **C3_primer_esquiva_mas**: ¿el primer sorteo esquiva la fecha MÁS que las demás horas? Multiplicadores ajustados solo con
  primeros sorteos de dev (día ×0,584, día+1 ×0,368). Contraste primario: O de día y día+1 contra E = Σ q_C1 (motor ya
  corregido con C1); p unilateral P(O ≤ obs). Dev por era: 9:00 0,86, 8:00 0,61.
- Umbral (brief común): CONFIRMADO si p < 0,0017 y mismo signo en las dos eras de dev; PROMETEDOR si p < 0,05; si no, NULO.
- Se reporta además: O/E con IC Poisson exacto, mbits por primer sorteo (bootstrap de días) contra P_aj, Top-5/Top-15 y
  retorno por ficha (pago 30) de Top-5 y Top-15 planos frente a P_aj, con IC por bloques de días. Vivo (15) solo se reporta.
