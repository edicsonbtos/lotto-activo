export const meta = {
  name: 'motor-nuevo-reanudar',
  description: 'Reanuda el loop motor-nuevo tras el apagón: verifica ag02/ag10/ag01 (ronda 1 ya hecha) y sigue rondas si nadie sobrevive',
  phases: [
    { title: 'Verificar', detail: 'reproducción independiente + revisor-sesgo por candidato de la ronda 1' },
    { title: 'Estrategia', detail: 'nuevos ángulos si nadie pasa' },
    { title: 'Buscar', detail: '10 agentes por ronda nueva' },
  ],
}
const WT = 'C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor'
const MAX_ROUNDS = 3

const COMMON = `
CONTEXTO (Lotto Activo, 38 animales, ~12 sorteos/día; paga 30x):
- Trabajas SOLO en el worktree ${WT} (rama motor-nuevo). NO toques el repo principal C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo ni el motor en producción (herramientas/modelos/*, servidor.py, prediccion.py, pesos_ensamble.json, historial.txt, predicciones.json). No hagas git commit ni push. No despliegues nada.
- Lee primero ${WT}\\motor_nuevo\\PREREGISTRO.md y ${WT}\\motor_nuevo\\arnes.py (arnés común), y ${WT}\\.claude\\skills\\lotto-nueva-idea\\SKILL.md (lista de ideas YA CERRADAS: no las repitas sin una razón nueva y explícita). Mira también herramientas/resultados/ y verificacion/hilo9/INFORME.md si necesitas saber qué se probó.
- DATOS: solo desarrollo, filas [2000, 9357) de historial.txt vía arnes.datos()/arnes.base(). PROHIBIDO usar o mirar filas >= 9357. PROHIBIDO descargar o leer historial de Lotto Activo anterior a 2023-09-04 (es el tramo sellado de la prueba final). No uses RD Internacional ni otras loterías como variables (RD no existe antes de 2023-09 y la dirección RD->LA ya falló a ciegas).
- La única estructura conocida: el operador evita repetir el animal el mismo día y recicla con 1-2,5 días de hueco. El ensamble_v2 da +120 mbits en desarrollo; ya lo captura.
- Métrica primaria: Δmbits frente al ensamble con arnes.evaluar(P_cand). Barra de candidato (pasa_barra_dev): Δ >= +3 mbits, IC95 por jornadas con límite inferior > 0, y positivo en las dos mitades.
- ANTI-FUGA: la fila t (sorteo W+j) solo usa seq[:t]. Todo parámetro ajustado se estima por cross-fitting en bloques CONTIGUOS de jornadas (p. ej. 5 bloques de días: la fila se predice con parámetros ajustados SIN su bloque) o por forward-chaining. Nada in-sample.
- Entregables en ${WT}\\motor_nuevo\\<tu_carpeta>\\ :
  1) PREREGISTRO.md escrito ANTES de correr el experimento principal (hipótesis, mecanismo, variables, cómo se ajusta, qué resultado la falsaría). Si luego cambias algo, anótalo como desviación, no lo borres.
  2) experimento.py reproducible (semillas fijas) que imprime arnes.informe(...) y guarda resultados.json con arnes.evaluar(...).
  3) modelo.py con class Modelo (interfaz de herramientas/lotto_eval.py: nombre, predecir(datos, desde) -> (n-desde, 38), fila j usa solo datos[:desde+j]) que cargue parámetros CONGELADOS de un archivo de tu carpeta ajustados SOLO con filas < 9357, capaz de correr sobre otro historial (días de 11 o 12 sorteos). Si tu idea es una corrección sobre el ensamble, modelo.py puede cargar el ensamble_v2 del repo (herramientas/modelos/ensamble_v2.py + pesos_ensamble.json) y aplicar la corrección. Verifica que pasa lotto_eval.prueba_fuga sobre un prefijo corto (p. ej. datos.prefijo(2600), desde 2000).
  4) README.md: qué se probó, números exactos (copiados de la salida), veredicto honesto.
- RECURSOS: 4 CPUs y ~5 GB libres compartidos con otro agente: usa <= 1,5 GB de RAM y un solo hilo pesado. Limita cada corrida completa a ~40 min; prueba primero en un subconjunto. Python: \`python\` (3.14, numpy, scipy, scikit-learn, lightgbm instalados). Consola Windows: usa PYTHONIOENCODING=utf-8.
- HONESTIDAD: si no pasa la barra, dilo. No ajustes la idea mirando el resultado y vuelvas a medir hasta que pase (si iteras, cuenta cuántas variantes probaste e infórmalo; más de 3 variantes => el resultado final se reporta como exploratorio).
`

