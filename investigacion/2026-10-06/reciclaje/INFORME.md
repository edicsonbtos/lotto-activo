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

# Días malos y día de la semana en 2026 (exploratorio; scripts `malos.py`, `semana.py`, `semana2.py`, `plata.py`)
- Domingo 4-oct (reconstrucción): Top-15 5/12 (esperaba 6,1), con 5 reciclados de 12. Siete ganadores llevaban 4 a 8 días
  sin salir (Lapa, Jirafa, Caimán, Mono, Ciempiés, Vaca). Es lo contrario del 5-oct.
- 2026 (271 días): Top-15 medio 5,92/12 (el motor esperaba 6,30). Días malos (≤ 4): 46, 1 cada 6 días, y con un motor
  exacto se esperaban 41 [30-53]. Rachas: 33 sueltos y solo 5 rachas de 2-4 días. Tras un día malo, el siguiente da
  5,91 (igual que el resto, corr +0,08). Los días malos reciclan menos (5,2 contra 6,2 en los normales).
- **Día de la semana: el hallazgo de esta revisión, NO confirmado a ciegas** (se vio mirando 2026, que es prueba + vivo).
  - En 2026, el Top-15 O/E es miércoles 0,85 (z −3,4), jueves 0,82 (z −4,0) y viernes 0,84 (z −3,6). Los demás días:
    0,98-1,05. Se repite en los 3 trimestres de 2026 (0,81; 0,86; 0,85). En dev (2024-25) NO existía: 1,00-1,04.
    Allí el día malo era el domingo (0,82), un patrón que desapareció en 2026.
  - Mecanismo: miércoles a viernes el operador recicla menos de lo que el motor espera (47-51 % contra 53-56 %). Sábado a
    martes recicla más (57,5 contra 55,3).
  - Plata, Top-5 escalonado en 2026: miércoles-viernes −0,5 % por ficha [−13; +12], sábado-martes +29,8 % [+18; +41].
- **Pre-registro en vivo (escrito el 2026-10-06, antes de ver datos posteriores):** del 2026-10-07 al 2027-01-06, Top-15
  O/E contra el motor congelado, miércoles-viernes contra el resto. Se confirma si el O/E de miércoles-viernes queda
  ≤ 0,92 y el IC 90 % por jornadas de la diferencia no toca 0. Se descarta si el O/E de miércoles-viernes es ≥ 0,98. Hasta
  entonces la jugada no cambia.
