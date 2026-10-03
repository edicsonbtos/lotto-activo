# Brief común — Investigación "solo el primer sorteo del día (8:00 AM)" de Lotto Activo (2026-10-03)

Eres 1 de 10 investigadores en paralelo. Cada uno ataca UNA hipótesis distinta sobre el primer sorteo del día.
Escribe en español. Trabaja SOLO en tu carpeta `BASE/agNN/` (BASE = la carpeta de este archivo). NO edites nada del
repo `/home/user/lotto-activo`, NO hagas commits, NO toques ningún archivo de historial del repo. Solo lees el repo.
(Un hook bloquea cualquier comando de shell que contenga el texto "historial" + ".txt"; usa la copia `BASE/hist_la.txt`.)

## Contexto del juego
- Lotto Activo: 38 animales (códigos "0","00","1".."36" → índices 0..37 en el orden de `lotto_eval.POS`), 12 sorteos/día
  (hora 0 = 8:00 … hora 11 = 19:00). Hasta 2024-11-27 el primer sorteo era a las 9:00 (hora 1, 11 sorteos/día);
  desde 2024-11-28 es a las 8:00 (hora 0). Paga 30 a 1. Equilibrio: un animal necesita p ≥ 1/30 = 3,33 %.
- Operador con licencia MGA y RNG certificado. 308 hipótesis de la "Operación Turing" dieron 0 señales.
  Estructura real conocida: no repite animal el mismo día, recicla con 1–2,5 días de hueco, esquiva el número
  de la fecha (día del mes) y de la hora (reloj 12 h). El motor (ensamble_v2) ya captura "no repetir" y el reciclaje.
- HALLAZGO DE HOY (ya en producción): el primer sorteo casi nunca repite el primer sorteo de ayer (O/E 0,12–0,19)
  y el primer sorteo de hace 3 días sale de más (O/E 1,45–1,89). Producción multiplica ×0,272 y ×1,736.
  Informe: `/home/user/lotto-activo/investigacion/2026-10-03/primer_sorteo_ayer/INFORME.md` (léelo primero).
- Ideas YA CERRADAS (no repetir sin razón nueva): `/home/user/lotto-activo/.claude/skills/lotto-nueva-idea/SKILL.md`.

## Datos (ya preparados, no recalcules el motor)
`BASE/base8.npz` (np.load):
- `seq` (n,) índice del animal ganador 0..37; `hora` 0..11; `dia` nº de día consecutivo; `fecha` 'YYYY-MM-DD'; `dow` 0=lunes.
- `P` (n,38): ensamble_v2 walk-forward (fila t usa SOLO seq[:t]); NaN para t < 2000.
- `P_aj` (n,38): P con el ajuste del primer sorteo de producción. **Esta es la línea base a superar.**
- `es_primero` (n,) bool: primer sorteo de su día. `tramo`: 'cal' (t<2000, sin motor), 'dev', 'prueba', 'vivo'.
- Filas de primer sorteo: dev = 263 (era 9:00, 2024-03-08..11-27) + 372 (era 8:00, 2024-11-28..2025-12-19);
  prueba = 261 (8:00, 2025-12-20..2026-09-14); vivo = 15 (8:00, 2026-09-15..09-29). Hay además ~180 primeros
  sorteos en 'cal' (2023-09-04..2024-03) utilizables SOLO para conteos crudos contra azar (1/38), sin motor.
- Historial crudo (copia): `BASE/hist_la.txt` (líneas "fecha hora código"); loader:
  `sys.path.insert(0,'/home/user/lotto-activo/herramientas'); import lotto_eval as LE; D = LE.cargar(ruta)`.
- Otras loterías: `/home/user/lotto-activo/datos_multiloteria/` (oficial_multi.csv: API oficial desde 2025-07-01, juegos
  1=Lotto Activo, 2=RD Internacional h:30, 3=LARD h:00; rdint_hist.csv desde 2023-09; lagranjita/guacharoactivo/selvaplus/
  lottoactivordint/lottoactivo .csv desde 2026-04-13).
- Python con numpy 2.4 y scipy 1.17; 4 CPU, 15 GB RAM (compartidos con otros 9 agentes: sé moderado).

## Protocolo obligatorio (para no fabricar estadística fantasma)
1. **Pre-registra** antes de mirar prueba: escribe `BASE/agNN/PREREGISTRO.md` con hipótesis, métrica, candidatos y
   umbral. Explora libremente en DEV (y en 'cal' para conteos crudos); elige en dev.
2. Envía a PRUEBA como mucho **3 candidatos**, una sola vez. Hay 10 agentes × 3 = 30 contrastes: en prueba,
   **CONFIRMADO** exige p unilateral < 0,0017 (Bonferroni) Y mismo signo en las dos eras de dev (9:00 y 8:00).
   p < 0,05 = **PROMETEDOR** (pendiente de vivo). Si no, **NULO**. El vivo (15 filas) solo se reporta, no decide.
3. Mide contra el motor `P_aj`, no contra el azar: O/E = observados / suma de probabilidades del motor, con IC de
   Poisson exacto; y ganancia en **mbits por primer sorteo** = 1000·mean(log2(q[y]/P_aj[y])) con IC por bootstrap de días.
   Un multiplicador/corrección se ajusta SOLO en dev (con suavizado) y se aplica tal cual en prueba.
4. Si comparas grupos de sorteos de distintas horas, estratifica por hora. Corrige por comparaciones múltiples en dev
   (cuenta cuántas cosas miraste y dilo).
5. Si algo pasa, estima el efecto en plata: cambio en aciertos del Top-5 y Top-15 a las 8:00, y retorno por ficha
   (pago 30) contra la jugada actual, con IC por bloques de días.
6. Sé escéptico de tu propio hallazgo: busca el artefacto (datos, fuga de futuro, elección del umbral) antes de creerlo.

## Entregable
`BASE/agNN/RESULTADO.md` (máx. ~80 líneas): primera línea `VEREDICTO: CONFIRMADO | PROMETEDOR | NULO`, luego
qué probaste (nº de cosas miradas en dev), tablas dev (por era) → prueba → vivo, mbits con IC, efecto en Top-5/Top-15,
y si recomiendas algo concreto para producción. Deja el script reproducible en tu carpeta.
Tu respuesta final al orquestador: el veredicto, el número clave y la ruta del RESULTADO.md (máx. 15 líneas).