const ANGLES1 = [
  { slug: 'ag01_gbm_ranker', text: 'Modelo de árboles potenciados (lightgbm, objetivo multiclase o lambdarank por sorteo) sobre variables por (sorteo, animal): hueco en sorteos y en días, veces hoy/ayer/anteayer, hora/k, posición del día, repeticiones del día, conteos en ventanas 12/24/36/60/120, rango del animal en el ensamble y su logit. Busca interacciones no lineales que el log-lineal no ve. Compáralo solo y apilado (logit del ensamble como variable).' },
  { slug: 'ag02_residuo_boost', text: 'Corrección residual sobre el ensamble: logit_final = logit_ensamble + g(x), con g aprendida para maximizar la log-verosimilitud condicional (softmax por sorteo), con regularización fuerte. Variables que el ensamble NO tiene explícitas: secuencias exactas de los últimos 2-3 ganadores, patrones de pares del día, orden en que salieron los animales de ayer, "último sorteo del día anterior", distancia en el tablero numérico. Usa cross-fitting.' },
  { slug: 'ag03_red_secuencial', text: 'Red neuronal secuencial (MLP o red recurrente pequeña implementada en numpy/scikit-learn) que ve los últimos 36-72 ganadores codificados (one-hot + hora + marca de cambio de día) y emite la distribución de 38. Equivariante a permutación de animales (comparte pesos entre animales: la identidad del animal no importa) para no sobreajustar. Evalúa sola y como experto apilado con el ensamble.' },
  { slug: 'ag04_no_estacionario', text: 'No estacionariedad: ¿la política del operador cambia con el tiempo? Reajusta los pesos del ensamble y/o los parámetros de sus submodelos con olvido exponencial (forward-chaining, re-ajuste cada N jornadas usando solo pasado), o con filtro de Kalman sobre los coeficientes. Prueba si un ensamble adaptativo supera al de pesos fijos.' },
  { slug: 'ag05_baraja_operador', text: 'Modelo generativo del operador como "baraja": el operador podría sacar sin reemplazo de un mazo que se rehace cada D días, o imponer cuotas por ventana (cada animal ~k veces cada N sorteos). Formula varias versiones generativas explícitas (mazo diario, mazo de 2-4 días, cuota deslizante), calcula la verosimilitud exacta o aproximada de cada una y usa la mejor como predictor. Compara con el ensamble y apílalo.' },
  { slug: 'ag06_objetivo_dinero', text: 'Optimizar directamente el dinero: en vez de log-verosimilitud, entrena un reordenador (sobre el logit del ensamble + variables de contexto) con una pérdida lista-a-lista que maximice el retorno del Top-5 escalonado 2-2-2-1-1 (pérdida suavizada, p. ej. softmax con temperatura sobre el puesto). Reporta Δ retorno por ficha con IC por jornadas además de Δmbits. Si mejora el dinero pero no los mbits, dilo claro.' },
  { slug: 'ag07_mezcla_expertos', text: 'Mezcla de expertos con compuerta dependiente del contexto: los pesos del ensamble (intradia_v2, secuencia_v3, haz_v1 y un modelo de recencia simple) varían según k/hora, nº de repeticiones del día y dispersión de la distribución. Ajusta la compuerta (regresión multinomial pequeña) por cross-fitting. Carga los submodelos del repo (herramientas/modelos) para tener sus predicciones walk-forward en desarrollo (cachea en tu carpeta).' },
  { slug: 'ag08_periodicidad', text: 'Periodicidades y estructura temporal fina no probadas: análisis espectral/autocorrelación de la serie de cada animal a desfases 12, 24, 36, 38, 76, 84 (semana) sorteos; efectos de día de la semana x hora x hueco; ciclos de 38 sorteos (¿el operador recorre el tablero?). Primero un barrido con corrección de BH en la mitad 1 del desarrollo, confirmar en la mitad 2, y solo entonces construir un predictor con lo que sobreviva.' },
  { slug: 'ag09_multi_escala', text: 'Suavizado multi-escala / modelo bayesiano jerárquico de la curva de hueco: en vez de bins fijos, estima la tasa de repetición como función continua de (hueco en sorteos, hueco en días, hora de la última salida, hora actual, veces que salió en los últimos 3 días) con splines penalizados y efectos aleatorios, y combínala con la regla del mismo día. Objetivo: extraer la curva de reciclaje con menos varianza que el ensamble.' },
  { slug: 'ag10_comodin', text: 'Comodín crítico: lee los informes cerrados (hilos 1-9, Operación Turing, verificacion/hilo9) y busca la hipótesis con más potencial que NADIE ha probado todavía (distinta de los otros 9 ángulos: GBM, residuo, red secuencial, no estacionariedad, baraja del operador, objetivo dinero, mezcla de expertos, periodicidad, suavizado multi-escala). Justifica por qué es nueva, prerregístrala y pruébala.' },
]

const RESULT = {
  type: 'object',
  properties: {
    slug: { type: 'string' },
    idea: { type: 'string' },
    carpeta: { type: 'string' },
    delta_mbits: { type: 'number' }, ci_lo: { type: 'number' }, ci_hi: { type: 'number' },
    mitad1: { type: 'number' }, mitad2: { type: 'number' },
    top5_cand: { type: 'number' }, top5_ens: { type: 'number' },
    delta_ret_t5: { type: 'number' },
    pasa_barra_dev: { type: 'boolean' },
    variantes_probadas: { type: 'integer' },
    fuga_ok: { type: 'boolean' },
    veredicto: { type: 'string' },
    comando_reproducir: { type: 'string' },
  },
  required: ['slug', 'idea', 'carpeta', 'delta_mbits', 'ci_lo', 'ci_hi', 'pasa_barra_dev', 'variantes_probadas', 'fuga_ok', 'veredicto', 'comando_reproducir'],
}

