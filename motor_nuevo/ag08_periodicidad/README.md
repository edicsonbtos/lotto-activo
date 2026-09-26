# ag08_periodicidad: periodicidades y estructura temporal fina

**Veredicto: NO pasa la barra. No hay periodicidad útil más allá de lo que ya captura el ensamble_v2.**
Candidato primario (reserva prerregistrada): Δ −0,45 mbits [−1,89, +1,00].

## Qué se probó (prerregistro en `PREREGISTRO.md`, escrito antes de correr)
Barrido de 1936 pruebas sobre los RESIDUOS del ensamble (O observado vs E esperado bajo P_ens), descubrimiento
con Benjamini-Hochberg q=0,05 en la mitad 1 del desarrollo y confirmación en la mitad 2:
- F1 desfase agregado L=1..168 (¿sale el animal de hace L sorteos?); F1b misma hora hace k=1..7 días naturales;
- F2 desfase por animal (38 × L∈{12,24,36,38,76,84}); F3 espectro del residuo por animal en esos periodos y agregado T=2..200;
- F4 día de la semana × hora × tramo de hueco; F5 animal × hora y animal × día de la semana;
- F6 recorrido del tablero: (y_t − y_{t−L}) mod 38 para L∈{1,2,12,38}.

## Barrido (`salida_barrido.txt`)
```
Pruebas: 1936 · supervivientes BH(q=0,05) en mitad 1: 1 · confirmados en mitad 2: 0
   ['gh', 6, 7] F4  m1 O=64 E=37.58 z=+4.64   m2 O=40 E=33.04 z=+1.30  no
  F1: 168 pruebas · p mín m1 4.69e-03 · n(p<0,05) 7 (esperado 8.4)
  F1b: 7 · p mín 1.67e-01 · 0 (0.4)       F2: 228 · 1.14e-04 · 11 (11.4)
  F3a: 228 · 2.90e-03 · 7 (11.4)         F3b: 199 · 2.44e-03 · 16 (10.0)
  F4: 236 · 3.43e-06 · 25 (11.8)         F5: 722 · 6.02e-03 · 34 (36.1)
  F6: 148 · 6.04e-04 · 12 (7.4)
  Desfases objetivo z m1/m2: L=12 +1.37/+0.19 · 24 −0.90/−0.61 · 36 +0.73/+0.18 · 38 +2.01/+1.77
                             76 +0.35/+0.14 · 84 −0.46/−1.42 · misma hora hace 1..7 días: todas |z|<1,8
```
El único superviviente (hueco 72-119 sorteos a la hora índice 7) no se confirma. No hay ciclo diario, semanal
ni de 38 sorteos por animal, ni recorrido del tablero. F4 muestra algo de exceso de p pequeños (25 vs 11,8),
compatible con pequeñas descalibraciones del ensamble por hora/día que no se sostienen (ver variante 2).
L=38 sale positivo en ambas mitades (z +2,01 / +1,77) pero no sobrevive a BH y su aporte al candidato no es positivo.

## Candidato (`salida_experimento.txt`, cross-fitting en 5 bloques contiguos de jornadas)
Primario (reserva prerregistrada: 8 indicadoras, desfases 12/24/36/38/76/84 + misma hora hace 1 y 7 días, ridge 1):
```
mbits: cand +119.6 · ensamble +120.1
Delta mbits -0.45 [-1.89, +1.00] · mitad1 -0.32 [-2.51, +1.87] · mitad2 -0.57 [-2.61, +1.44]
Top-3 12.70% vs 12.89% · Top-5 20.05% vs 20.25% · Top-15 52.85% vs 53.07%
Top-5 escalonado por ficha: +22.79% vs +24.27% · delta -0.01 [-0.04, +0.01]
PASA BARRA DEV: False
```
Variante 2 (EXPLORATORIA, decidida tras ver el barrido): familia F4 completa, 236 variables, ridge 30:
```
Delta mbits -1.74 [-6.31, +2.97] · mitad1 -3.76 [-10.16, +2.69] · mitad2 +0.29 [-6.43, +7.16]
Top-5 20.40% vs 20.25% · Top-5 escalonado delta +0.01 [-0.04, +0.05]
PASA BARRA DEV: False
```
Variantes probadas: 2 (primario + 1 exploratoria). Nada iterado sobre el resultado.

## Modelo congelado
`congelar.py` → `parametros.json` (θ con todo [2000, 9357)): [0.1403, −0.0766, 0.0466, 0.1756, 0.0219, −0.0551, −0.098, −0.0801]
(orden: L12, L24, L36, L38, L76, L84, misma hora −1 día, −7 días).
`modelo.py`: ensamble_v2 del repo + esa corrección. `prueba_fuga.py` → `(True, None, 0.0)` sobre prefijo(2600) desde 2000;
el ensamble recalculado coincide con la caché (máx |dif| 1,2e-6). No se recomienda como candidato.

## Archivos
`rasgos.py` (indicadoras causales, ajuste y aplicación), `barrido.py` → `barrido.json`, `salida_barrido.txt`;
`experimento.py` → `resultados.json`, `P_primario.npy`, `salida_experimento.txt`; `congelar.py`, `modelo.py`, `prueba_fuga.py`, `salida_fuga.txt`.
Reproducir: `cd motor_nuevo/ag08_periodicidad; $env:PYTHONIOENCODING='utf-8'; python barrido.py; python experimento.py`.
