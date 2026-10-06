# A5 — ¿Se convierte "mié-vie recicla menos" en una mejora? (pre-registro)
Escrito el 2026-10-06 ANTES de calcular cualquier resultado de este agente. Lo único visto antes es el INFORME de
`../../reciclaje/` (que ya miró TODO 2026, incluidas AJUSTE y PRUEBA). Por eso PRUEBA no es ciega respecto a la
*elección* de la hipótesis (mié-vie); solo es fuera de muestra para los *parámetros*. Esto se declara en el informe.

## Datos y definiciones
- Motor: `prod_0605.npz` (walk-forward, sin fuga). Historial `hist_0605.txt`.
- AJUSTE = 2026-01-01..2026-05-31; PRUEBA = 2026-06-01..2026-10-05. Extra (solo descriptivo): dev = t < 9357.
- Reciclados del sorteo i = animales que salieron en las 2 jornadas previas del historial (misma definición que `semana2.py`).
- mié-vie = weekday ∈ {2,3,4}.
- Métrica primaria: Δmbits por sorteo = 1000·media(log2 P'(y) − log2 P(y)) sobre TODOS los sorteos del tramo de prueba
  (los no tocados aportan 0). También se da por sorteo tocado. IC 90 % por bootstrap de jornadas (4000 réplicas, semilla 0;
  se remuestrea la suma diaria de Δ y se divide por el n total).
- Secundarias: Top-5 y Top-15 (% de aciertos, nuevo − motor, IC 90 % por jornadas), retorno Top-5 escalonado 2-2-2-1-1
  (8 fichas, pago 30) por ficha, nuevo − motor.

## Candidatas (parámetros por máxima verosimilitud en el tramo de ajuste, rejilla fina)
- C1: en mié-vie, P(reciclados)·m, renormalizar. 1 parámetro m ∈ [0,3; 2].
- C2: en mié-vie, P^T renormalizado. 1 parámetro T ∈ [0,5; 1,5].
- C3: multiplicador m_d por día de la semana sobre reciclados (7 parámetros), con contracción: se maximiza
  LL − Σ_d (log m_d)² / (2·0,10²) (previa normal en log m con σ = 0,10, fijada ahora).
- C0 placebo: el ajuste C1 aplicado a (a) un día elegido al azar con `np.random.default_rng(5).integers(7)` (se re-sortea
  si cae en mié-vie), y (b) la distribución completa de las 35 ternas de días (C1 aplicado a cada terna) para ver cuánto
  "mejora" una terna cualquiera en ajuste y en prueba. La terna {2,3,4} se ubica en esa distribución.
- Robustez: todo se repite al revés (ajustar en PRUEBA, medir en AJUSTE).

## Criterio de éxito (fijado ahora)
Una candidata PASA si el IC 90 % de Δmbits/sorteo es > 0 en PRUEBA (ajuste ene-may) Y en la dirección invertida
(medida en ene-may con ajuste jun-oct). Además, para considerarla útil en plata: el Top-5 escalonado no debe empeorar
(punto estimado ≥ 0 en ambas direcciones). Si pasa C1/C2 pero la terna {2,3,4} no queda en el 10 % superior de las 35
ternas en PRUEBA, se marca como "no distinguible del placebo".
FRACASA si en PRUEBA el Δmbits punto es ≤ 0, o si el m (o T) ajustado en una dirección cae del lado opuesto de 1 en la otra.
Cualquier otra cosa: DUDOSO.

## Estrategia "no jugar mié-vie"
En PRUEBA, Top-5 escalonado del motor: (A) jugar los 7 días; (B) no jugar mié-vie. Se reporta retorno total en fichas,
retorno por ficha, IC 90 % por jornadas de la diferencia de retorno/ficha mié-vie − resto (también estratificado por hora:
media de las 12 diferencias por hora con pesos iguales), y máxima caída (en fichas) de la curva acumulada por jornada.
B "vale la pena" solo si la diferencia mié-vie − resto tiene IC 90 % < 0 en PRUEBA y también en AJUSTE.
