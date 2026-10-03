# ag02 — Pre-registro: "Calendario en el primer sorteo" (escrito 2026-10-03, ANTES de mirar el tramo de prueba)

## Hipótesis
La esquiva del operador al "número del calendario" (día del mes, hora 12 h) ya se conoce para todas las horas y no está
en P_aj. H: en el PRIMER sorteo del día esa esquiva es más fuerte, distinta o adopta otras formas
(día±1, mes, día+mes, año 2 dígitos, número de la hora del primer sorteo [8 en era 8:00, 9 en era 9:00], día de la
semana 1-7, día del año mod 37).

## Métrica
- O/E del animal-objetivo en primeros sorteos contra P_aj (O = aciertos del objetivo, E = suma de P_aj[objetivo]),
  IC de Poisson exacto; por era de dev (9:00: 263 filas; 8:00: 372 filas).
- Especificidad: el mismo rasgo en las demás horas (contra P, por hora, filas no-primeras) y contraste de interacción
  O1 | O1+O2 ~ Binomial(O1+O2, E1/(E1+E2)) (primer sorteo vs. resto).
- Conteos crudos en 'cal' (183 primeros sorteos 9:00) contra 1/38, solo descriptivo.
- Candidato a prueba = multiplicador m sobre P_aj en el primer sorteo, m = (O+0,5)/(E+0,5) ajustado SOLO en dev.
  Ganancia en mbits por primer sorteo con IC bootstrap por días.
- Para que el aporte sea ESPECÍFICO del primer sorteo, en prueba cada candidato de tipo "día del mes / hora" se juzga
  contra la línea base P_aj × (multiplicador general del mismo rasgo ajustado en dev en las horas NO primeras).
  (Ver sección de candidatos: se completa tras dev y antes de abrir prueba.)

## Regla de selección (dev)
Se miran todos los rasgos listados; pasan a prueba como mucho 3, con |log O/E| grande, mismo signo en ambas eras de dev
y p (dev combinado) < 0,01 tras contar los contrastes mirados. Si ninguno cumple, se envían a prueba como mucho los
2 mejores con mismo signo en ambas eras (para documentar) o ninguno.

## Umbrales en prueba (fijados por el brief)
CONFIRMADO: p unilateral < 0,0017 en la dirección de dev y mismo signo en las dos eras de dev. PROMETEDOR: p < 0,05.
Si no, NULO. Vivo (15 filas) solo se reporta.

## Adenda tras dev (escrita ANTES de abrir prueba) — candidatos
Miradas en dev: 15 rasgos × (1º por era, 1º total, resto, interacción, cal) + 4 controles cruzados de la hora +
3 ventanas + 17 corrimientos placebo + 4 periodos ≈ 45 contrastes (salida_dev.txt, salida_dev2.txt).
Lo que quedó: la ventana del día {D−1, D0, D+1} en el primer sorteo: dev 25/52,0 = 0,48 (9:00: 0,60; 8:00: 0,40)
frente a 0,74 en las demás horas (interacción unilateral p = 0,018; NO sobrevive a ~45 contrastes por sí sola).
Hora del primer sorteo (8 / 9), mes, año, día de la semana, día del año: nada específico (descartados).
Advertencia: en 'cal' (183 primeros 9:00, 2023-09..2024-03) la ventana da 1,66 contra azar (al revés).

Multiplicadores (todos ajustados SOLO en dev, suavizado m = (O+0,5)/(E+0,5)):
- Generales g_s, s ∈ {−1, 0, +1}: filas NO primeras de dev contra P. B_gen = P_aj × g (renormalizado) en el 1º.
- C1 (ESPECÍFICO, primario): q1 = B_gen × x sobre los 3 animales de la ventana, x ajustado en primeros de dev contra
  B_gen. Estadístico en prueba: O de la ventana vs E bajo B_gen en los 261 primeros sorteos; p = P(Poisson(E) ≤ O).
- C2 (práctico, no específico): q2 = P_aj × m sobre la ventana, m ajustado en primeros de dev contra P_aj.
  Estadístico: O vs E bajo P_aj; p = P(Poisson(E) ≤ O). Si C2 pasa y C1 no, es la señal general ya conocida.
Se reporta además mbits (q vs base) con IC bootstrap por días (B = 4000), Top-5/Top-15 y retorno por ficha (pago 30).
