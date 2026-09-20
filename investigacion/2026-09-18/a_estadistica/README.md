# ENJAMBRE A — barrido estadístico masivo (Operación Turing)

Certifica si queda señal residual explotable sobre `ensamble_v2` en el tramo de
**desarrollo `[2000, 9357)`**, o cierra el espacio. **No toca prueba (>=9357),
ni producción, ni pesos, ni modelos, ni registros. Solo lee.**

## Qué hace
1. Congela **una vez** la salida walk-forward de `ensamble_v2` (log-prob por
   sorteo×animal) → cache `baseline_dev_full.npz` (~5 min).
2. Genera **>300 hipótesis** (singles + interacciones × 2 suavizados). Cada una
   es una *feature causal*: log-rate empírico estimado solo con el pasado
   (cuentas acumuladas estrictas `< t`, cumsum desplazado). Familias:
   gap exacto/binned, g2, veces-hoy, salió-hoy, k, día-semana, borde de jornada,
   días-desde (dd), ganó-anterior, vecino-de-tablero, conteos móviles
   (12/24/38/76/150/300), régimen de repetición, y todas sus interacciones de
   pares sobre 14 covariables base.
3. Sonda directa: añade la feature al logit congelado con **un peso escalar**
   ajustado por máxima verosimilitud. Aporte = `1000·media(log2 p_con[y] − log2 p_base[y])` mbits.
4. **Compuerta**: OOF por cuartos (peso ajustado con 3 cuartos, puntúa el 4º).
   SEÑAL exige aporte OOF **> 0 en 4/4 cuartos** Y `q(Benjamini-Hochberg) < 0.05`
   (p-valor por bootstrap de bloque-día, 2000 remuestreos).

## Por qué el "+90/+120 mbits" NO es la compuerta
Esos mbits son la ventaja del ensamble **entero** sobre uniforme. El oráculo
walk-forward de la política medible es 10.38 % Top-3, **por debajo** del ensamble
(12.89 %): ninguna feature residual puede acercarse a +90 mbits. Ese número es la
vara de "¿vale la pena integrarlo?", no el filtro. El filtro real es 4/4 + BH.

## Reproducción
```powershell
$env:PYTHONIOENCODING="utf-8"
cd C:\Users\edics\Downloads\lotto-activo\lotto-activo
python investigacion\2026-09-18\a_estadistica\barrido.py            # completo (~5 min base + barrido)
python investigacion\2026-09-18\a_estadistica\barrido.py --smoke    # rápido, valida mecánica
python investigacion\2026-09-18\a_estadistica\barrido.py --rebuild  # recalcula la base
```
Salidas: `barrido_full.json` (tabla completa), `tabla_full.md` (resumen + veredicto).
Semilla fija `20260918`.

## Qué mirar
- `SENALES: N / total`. Si **N=0** → ESPACIO CERRADO; el archivo reporta el mejor
  negativo. Si **N>0** → cada señal es una rendija candidata con su efecto en mbits.
- Cualquier señal con aporte < ~5 mbits, aunque pase la compuerta, es irrelevante
  frente a los +120 del ensamble (candidata a vigilar, no a integrar).
