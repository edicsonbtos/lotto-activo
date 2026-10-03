# PRERREGISTRO — "Geometría y macro-estacionalidad" (2026-10-03)

Tercer texto pegado por el usuario. Solo desarrollo LA [2000, 9357), caché `calor_cache.npz`. No se mira el tramo de prueba. Sin multiplicadores sobre P: las capas solo reordenan o seleccionan.
Etiqueta numérica del animal: `lotto_eval.POS` ("0" y "00" → número 0, par, terminación 0, excluidos de las pruebas de paridad/magnitud). 8 pruebas → IC 99,375 % (Bonferroni 0,05/8), bootstrap por jornada, 5000 réplicas, semilla 20261002.
Referencia: Top-5 escalonado 2-2-2-1-1 (pago 30, 8 fichas), retorno por ficha.

## G1 clúster dinámico
Se ordenan las 38 P de mayor a menor. Clúster de alta probabilidad = prefijo del ranking que termina en la primera brecha entre vecinos consecutivos > eps = 0,002 (equivale a DBSCAN 1-D con eps 0,002 y min_samples 2 tomando el clúster de la máxima). Se juega 1 ficha por animal del clúster (tamaño k variable).
Comparación pareada por sorteo, retorno por ficha: clúster (k variable) − Top-5 plano (k=5, 1 ficha c/u). PASA si IC de la diferencia entero > 0 y ambas mitades > 0.
Descriptivo: distribución de k; retorno del clúster contra el Top-5 escalonado.

## G2 diversificación del Top-5 (reordenamiento, sin tocar P)
- G2a terminación: si el 5º del Top-5 comparte terminación (0-9) con alguno de los 4 primeros, se reemplaza por el siguiente animal del ranking (puesto 6, 7, …) cuya terminación no esté entre las de los 4 primeros. Se juega el escalonado sobre el nuevo ranking.
- G2b paridad: si los 5 del Top-5 tienen todos la misma paridad (el 0 cuenta como par), el 5º se reemplaza por el siguiente de paridad opuesta.
Métrica: retorno por ficha (nuevo − base, pareado) y acierto Top-5. PASA si IC de la diferencia de retorno entero > 0 y ambas mitades > 0.

## G3 macro-estacionalidad (O/E del Top-5 del ensamble, razón de sumas estratificada por hora; mitades)
- G3a quincena: día del mes 15 o 30.
- G3b fin de mes: últimos 2 días del mes calendario.
- G3c festivos de fecha fija (Venezuela): 1-ene, 19-abr, 1-may, 24-jun, 5-jul, 24-jul, 12-oct, 24-dic, 25-dic, 31-dic. (Móviles —Carnaval, Semana Santa— excluidos: no hay calendario en el repo.)
PASA si IC de O/E queda entero a un lado de 1 y las dos mitades van en el mismo sentido.

## G4 alternancia de paridad / magnitud (contra el ensamble)
Para cada sorteo t con ganador previo (sorteo t-1, mismo juego) de número ≠ 0: probabilidad esperada de alternar = Σ P de los animales (≠0) de la clase opuesta al anterior. Se compara con las alternancias observadas (ganador ≠ 0). O/E de alternancia.
- G4a paridad (par/impar). G4b magnitud (1-18 bajo / 19-36 alto).
PASA si IC de O/E queda entero a un lado de 1 y ambas mitades van en el mismo sentido. Control: la misma O/E con el ganador de 2 sorteos atrás (debe ser ≈ 1).

## Veredicto
Nada va a producción por desarrollo. Si algo pasa, se propone sombra en vivo; confirmación solo del marcador.
