# Puntuar un sorteo prospectivo

`herramientas/evaluacion_prospectiva.py` compara la candidata y ensamble_v2 desde sus archivos congelados. Solo lee los pronósticos/capturas y escribe un registro nuevo; rechaza sobrescribir una salida existente.

## Antes de puntuar

1. Confirma manualmente el resultado de Lotto Activo, fecha y hora en dos sitios independientes.
2. Guarda la captura HTML o respuesta cruda de cada sitio. Registra su SHA-256 y la hora de descarga en UTC.
3. Crea un JSON de resultado como este, sustituyendo paths, enlaces, ganador y hashes por los datos observados:

```json
{
  "fecha_sorteo": "2026-10-17",
  "hora": 8,
  "ganador": "12",
  "fuentes": [
    {
      "nombre": "TuAzar",
      "url": "https://tuazar.com.ve/loteria/animalitos/resultados/semana/",
      "archivo": "captura-tuazar.html",
      "capturado_utc": "2026-10-17T12:10:00Z",
      "sha256": "<sha256 de la captura>",
      "ganador_confirmado": "12"
    },
    {
      "nombre": "Lotto Activo",
      "url": "https://lottoactivo.com/historial/",
      "archivo": "captura-lottoactivo.html",
      "capturado_utc": "2026-10-17T12:11:00Z",
      "sha256": "<sha256 de la captura>",
      "ganador_confirmado": "12"
    }
  ]
}
```

`ganador_confirmado` es una confirmación manual: el programa comprueba que ambas fuentes declaren el mismo ganador, que los archivos existan, que sus hashes correspondan y que la descarga no sea anterior al sorteo. **No interpreta el contenido HTML**; quien registra el resultado debe verificar que cada captura muestra Lotto Activo en la fecha y hora indicadas.

## Ejecutar

Desde la raíz del repositorio:

```powershell
python herramientas/evaluacion_prospectiva.py `
  --prediccion investigacion/2026-10-16/motor_iteraciones/prospectiva_2026-10-17/prediccion_ciega.json `
  --ensamble investigacion/2026-10-16/motor_iteraciones/prospectiva_2026-10-17/pronostico_ensamble.json `
  --sello-candidata investigacion/2026-10-16/motor_iteraciones/prospectiva_2026-10-17/ag14_sello_2026-10-17.json `
  --resultado investigacion/2026-10-16/motor_iteraciones/prospectiva_2026-10-17/resultado_fuentes.json `
  --salida investigacion/2026-10-16/motor_iteraciones/prospectiva_2026-10-17/puntuacion_2026-10-17_08.json
```

El resultado incluye rangos, aciertos Top-3/5/15, mbits, retorno Top-5 por ficha, diferencias entre candidata y ensamble, hashes de pronósticos y capturas. El ganador acepta `0` (Delfín) y `00` (Ballena) como códigos distintos.
