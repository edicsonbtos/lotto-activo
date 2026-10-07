# Hipotesis "miercoles-viernes es mas flojo" - 2026-10-07

Veredicto: **NO PASA.** Mie-vie no es mas flojo; es igual o mejor que el resto. El unico dia realmente flojo es el domingo (ya conocido).
Reproducir: `python mie_vie.py` (salida.txt) y `python extra_sin_domingo.py` (salida_extra.txt). Preregistro: PREREGISTRO.md (escrito antes de mirar).

## Datos y alcance
- Solo desarrollo: filas [2000,9357) = 7357 sorteos, 2024-03-07..2025-12-17, 636 dias. Ensamble_v2 walk-forward (calor_cache.npz). No existe `arnes.py`; se uso `lotto_eval.cargar` + esa cache. No se miraron filas >=9357.
- ag12: NO medido (no hay cache walk-forward de ag12; recalcularlo cae fuera del encargo).
- Marcador en vivo: el `predicciones.json` local solo tiene 46 registros viejos (hasta 2026-09-16); el marcador real vive en /data de Railway. No hay datos locales utilizables, no se midio.

## Prueba unica preregistrada (mie-vie vs resto, mbits, estratificada por hora)
- Diferencia = **+32,2 mbits/sorteo** (mie-vie MEJOR), IC95 por bloques de dia [+8,6; +57,1]. Permutacion de etiquetas dentro de la semana: p una cola para "mas flojo" = 0,996. H1 (peor) rechazada.
- Top-5: -0,08 pp [-1,76; +1,68]. Top-15: +1,87 pp [-0,44; +4,20].
- Ojo: el "resto" incluye el domingo, que arrastra el resto hacia abajo. Por eso el contraste sale a favor de mie-vie. Mide "domingo malo", no "mie-vie bueno".

## Por dia (mbits [IC95 bloques-dia]; Top-5 azar 13,16 %; Top-15 azar 39,47 %)
| dia | mbits | Top-5 | Top-15 |
|---|---|---|---|
| lun | 141 [113;169] | 22,4 | 54,7 |
| mar | 148 [123;173] | 21,2 | 54,8 |
| mie | 111 [84;138] | 18,8 | 52,5 |
| jue | 149 [118;178] | 20,2 | 54,4 |
| vie | 155 [125;184] | 21,6 | 55,5 |
| sab | 118 [84;151] | 21,5 | 54,4 |
| dom | 9 [-33;50] | 15,8 | 44,5 |

Cada dia contra el resto (Bonferroni x7, alfa 0,0071): solo el domingo pasa (-128 mbits, z=-5,6). Mie -10,5 (p=0,49), jue +33 (p=0,045), vie +41 (p=0,014), mar +33 (p=0,027): ninguno pasa Bonferroni.
Omnibus (7 dias, permutacion dentro de semana): p=0,0003 con domingo; **sin domingo p=0,27** (los 6 dias restantes no se distinguen).

## Sensibilidad post-hoc (no preregistrada, solo descriptiva)
- Mie-vie vs lun,mar,sab (sin domingo): +2,3 mbits [-20,7; +26,7]; Top-5 -1,5 pp [-3,5; +0,5]. Sin diferencia.
- El miercoles solo, contra los otros 5 dias no domingo: -31 mbits [-61; -2], Top-5 -2,6 pp [-4,9; -0,2]. Fue la mirada 1 de ~7 y se miro despues de ver la tabla: con correccion por multiples comparaciones no se sostiene (y el omnibus sin domingo da p=0,27). El jueves y el viernes contiguos son los mejores de la semana, lo que va contra un "tramo mie-vie". Trata el miercoles como ruido salvo que se replique a ciegas.

## Confusores
- Hora: la composicion horaria por dia es la misma (8,6 % cada hora; la hora 0 pesa 5 %); todo contraste va estratificado por hora de todos modos.
- Feriados (lista fija VE aprox., 22 dias, 256 sorteos): sin ellos el contraste principal es +34,3 mbits (con ellos +32,2). Sin efecto.

## Modelo u operador
Calibracion del Top-5 identica en ambos grupos (O/E 0,96 mie-vie y 0,96 resto; Top-15 1,015 y 0,978; IC solapados): el modelo no esta mas descalibrado en mie-vie. No hay debilidad que explicar. (Para el domingo ya se sabe: el motor promete mas de lo que sale, O/E Top-5 0,75; es un dia mas impredecible, y se archivo como ruido/no replicado a ciegas en animal-del-dia.)

## Ajuste (aplanar P^a solo en mie-vie), validacion hacia delante
Elegido con el pasado y medido en 2025: a=1,1 (es decir, afilar, no aplanar); +0,96 mbits [-1,6; +3,5]. Con la cuadricula completa, el optimo in-sample en mie-vie es a=1,1 (139 vs 138), no aplanar. Aplanar (a<1) empeora mie-vie: a=0,8 da 131. No hay ajuste que proponer. (Solo 2025 es "hacia delante": con 2024 como unico anio previo la validacion es corta.)

## Conclusion
No tocar nada en produccion. Mie-vie no es mas flojo. La unica debilidad real del ensamble por dia de la semana es el domingo, y ese ya esta documentado. Cifras de desarrollo; sin confirmacion a ciegas ni en vivo.
