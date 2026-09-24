# ¿Se pueden subir los porcentajes de acierto? — Informe verificable (hilo 9, 2026-09-23)

Proyecto: predicción de **Lotto Activo** (LA, Venezuela, 12 sorteos/día a las h:00, 8:00-19:00) y
**Lotto Activo RD Internacional** (RD, 12 sorteos/día a las h:30, 8:30-19:30). Mismo operador
(licencia MGA). 38 animales (0, 00, 1-36). Paga **30 a 1**.

## Respuesta corta

**No se encontró ninguna forma demostrable de subir los porcentajes por encima de lo que ya está en
producción.** Se probaron 16 ideas nuevas con pre-registro y, al final, un modelo flexible de 91 variables
que junta todas las señales. Ninguno supera al modelo actual (ensamble_v2) en datos que no se usaron para
ajustarlo. Las dos señales reales que se encontraron (L3 y R4) son estadísticamente sólidas pero aportan
+1,4 y +0,3 mbits: no mueven el Top-5 ni el Top-15.

Lo que SÍ funciona ya está en uso: el ensamble de LA, el modelo cruzado de RD (B1) y la regla de cambio.
Un Top-15 del 60-65 % no es alcanzable con la información que existe (ver §4).

## 1. Umbrales que importan

| Jugada | Fichas | Acierto necesario para no perder | Azar puro |
|---|---|---|---|
| Top-3 plano | 3 | 10,0 % | 7,9 % |
| Top-5 plano | 5 | 16,7 % | 13,2 % |
| Top-15 plano | 15 | 50,0 % | 39,5 % |

Top-15 al 55 % → +10 % por ficha; al 60 % → +20 %; al 65 % → +30 %.

## 2. Lo que funciona (probado a ciegas y en producción)

| Qué | Evidencia | Archivo |
|---|---|---|
| Ensamble LA (intradia_v2 + secuencia_v3 + haz_v1) | Prueba ciega 3.154 sorteos: Top-3 12,27 %, Top-5 19,50 %, Top-15 49,46 %; Top-5 escalonado 2-2-2-1-1 ≈ +19 % por ficha. z ≈ 9-10 contra el azar | `herramientas/resultados/estrategia_top5.md`, `final.txt` |
| RD con memoria de LA (B1) | Prueba ciega 3.237 sorteos: Top-3 12,05 %, Top-5 escalonado +20,0 % [+11,7, +28,6] | `hilo7_prueba_ciega.md` |
| Regla de cambio (LA h:00 saca del Top-5 el animal de RD (h−1):30; el 6º entra 5º) | +1,39 pp por ficha [+0,00, +2,66] en 9 meses no usados para esta regla (adoptada sin confirmar) | `hilo7_cambio_top5.md` |

La única estructura real conocida: el operador **evita repetir** el animal del sorteo inmediatamente
anterior, **incluso entre LA y RD** (RD h:30 repite LA h:00 0,13-0,21 veces lo esperado), evita repetir
en el mismo día y **recicla** animales con 1 a 2,5 días de hueco. La noche corta el efecto.

## 3. Lo que se probó y NO sube los porcentajes

| Idea | Resultado | Archivo |
|---|---|---|
| Frecuencias, animales calientes, Markov 38×38, PRNG/semilla | Ruido | `reporte_vectores_1_2.md`, `vector3_prng.txt` |
| 308 hipótesis (Operación Turing) | 0 señales | memoria del proyecto |
| Racha del favorito (hilo 5) | Descartada (z_MH = +1,38) | `racha_favorito.md` |
| Elegir sorteos por la probabilidad del Top-N (hilo 6) | Falló a ciegas, efecto invertido | `registro_final.jsonl` |
| LA usando RD como modelo (H4) | Falló a ciegas (+3 mbits, IC cruza 0) | `hilo7_sonda_inversa.md` |
| H4b (LA ← RD (h−1):30) | +9,7 mbits, pero el Top-5 escalonado baja (19,0 → 16,6 %) | `hilo7_h4b_reciproca.md` |
| RD 19:30 de la víspera → LA 8:00 | Descartada: en desarrollo, 16 repeticiones contra 9,3 esperadas (al revés) | `hilo7_cambio_noche.md` |
| Tercer juego LARD (API id 3) como cruce | Independiente (ratios 0,99-1,09); los controles LA↔RD sí salen | `hilo8_lard_senal.md` |
| **Hilo 9, paso 1** (9 hipótesis, residuo contra el modelo en uso, Bonferroni) | Pasan sólo L3 (LA evita RD (h−2):30, O/E 0,70, p = 9e-5) y R4 (RD evita su propio día, O/E 0,83, p = 0,003). Reciclaje entre juegos de días anteriores: O/E 0,997-1,015 (nada) | `herramientas/resultados/hilo9_residuos.md` |
| **Hilo 9, paso 2** (L3 y R4 como término walk-forward) | L3 +1,40 mbits, R4 +0,30 (hacía falta +5). Top-5 igual (20,25 → 20,24 %; 17,81 → 17,81 %) | `hilo9_paso2.md` |
| Mezclar RD con intradia_v2 (E1) | −0,18 mbits | `hilo9_residuos.md` |
| **Techo M-A**: modelo flexible (91 variables: hueco × franja horaria, conteos, veces hoy, días, 4 cruces con RD), sin ensamble | **−38,3 mbits** [−47,9, −28,5]; Top-5 18,33 % frente a 20,35 % | `hilo9_techo.md` |
| **Techo M-B**: lo mismo + el ensamble | −4,4 mbits [−11,3, +2,8]; no agrega nada | `hilo9_techo.md` |
| Robustez M-B con λ = 30 (elegido DESPUÉS, exploratorio) | +4,5 mbits [+0,2, +9,3], sobre todo por RD (h−1) ×0,49 y (h−2) ×0,74; no pasa por mitades y **el Top-5 baja** (20,35 → 20,18 %), Top-15 53,39 → 53,17 % | `hilo9_techo_lambda30.md` |

