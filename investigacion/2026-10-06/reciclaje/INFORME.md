# Días de mucho reciclaje (2026-10-06)
Pre-registro: `PREREGISTRO.md`. Script: `analisis.py` (lee la reconstrucción de producción del scratchpad). Salida: `salida.txt`.
R = ganadores del día que habían salido ayer o anteayer. El 5-oct: R = 9 de 12.

| | dev (372 días) | prueba (261 días) |
|---|---|---|
| R medio real / esperado por el motor | 6,65 / 6,65 | 6,51 / 6,59 |
| Días con R ≥ 9 | 38 (1 cada 10 días) | 23 (1 cada 11 días) |
| Top-15 en días R ≥ 9 | 7,7 / 12 | 7,7 / 12 |
| Top-15 en días R 6-7 | 6,5 / 12 | 5,9 / 12 |
| Top-15 en días R 0-5 | 5,5 / 12 | 5,3 / 12 |

- En los días de mucho reciclaje el motor rinde mucho mejor, y eso se repite igual en la prueba ciega. Es el patrón del
  que vive el motor. En promedio, el motor ya sabe cuánto recicla el operador (esperado ≈ real). Lo que no sabe es
  QUÉ día va a reciclar más.
- **¿La mañana avisa?** No pasa el umbral (|z| ≥ 3 en dev). La tendencia va al revés: con 5-6 reciclados en la mañana,
  la tarde recicla MENOS de lo que espera el motor (2,95 contra 3,27 en dev y 2,47 contra 3,10 en prueba), y el Top-15
  de la tarde baja (O/E 0,93 y 0,86, z −1,6 y −2,3). Una explicación mecánica posible: los animales reciclables ya
  salieron y el operador no repite en el mismo día. Solo vigilancia.
- **¿Al día siguiente sigue?** No. Correlación de R entre días seguidos: −0,11 y −0,06. Tras un día de R ≥ 9, el Top-15
  del día siguiente es 6,9 y 6,3 de 12, contra 6,5 y 5,9 en el resto: diferencias de ruido.
- **Qué esperar:** un día normal, de unos 6 de 12 en el Top-15. El 5-oct fue uno de los días "1 cada 10" en que el
  operador recicla mucho, y no avisa ni antes ni durante.