const VERDICT = {
  type: 'object',
  properties: {
    ok: { type: 'boolean' },
    delta_reproducido: { type: 'number' },
    problemas: { type: 'array', items: { type: 'string' } },
    resumen: { type: 'string' },
  },
  required: ['ok', 'problemas', 'resumen'],
}

const ANGLES_SCHEMA = {
  type: 'object',
  properties: { angulos: { type: 'array', items: { type: 'object', properties: { slug: { type: 'string' }, text: { type: 'string' } }, required: ['slug', 'text'] } } },
  required: ['angulos'],
}

function research(a, round) {
  return agent(`${COMMON}\n\nTU ÁNGULO (${a.slug}, ronda ${round}): ${a.text}\n\nCrea tu carpeta ${WT}\\motor_nuevo\\${a.slug}\\ y entrega todo. Devuelve el resumen estructurado con los números EXACTOS de arnes.evaluar (delta_mbits = media, ci_lo/ci_hi = IC95, mitad1/mitad2 = medias por mitad, delta_ret_t5 = media).`,
    { label: `buscar:${a.slug}`, phase: 'Buscar', schema: RESULT })
}

function verify(r) {
  const repro = agent(`Eres un verificador independiente y escéptico. En el worktree ${WT} (rama motor-nuevo) un agente afirma que su candidato ${r.slug} (carpeta ${r.carpeta}) supera al ensamble_v2 en desarrollo: Δmbits ${r.delta_mbits} [${r.ci_lo}, ${r.ci_hi}]. Comando: ${r.comando_reproducir}.
${REPRO_NOTA[r.slug] || ''}
1) Re-ejecuta el experimento desde cero (borra cachés propios de la carpeta si los hay, con PYTHONIOENCODING=utf-8) y confirma que el Δ se reproduce (tolerancia ±0,5 mbits).
2) Corre lotto_eval.prueba_fuga sobre su modelo.py con un prefijo corto y verifica que modelo.py produce, para las filas de desarrollo, predicciones coherentes con el experimento (sin usar la fila t).
3) Revisa el código buscando fuga: uso de filas >= 9357, parámetros ajustados con la fila predicha, normalización con datos futuros, selección de hiperparámetros sobre el mismo tramo sin cross-fitting, desempates que inflen, y si probó muchas variantes (sobreajuste por selección).
No modifiques su código; si necesitas scripts auxiliares, ponlos en ${r.carpeta}\\_verificacion\\. ok=true solo si todo se sostiene.`,
    { label: `repro:${r.slug}`, phase: 'Verificar', schema: VERDICT })
  const sesgo = agent(`Audita de forma adversarial el candidato ${r.slug} en ${r.carpeta} (worktree ${WT}, rama motor-nuevo). Afirma Δmbits ${r.delta_mbits} [${r.ci_lo}, ${r.ci_hi}] frente al ensamble_v2 en desarrollo [2000, 9357), con ${r.variantes_probadas} variantes probadas. Busca fuga (look-ahead), sobreajuste al tramo de desarrollo, selección múltiple, empates que inflen, y cualquier motivo por el que no vaya a generalizar a otra época (tramo sellado de 2020-2023 con 11 sorteos/día). Lee su PREREGISTRO.md, experimento.py, modelo.py y resultados. No modifiques nada. ok=true solo si no encuentras un problema que invalide el resultado.`,
    { label: `sesgo:${r.slug}`, phase: 'Verificar', schema: VERDICT, agentType: 'revisor-sesgo' })
  return parallel([() => repro, () => sesgo]).then(([v1, v2]) => ({ ...r, repro: v1, sesgo: v2, sobrevive: !!(v1 && v1.ok && v2 && v2.ok) }))
}


