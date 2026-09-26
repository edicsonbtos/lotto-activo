# Segunda prueba ciega: época reciente (2026-09-26, escrito ANTES de correr)

## Por qué existe (declarado)
La prueba sellada 2019-2023 falló (commit 9884e74). Un diagnóstico posterior sugirió que la evitación de pares
nace hacia 2022. Esta es una **segunda prueba**, motivada por ese diagnóstico, y se corrige como tal.

## Datos
- `historial.txt` filas **[9357, 12511)**: 2025-12-17 .. 2026-09-16, 3.154 sorteos.
- Los modelos se congelaron en c4a2b17 con filas < 9357: estas filas son futuro puro para ag12.
- Historia del tramo: el proyecto evaluó aquí OTROS modelos 5 veces (registro_final.jsonl). ag12 nunca se evaluó aquí
  ni se construyó mirándolo. Esta es la 6.ª mirada al tramo y la 1.ª de ag12.
- Días con la fecha corrida (hilo 8): 2025-12-15..19, 12-25..27, 2026-01-01..03 → se usan como historia pero NO se puntúan.

## Candidatos y criterio (sin cambios desde el congelado)
- ag12_V1 y ag12_V0 (parametros de c4a2b17), frente a ensamble_v2 walk-forward con los pesos de producción.
- **Corrección: Bonferroni k = 4** (2 candidatos × 2 pruebas) → IC bilateral 98,75 %. PASA si queda entero > 0 en Δmbits.
- Secundarias: Top-3, Top-5, Top-15, Δ retorno Top-5 escalonado.
- Potencia (dicha antes): con ~3.100 sorteos el error típico de Δmbits es ~4, así que hace falta Δ ≈ +10 para pasar.
  Si el efecto real es el de desarrollo en forward (+16) debería pasar; si encoge a ~60 % (+10) queda en el límite.
- Se corre UNA vez (`reciente/prueba_reciente.py` se niega a repetir). Se informa el resultado sea cual sea.
