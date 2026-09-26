# ag05_baraja_operador: el operador como "baraja" o "cuota"

**Veredicto: NO pasa la barra. Sale peor que el ensamble: −1,21 mbits [−1,79, −0,65].**
No hay mazo con fronteras fijas (ni por días ni por bloques de 38 sorteos). La única parte de
"baraja" que existe es el mazo diario suave: el animal que ya salió hoy aparece a 0,4x. El ensamble_v2
ya lo tiene bien calibrado, y cualquier corrección encima solo añade ruido.

## Qué se probó (prerregistro en `PREREGISTRO.md`, escrito antes de correr)
Modelos generativos secuenciales P(x_t = a | seq[:t]) ∝ exp(θ·f_a(t)). La verosimilitud es exacta
(producto de condicionales), y θ es el log de la "fuga" del mazo.
- G1: mazo diario, con la variable [salió hoy].
- G2: mazo de D ∈ {2, 3, 4} días naturales con fase φ anclada a la fecha absoluta.
- G3: mazo de 38 sorteos, con fase φ ∈ 0..37 sobre el índice global.
- G4: cuota deslizante en los últimos N ∈ {12, 24, 36, 48, 72} sorteos.
- G5: control de recencia pura, sin fronteras (días desde la última aparición).

En total son 54 configuraciones. Se usó cross-fitting en 5 bloques contiguos de jornadas del tramo
[2000, 9357). Dentro de cada bloque de entrenamiento se ajusta θ y se elige la configuración por BIC,
y con eso se predice el bloque retenido. El candidato primario es log P_ens + θ·f_mejor.

## Resultados (copiados de `salida_experimento.txt`, desarrollo n=7357)
Candidato primario: en los 5 bloques se eligió G1, con θ ≈ −0,04 (una corrección casi nula):
```
mbits: cand +118.9 · ensamble +120.1
Delta mbits -1.21 [-1.79, -0.65] · mitad1 -1.16 [-2.04, -0.30] · mitad2 -1.26 [-2.04, -0.51]
Top-3 12.89% vs 12.89% · Top-5 20.25% vs 20.25% · Top-15 53.04% vs 53.07%
Top-5 escalonado por ficha: +24.27% vs +24.27% · delta +0.00 [-0.00, +0.00]
PASA BARRA DEV: False
```
- **Baraja sola (sin ensamble):** la mejor (G4_72) da +60,0 mbits, frente a +120,1 del ensamble
  (Δ −60,12 [−70,25, −50,51]).
- Solo, G1 da +51,4. Los mazos de fase fija G2 dan de +51,8 a +56,6, G3 de +52,6 a +55,2 y
  la cuota G4 de +51,4 a +60,0. La recencia sin fronteras (G5) da **+60,2**, más que cualquier mazo con frontera fija.
- **Todas** las configuraciones apiladas sobre el ensamble salen negativas, de −0,86 a −1,94 mbits.
- ¿Por qué pierde el apilado de G1? El θ residual de [salió hoy] cambia de signo de un bloque a otro
  (en el bloque vale +0,16, −0,01, +0,24, −0,36 y −0,29), así que el ajustado fuera del bloque se equivoca de dirección.
  Es deriva o ruido alrededor de la calibración del ensamble, que en promedio ya es correcta.

## Diagnóstico de fronteras (`diagnostico_fronteras.py`, informativo)
Añadí [salió en el mazo actual antes de hoy] a G5, solo y con cross-fit, para cada (D, fase).
Si existiera un mazo, la fase verdadera destacaría.
```
D=2: fase 0: -0.46 [-0.79,-0.13] | fase 1: -0.46 [-0.79,-0.14]
D=3: fase 0: -0.06 [-0.29,+0.17] | fase 1: +0.10 [-0.31,+0.53] | fase 2: -0.15 [-0.43,+0.13]
D=4: fase 0: -0.08 [-0.31,+0.13] | fase 1: +0.01 [-0.43,+0.48] | fase 2: -0.10 [-0.47,+0.27] | fase 3: +0.01 [-0.27,+0.28]
D=5 y D=7: todas las fases entre -0.81 y +0.34, con IC que cruzan 0 o negativos
```
Ninguna fase aporta. **No hay mazo con fronteras fijas.** Desviación: D = 5 y 7 no estaban en el
prerregistro. Solo son diagnóstico y no afectan al candidato.

## Variantes
Hubo 1 variante primaria, prerregistrada y sin iterar. Las 54 configuraciones son la rejilla
prerregistrada y la elección se hizo dentro de cada entrenamiento. No se ajustó nada mirando el resultado.

## Archivos
- `baraja.py`: las variables de cada modelo generativo (la fila t usa solo seq[:t]) y el logit condicional con offset.
- `experimento.py`: el experimento completo. Genera `salida_experimento.txt`, `resultados.json` y `P_primario.npy`.
- `diagnostico_fronteras.py`: genera `salida_diagnostico.txt`.
- `congelar.py`: calcula θ(G1) = −0,0401 con todo [2000, 9357) y lo escribe en `parametros.json`.
- `modelo.py`: `Modelo` = ensamble_v2 del repo con la corrección G1 congelada. Admite días de 11 o 12
  sorteos. Es peor que el ensamble y **no se propone como candidato**.
- `prueba_fuga.py`: `lotto_eval.prueba_fuga` sobre prefijo(2600), desde 2000, da (True, None, 0.0).
  El ensamble recalculado coincide con la caché (máx |dif| 1,2e-6).

## Reproducir
```
cd motor_nuevo/ag05_baraja_operador
$env:PYTHONIOENCODING="utf-8"; python experimento.py; python diagnostico_fronteras.py; python congelar.py; python prueba_fuga.py
```
El experimento tarda unos 60 s.
