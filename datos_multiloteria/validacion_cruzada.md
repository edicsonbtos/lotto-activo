# Validacion cruzada de fuentes (v2)

Fuentes INDEPENDIENTES: loteriadehoy.com (LH), tuazar.com (TZ)
y api.lotterly.co (ARBITRO oficial, backend de selvaplus.com y
guacharoactivo.com.ve). lotoven.com queda DESCARTADO como fuente:
comparte base de datos con LH (mismos animales y rutas de imagen
/dist/animals_img/ verificados en la misma semana).

## lottoactivo
- fuentes votantes: LH, TZ
- registros canonicos: 1800 (150 dias)
- acuerdos: {'acuerdo_2_fuentes': 1799}
- unicos: {'solo_LH': 1}
- discrepancias reales: 0 (ninguna)
- n_tablero observado: [0, 36] -> N=37 (nombres desde tuazar)
- conflictos de nombre en tablero: [(0, {'BALLENA': 53, 'DELFIN': 47})]

## lottoactivordint
- fuentes votantes: LH, TZ
- registros canonicos: 1800 (150 dias)
- acuerdos: {'acuerdo_2_fuentes': 84}
- unicos: {'solo_LH': 1716}
- discrepancias reales: 0 (ninguna)
- n_tablero observado: [0, 36] -> N=37 (nombres desde tuazar)
- conflictos de nombre en tablero: ninguno

## lagranjita
- fuentes votantes: LH, TZ
- registros canonicos: 1800 (150 dias)
- acuerdos: {'acuerdo_2_fuentes': 1800}
- unicos: {}
- discrepancias reales: 0 (ninguna)
- n_tablero observado: [0, 36] -> N=37 (nombres desde tuazar)
- conflictos de nombre en tablero: [(0, {'BALLENA': 39, 'DELFIN': 50})]

## selvaplus
- fuentes votantes: LH, TZ, ARBITRO oficial
- registros canonicos: 1723 (143 dias)
- acuerdos: {'acuerdo_2_fuentes': 1632, 'acuerdo_3_fuentes': 91}
- unicos: {}
- discrepancias reales: 0 (ninguna)
- n_tablero observado: [0, 99] -> N=100 (nombres desde pareo(LH,arbitro)+tuazar)
- conflictos de nombre en tablero: [(0, {'BALLENA': 1, 'DELFIN': 1}), (75, {'GUAHCARO': 1, 'GUACHARO': 1})]

## guacharoactivo
- fuentes votantes: LH, TZ, ARBITRO oficial
- registros canonicos: 1800 (150 dias)
- acuerdos: {'acuerdo_3_fuentes': 1748, 'acuerdo_2_fuentes': 52}
- unicos: {}
- discrepancias reales: 0 (ninguna)
- n_tablero observado: [0, 75] -> N=76 (nombres desde pareo(LH,arbitro)+tuazar)
- conflictos de nombre en tablero: [(44, {'CHIGUIRE': 1, 'CHUGUIRE': 26}), (55, {'OSOHORMIGUERO': 1, 'HORMIGUERO': 26}), (0, {'DELFIN': 21, 'BALLENA': 22})]
