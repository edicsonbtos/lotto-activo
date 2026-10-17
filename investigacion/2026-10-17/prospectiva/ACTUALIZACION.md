# Seguimiento prospectivo — captura 17-oct-2026

Captura de solo lectura de la API pública de producción de Lotto Activo, hecha a las 03:28 UTC (23:28 Caracas del 16-oct). Las respuestas JSON y sus SHA-256 están en `meta_captura.json`; no se cambió producción.

## Evidencia más reciente

- Último sorteo que devuelve la mesa: 16-oct, 7:00 PM, ganador 19 (Chivo). El pronóstico de 08:00 del 17-oct sigue sellado y pendiente.
- `/api/sombra` acumula 250 sorteos para ensamble, Ag12 y Ag12+RD; la rama de exposición tiene 179 sorteos y 15 jornadas.
- En esas 179 filas, ag12+RD+exposición obtiene 125,8 mbits medios frente a 117,1 para ag12+RD: efecto incremental de exposición **+8,70 mbits** (IC90 por jornada: +2,25 a +15,15). Top-5 escalonado no cambia en el resumen (0 pp; IC90 −1 a +1).
- Frente al ensamble sin exposición (100,7 mbits), la diferencia de medias publicada para ag12+RD+exposición es **≈+25,1 mbits**; Top-5 registra 43/179 frente a 36/179 (**+3,91 pp**). Ambos conteos usan n=179 en el mismo bloque. La API no da el IC pareado de esta comparación directa; queda como descripción, no como resultado decisorio.
- La comparación preregistrada de exposición aplicada al ensamble es +9,08 mbits (IC90 +2,57 a +15,59) frente a ensamble sin exposición, con Top-5 −1 pp (IC90 −2 a +1). La API no ofrece el IC pareado de ag12+RD+exposición contra ensamble sin exposición en el resumen.
- Ag13 tiene 24 sorteos válidos de dos jornadas, sin faltantes de pronóstico (`sin_pron_aun=0`). Ag13−ag12+RD+exposición es **−8,49 mbits** (IC90 −14,45 a −2,53); ag13−ensamble es +32,35 (−26,89 a +91,60), demasiado impreciso para inferir mejora. El componente de datos publicados registra O=6, E=5,3, O/E=1,122 (IC95 0,948–1,296), todavía muy lejos de la información esperada E=350.
- El conteo de Ag13 sigue `acumulando (24 de 931)`; esta lectura temprana **no decide ni altera** el preregistro.

## Validez y límites

El marcador productivo solo incorpora pronósticos de días con ambas páginas guardadas antes de las 08:00: `experimentos.py` comprueba `meta.json`, y para estas 24 filas informa que no hay pronóstico pendiente. `/api/datos_publicados` indica ambas fuentes disponibles para los 15 días del 2 al 16-oct. Sin embargo, ese endpoint no expone los HTML originales ni su timestamp exacto; el marcador de producción aporta la comprobación temporal interna, pero no permite una auditoría externa de cada captura.

La diferencia negativa de Ag13 contra ag12+RD+exposición es una señal temprana a seguir, con n=24, no evidencia confirmatoria. Ag14 no figura en la API porque su versión local no se ha desplegado; no se utilizó ni modificó producción. La decisión continúa reservada a los cortes preregistrados (931 sorteos válidos; componente U al alcanzar E=350).

## Fuentes guardadas

- `sombra.json`: marcadores agregados de ensamble, Ag12/RD, exposición y Ag13.
- `mesa_ultimo_ensamble.json` y `mesa_ultimo_sombra.json`: último sorteo resuelto según ambas vistas.
- `datos_publicados.json`: disponibilidad diaria informada por la API.
- `meta_captura.json`: URL, hora de captura y hash de cada respuesta.

## Control antes del sorteo de las 08:00

A las 03:32 UTC del 17-oct (23:32 Caracas del 16-oct), la API de producción aún muestra el sorteo del 17 a las 08:00 como pendiente. Su archivo de ensamble es byte por byte idéntico al ensamble sellado. Al aplicar al pronóstico de Ag12+RD de producción la exposición congelada, su Top-15 coincide con Ag14 sellado y la diferencia máxima entre probabilidades es 1,02×10⁻⁶, compatible con el redondeo de la respuesta de la API. Esto valida consistencia previa, **no es puntuación** ni añade un resultado al experimento. Capturas y huellas: `captura_20261017T033218Z/`; resumen reproducible: `captura_20261017T033218Z/verificacion_sello.json`.


## Evidencia previa al sorteo de las 08:00

A las 03:39:53–03:39:54 UTC (17-oct), se guardaron respuestas crudas de la API de producción y de TuAzar en `captura_pre_sorteo_20261017T033953Z/`. La API devuelve fecha 2026-10-17, 8:00 AM y `winner: null`; la fila de Lotto Activo en TuAzar muestra `-` para el sábado 17-oct a las 08:00. Los SHA-256 están en `meta.json` y se verificaron contra ambos archivos. Esta captura es evidencia de estado previo, no una puntuación. El sorteo está programado para las 12:00 UTC.

## Revisión prospectiva — 2026-10-17, 16:53 Caracas (20:53 UTC)

- Se verificó el sorteo sellado del 8:00 AM: el sitio primario de Lotto Activo muestra la fecha 17/10/2026 pero la captura HTML de resultados no contiene los ganadores (la sección se entrega vacía/dinámica). TuAzar y la API de producción muestran Delfín (0), pero no se cumple el preregistro de resultado confirmado manualmente en una fuente primaria y otra independiente. **No se puntuó ni se añadió a `resultado_fuentes.json`.**
- La revisión encontró un único pronóstico sellado para hoy (8:00 AM); no se hallaron sellos previos para los sorteos posteriores. Por ello no se imputan ni se crean pronósticos retrospectivos.
- Captura inmutable de monitoreo (GET): `captura_monitor_20261017T205339Z/`, con `/api/sombra`, `/api/datos_publicados`, `/api/mesa?offset=1&modelo=la`, HTML del sitio primario y TuAzar; `meta.json` registra URL y SHA-256 de cada archivo. La mesa de offset 1 corresponde a 4:00 PM y marca Delfín (0). Los agregados de `/api/sombra` registran exposición n=188: +9.87 mbits frente al ensamble (IC90 [3.55, 16.20], top-5 −1 pp; IC90 [−2, 1]); ag13 n=33: +6.73 mbits frente a ag12+RD+exposición (IC90 [−20.85, 34.31]), todavía inconcluso. Son indicadores agregados y no cuentan como sorteos prospectivos puntuados.
- Limitación de esta ejecución: el resultado oficial primario no fue legible en la captura HTML, y no existen predicciones selladas para los sorteos publicados posteriores a las 8:00 AM. No se puntúa sin doble confirmación ni se reconstruyen predicciones después del sorteo.
