# Tableros observados (rango de numeros por loteria)

Derivado de 1.723-1.800 sorteos por loteria, validados cruzando
fuentes independientes (ver validacion_cruzada.md).

## lottoactivo
- sorteos en CSV: 1800
- rango observado: 0..36 -> N = 37 (37 numeros distintos)
- numeros sin nombre conocido: ninguno
- notas: Se anuncia '38 figuras (delfin 0 - culebra 36)': en la practica son 37 numeros. El 37 JAMAS aparece en 12.502 sorteos de historial.txt ni en 1.800 de esta muestra. El modelo del repo asumia K=38 (azar 2,63%); el azar real es 1/37 = 2,70%.

## lottoactivordint
- sorteos en CSV: 1800
- rango observado: 0..36 -> N = 37 (37 numeros distintos)
- numeros sin nombre conocido: [6, 14, 21, 22]
- notas: Tablero identico al de Lotto Activo (0-36). Validacion cruzada TZ solo 1 semana (es nueva en tuazar): 100% acuerdo; el resto del periodo es LH+tablero verificado.

## lagranjita
- sorteos en CSV: 1800
- rango observado: 0..36 -> N = 37 (37 numeros distintos)
- numeros sin nombre conocido: ninguno
- notas: Misma numeracion base 0-36 (37 numeros); el 0 es Ballena (no Delfin).

## selvaplus
- sorteos en CSV: 1723
- rango observado: 0..99 -> N = 100 (82 numeros distintos)
- numeros sin nombre conocido: ninguno
- notas: La mision asumia 38; el tablero actual es 0-99 (100 figuras). La API oficial (api.lotterly.co) confirma el rango completo.

## guacharoactivo
- sorteos en CSV: 1800
- rango observado: 0..75 -> N = 76 (76 numeros distintos)
- numeros sin nombre conocido: ninguno
- notas: La mision asumia 77; se observa 0-75 (76 figuras). El 76 nunca aparecio en 1.800 sorteos (P bajo nula 77 ~ e^-23).
