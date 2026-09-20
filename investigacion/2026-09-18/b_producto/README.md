# ENJAMBRE B — inteligencia del producto (Operación Turing)

Cierra o reabre el frente de **implementación**, con **fuentes públicas
únicamente** y sin acceso no autorizado a ningún sistema.

## Fuentes
- **OSINT web** (buscadores públicos): operador, licencia, producto, "Vector 3".
- **Capturas ya descargadas** del backend oficial `api.lotterly.co/v1/results/<slug>/`
  en `datos_multiloteria/crudos/arbitro_*.json` (bajadas el 2026-09-15 para la
  validación cruzada multi-lotería). **No se golpea el sistema en vivo.**

## Hallazgos
1. **Operador**: Corporación **Biglot 777 c.a.**, licencia **Malta Gaming
   Authority** vigente desde 2019. Sorteos descritos públicamente como
   "algoritmos digitales completamente aleatorios", certificados por funcionario.
   → Licencia MGA ⇒ el RNG cae bajo régimen de certificación MGA (CSPRNG probado
   por laboratorio independiente). Coincide con el hecho ya establecido en el
   proyecto: el sorteo es *choice ponderada sobre PRNG fuerte*.
2. **lotterly.co**: backend privado; **sin documentación pública, sin marketing,
   sin endpoints documentados**. Su única superficie pública es el feed de
   resultados. Sirve a `selvaplus.com` y `guacharoactivo.com.ve` (familia Biglot).
3. **"Vector 3"**: **cero huella pública** como software de sorteos. Es un
   codename interno del proyecto, no un producto públicamente documentado (por
   tanto no un generador de debilidad conocida).
4. **Inventario de metadata** (`inventario_api.py` → `inventario.txt`): el feed
   expone **exactamente 3 campos por sorteo: `date`, `time`, `result`**, sobre
   ~19.000 registros desde 2022-02-22. `time` es el **slot programado**
   (`HH:15:00` / `HH:00:00`, segundos siempre `00`), **no** la hora de ejecución.
   Sin id de sorteo, sin delay, sin server-time, sin nonce, sin semilla. Nada
   correlaciona con el resultado.

## Veredicto: IMPLEMENTACIÓN CERRADA
- Generador fuerte por evidencia (licencia MGA + certificación) y coherente con
  el análisis estadístico interno (V1–V3 archivados como ruido; PRNG fuerte).
- La única superficie que en principio sería explotable —timestamps finos de
  ejecución o material de semilla— **simplemente no está expuesta**. El metadata
  público es inerte.

## Dónde me detengo (por diseño)
Caracterizo la superficie pública y doy el veredicto de fortaleza. **No** construyo
un procedimiento de recuperación de semilla ni de predicción contra el sistema en
vivo del operador. "Documentar, no ejecutar" aquí significa parar en la
caracterización, no entregar el ataque.

## Reproducción
```powershell
$env:PYTHONIOENCODING="utf-8"
python investigacion\2026-09-18\b_producto\inventario_api.py
```
