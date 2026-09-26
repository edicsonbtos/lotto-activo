# Prueba sellada — decisiones fijadas antes de descargar (2026-09-25)

Complementa `motor_nuevo/PREREGISTRO.md` (commit 06271e1). Se commitea junto con el código y los pesos congelados.

## Candidatos (k = 2, Bonferroni: IC bilateral 97,5 %)
- **ag12_V1**: ensamble_v2 + 33 variables (27 de ag02 + 6 transiciones), `ag12_transiciones/parametros_V1.json`.
- **ag12_V0**: ensamble_v2 + solo las 6 transiciones, `parametros_V0.json`.
ag02, ag10 y ag01 NO van: ag02 y ag10 están contenidos en ag12 V1 (mismo mecanismo); ag01 no mueve el dinero.

## Datos
- Todo Lotto Activo disponible en loteriadehoy **antes del 2023-09-04** (el descargador pide desde 2019-01-07;
  las semanas vacías no aportan filas). Sin cortar el principio después de ver nada.
- Control de integridad (`prueba.py/integridad`, sin mirar animales): si alguna (fecha, hora) trae más de un animal, se aborta.
- Calentamiento: primeras 2000 filas; se evalúa desde la fila 2000, igual para ensamble y candidatos.

## Criterio
- PASA un candidato si el IC 97,5 % de Δmbits (bootstrap por jornadas) queda entero por encima de 0.
- Secundarias informativas: Top-3, Top-5, Top-15, Δ retorno del Top-5 escalonado.

## Qué se espera (dicho antes, por el revisor de sesgo)
- En [300, 2000) (días de 11 sorteos, fuera del ajuste) las transiciones s1→i de 2-7 días se reproducen (O/E 0,60),
  pero las inversas i→s1 y la ventana 8-30 no. Esperable: el efecto encoge a ~60 % (≈ +5..+10 mbits). Umbral para pasar ≈ +4.
- Era distinta (11 sorteos/día; quizá otra política). Si el ensamble mismo pierde señal, se informa.

## Incidente previo
Un ensayo en seco con filas de desarrollo escribió por error el registro (ver `ensayo_2026-09-25/LEEME.md`).
No era el tramo sellado (no estaba descargado). Se archivó y se corrigió el script.
