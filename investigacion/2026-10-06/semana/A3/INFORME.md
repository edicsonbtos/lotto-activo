# A3 · Mecanismo del déficit miércoles-viernes (MVF) en 2026
Pre-registro: `PREREGISTRO.md`. Scripts: `comun.py`, `m1_perfil.py`, `m1b_descomp.py`, `m2m3.py`, `m4_motor.py`,
`datos_check.py`, `control.py`, `m5_ablacion_regla.py`, `m5b.py`. Salidas: `salida_*.txt`. MVF = mié-vie, SM = sáb-mar.

## Qué cambia: el operador deja de evitar la repetición en el mismo día
| 2026, O/E contra el motor | MVF | SM | ratio [IC95 días] | dev: ratio |
|---|---|---|---|---|
| Ganador que ya salió HOY | 1,68 (9,3 % vs 5,5) | 0,73 | **2,30 [1,85; 2,89]** | 0,95 [0,81; 1,13] |
| Anteayer, no ayer | 0,83 | 1,20 | 0,69 [0,60; 0,79] | 1,03 |
| Ayer (no hoy) | 0,94 | 0,99 | 0,95 [0,86; 1,05] | 1,13 |
| ≥ 4 días sin salir | 1,12 | 0,91 | 1,23 [1,13; 1,35] | 0,96 |
| Retraso > 120 sorteos | 1,35 | 0,82 | 1,65 [1,19; 2,36] | 0,84 |

- Sin motor: repeticiones/día MVF-2026 = 1,11 (SM 0,52; dev 0,63-0,71; azar puro 1,60). Están en los 3 trimestres
  (O/E mié/jue/vie: T1 2,43/1,89/2,92, T2 1,44/1,86/1,49, T3 1,47/1,05/1,37; los otros días 0,34-1,06).
- MVF-2026 se parece más al azar: el motor gana +36 mbits/sorteo [+9; +63] sobre el uniforme (SM +135, dev +111/+141).
  Top-15 43,9 % (azar 39,5 %).
- Descomposición pre-registrada: dar a los ganadores MVF la mezcla hoy/ayer/anteayer/resto de SM recupera **el 65 %** del
  déficit Top-15 (de 600 a 676 aciertos; el motor esperaba 716). Un ganador repetido casi nunca está en el Top-15 (1,6 %),
  porque el motor lo excluye.
- Antecedente: en dev el domingo (día malo, 0,82) también tenía repeticiones de más (O/E 2,53 en 2024, 1,61 en 2025-S1) y
  se normalizó en 2025-S2 (0,21). El patrón "días en que el operador no evita repetir" existe, pero cambia de día.

## Por hora (M2): difuso
Déficit mañana 0,86 [0,78; 0,94] y tarde 0,80 [0,72; 0,88]: diferencia z +1,0. Las peores horas son 13:00 (0,60), 15:00,
18:00 y 19:00 (0,61-0,72). Las repeticiones se acumulan a las 12-13 y 18-19 (18:00: 39,5 % de ganadores ya salidos hoy,
contra 12 % en SM). El primer sorteo de las 8:00 sale 0,93 [0,74; 1,17], sin déficit claro.

## El motor y el día de la semana (M4): no es la causa
Producción = ensamble_v2 (intradia_v2 + secuencia_v3 + haz_v1). `dowbal` existe en secuencia_final/v1/v2_dow, pero
secuencia_v3 no lo activa. La única dependencia semanal está en intradia_v2: los conteos de la "semana natural" (actual y
anterior, desde el lunes). Coeficientes −0,13/+0,03 (al 1-ene-2026), con peso de ensamble 0,52: mueven ~0,03 en log P.
Si se quitan, el Top-15 O/E de MVF-2026 pasa de 0,837 a 0,849, y dev y SM no cambian. El residuo de "semana anterior" en
MVF-2026 (−0,07, z −3,7) es un síntoma del mismo cambio (ganan animales fríos), no un patrón que el motor arrastre: su
coeficiente es ≈ 0.

## Controles adversariales
- **Datos:** la API oficial coincide con el historial en 2026: 3.092 coinciden y 4 difieren, sin sesgo por día. Las
  repeticiones no son copias del sorteo anterior (hueco 1: 18 de 127).
- **Selección:** de las 7 ternas de días seguidos, mié-vie da z −6,1 (×7: p ≈ 4·10⁻⁹). Barajando el día dentro de cada
  semana, p = 0,0005 (el mínimo posible con 2.000 réplicas). No es azar dentro de 2026.
- **Otras loterías** (repeticiones/azar, MVF vs SM en 2026): RD 0,26/0,20, La Granjita 0,73/0,58, Selva 0,96/0,87,
  Guácharo 0,36/0,31, LARD 1,02/1,03. La inclinación va en la misma dirección, pero es leve (descriptivo).
- **Regla simple** (en MVF, ×a a "salió hoy" y ×b a "anteayer"), solo descriptiva: ajustada en T1 (a = 2,69,
  b = 0,68), en T2+T3 da **−22,6 mbits** [−48; +4]. Ajustada en T1+T2, en T3 da −12,3 mbits. El Top-15 sube +0,9 a
  +1,6 pp, pero la verosimilitud empeora porque la fuerza del efecto varía entre trimestres (T1 mucho más fuerte).

## Veredicto: REAL como fenómeno de 2026, NO corregible con una regla simple
Por la regla del pre-registro es REAL: explica el 65 % (≥ 50 %), es nuevo de 2026, no hay artefacto y el control de
selección da p < 0,001. Pero la amplitud varía y el día afectado ya cambió una vez (domingo → mié-vie), y la regla
ajustada en el pasado pierde en el futuro inmediato. No se toca la jugada. Para el vivo pre-registrado (07-oct a 06-ene),
la métrica mecánica que hay que vigilar es: repeticiones del día MVF contra el motor (hoy 1,68; SM 0,73).
