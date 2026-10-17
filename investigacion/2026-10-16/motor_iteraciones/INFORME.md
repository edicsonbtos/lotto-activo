# Búsqueda de un motor que repita los buenos días — 2026-10-16

## Decisión

El día 16-oct (10/12 Top-15) se reserva como resultado ya observado: no se usa para ajustar pesos ni para comparar variantes nuevas. La mejor candidata disponible es **ag13 en sombra**, que combina ag12, la corrección RD, exposición y los datos publicados por dos fuentes. No se encontró una regla adicional sustentada por la jornada de 10 aciertos. No se modifica el pronóstico principal ni se despliega nada.

## Iteraciones y qué aprendimos

| Hipótesis | Evidencia revisada | Decisión |
|---|---|---|
| Los días de mayor confianza fallan más | En los 310 pronósticos completos previos al 16-oct, Top-15 obtuvo 149 frente a 159,1 esperados y Top-5 55 frente a 60,2. Sin embargo, el cuartil de mayor masa Top-15 obtuvo 43/78 (55,1%) frente a 54,6% esperado; la relación no es monotónica. | Señal de sobreestimación agregada reciente, pero no hay umbral que identifique los días malos. No crear un “freno por confianza”. |
| Algunos animales tienen una ventaja fija | Perico (7) acumula el mayor conteo bruto, 10 Top-15 y 6 Top-5 en el tramo con probabilidades completas. Ratón (8) y Tigre (10) superan su expectativa en ciertos cortes, pero la búsqueda entre 38 animales y dos tamaños de Top elimina la aparente significancia. | No agregar pesos fijos por animal. |
| Ajustar el día después de una mañana buena | La reauditoría de 30 jornadas no encontró que la mañana, la confianza, el día de semana ni la jornada previa anticipen el resultado del día. La ronda preregistrada de reciclaje tampoco justificó un filtro. | No cambiar el motor en mitad del día ni perseguir el resultado de la mañana. |
| Aprovechar el patrón de animales recientes | En el corte de 349 sorteos auditado, los ganadores con última salida el día anterior entraron al Top-15 65% de las veces; con 2–5 días, 53%; los fríos de 6+ días, 11%; los repetidos del día, 0% en esa muestra. Los 10 aciertos del 16-oct fueron animales de gaps 1–4; los dos fallos fueron Pescado (posición 32, gap 1) y Rana repetida ese día (posición 29). | El motor ya concentra su masa en el patrón reciente y evita repeticiones del día. El resultado de hoy es compatible con que ese sesgo estructural funcionara, pero no demuestra un nuevo ajuste de gaps. |
| Añadir ag12, RD, exposición y pronosticadores | La réplica ag13 de 2026 reporta +45,60 mbits/sorteo vs. ensamble, IC90 [+37,79; +53,37], en 2.899 sorteos; Top-15 54,92% vs. 49,74%. | Es la candidata más prometedora, pero el resultado histórico no autoriza adopción: ag12 ya se había evaluado en ese período y el archivo histórico de pronosticadores no conserva hora de captura previa al sorteo. |

## Auditoría adversarial de la “prueba ciega” de ag13

La regla retrospectiva de ag13 se fijó antes de abrir su corrida 2026 y el informe la marca como PASA. Sin embargo, la validez externa es limitada:

1. La prueba 2026 vuelve a usar ag12 sobre enero–septiembre, período que ya había servido como segunda prueba ciega y réplica de ag12. Por tanto, el componente grande de la ganancia de ag13 no es evidencia nueva.
2. Los archivos de `publicados_2026.jsonl` contienen fecha de página y animales, pero no la hora de captura ni el hash del HTML original. La prueba histórica no permite confirmar que esas recomendaciones existían antes de los resultados. El preregistro identificó este riesgo.
3. El efecto de pronosticadores es sensible a período: desarrollo 2024–inicios de 2025 dio O/E 1,00; la confirmación de 2025 dio 0,86; el vivo corto dio 0,70 con IC95 [0,51; 0,92]. Ese cambio puede ser un cambio real de conducta o una irregularidad del archivo; la evidencia prospectiva debe decidirlo.

Por eso esa corrida sirve para **seleccionar qué candidato vigilar**, no para llamarlo motor probado ni para publicar un nuevo porcentaje de aciertos esperado.

## Candidata y prueba prospectiva

El candidato está implementado en [ag13.py](../../../herramientas/modelos/ag13.py) y su marcador experimental en [experimentos.py](../../../experimentos.py:233). La definición y las reglas de decisión están congeladas en [PREREGISTRO_ag13.md](../../../herramientas/exploracion/PREREGISTRO_ag13.md).

