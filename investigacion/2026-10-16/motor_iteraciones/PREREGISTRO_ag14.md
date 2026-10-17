# Preregistro Ag14 — 2026-10-17

## Definición congelada

Ag14 es una candidata de sombra compuesta por **probabilidades ag12 V1 ya congeladas → regla RD existente cuando el resultado RD esté disponible antes del sorteo → multiplicadores de exposición ya congelados**. No incorpora pronosticadores externos (sus capturas no son verificables para todas las fechas), no añade pesos por animal, confianza o racha y no vuelve a ajustar parámetros con el 10/12 del 16-oct.

La composición está implementada en `herramientas/modelos/ag14.py` y el marcador de sombra en `experimentos.py`. Para el sorteo de las 08:00 del 17-oct, aún no hay RD intradía; por tanto la predicción válida es **ag12 V1 + exposición**, idéntica a la candidata prospectiva ya sellada esa noche. Ese archivo no se modifica; este preregistro identifica la misma transformación como Ag14 y registra el inicio de su seguimiento.

## Evaluación ciega

- Inicio: sorteos desde 2026-10-17, con el pronóstico ag12 guardado antes de conocer el resultado. Solo usar resultados futuros frente al pronóstico ya congelado; excluir anulados y sorteos sin ag12 o ensamble comparable.
- Comparador primario: ensamble del mismo sorteo, usando el vector base sin el ajuste especial de las 08:00, y el mismo resultado ganador. Si se conoce RD a tiempo para un sorteo posterior, se aplica el mismo dato a ag12 antes de exposición; se conserva sin cambios para el ensamble al medir el desempeño probabilístico.
- Métrica primaria: diferencia de log-score en mbits por sorteo, `ag14 − ensamble`, con IC90 agrupado por jornada.
- Métrica de seguridad: diferencia del retorno Top-5 escalonado, en puntos porcentuales por ficha, con RD del sorteo si corresponde.
- Una sola decisión al llegar a los primeros 931 sorteos válidos: PASA solo si el límite inferior del IC90 de mbits es mayor que cero y el promedio Top-5 no es peor que −3 pp/ficha. Antes de ese tamaño, mostrar acumulación sin decidir. No inspeccionar cortes intermedios para ajustar.
- Las métricas descriptivas Top-3/5/15 no son reglas de ajuste. No se reinterpretan días ya vistos como prueba ciega.

## Alcance y limitación

Ag14 no introduce una señal nueva independiente: formaliza como candidata autónoma una capa ya ensayada de ag12+RD+exposición, sin la fuente U. La prueba histórica sirve para contexto, no para aprobar Ag14. El resultado extraordinario del 16-oct se considera observado y fuera de la evaluación. Un PASA en sombra solo justifica una revisión; no autoriza automáticamente despliegue ni promete replicar rachas de 10 aciertos.
