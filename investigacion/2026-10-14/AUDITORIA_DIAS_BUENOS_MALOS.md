# Reauditoría y días buenos/malos — 2026-10-14

Datos: producción en Railway (`/api/mesa`, `/api/salud`, `/api/sombra*`) a las 21:30 de Caracas. Son 374 sorteos entre 2026-09-13 y 2026-10-14 a las 19:00. Tienen puesto 349 y probabilidades congeladas 310.
Hubo cuatro subagentes: días buenos, días malos, control estadístico y revisor adversarial. Sus scripts están en el scratchpad de la sesión y no se modificó nada del motor.

## 1. Estatus de avance

| Área | Estado |
|---|---|
| Railway | Activo. El despliegue `f2f1769` es del 8-oct. El auto-registro funciona ("no falta ningún resultado"). Responde lento (~4-14 s por página) y corta respuestas JSON cuando hay carga. |
| Tests locales | 97/97 pasan. |
| Código sin commit | `servidor.py`, `static/` y `oficial_multi.csv` tienen cambios sin commit y SIN desplegar. Entre ellos `?modelo=sombra` en `/api/mesa`: producción lo ignora, así que el detalle sorteo a sorteo de ag12 no se puede extraer. |
| Marcador LA (349) | Top-15 46,7 % (referencia ciega 49,5 %). Top-5 16,9 % (19,4 %). Top-2 6,9 % (8,5 %). Todo compatible con la referencia (p 0,25-0,34). |
| Señal | +108,6 mbits por sorteo, IC90 [73,6; 143,6]. El modelo esperaba +101,6: está bien calibrado y la ventaja sobre el azar es real. |
| Plata (pago 30x) | Top-5 escalonado +3,2 % (+88 u). Top-3 plano +6,0 %. Top-2 +3,2 %. Top-15 ponderado −3,4 %. Top-15 plano −6,6 %. |
| RD Internacional (255) | Top-5 escalonado +4,4 %, Top-15 ponderado +0,3 %. |
| Motor en sombra ag12 (226) | Top-15 52,2 % contra 46,9 %. Δ +16,9 mbits, IC90 [−7,6; 41,4]. **Todavía no pasa** la regla preregistrada. Si el efecto se mantiene, pasaría hacia los ~470 sorteos (unas 3 semanas). |

## 2. Días buenos y malos (Top-15)

**Veredicto: es varianza normal; no existen días buenos o malos como fenómeno.**

- Los aciertos por día tienen menos dispersión que la que el propio modelo predice (φ = 0,65; χ² = 26,1 con 30 gl, p = 0,67).
- Se esperaban unos 6 días malos (≤ 4/12) y hubo 6. Se esperaban unos 5 días ≥ 8 y hubo 2.
- No hay racha: un día no predice el siguiente (r = −0,04) y la mañana no predice la tarde (r = −0,36, p = 0,08, y además en sentido contrario).
- La concentración del pronóstico no anticipa nada: la masa del Top-15 varía de 0,45 a 0,59 y no predice el día (r = −0,02).
- Ninguna hora, día de semana ni versión del motor es distinta después de corregir por múltiples pruebas.

**Por qué un día sale bueno.** El Top-15 son casi siempre animales que salieron hace 1-5 días y que no han salido hoy. Según cuándo salió el ganador por última vez, el acierto fue:

| Último salida del ganador | Acierto Top-15 |
|---|---|
| Hoy mismo (repetido) | 0 % |
| Ayer | 65 % |
| Hace 2-5 días | 53 % |
| Hace 6-12 días | 12 % |
| Hace 13 días o más | 0 % |

Los días buenos (09-22, 10-03, 10-05, 10-10, 10-11, 10-13) casi no tuvieron repetidos del día: 1,4 % contra 5,7 % del resto. Además, el ganador cayó más arriba dentro de ese grupo de recientes. Esto se sabe solo después del sorteo.

**Por qué un día sale malo.** De los días malos (09-16, 09-17, 09-23, 09-28, 10-08, 10-09), 4 son azar puro. 09-16 y 09-17 fueron azar más fallas de operación: el pronóstico no se congelaba si nadie abría la web, y hubo el dato corrupto que se describe abajo.

**Qué replicar.** La estructura que ya está en el motor (recientes, sin repetidos del día) funciona igual en días buenos y malos. Lo único que vale vigilar es el sábado: en el historial largo rinde +0,5 aciertos por día, pero en vivo solo hay 4 sábados (p = 0,43) y se midió con una regla simple, no con el ensamble. Hay que dejarlo en observación unos 20 sábados sin cambiar nada.

## 3. Hallazgos operativos (verificados contra la fuente oficial)

1. **El historial de producción tiene 5 resultados mal anotados**, y el motor sigue calculando con ellos hoy:

   | Fecha y hora | Anotado | Oficial |
   |---|---|---|
   | 09-16 10 AM | 15 | 0 Delfín |
   | 09-16 11 AM | 34 | 15 |
   | 09-16 12 PM | 12 | 34 |
   | 09-18 9 AM | 34 | 30 Caimán |
   | 10-07 5 PM | 23 Cebra (repite la de las 4 PM) | 32 Ardilla |

   Lo confirmaron tres fuentes: la API oficial, `oficial_multi.csv` y la copia local. El efecto sobre el Top-15 es casi nulo (ningún acierto cambia), pero desde el 10-07 el Top-15 cambia 1-2 animales en casi todos los sorteos, y el registro de las 5 PM hunde las métricas de esa hora (−1775 mbits).
2. **Causa probable:** `registrar(num)` escribe en el siguiente hueco libre sin saber la hora. Además, `POST /registrar`, `POST /` y `/deshacer` no piden ninguna clave (servidor.py:2201-2207). Un doble envío o un tercero corre el historial.
3. No hay alarma diaria que compare con la fuente oficial.
4. El certificado de lottoactivo.com está vencido. El scraper sigue, validando contra el tablero.
5. Faltan 11 sorteos sin pronóstico congelado, casi todos antes del 09-22. Los días con n = 10-11 no se pueden comparar directamente con los demás.

## 4. Recomendaciones (ninguna aplicada)

1. Corregir esas 5 líneas una sola vez con un JSON auditado (como `corregir_historial()`) y marcar los registros afectados en el marcador.
2. Pedir clave en las rutas POST y que `registrar` reciba fecha y hora explícitas: rechazar si no corresponden al hueco.
3. Agregar un chequeo nocturno contra `fuente_oficial` que avise si hay diferencias.
4. Hacer commit y desplegar los cambios locales pendientes, o descartarlos.
5. No tocar el modelo ni la apuesta por días buenos o malos. Seguir con Top-5 escalonado y dejar que ag12 llegue a su corte preregistrado.
