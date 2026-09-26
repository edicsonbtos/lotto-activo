# Prerregistro ag08_periodicidad (escrito ANTES de correr el barrido y el experimento)

Fecha: 2026-09-25. Tramo: desarrollo [2000, 9357) vía `arnes.datos()` / `arnes.base()`. Nada >= 9357.
Hecho antes de escribir esto (solo estructura, sin mirar animales frente a resultados): n=7357 filas,
`hora` es índice 0..11, 371 jornadas de 12 sorteos, 263 de 11, 1 de 9 y 1 de 3.

## Hipótesis
H1: además del "no repetir hoy / reciclar a 1-2,5 días" que el ensamble_v2 ya captura, existe estructura
temporal fina que el ensamble NO captura: periodicidades por animal (desfases de 12, 24, 36, 38, 76, 84
sorteos), efectos calendario (día de la semana x hora x hueco), o un recorrido del tablero (el operador
avanza por el orden del tablero: diferencia (y_t − y_{t−L}) mod 38 no uniforme).

Mecanismo plausible: un operador humano o un "barajador" con ciclo fijo (día, semana, 38 sorteos) dejaría
huella en esas frecuencias. H0: RNG certificado + evitación intradía ya modelada => residuos del ensamble sin estructura.

## Todo se mide como RESIDUO frente al ensamble
Para una variable indicadora f(t,a) (1 si el candidato a cumple la condición en el sorteo t, usando solo seq[:t]
y el calendario del propio t): O = Σ_t f(t, y_t), E = Σ_t Σ_a f(t,a)·P_ens[t,a], V = Σ_t (e_t − e_t²) con
e_t = Σ_a f(t,a)P_ens[t,a]; z = (O−E)/√V; p bilateral normal.

## Familias del barrido (fijas de antemano)
- F1 desfase agregado: f = 1[a = seq[t−L]], L = 1..168 (168 pruebas; objetivo: 12, 24, 36, 38, 76, 84).
- F1b misma hora hace k días naturales: f = 1[a = animal del día (dia_t − k) con la misma `hora`], k = 1..7 (7).
- F2 desfase por animal: f = 1[a = A y seq[t−L] = A], A = 38 animales, L ∈ {12, 24, 36, 38, 76, 84} (228).
- F3 espectral del residuo: r_t(a) = 1[y_t=a] − P_ens[t,a]; ordenada I = |Σ r_t e^{−2πit/T}|² / Σ p(1−p).
  F3a por animal y T ∈ {12, 24, 36, 38, 76, 84} (228; I ≈ Exp(1) => p = e^{−I}).
  F3b agregada Σ_a I_a (≈ Gamma(38,1)) para T = 2..200 (199).
- F4 calendario x hueco: hueco g(t,a) = sorteos desde la última salida de a; tramos
  {1-5, 6-11, 12-23, 24-35, 36-47, 48-71, 72-119, 120+/nunca}. f = 1[g en tramo b y hora_t = h] (96),
  1[g en b y dow_t = d] (56), 1[g en 12-35 y dow_t = d y hora_t = h] (84). Total 236.
- F5 animal x calendario: f = 1[a = A y hora_t = h] (456), 1[a = A y dow_t = d] (266).
- F6 recorrido del tablero: f = 1[(a − seq[t−L]) mod 38 = δ], δ = 1..37, L ∈ {1, 2, 12, 38} (148).
Total ≈ 1940 pruebas.

## Descubrimiento y confirmación
- Barrido en la MITAD 1 (filas [0, 3678) del desarrollo, la misma mitad que usa `arnes.evaluar`).
  Corrección Benjamini-Hochberg q = 0,05 sobre TODAS las pruebas juntas.
- Confirmación en la MITAD 2 (filas [3678, 7357)): un superviviente se confirma si z tiene el mismo signo
  y p unilateral < 0,05 / (nº de supervivientes) (Bonferroni).
- Advertencia: la mitad 2 también entra en la evaluación final; eso se declara.

## Predictor (solo con lo confirmado)
P_cand(t,a) ∝ P_ens(t,a)·exp(Σ_k θ_k f_k(t,a)). θ por máxima verosimilitud condicional (logit multinomial con
offset log P_ens) y ridge λ = 1 (sobre la escala de las indicadoras), por **cross-fitting en 5 bloques
contiguos de jornadas** del desarrollo completo: la fila de cada bloque se predice con θ ajustado en los otros 4.
- Si NINGUNA prueba se confirma, el candidato de reserva (fijado ahora, no elegido mirando) es el de las
  6 indicadoras de desfase objetivo F1 L ∈ {12, 24, 36, 38, 76, 84} + F1b k = 1 y k = 7 (8 variables),
  con el mismo cross-fitting. Se reporta aunque salga negativo.
- `modelo.py`: ensamble_v2 del repo + corrección con θ congelado ajustado en todo [2000, 9357).

## Qué falsa H1
- Ningún superviviente BH en la mitad 1, o ninguno confirmado en la mitad 2 => no hay periodicidad útil.
- Barra del candidato (arnes): Δ ≥ +3 mbits, IC95 inferior > 0, positivo en ambas mitades. Si no, NO PASA.
- Variantes: 1 primaria. Cualquier otra se cuenta y se reporta; > 3 => exploratorio.

## Desviaciones (añadidas después del barrido, antes del experimento)
- Resultado del barrido (salida_barrido.txt): 1936 pruebas, 1 superviviente BH (F4: hueco 72-119 x hora 7,
  z=+4,64 en mitad 1), NO confirmado en mitad 2 (z=+1,30). => se corre el candidato de RESERVA prerregistrado.
- Variante 2, EXPLORATORIA (decidida viendo que F4 tuvo 25 pruebas con p<0,05 frente a 11,8 esperadas):
  apilar la familia F4 completa (236 indicadoras) con ridge λ=30 (fijado a priori, sin barrer), mismo cross-fitting.
  No es el primario y cuenta como variante adicional.
- Nota técnica: en F3b, T=2 la ordenada es real (chi² de 1 gl por animal), la aproximación Gamma(38) no es exacta ahí.
