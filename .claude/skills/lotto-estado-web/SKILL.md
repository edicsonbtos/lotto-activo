---
name: lotto-estado-web
description: Comprueba si la web de Lotto Activo en Railway está viva, qué versión está desplegada y si el pronóstico ya terminó de calcularse. Úsala cuando el usuario diga que la página no carga, se queda en "calculando", pregunte si Railway está corriendo o si cambió el enlace, y también justo después de cada git push a master (que despliega solo).
---

# Estado de la web (Railway)

Enlace fijo: **https://lotto-activo-production.up.railway.app** (proyecto `82f19226-b1bd-4b5e-bb7e-da0e0a1fe6d4`, servicio `23b7bdd8-fef0-45f0-b020-2bd43dd810bb`).

1. **¿Responde?** `curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 60 <enlace>/`
2. **¿Terminó de calcular?** `curl -s <enlace>/listo.json`. Si devuelve `{"listo": false}` justo tras un despliegue, es normal: el servidor recalcula el pronóstico (1-2 min) y la página se recarga sola mientras tanto. Vuelve a consultar en 20-30 s. Si sigue en `false` más de 5 min, revisa los logs.
3. **Despliegue**: usa la herramienta Railway `list-deployments` (projectId y serviceId de arriba, limit 2) y comprueba que el último está en SUCCESS con el hash del último commit. Si ves `-` en el commit, ese despliegue no vino de GitHub.
4. **Logs**: `get-logs` con el deploymentId. "Modelo: ensamble (numpy/scipy OK)" es lo esperado. Las líneas `"GET ..." 200` salen marcadas como error, pero son normales.
5. **RD Internacional**: `curl -s <enlace>/api/rdint`. Debe traer `sorteo`, y `estado.error` debe ser null. `pronostico` es null solo mientras calcula (1-2 min tras cada resultado RD). `con_la_h: false` es normal hasta que sale Lotto Activo de las h:00. Los logs de RD llevan el prefijo `[rdint]`.
6. Explica al usuario en una o dos frases qué pasaba y si ya está bien. No redespliegues ni reinicies sin preguntarle.
