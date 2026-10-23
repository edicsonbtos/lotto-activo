# Auditoría del archivo de pronosticadores — 2026-10-23

Pendiente 7a de `investigacion/2026-10-15/RETOMAR.md`: ¿el archivo por fecha de lotoven y loteriadehoy es lo que se
publicó esa mañana, o se rehace después de los sorteos? Si se rehiciera, el O/E < 1 del estudio del 15-oct sería falso.

Método (`auditar.py`):
1. Página guardada por Railway entre 6:00 y 7:55, antes del primer sorteo
   (`/datos_publicados/<fecha>/<fuente>.html`, desplegado en a8e38c6).
2. Archivo de esa fecha bajado hoy (POST fecha=...).
3. Copia del archivo bajada el 15-oct, donde la hay.

El parser es el mismo del estudio original. Son 22 días (2026-10-02..10-23), con 2 fuentes y 2 juegos: 88 comparaciones.

## Resultado
- **loteriadehoy: 44/44 idénticas** (LA y RD).
- **lotoven: 42/44 idénticas.** Las 2 diferencias (LA 08-oct y RD 18-oct) son un número repetido en el archivo
  ("3, 3" y "22, 22"). El conjunto de animales es el mismo. No hay animales quitados ni agregados que luego salieran.
- La página de la mañana corresponde siempre a la fecha del día.
- La copia del 15-oct coincide con el archivo de hoy en los días que comparten.

**Veredicto: el archivo NO se rehace.** Lo que esas webs muestran para una fecha es lo que publicaron esa mañana, antes
del primer sorteo. Se descarta la explicación de la contaminación del O/E < 1 (0,86 en confirmación 1 y 0,70 en vivo).
Límite: solo se pudo comprobar en 22 días de 2026. Que 2024-2025 tampoco se haya rehecho se infiere, pero no se verificó.

## Siguiente paso (decisión del usuario, toca producción)
Pendiente 7b: poner p × 0,86 sobre los animales publicados (unión lotoven ∪ loteriadehoy) en **sombra**, junto con la
exposición a la fecha, y decidir con la regla preregistrada a ~140 días de vivo (E ≈ 350). Lo propio de los pronosticadores
sin la fecha (O/E ≈ 0,92) no se puede confirmar en un plazo razonable (2-4 años).
