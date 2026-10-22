---
name: lotto-historial
description: Trae el historial VIVO de Lotto Activo y RD Internacional (sorteos y pronósticos congelados en Railway) a la sesión para analizarlo. Úsala antes de cualquier análisis de comportamiento, de rachas, de "días buenos/malos" o del estado del bot, y cuando el usuario adjunte un archivo lotto_historial_*.txt.
---

# Traer el historial vivo

El `historial.txt` del repo va atrasado: los datos buenos viven en el volumen de Railway. Hay tres caminos, en este orden:

1. **El usuario adjuntó `lotto_historial_AAAA-MM-DD.txt`** (botón «Descargar historial», arriba de todo en la web): úsalo directamente.
2. **Bajarlo tú:** `python .claude/skills/lotto-historial/bajar.py` lo guarda en el scratchpad (o en la ruta que le pases) y lo separa en `historial.txt`, `rdint_historial.txt`, `predicciones.jsonl` y `rdint_predicciones.jsonl`. No pide clave.
3. **Si el paso 2 falla con `connect_rejected` / 403 del proxy:** la red del entorno no deja salir a `lotto-activo-production.up.railway.app`. Dile al usuario, en dos líneas, que tiene dos salidas:
   - pulsar «Descargar historial» en la web y adjuntar aquí el `.txt`;
   - o añadir ese dominio en **Network access → Allowed domains** del entorno (menú del entorno en el título de la sesión → Edit). Así cualquier sesión futura lo baja sola con el paso 2.

No inventes ni reconstruyas resultados que no tienes. Para medir rendimiento, sigue `lotto-marcador` y, ante cualquier idea nueva, `lotto-nueva-idea`.

## Formato del .txt

- Cabecera con fecha de generación y conteos.
- `===== historial.txt =====` y `===== rdint_historial.txt =====`: una línea por sorteo, igual que los archivos originales.
- `===== predicciones.jsonl =====` y `===== rdint_predicciones.jsonl =====`: un registro JSON por línea con el orden congelado **antes** del sorteo (`orden_completo`, índices 0-37), `salio`, `modelo` y, si hay, `sombra`. Sin `scores`, para que pese poco. Los puntajes completos están en `/historial.zip`, que pide la clave.