const R1 = [
 {
  "slug": "ag02_residuo_boost",
  "idea": "Linear residual correction on ensamble_v2: logit = log P_ens + x·w, fitted with a conditional softmax, L2 lambda=30, cross-fitted over 5 contiguous blocks of days. It uses 27 content variables the ensemble does not see: board relations to the last 3 winners (±1 neighbour, same digit, column, row, tens), the successor and predecessor of s1 the last time it came out, the successor of the pair (s2,s1), and yesterday's order and last draw. The two strong signals: the operator avoids repeating the s1→i transition that already happened (O/E 0.58, z -5.8, clean placebo at other anchors) and avoids animals that look like the last one on the board (neighbour, same digit, same column).",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag02_residuo_boost",
  "delta_mbits": 12.151714524974476,
  "ci_lo": 7.6395235162390644,
  "ci_hi": 16.750403285511705,
  "mitad1": 12.563065389885006,
  "mitad2": 11.740475470573575,
  "delta_ret_t5": 0.07543835802636945,
  "top5_cand": 0.21557700149517467,
  "top5_ens": 0.202528204431154,
  "pasa_barra_dev": true,
  "variantes_probadas": 4,
  "fuga_ok": true,
  "veredicto": "The primary variant V1 (linear, lambda=30, pre-registered before running) PASSES the development bar: +12.15 mbits, 95% CI [+7.64, +16.75], half 1 +12.56, half 2 +11.74. Top-5 is 21.56% vs 20.25%, and the tiered Top-5 return per chip is +0.075 [+0.029, +0.120].\n\nFour variants were run, but the candidate was fixed in advance and none was picked by looking at results. The other three all pass too: V2 LightGBM +11.51 [+8.41, +14.72], lambda=10 gives +12.05 and lambda=100 gives +11.64. The stricter informative forward-chaining check gives +9.03 [+5.21, +12.98].\n\nChecks:\n- The weights keep the same sign in all 5 blocks.\n- The placebo concentrates the effect at the s1 anchor with offset ±1; the s2, s3 and t-6 anchors are flat.\n- The ablation shows board (+6.15) and pairs (+5.45) contributing separately.\n- prueba_fuga passes (True, None, 0.0), and the ensemble rebuilt in modelo.py matches the cache to 2.8e-17.\n\nThis contradicts earlier findings (Markov/Turing gave noise), so the bias reviewer should audit it before it is frozen for the sealed test. It is a candidate, not a confirmed improvement.",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor; $env:PYTHONIOENCODING=\"utf-8\"; python motor_nuevo/ag02_residuo_boost/experimento.py; python motor_nuevo/ag02_residuo_boost/congelar.py; python motor_nuevo/ag02_residuo_boost/prueba_fuga.py"
 },
 {
  "slug": "ag01_gbm_ranker",
  "idea": "LightGBM trained with a per-draw softmax objective (conditional logit) on 15 causal features per (draw, animal): gaps in draws (last and second-to-last appearance) and in days, times today/yesterday/day before, hour, position in the day, same-day repeats, draws since it came out today, counts in windows 12/24/36/60/120. Variant A uses the trees alone. Variant B, the candidate, is stacked: it adds log P_ens and the ensemble rank as features, with init_score = log P_ens. Fitting uses cross-fitting over 5 contiguous blocks of days with a 2-day embargo. A recalibration-only control gives +0.03, and forward-chaining gives +3.37. B passes the mbits bar but barely moves Top-5 or returns.",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag01_gbm_ranker",
  "delta_mbits": 5.870930932814079,
  "ci_lo": 2.9451129458673853,
  "ci_hi": 8.78019520206597,
  "pasa_barra_dev": true,
  "variantes_probadas": 2,
  "fuga_ok": true,
  "veredicto": "Candidate (variant B, stacked) that passes the development bar in mbits: +5.87 [+2.95, +8.78], half 1 +6.27, half 2 +5.47, both with lower CI bound > 0. Recalibration alone explains none of the gain (+0.03), and the signal persists with forward-chaining (past data only: +3.37 [+1.54, +5.21], half 1 +0.86 whose CI crosses 0). The money effect is not significant: Top-5 20.63% vs 20.25%, Top-5 tiered +0.012 per chip [-0.019, +0.044]; Top-3 and Top-15 unchanged. A alone gives -21.85 mbits. The frozen model scores +29.6 on its own training rows, so in-sample overfitting is strong and the honest number is the cross-fit one. Era risk: hour and position in the day carry 21% of the gain, and the sealed stretch has 11 draws per day. There were 2 pre-registered variants and 2 diagnostics. A --rapido pipeline test was seen before the main run (logged as a deviation, nothing changed), so the result is not exploratory.",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor; $env:PYTHONIOENCODING=\"utf-8\"; python motor_nuevo\\ag01_gbm_ranker\\experimento.py",
  "mitad1": 6.270906406999546,
  "mitad2": 5.471064177159241,
  "delta_ret_t5": 0.012233247247519369,
  "top5_cand": 0.2063341035748267,
  "top5_ens": 0.202528204431154
 },
 {
  "slug": "ag03_red_secuencial",
  "idea": "A small MLP shared across the 38 animals (permutation-equivariant). For each animal it sees 116 inputs from the last 72 winners: one-hot winner per lag, a same-day mark, days since the animal last appeared, whether it followed or preceded s1 (the previous draw's winner) the last time s1 won, and hour and position in the day. It was tested alone and stacked as logit = log P_ens + g(x). Parameters were cross-fit on 5 contiguous blocks of days.",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag03_red_secuencial",
  "delta_mbits": 2.053633965379162,
  "ci_lo": -0.30370937220996685,
  "ci_hi": 4.49513018085432,
  "pasa_barra_dev": false,
  "variantes_probadas": 2,
  "fuga_ok": true,
  "veredicto": "Does NOT pass the dev bar. The primary variant (network stacked on the ensemble) gives +2.05 mbits with 95% CI [-0.30, +4.50]. Half 1 is +1.11 and half 2 is +3.00, neither significant. Alone, the network gives -50.04 mbits [-59.63, -40.35]. Forward-chaining (informative) gives -0.99 [-4.24, +2.38]. The +0.04 Top-5 return in the cross-fit does not hold up under forward-chaining (-0.02), so I do not count it as a signal. The equivariant network finds nothing robust beyond ensemble_v2; the small effect that remains probably comes from the successor-of-s1 feature, which ag02 already captures better. The frozen model passes prueba_fuga with (True, None, 0.0). Variants: 2 pre-registered plus 1 diagnostic, and nothing was tuned after seeing results.",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag03_red_secuencial; $env:PYTHONIOENCODING='utf-8'; $env:OPENBLAS_NUM_THREADS='1'; python experimento.py; python congelar.py; python prueba_fuga.py",
  "mitad1": 1.108572186998494,
  "mitad2": 2.998438863689599,
  "delta_ret_t5": 0.03924833491912464,
  "top5_cand": 0.20878075302433058,
  "top5_ens": 0.202528204431154
 },
 {
  "slug": "ag04_no_estacionario",
  "idea": "A Kalman filter (random walk plus a Laplace update after every draw) that tracks the ensemble_v2 log-linear weights, with q chosen by cross-fitting over 5 contiguous blocks of days. Two secondary variants were also preregistered: V2 refits every 50 draws with short forgetting (tau chosen by cross-fitting) and V3 adds fast-forgetting submodels. None passes. The best gain is +0.6 mbits against the +3 the bar requires, and every IC95 crosses 0. The ensemble_v2 already adapts fast enough and shows no exploitable drift.",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag04_no_estacionario",
  "delta_mbits": 0.5019751858160426,
  "ci_lo": -0.649685765794005,
  "ci_hi": 1.7302702587753283,
  "mitad1": 0.36645586623258025,
  "mitad2": 0.6374576694876855,
  "delta_ret_t5": 0.0025485931765665353,
  "top5_cand": 0.20429522903357347,
  "top5_ens": 0.202528204431154,
  "pasa_barra_dev": false,
  "variantes_probadas": 3,
  "fuga_ok": true,
  "veredicto": "DOES NOT PASS. Primary V1 (Kalman): Δ +0.50 mbits [-0.65, +1.73], half 1 +0.37, half 2 +0.64, Top-5 20.43% vs 20.25%. V2 (short forgetting, R=50): +0.58 [-0.52, +1.71]. V3 (fast submodels): +0.15 [-0.52, +0.85]. Adapting faster makes it worse: with q=1e-4 the result is +119.51 mbits against +120.1 for the ensemble. The Kalman weights move within the band expected from noise, with no change of regime. The quarterly Δ swings between -1.3 and +2.9 with no trend. The ensemble rebuilt from the submodel cache matches the harness cache (max|dif| 6e-6). prueba_fuga returned (True, None, 0.0). The model is frozen in modelo.py (q=1e-5). It is not a candidate. There were 3 preregistered variants and no iteration, so the result is not exploratory.",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag04_no_estacionario; $env:PYTHONIOENCODING='utf-8'; python cache_sub.py base; python cache_sub.py rapidos; python experimento.py; python prueba_fuga.py"
 },
 {
  "slug": "ag06_objetivo_dinero",
  "idea": "Reordenador lineal sobre el logit del ensamble_v2 con 9 variables de contexto (tablero y sucesor/predecesor de s1, ayer, huecos 12-23/24-35), entrenado con una pérdida suavizada de dinero del Top-5 escalonado 2-2-2-1-1 (rango suave del ganador con sigmoides, τ=0,25), comparado con un control log-loss que usa las mismas variables. Cross-fit en 5 bloques contiguos de jornadas.",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag06_objetivo_dinero",
  "delta_mbits": -60.48332503174103,
  "ci_lo": -69.44235534783968,
  "ci_hi": -51.46889316562806,
  "mitad1": -49.059389959354675,
  "mitad2": -71.9041549301474,
  "delta_ret_t5": -0.03466086720130488,
  "top5_cand": 0.19478048117439173,
  "top5_ens": 0.202528204431154,
  "pasa_barra_dev": false,
  "variantes_probadas": 4,
  "fuga_ok": true,
  "veredicto": "FALLA. La variante primaria V_dinero empeora los mbits y el dinero: −60,48 mbits [−69,44, −51,47] y Δret Top-5 de −0,035 [−0,094, +0,026]. No mejora el dinero a costa de los mbits: empeora las dos cosas. La sensibilidad τ=0,1 da −39,31 mbits y −0,04 por ficha. La V4 exploratoria (afinar el dinero desde la solución log-loss, añadida después de ver el fallo) da −19,31 mbits y −0,01 por ficha. El diagnóstico muestra que el sustituto suave ni siquiera sube el retorno real dentro de muestra, y que empuja hueco_12_23 hasta w≈+2. Además, la señal de dinero es escasa: solo acierta ~20 % de las filas. El control V_logloss, con las mismas 9 variables, sí pasa la barra: +9,51 mbits [+5,60, +13,28], mitades +10,39 y +8,64, y Δret +0,06 [+0,02, +0,10]. Pero no es la idea de este agente: replica el hallazgo de ag02 y no se propone como candidato propio. Conclusión: con estos datos, entrenar por log-verosimilitud da más dinero que entrenar para el dinero. Hubo 4 variantes (3 pre-registradas y 1 exploratoria). prueba_fuga sobre prefijo(2600), desde 2000, da (True, None, 0.0).",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag06_objetivo_dinero; $env:PYTHONIOENCODING='utf-8'; python experimento.py; python prueba_fuga.py; python diagnostico_sobreajuste.py; python exploratorio_v4.py"
 },
 {
  "slug": "ag05_baraja_operador",
  "idea": "Se modeló al operador como una baraja: mazo diario (G1), mazo de 2 a 4 días con fase fija (G2), mazo de 38 sorteos con fase (G3), cuota deslizante de N sorteos (G4) y un control de recencia sin fronteras (G5). Son 54 configuraciones con verosimilitud exacta de logit condicional. En cada uno de los 5 bloques contiguos de jornadas se ajustó con los otros 4 y se eligió la configuración por BIC en entrenamiento. Después se apiló sobre el ensamble_v2 como corrección log P_ens + θ·f.",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag05_baraja_operador",
  "delta_mbits": -1.209752138384272,
  "ci_lo": -1.7855430473525584,
  "ci_hi": -0.6456083190798814,
  "pasa_barra_dev": false,
  "variantes_probadas": 1,
  "fuga_ok": true,
  "veredicto": "No pasa la barra: el apilado queda por debajo del ensamble, con −1,21 mbits (IC95 de −1,79 a −0,65), negativo en las dos mitades (−1,16 y −1,26). El Top-5 queda igual (20,25 % contra 20,25 %). La selección eligió G1 (mazo diario) en los 5 bloques, con θ≈−0,04. El θ residual de «salió hoy» cambia de signo entre bloques, así que la corrección solo añade ruido; el ensamble ya tiene bien calibrada esa exclusión. Todas las configuraciones apiladas salen negativas, entre −0,86 y −1,94. Sola, la mejor baraja da +60 mbits contra +120 del ensamble, y la recencia sin fronteras (G5, +60,2) supera a cualquier mazo con frontera fija. En el diagnóstico de fronteras, añadir la pertenencia al mazo (D=2,3,4,5,7, todas las fases) sobre G5 no aporta nada: entre −0,81 y +0,34, con IC que cruzan 0 o negativos. No hay mazo con fronteras fijas. D=5 y D=7 quedaron fuera del prerregistro y se anotaron como desviación informativa. modelo.py se entrega por completitud, pero no es candidato.",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag05_baraja_operador; $env:PYTHONIOENCODING=\"utf-8\"; python experimento.py; python diagnostico_fronteras.py; python congelar.py; python prueba_fuga.py",
  "mitad1": -1.1603432036573176,
  "mitad2": -1.2591476431208144,
  "delta_ret_t5": 0,
  "top5_cand": 0.202528204431154,
  "top5_ens": 0.202528204431154
 },
 {
  "slug": "ag07_mezcla_expertos",
  "idea": "Weights of a log-linear mixture of experts (intradia_v2, secuencia_v3, haz_v1 and a forward-built recency expert) that depend on context: the draw's position in the day (k), how many animals have repeated so far that day, and the spread of the combined distribution. Primary variant V1 is log-linear with weights a+b·x. V2 is a linear mixture with a softmax gate. V3 is V1 without the recency expert. All fitted by cross-fitting over 5 contiguous blocks of days.",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag07_mezcla_expertos",
  "delta_mbits": 0.6659861887897421,
  "ci_lo": -0.8515070958494714,
  "ci_hi": 2.1833209031645446,
  "mitad1": 1.9016738869593195,
  "mitad2": -0.5693656334086011,
  "delta_ret_t5": 0.004587467717819763,
  "top5_cand": 0.20266412940057088,
  "top5_ens": 0.202528204431154,
  "pasa_barra_dev": false,
  "variantes_probadas": 3,
  "fuga_ok": true,
  "veredicto": "NO, the primary V1 does not clear the development bar. It gains +0.67 mbits, IC95 [-0.85, +2.18]; the first half is +1.90 and the second half -0.57. V2 (MoE linear) comes out at -3.32 [-5.54, -1.17] and V3 (without recency) at -0.05 [-1.32, +1.20]. The context coefficients are small (|b| <= 0.17 against base weights of about 0.5-0.7) and the recency expert gets a weight of about -0.05. Letting the ensemble weights depend on context therefore adds nothing usable. All 3 variants were preregistered and none was iterated, so the result is not exploratory. The frozen model.py (V1, parametros.json fitted on rows [1000, 9357)) passes prueba_fuga on prefijo(2600) from 2000: (True, None, 0.0).",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag07_mezcla_expertos; $env:PYTHONIOENCODING=\"utf-8\"; python experimento.py; python congelar.py; python prueba_fuga.py"
 },
 {
  "slug": "ag08_periodicidad",
  "idea": "Barrido prerregistrado de 1936 pruebas sobre los residuos del ensamble_v2: desfases L=1..168, misma hora hace 1..7 días, desfase por animal en 12/24/36/38/76/84, espectro del residuo, día de semana x hora x hueco, animal x hora/día y recorrido del tablero mod 38. BH q=0,05 en la mitad 1 y confirmación en la mitad 2. Hubo 1 superviviente (hueco 72-119 x hora 7) que no se confirmó (z +4,64, luego +1,30), así que se corrió el candidato de reserva prerregistrado: ensamble + 8 indicadoras (desfases 12/24/36/38/76/84 y misma hora hace 1 y 7 días), con theta por cross-fitting en 5 bloques contiguos de jornadas.",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag08_periodicidad",
  "delta_mbits": -0.44596698565053783,
  "ci_lo": -1.8925471682468993,
  "ci_hi": 1.0037198863246688,
  "mitad1": -0.32328058589452335,
  "mitad2": -0.568620037649076,
  "delta_ret_t5": -0.014781840424085904,
  "top5_cand": 0.20048932988990079,
  "top5_ens": 0.202528204431154,
  "pasa_barra_dev": false,
  "variantes_probadas": 2,
  "fuga_ok": true,
  "veredicto": "NO PASA. No encontré ninguna periodicidad útil más allá de lo que ya captura el ensamble. De 1936 pruebas, BH dejó 1 superviviente en la mitad 1 y ninguno se confirmó en la mitad 2. Ninguna periodicidad por animal (día, semana, 38 sorteos) ni el recorrido del tablero se sostienen. El desfase L=38 salió positivo en las dos mitades (z +2,01 y +1,77), pero no sobrevive a BH. Candidato primario: Δ −0,45 mbits [−1,89, +1,00], mitades −0,32 y −0,57, y el Top-5 baja de 20,25 % a 20,05 %. Probé además una variante 2, exploratoria: apilar la familia calendario x hueco entera (236 variables, ridge 30). Da Δ −1,74 [−6,31, +2,97] y tampoco pasa. prueba_fuga da (True, None, 0.0) sobre prefix(2600) desde 2000. modelo.py y parametros.json se entregan congelados, pero no los recomiendo como candidato.",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag08_periodicidad; $env:PYTHONIOENCODING='utf-8'; python barrido.py; python experimento.py; python congelar.py; python prueba_fuga.py"
 },
 {
  "slug": "ag10_comodin",
  "idea": "La composición del día como conjunto y el déjà-vu con memoria de varios días. Nueve variables sumadas al logit congelado del ensamble_v2: co-ocurrencia de i con los animales ya salidos hoy (ayer, en 2-7 días y en 8-30 días), la cuota de reciclaje de ayer, el orden de precedencia dentro del día en 30 días y las transiciones s1->i y s2->i acumuladas en 30 días. Es un logit condicional con L2 λ=30 y cross-fitting en 5 bloques contiguos de jornadas.",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag10_comodin",
  "delta_mbits": 8.544462044415821,
  "ci_lo": 5.034801316124337,
  "ci_hi": 12.172002095122838,
  "mitad1": 10.21846088395276,
  "mitad2": 6.87091821951317,
  "delta_ret_t5": 0.048932988990077475,
  "top5_cand": 0.2098681527796656,
  "top5_ens": 0.202528204431154,
  "pasa_barra_dev": true,
  "variantes_probadas": 1,
  "fuga_ok": true,
  "veredicto": "V1, la variante primaria y única que decide, pasa la barra de desarrollo: +8,54 mbits [+5,03, +12,17], mitad 1 +10,22 y mitad 2 +6,87, Top-5 20,99 % frente a 20,25 %, Top-5 escalonado +0,049 por ficha. En forward-chaining, informativo, da +6,05 [+2,46, +10,00].\n\nPero la parte nueva de la hipótesis, la composición del día, queda falsada. La ablación informativa, añadida después de ver V1, lo muestra: sola da +1,45 [−0,19, +3,19]. Casi toda la ganancia viene de trans1_30, las transiciones s1->i acumuladas en 30 días, con un peso de −0,22 a −0,25 estable en los 5 bloques. Sola, esa variable (junto con trans2_30) da +7,99 mbits. Es el mismo mecanismo que el sucesor_s1 de ag02, ahora con memoria de 30 días en vez de solo la última ocurrencia.\n\nSobre ag02, re-ajustado aquí, suma +5,36 [+2,27, +8,62], pero en la mitad 2 da +3,77 con un IC que cruza 0. Juntos (ag02 + ag10) llegan a +17,04 [+11,02, +23,06] frente al ensamble, un resultado informativo.\n\nRecomendación: si se congela algo para la prueba sellada, que sea ag02 + trans1_30 y no V1 completo. Esa sería una variante nueva, sin medir aquí.\n\nLa prueba de fuga lotto_eval.prueba_fuga sobre prefijo(2600) desde 2000 da (True, None, 0.0).",
  "comando_reproducir": "cd C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor; $env:PYTHONIOENCODING=\"utf-8\"; python motor_nuevo/ag10_comodin/experimento.py; python motor_nuevo/ag10_comodin/ablacion.py; python motor_nuevo/ag10_comodin/congelar.py; python motor_nuevo/ag10_comodin/prueba_fuga.py"
 },
 {
  "slug": "ag09_multi_escala",
  "idea": "Curva de reciclaje continua (splines penalizados de hueco en sorteos/días, hora, veces en 3 días, efecto animal) sumada al logit del ensamble_v2, cross-fit 5 bloques, λ=300",
  "carpeta": "C:\\Users\\edics\\Downloads\\lotto-activo\\lotto-activo-motor\\motor_nuevo\\ag09_multi_escala",
  "delta_mbits": 0.84,
  "ci_lo": -0.8,
  "ci_hi": 2.51,
  "mitad1": -0.01,
  "mitad2": 1.69,
  "pasa_barra_dev": false,
  "variantes_probadas": 2,
  "fuga_ok": true,
  "veredicto": "NO PASA (recuperado de salida_experimento.txt tras el apagón; el agente no llegó a escribir README). V1 sobre ensamble +0,84 [-0,80, +2,51]; V2 sola -47,48.",
  "comando_reproducir": "cd motor_nuevo/ag09_multi_escala && python experimento.py"
 }
]
const REPRO_NOTA = {
  ag02_residuo_boost: 'NOTA: un verificador anterior se cortó por un apagón a mitad de trabajo. Dejó scripts en _verificacion/ (verif.py, fuga2.py). Sus resultados parciales: rasgos sin dependencia del futuro 0/60; modelo.py coincide con lineal(w) (max dif 5.6e-17); Δ cross-fit recalculado [12.15, 7.64, 16.75]; nulo permutado x3 negativo; forward 20 bloques +9.14 [4.79, 13.22]. Puedes reutilizarlos, pero confirma tú mismo lo esencial y termina lo que falte (prueba de fuga de modelo.py y revisión del código).',
}

