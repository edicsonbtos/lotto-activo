# Pruebas ciegas del motor nuevo S2 (2026-10-06/07): veredicto según el pre-registro
Candidato congelado: S2 (LightGBM, mezcla de expertos normal/relajado, C-90) y S2+PROD w = 0,75. Nada se reajustó.

| prueba | resultado | estado |
|---|---|---|
| C1 ANTIGUO 2024-03..2025-06, reentreno mensual (T1) | mezcla +7,4 mbits [+1,5; +13,4]; plata +1,0 pp [−4,5; +6,4]; S2 solo −1,6 | PASA justo (la plata cumple solo por la estimación puntual; ρ calibrado con datos posteriores, así que es algo optimista) |
| C2 transferencia a RD Internacional (T1) | S2-RD −4,2 mbits [−10,8; +2,4] contra el motor de RD | NO PASA |
| C3 batería Turing (T2) | sin fuga (placebo y fuga temporal pasan); falla el retraso de 1 mes (la ventaja cae un 74 %) y el rasgo de ruido (puesto 6 de 38) | NO PASA |

**Veredicto global (regla pre-registrada: REAL solo si pasan C1 y C3): NO CONFIRMADO.**
- S2 no tiene fuga y es complementario a PROD: la mezcla suma +7 mbits incluso en el régimen antiguo. Es la señal positiva más
  limpia de la sesión.
- Pero su ventaja depende del último mes de datos: con un hueco de 1 mes cae un 74 %. Además sobreajusta (un rasgo de ruido
  pesa más que 32 de los 37 rasgos reales) y no se transfiere a RD.
- En plata no supera a la jugada actual de forma demostrable en ningún tramo ciego.
- Si se quiere seguir con S2: sombra en vivo, reentreno mensual estricto, más regularización (quitar rasgos débiles,
  feature_fraction) y juzgarlo en plata contra la jugada actual. No entra en la jugada.
