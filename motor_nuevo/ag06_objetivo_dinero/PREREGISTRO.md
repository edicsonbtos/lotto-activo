# Prerregistro ag06_objetivo_dinero (escrito antes de correr el experimento principal, 2026-09-25)

## Hipótesis
El ensamble_v2 se ajustó por log-verosimilitud, que reparte el esfuerzo sobre los 38 animales.
El dinero del Top-5 escalonado 2-2-2-1-1 depende solo del ORDEN de los 5 primeros. Un reordenador
entrenado para maximizar directamente ese retorno (pérdida lista-a-lista suavizada) podría ganar
dinero aunque no gane mbits.

## Mecanismo / modelo
Puntaje por animal: s_i = logit_ens_i + x_i · w   (logit_ens = log P_ens, peso fijo 1, fija la escala).
x_i: 9 variables de contexto binarias (rasgos.py), la fila t usa solo seq[:t]:
 1. s1_vec1: número de tablero a distancia 1 del último ganador s1 (0 y 00 sin número)
 2. s1_digito: mismo último dígito que s1
 3. s1_col: misma columna (mod 3) que s1
 4. sucesor_s1: el animal que siguió a s1 la vez anterior que salió s1
 5. predecesor_s1: el que precedió a s1 la vez anterior
 6. ult_ayer: último animal de la jornada anterior
 7. ayer_misma_hora: el que salió ayer a la misma hora
 8. hueco_12_23: salió por última vez hace 12-23 sorteos
 9. hueco_24_35: salió por última vez hace 24-35 sorteos
(Divulgación: las variables 1-5 se inspiran en el hallazgo publicado por ag02; el ángulo de este agente
es la PÉRDIDA, no las variables. Por eso se compara contra un control con las mismas variables y log-loss.)

Pérdida de dinero (primaria, "V_dinero"): rango suave del ganador w
  r = 1 + Σ_{j≠w} sigmoid((s_j − s_w)/τ),  τ = 0,25
  ganancia suave g(r) = sigmoid((3,5 − r)/σ) + sigmoid((5,5 − r)/σ),  σ = 0,5  (≈ fichas 2,2,2,1,1)
  minimizar −mean g(r) + λ‖w‖²,  λ = 1e-3 (por fila media), L-BFGS desde w = 0.
Probabilidad publicada: P = softmax(c · s), con c escalar ajustado por log-loss en el MISMO conjunto de
entrenamiento del bloque (no cambia el orden; solo sirve para que los mbits tengan sentido).

Control ("V_logloss", informativo): mismas variables, s = logit_ens + x·w, softmax con entropía cruzada,
λ igual (L2 = 1e-3 por fila), c = 1.

## Ajuste (anti-fuga)
Cross-fitting en 5 bloques CONTIGUOS de jornadas del desarrollo [2000, 9357): cada fila se predice con w y c
ajustados sin su bloque. Hiperparámetros τ, σ, λ fijados aquí, sin mirar resultados.
modelo.py: w y c congelados ajustando con todo [2000, 9357) (V_dinero).

## Métricas y falsación
Primaria del arnés: Δmbits frente al ensamble (arnes.evaluar). Barra: Δ >= +3, IC95 inferior > 0, ambas mitades > 0.
Específica del ángulo: Δ retorno por ficha del Top-5 escalonado (IC95 por jornadas).
Se considera FALSADA la idea del objetivo-dinero si V_dinero no supera en Δret_t5 al control V_logloss
(la pérdida de dinero no aporta sobre la log-loss) o si su Δret_t5 tiene IC que incluye 0.
Si mejora el dinero pero no los mbits, se dirá explícitamente.
Máximo previsto: 2 variantes (V_dinero, V_logloss) + a lo sumo 1 de sensibilidad de τ (0,1). Más => exploratorio.

## Desviaciones (añadidas después de correr)
- D1: tras ver que V_dinero falló, se añadió UNA variante exploratoria (V4, `exploratorio_v4.py`): pérdida de
  dinero con τ = 0,05 arrancando desde la solución log-loss del mismo entrenamiento. Es la 4ª variante, así que
  cuenta como exploratoria y no puede ser candidata. Para ello `nucleo.ajustar` admite `w0` (sin cambiar el resto).
- D2: se añadió `diagnostico_sobreajuste.py` (retorno dentro/fuera de muestra por bloque), sin nueva variante.