phase('Verificar')
log('Ronda 1 recuperada del diario: ' + R1.length + ' resultados; verificando ' + R1.filter(r => r.pasa_barra_dev).map(r => r.slug).join(', '))
const r1 = await pipeline(R1, r => (r.pasa_barra_dev ? verify(r) : { ...r, sobrevive: false }))
const historial = [{ round: 1, results: r1.filter(Boolean) }]
historial[0].results.forEach(r => log(`${r.slug}: Δ ${r.delta_mbits?.toFixed?.(2)} barra=${r.pasa_barra_dev} sobrevive=${r.sobrevive}`))
let survivors = historial[0].results.filter(r => r.sobrevive)
for (let round = 2; round <= MAX_ROUNDS && !survivors.length; round++) {
  phase('Estrategia')
  const resumen = historial.flatMap(h => h.results).map(r => `- ${r.slug}: ${r.idea} → Δ ${r.delta_mbits} [${r.ci_lo}, ${r.ci_hi}]; ${r.veredicto}` + (r.repro ? ` | repro: ${r.repro.resumen} | sesgo: ${r.sesgo && r.sesgo.resumen}` : '')).join(String.fromCharCode(10))
  const nuevo = await agent(`${COMMON}

Eres el estratega. Ningún candidato sobrevivió todavía a la verificación. Resultados hasta ahora:
${resumen}

Lee las carpetas en ${WT}/motor_nuevo/ (README de cada una) y propone 10 ángulos NUEVOS, distintos entre sí y de todo lo ya probado (incluidos los hilos cerrados de la skill lotto-nueva-idea), priorizando los que tengan una razón mecánica para existir. Cada slug con prefijo r${round}_ (p. ej. r${round}_a01_...). Texto de cada ángulo: 2-4 frases concretas y comprobables.`,
    { label: `estratega:r${round}`, phase: 'Estrategia', schema: ANGLES_SCHEMA })
  const angles = (nuevo && nuevo.angulos ? nuevo.angulos : []).slice(0, 10)
  if (!angles.length) break
  log(`Ronda ${round}: ${angles.length} ángulos`)
  const results = await pipeline(angles, a => research(a, round), r => (r && r.pasa_barra_dev) ? verify(r) : { ...r, sobrevive: false })
  const ok = results.filter(Boolean)
  historial.push({ round, results: ok })
  ok.forEach(r => log(`${r.slug}: Δ ${r.delta_mbits?.toFixed?.(2)} barra=${r.pasa_barra_dev} sobrevive=${r.sobrevive}`))
  survivors = historial.flatMap(h => h.results).filter(r => r.sobrevive)
}
return { survivors, historial }
