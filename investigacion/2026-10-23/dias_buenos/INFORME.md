# ¿Se pueden replicar los días buenos del Top-15 y evitar los malos? — 2026-10-23

Pregunta del usuario: replicar los días en que el Top-15 acierta bien, evitar los días malos y saber qué hizo el motor esos días.
Datos: desarrollo LA [2000, 9357) con el ensamble walk-forward (636 días) y el vivo congelado de `/api/mesa` (2026-09-13..10-23).
Scripts: `dias.py`, `que_hizo.py`, `calib_hueco.py`, `vivo.py`; salidas `salida_*.txt`. Nada toca el tramo de prueba ni producción.

## Resultado
1. **No existen días buenos/malos como estado.** Aciertos por día φ = 1,07 contra 1,00 del azar [0,90; 1,10], P = 0,10.
2. **Qué pasa en un día bueno:** el motor hace lo mismo todos los días (entropía 5,13 y masa Top-15 0,53 iguales en
   días buenos y malos). Lo que cambia es de qué grupo saca el operador:
   - Día bueno: el 58 % de los ganadores había salido hace 1-2 días; repetidos el mismo día, 3 %.
   - Día malo: solo el 41 % había salido hace 1-2 días; repetidos, 9 %.
   - Acierto del Top-15 por hueco del ganador:

     | Hueco del ganador | Desarrollo | Vivo |
     |---|---|---|
     | 1-2 días | 72 % | 75 % (141/189) |
     | 3-5 días | 35 % | 31 % |
     | Más de 5 días | 21-45 % | 10 % |
     | Ya salió hoy | 9 % | 0 % (0/19) |
3. **No se puede anticipar qué grupo tocará:**
   - Los días "fríos" no se agrupan: φ = 1,05, P = 0,18.
   - Una mañana fría no anuncia una tarde mala (r = +0,07).
   - El día anterior no sirve (r = −0,08).
   - La masa prevista del día va al revés (r = −0,10), como ya pasó con el "calor de la lista" (hilo 6).
4. **Reglas de "parar el día"** (Top-15 plano, desarrollo):

   | Regla | Retorno por ficha |
   |---|---|
   | Jugar siempre | +6,1 % |
   | Parar tras 3 fallos seguidos | +6,0 % |
   | Seguir solo si el día va ≥ 40 % | +6,4 % |
   | Jugar solo si el anterior acertó | +7,5 % |

   La última no es significativa: O/E tras acierto 1,01 y tras fallo 0,97. Ninguna regla cambia el retorno.
5. **Calibración por hueco:** O/E entre 0,97 y 1,03 en todos los grupos, salvo "más de 10 días sin salir": O/E 0,83 (z −3,4;
   dev-A 0,91, dev-B 0,77). El efecto es pequeño (≈ 5 % de la masa) y casi nunca entra al Top-15. Candidato a sombra, no a jugada.
6. **Día de la semana en el vivo:** mié 41 % y jue 37 % contra 50 % esperado. El domingo de desarrollo (O/E 0,83) ya falló
   a ciegas (`PREREGISTRO_estrategias_v2.md`). Es ruido mientras no se repita a ciegas.

## Conclusión
El día bueno es suerte del operador al sacar del grupo "salió hace 1-2 días", donde el motor concentra su Top-15.
No se puede ver venir con estos datos. La palanca está en cada sorteo (qué y cuánto se juega), no en elegir días.