Lectura de la última fila: lo que RD sabe de LA es información real, pero afina animales que ya estaban
abajo; no reordena los de arriba. Por eso se aprovecha con la regla de cambio (que sí gana plata) y no
metiéndolo en el modelo.

## 4. Por qué no se llega a un Top-15 del 60 %

- Si el operador nunca repitiera en el día y se supiera a la perfección, el Top-15 llegaría sólo al
  **46,7 %** de media (15 / animales que quedan, promediado en las 12 horas).
- El ensamble llega al 49,5 % porque además captura el reciclaje de 1 a 2,5 días.
- Un modelo mucho más flexible con todas las variables conocidas y los cruces con RD **no lo supera**
  (M-A, M-B). Es la evidencia más directa de que el ensamble está en el techo de estos datos.
- Toda fuente de información nueva disponible (RD, noche anterior, tercer juego) ya se probó.

## 5. Qué hacer

1. Jugar lo que está probado: Top-5 escalonado en LA y en RD, con la regla de cambio (9:00 a 19:00).
2. No ampliar a Top-15 plano: del 6º al 15º cada puesto acierta ~3,0 %, por debajo del 3,33 % que pide
   el pago. Si se quiere Top-15, el ponderado 3-2-1 (≈ +6 % a ciegas).
3. Apuesta chica hasta que el marcador en vivo confirme: ~300 sorteos (≈ 25 días) para separar 19,5 %
   de 13,2 % en el Top-5.

## 6. Limitaciones declaradas

- La prueba ciega de LA (filas ≥ 9357) ya se miró 5 veces: no se usó aquí. El hilo 9 trabaja sólo en
  desarrollo; lo que pasara iba a confirmarse en vivo.
- `historial.txt` tiene 10 días de fiestas (2025-12-15..19, 12-25..27, 2026-01-01..03) con la fecha
  corrida un día (hilo 8). El hilo 9 excluye fechas ≥ 2025-12-15 en LA.
- El paso 1 corrige por 9 comparaciones; el anexo M es una comparación más, añadida antes de correrla.
- λ = 1 en M fue fijado antes de correr; la robustez con λ = 30 (`HILO9_LAMBDA=30`) está en
  `hilo9_techo_lambda30.md` y da +4,5 mbits en total sin subir el Top-5 ni el Top-15.
- El marcador en vivo lleva 98 sorteos (Top-5 16,3 %, IC95 9-24 %): todavía no separa modelo de azar.

## 7. Cómo verificarlo (cualquier IA o persona)

Requisitos: Python 3.10+, numpy, scipy. Desde la raíz del repo:

```
python verificacion/hilo9/verificar.py --rapido   # residuos + paso 2, ~2 min
python verificacion/hilo9/verificar.py            # + techo, 10-20 min
```

El verificador comprueba las huellas SHA-256 de los datos congelados (`verificacion/hilo9/SHA256SUMS.txt`),
corre los análisis contra esa copia y compara cada número con `verificacion/hilo9/esperado/`. El
2026-09-23 dio: `residuos: IGUAL 128 números`, `paso2: IGUAL 70 números`.

| Dato congelado | Qué es |
|---|---|
| `historial.txt` | LA, 12.511 sorteos (fecha, hora 0-11, código) |
| `calor_cache.npz` | P walk-forward del ensamble en desarrollo (7.357 × 38) |
| `cache_todo.npz` / `cache_dev.npz` | P walk-forward de RD (B0 y B1) por tramo |
| `_b0_intradia_v2.npz` | P walk-forward de intradia_v2 sobre RD |
| `datos_multiloteria/rdint_hist.csv` (en el repo) | RD, desde 2023-09-04 |

Pre-registros (escritos y guardados en git ANTES de ver cada resultado):
`herramientas/exploracion/PREREGISTRO_hilo9_subir.md` (+ anexo M), `PREREGISTRO_lard_cruzado.md`,
`PREREGISTRO_cambio_rd_noche.md`, `PREREGISTRO_cambio_rd_top5.md`. Registro de todas las miradas a
tramos de prueba: `herramientas/registro_final.jsonl`.

Preguntas útiles para otra IA: ¿hay fuga de información futura en `techo.py` (las variables se calculan
antes de añadir el sorteo actual)? ¿El walk-forward usa sólo filas pasadas? ¿El umbral de +5 mbits y la
corrección de Bonferroni se fijaron antes? ¿Hay alguna fuente de información que no esté en §3?