- Mantener ag13 fuera de producción; no reajustar 0,862, 0,924, los pesos de ag12 ni las reglas de corte.
- Solo contar pronósticos congelados antes del sorteo con los dos HTML capturados entre 6:00 y 7:55, fecha correcta y hashes guardados. Si falta una fuente, excluir por la falta antes de conocer el resultado.
- Usar una sola mirada a los primeros 931 sorteos válidos. PASA únicamente si el límite inferior del IC90 de Δmbits ag13−ensamble es >0 y el retorno Top-5 escalonado no queda más de 3 pp/ficha por debajo. Freno preregistrado: apagar si, con n≥600, Δmbits <−10.
- Evaluar el aporte de pronosticadores aparte cuando la expectativa acumulada de U llegue a 350 aciertos; exigir O/E<1 con IC95 superior <1 y ganancia sobre ag12+RD+exposición.
- No volver a probar variantes sobre el 16-oct ni sobre la réplica 2026 ya vista. Cualquier ajuste nuevo requiere un período de desarrollo separado y otra ventana futura intacta.

## Lectura del 16-oct

El Top-15 obtuvo 10/12 frente a 5,91 esperados. Bajo probabilidades congeladas e independencia aproximada, la probabilidad de 10 o más es ~1,7%. La masa media Top-15 del motor fue corriente (~49,2%), así que el día no señala una calibración especial ni una condición detectable antes del sorteo. Debe permanecer como éxito de prueba del motor existente, no como receta que se ajusta hasta reproducir exactamente ese conteo.

## Archivos del experimento

- `prospectiva_2026-10-17/` conserva fuentes y probabilidades selladas antes del sorteo de mañana. Ambas páginas no entregaban un conjunto Lotto Activo válido para 2026-10-17 (`lotoven` no devolvió fecha; loteriadehoy devolvió la fecha sin números), así que **ag13 no es puntuable para este sorteo**. Para no descartar la oportunidad, quedó congelada como prueba prospectiva secundaria la variante ya existente **ag12 V1 + exposición**, sin dato U ni corrección RD intradía (no disponible antes de las 8:00). El Top-15 de esta candidata comparte 14/15 con el ensamble sin la ventana especial de las 8:00; solo entra 3 y sale 14. Esto es una predicción futura sin resultado todavía, no evidencia de que la variante mejore.
- El pronóstico base fue invertido para retirar la corrección extra de las 8:00 y se volvió a aplicar la transformación; diferencia máxima de ida y vuelta: 6,9×10⁻¹⁸. El historial candidato usa resultados de la mesa oficial local hasta el 7-oct y resultados API del 8–16-oct; esos últimos se congelaron para la ejecución, aunque no todos tienen una segunda fuente guardada en este experimento.
- La API de producción aún identifica el pronóstico principal como `ensamble_v2`. Los cambios locales relacionados con ag13 no se han considerado desplegados ni se atribuye a producción una evaluación que no se haya congelado allí.

## Conclusión del ciclo

Las hipótesis nuevas basadas en confianza, animal, mañana/tarde o ajuste del día no justifican un motor nuevo. La acción técnicamente defendible es preservar el mejor candidato ya especificado (ag13) en sombra y obtener datos realmente prospectivos. Un acierto de 10/12 puede volver a ocurrir; el método no puede garantizar ni forzar esa racha, y cualquier iteración que seleccione el ajuste por acertar hoy convertiría la jornada en entrenamiento.

## Ag14 — nueva candidata prospectiva

Ag14 formaliza una ruta verificable sin depender de `U`: **ag12 V1 congelado → RD disponible antes del sorteo → exposición congelada**. Los parámetros son reutilizados, no afinados con los días ya vistos, y el motor sigue fuera del marcador principal. Su alcance, fecha inicial, métricas y única regla de evaluación están fijados en [PREREGISTRO_ag14.md](PREREGISTRO_ag14.md). El día 17 a las 08:00 empieza sin RD intradía, por lo que se usa exactamente el vector ag12+exposición ya guardado en la predicción prospectiva; no se altera el archivo sellado anterior. El marcador Ag14 se expone dentro del bloque de sombra y cuenta solo sorteos desde el 17-oct con ag12 y ensamble comparables.

Esta candidata no es una señal independiente ni una afirmación de mejora: prueba prospectivamente una composición concreta que ya existía en piezas. La decisión se espera al primer corte único de 931 sorteos; antes de eso los conteos son descriptivos y no se ajustan pesos.

## Seguimiento recurrente

Quedó activa en Codex la automatización `Seguimiento ciego Lotto Activo`, programada antes de los sorteos horarios (7:55–18:55, hora de Caracas). En cada ciclo debe validar resultados ya publicados, puntuar solo pronósticos sellados y guardar el pronóstico del siguiente sorteo si los datos lo permiten. La automatización no puede sobrescribir sellos, ajustar parámetros del tramo ciego ni desplegar producción. El primer sello prospectivo disponible es el del 17-oct a las 08:00; su resultado sigue pendiente al redactar esta actualización.
