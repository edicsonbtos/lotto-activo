# ag07 — PREREGISTRO (escrito antes de mirar PRUEBA) — 2026-10-03

## Hipótesis
"La regla del primer sorteo es cruzada entre juegos del mismo operador": el ganador del primer sorteo de Lotto Activo
(LA, 9:00 hasta 2024-11-27, 8:00 después) esquiva (o favorece) el animal del PRIMER sorteo de hace k días de otro juego:
- RD Internacional (8:30, `rdint_hist.csv`, desde 2023-09; respaldo `oficial_multi.csv` juego 2).
- LARD (juego 3 de `oficial_multi.csv`, 8:00, desde 2025-07-01). Dev LARD = 2025-07-01..2025-12-19.
- La Granjita (8:00), Selva Plus (8:15), Guácharo (8:00) desde 2026-04-13: SOLO descriptivo (mapeo por nombre de animal;
  animales fuera de los 38 se descartan). Toda su muestra cae en prueba/vivo de LA: no decide nada.
- Reverso (solo descriptivo): ¿RD 8:30 de hoy esquiva LA primer sorteo de ayer? Y, como contexto, ¿cada juego esquiva
  su propio primer sorteo de ayer? (conteos crudos vs 1/38).

## Métrica
Para cada fila de primer sorteo de LA (tramo dev / prueba / vivo de base8.npz) y una característica X (animal a):
O = #(y == a), E = sum P_aj[t, a] (motor con el ajuste de producción). O/E con IC de Poisson exacto; p unilateral Poisson
en la dirección elegida en dev. "Ayer" = fecha calendario − k. Si falta el sorteo del otro juego, la fila no cuenta.
Ganancia: multiplicador m = (O_dev + 0,5)/(E_dev + 0,5) ajustado SOLO en dev, aplicado a P_aj[t,a] y renormalizado;
mbits por primer sorteo = 1000·mean(log2(q[y]/P_aj[y])), IC bootstrap por días (2000 réplicas).

## Rasgos explorados en DEV (familia = 6 contrastes de selección)
RD primero de hace k=1,2,3 días; LARD primero de hace k=1,2,3 días. (RD: dev en dos eras, 9:00 y 8:00; LARD solo era 8:00
de dev, 2025-07-01..12-19, ~150 filas.) Además se mira, sin contar como candidato, el conteo crudo en 'cal' (RD) contra 1/38.

## Regla de selección (fijada antes de correr dev)
Pasa a prueba como máximo 3 rasgos con p unilateral dev < 0,05/6 ≈ 0,0083 (Bonferroni de la familia dev) y, para RD,
mismo signo en las dos eras de dev. Si ninguno cumple, se envía como mucho el mejor (p dev < 0,05) solo para dejar
constancia, o ninguno. En prueba: CONFIRMADO si p unilateral < 0,0017 y mismo signo en las dos eras de dev;
PROMETEDOR si p < 0,05; si no, NULO. Vivo solo se reporta.

## Decisión tras DEV (anotada antes de cualquier mirada a prueba de RD/LARD)
Ningún rasgo cumple p dev < 0,0083 ni siquiera p < 0,05 (mejor: LARD k=1, O/E 0,23, p = 0,066, n = 159; RD k=1 y
RD k=3 cambian de signo entre eras). Por la regla escrita arriba se envían **0 candidatos a prueba**. La prueba de RD/LARD
queda sin gastar. Veredicto: NULO.
