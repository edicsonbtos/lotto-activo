# Prerregistro ag05_baraja_operador (ronda 1, 2026-09-25)

Escrito ANTES de correr el experimento principal. Solo se ha mirado: nº de sorteos por día en
desarrollo (444 días de 11, 371 de 12, 3 días raros) y la tasa de repetición intradía en desarrollo
(6,1 % frente a 15,8 % si fuera iid). Nada más.

## Hipótesis
El operador genera los resultados como una **baraja**: saca sin reemplazo (con fuga ε) de un mazo que
se rehace en fronteras FIJAS (cada D días naturales con fase φ, o cada 38 sorteos con fase φ), o impone
una **cuota** por ventana deslizante de N sorteos. Si el mazo tiene fronteras fijas, los animales ya
salidos "en este mazo" (no solo hoy) deberían estar deprimidos, y una fase φ debería destacar
claramente sobre las demás. Eso sería información que el ensamble_v2 (que ve huecos, recencia,
"salió hoy" y ventanas de días) no tiene en forma explícita.

## Modelos generativos (todos definen P(x_t = a | seq[:t]) de forma secuencial, así que la
verosimilitud es EXACTA: producto de condicionales)
Forma común: P_t(a) ∝ exp(θ · f_a(t)) (logit condicional de pocos parámetros; θ = log ε de la fuga).
- **G0 uniforme** (referencia).
- **G1 mazo diario**: f = [a salió hoy]. (1 parámetro)
- **G2 mazo de D días, D ∈ {2, 3, 4}, fase φ ∈ {0..D−1}**: el mazo se rehace el día natural d con
  (d − φ) mod D = 0. f = [a salió hoy, a salió en el mazo actual antes de hoy]. (2 parámetros, fase discreta)
- **G3 mazo de 38 cartas por conteo**: se rehace cada 38 sorteos del índice global con fase φ ∈ {0..37}.
  f = [salió hoy, salió en el mazo actual]. (2 parámetros, fase discreta)
- **G4 cuota deslizante N ∈ {12, 24, 36, 48, 72}**: f = [salió hoy, cuenta en los últimos N sorteos = 1,
  cuenta >= 2]. (3 parámetros)
- **G5 control sin fronteras** (recencia pura): f = one-hot de días desde la última aparición
  (0, 1, 2, 3, 4+; 0 = hoy). Sirve para ver si las fronteras fijas añaden algo sobre la recencia.

## Ajuste (anti-fuga)
Cross-fitting en 5 bloques CONTIGUOS de jornadas del tramo [2000, 9357). Para cada bloque, con las
filas de los otros 4: se ajusta θ de cada modelo y cada valor discreto (D, φ, N) por máxima
verosimilitud, y se ELIGE el mejor modelo/valor discreto por log-verosimilitud de entrenamiento
(con penalización BIC por nº de parámetros continuos). Con eso se predice el bloque retenido.
Las variables f de la fila t usan solo seq[:t] y el calendario (día natural) del sorteo t.

## Predictor apilado (candidato primario, fijado ahora)
z = log P_ens + θ · f_best (el ensamble entra con peso 1 como offset), θ y f_best elegidos en los
4 bloques de entrenamiento como arriba pero ajustando CON el offset del ensamble (la selección del
modelo se hace por la verosimilitud apilada de entrenamiento). Se evalúa con arnes.evaluar.

Informativo (no candidato): cada Gk solo (mbits frente al uniforme, verosimilitud por fase para G2 y G3,
para ver si alguna fase destaca), y cada Gk apilado por separado.

## Qué falsa la hipótesis
- Fronteras fijas: si en G2/G3 ninguna fase supera a las demás por más de lo que da el ruido
  (dispersión entre fases comparable a la de fases barajadas), y G2/G3 no mejoran a G1+G5,
  no hay mazo con fronteras fijas.
- Como predictor: si el apilado no da Δ >= +3 mbits con IC95 inferior > 0 y positivo en ambas mitades,
  NO pasa la barra. Lo esperado a priori: el ensamble ya captura "salió hoy" y la recencia, así que
  lo más probable es Δ ≈ 0.

## Variantes
Una primaria (el apilado arriba). Si hago otra variante, la cuento y lo informo; más de 3 → exploratorio.
