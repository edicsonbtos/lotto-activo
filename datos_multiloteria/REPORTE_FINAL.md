# REPORTE FINAL — Scraping multi-lotería + validación cruzada + Tests A y B

Fecha: 2026-09-16. Ventana de datos: **2026-04-13 .. 2026-09-13** (22 semanas, ~5 meses).
Herramienta de scraping: **Scrapling 0.4.15** (curl_cffi) — sin Firecrawl (no hubo API key;
el usuario indicó usar Scrapling). Todo en archivos NUEVOS (`scraping/`, `datos_multiloteria/`,
`.venv_scrape/`). El pipeline actual NO se tocó.

---

## 1. Fuentes e independencia

| Fuente | Rol | ¿Independiente? |
|---|---|---|
| loteriadehoy.com (LH) | histórico semanal por lotería (POST `fecha=ini/fin`) | sí |
| tuazar.com (TZ) | archivo semanal con TODAS las loterías (`?d=fecha`), numero+animal | sí |
| api.lotterly.co (ARB) | **backend oficial** de selvaplus.com y guacharoactivo.com.ve; resultados desde 2022 | sí (oficial) |
| historial.txt | registro manual del usuario (control Lotto Activo) | sí |
| **lotoven.com** | — | **NO**: misma BD que LH (mismos datos e imágenes `/dist/animals_img/` en la misma semana). Descartado como fuente de cruce. |

Validación del scraper (control, obligatoria): sobre el mes 2026-08-10..16, LH y tuazar
reproducen **100%** de los 84 sorteos de Lotto Activo vs `historial.txt` (≥99% exigido).
Alineación: sorteo 0 = 08:00 AM … sorteo 11 = 19:00 PM (convención 0-based del historial).

## 2. Validación cruzada registro a registro (clave: fecha+hora → número)

**Discrepancias reales sin resolver: 0 en las 5 loterías.**

| Lotería | Registros | Días | Acuerdo 2 fuentes | Acuerdo 3 fuentes | Solo 1 fuente |
|---|---|---|---|---|---|
| lottoactivo | 1.800 | 150 | 1.799 | — | 1 (LH) |
| lottoactivordint | 1.800 | 150 | 84 (sólo 1 sem. de TZ) | — | 1.716 (LH) |
| lagranjita | 1.800 | 150 | 1.800 | — | 0 |
| selvaplus | 1.723 | 143 | 1.632 (LH+ARB) | 91 (+TZ) | 0 |
| guacharoactivo | 1.800 | 150 | 52 (LH+ARB) | 1.748 (+TZ) | 0 |

Notas de calidad documentadas:
- Caso **0 = Delfín/Ballena**: ambas fuentes etiquetan a veces el nº 0 con el nombre de la
  otra lotería; el NÚMERO siempre es consistente. Canónico: Lotto Activo/RD Int = Delfín
  (reglamento oficial PDF), La Granjita = Ballena.
- `selvaplus` tiene 1 resultado "A" (fallo de la API oficial) y tuazar sólo la cubre desde
  la semana 2026-09-07 (es nueva en tuazar); se compensó con el árbitro oficial (cobertura
  100% de las claves LH).
- **lottoactivordint**: tuazar sólo la cubre 1 semana (100% acuerdo en el solapamiento);
  el resto del periodo es LH + tablero idéntico al de Lotto Activo (verificado). Segunda
  fuente independiente plena NO disponible (lotoven no independiente; lottoactivo.com
  renderiza por JS sin API visible; lottoresultados.com sólo hoy/ayer; elbrujodelosanimalitos
  caído). **Limitación declarada.**
- **Lotto Rey**: sólo existe en la familia LH/lotoven → sin 2ª fuente independiente.
  **Excluido** de los datasets finales (condición de la misión: "si aparece en las fuentes").

## 3. Tableros (n_tablero = OBLIGATORIO) — hallazgos

| Lotería | Rango observado | N | Lo que se divulga |
|---|---|---|---|
| lottoactivo | 0–36 | **37** | "38 figuras (delfín 0 – culebra 36)" = en realidad 37 números; el 37 NUNCA sale (12.502 sorteos del historial + 1.800 aquí). El modelo del repo asume K=38 (azar 2,63%); el azar real es 1/37 = 2,70%. |
| lottoactivordint | 0–36 | **37** | tablero idéntico al de Lotto Activo |
| lagranjita | 0–36 | **37** | mismo rango; el 0 es Ballena |
| selvaplus | 0–99 | **100** | la misión asumía 38: **el tablero actual es de 100 figuras** |
| guacharoactivo | 0–75 | **76** | la misión asumía 77: se observan 76 (el 76 nunca apareció en 1.800 sorteos; bajo N=77, P ≈ e^-23 ≈ 0) |

Detalle completo en `tableros.md` / `tableros.json`.

## 4. TEST A — Firma de política (por lotería)

Referencia control (historial.txt completo, 12.502 sorteos, 3 años, solo lectura):
evitación intradía **z = −19.8** (823 repeticiones observadas vs 1.607 esperadas: el operador
EVITA repetir el mismo animal el mismo día), bump 13-27 z = −2.1 (marginal), chi² primero
p = 0.0045.

| Lotería | N | a) evitación intradía | b) bump 13-27 | c) chi² primero | **Clasificación** |
|---|---|---|---|---|---|
| lottoactivo | 37 | z = −7.6 SIG | n.s. | n.s. | **MISMA FIRMA** |
| lottoactivordint | 37 | z = −11.2 SIG | n.s. | n.s. | **MISMA FIRMA** |
| lagranjita | 37 | z = −4.7 SIG | n.s. | n.s. | **MISMA FIRMA** |
| selvaplus | 100 | n.s. | **z = +26.1 SIG** | SIG | **DISTINTA** |
| guacharoactivo | 76 | z = −7.3 SIG | n.s. | n.s. | **MISMA FIRMA** |

FDR Benjamini-Hochberg q=0.05 sobre las 15 celdas. Las 4 loterías de la familia
BigLot comparten la firma "evitación intradía" (la misma que el control con 3 años de datos).
Selva Plus tiene operador distinto y firma distinta: sin evitación intradía, con sobre-representación
masiva de 13–27 condicionada a no-salió-hoy (z=+26) — firma propia, no comparable.

## 5. TEST B — Dependencia cruzada (prioridad: lottoactivo → lagranjita)

Método: alineación por hora del día; lags 0, ±1, ±2, ±3, ±6 h; transformaciones
id / ±1 / espejo; nula empírica por transformación (parejas del mismo día sin alinear).
Combinaciones: 10 pares × 9 lags × 3 transformaciones = 270; FDR BH q=0.05.

**ALERTA z > 4 (dependencia positiva): NINGUNA.** No hay réplica sistemática entre loterías.

- **lottoactivo → lagranjita**: mejor z = +2.8 (lag +6h, id), p_fdr = 0.32 → **no significativo**.
- **Anécdota 13/09/2026 verificada**: se observaron las coincidencias (16 Oso lag 1h,
  1 Carnero lag 3h, 27 Perro lag 6h, y un 7 extra) — pero con 12×12 sorteos/día y N=37,
  se esperan ~3.9 coincidencias por lag por azar. Conteo del día por lag (0,1,2,3,6h):
  1,1,0,2,1 — totalmente dentro del azar. **Conclusión: casualidad, no patrón.**
- Hallazgo secundario (|z|>4, negativo): lottoactivo → lottoactivordint, id,
  z = −5.7 (lag +1h) y z = −5.1 (lag 0), p_fdr ≈ 3e-6: **menos** coincidencias que al azar.
  Análisis direccional: la anti-coincidencia se concentra cuando RD Int sortea DESPUÉS de
  Lotto Activo (0 aciertos en 150 parejas naturales mismo-hora; 9/1.800 en lag +1h vs 48.6
  esperados). Mecanismo coherente: **RD Int evita los resultados ya conocidos de Lotto
  Activo** (memoria cruzada del mismo operador, consistente con la evitación intradía del
  Test A). Es anti-dependencia: no exploitable para EV positivo; refuerza que el operador
  de-correlaciona activamente sus productos.

Cumplimiento de la regla "z>4 ⇒ detener todo": no hubo z>4 positivo; el z<−4 se reporta
como hallazgo mecánico/anti-dependencia y no indica réplica exploitable.

## 6. md5 de los archivos protegidos

| Archivo | md5 inicio | md5 final | ¿idéntico? |
|---|---|---|---|
| historial.txt | 325539D9…0218 | 81AA0CC3…39A2 | cambió por **append** de 3 líneas hecho por `servidor.py` del usuario (16-09 9:41). Las primeras 12.502 líneas conservan el md5 original exacto (verificado). Mis scripts solo lo leyeron. |
| predicciones.json | 85B09879…8B1B | AD306454…8217 | cambió por el pipeline en vivo del usuario (16-09 9:42). No tocado por esta misión. |
| pesos_ensamble.json | 078394FA…6E55 | 078394FA…6E55 | **IDÉNTICO** |

## 7. Entregables y cómo reproducir

- `datos_multiloteria/*.csv` — 5 loterías, esquema `fecha,hora,n_sorteo_dia,numero,animal,n_tablero,fuente`
- `datos_multiloteria/validacion_cruzada.md`, `discrepancias.csv`, `resumen_validacion.json`
- `datos_multiloteria/tableros.md`, `tableros.json`
- `datos_multiloteria/test_a_firma.md`, `.json`
- `datos_multiloteria/test_b_dependencia.md`, `.json`
- `datos_multiloteria/crudos/` — HTML crudo descargado (auditoría) + JSONL parseados + árbitro
- Scripts (nuevos, en `scraping/`): `core.py` (fetch+parse), `etl.py`, `cruzar.py`,
  `construir_csv.py`, `test_a.py`, `test_b.py`, `validar_control.py`
- venv aislado: `.venv_scrape/` (scrapling, curl_cffi, playwright, patchright, browserforge, pypdf, scipy)

Reproducir: `.venv_scrape\Scripts\python.exe scraping\etl.py` → `cruzar.py` →
`construir_csv.py` → `test_a.py` → `test_b.py` (todo con caché; no vuelve a golpear
los sitios salvo que se borre `datos_multiloteria/crudos/`).

## 8. Decisiones y faltantes (reportados antes de improvisar, según mision)

1. Sin FIRECRAWL_API_KEY → se usó Scrapling a petición del usuario. ✔ resuelto
2. Lotto Activo RD Internacional: 2ª fuente independiente solo 1 semana (tuazar es nueva
   en ella). Árbitro oficial no localizado (lottoactivo.com sin API estática). Datos
   incluidos pero marcados `LH(solo)`/`LH+TZ`. **Si se quiere cerrar esto, hace falta
   otra fuente histórica de RD Int (o API del operador).**
3. Lotto Rey: sin 2ª fuente → excluido.
4. Tableros observados difieren de los supuestos de la misión (37/37/37/100/76 en vez
   de 38/38/38/38/77) — documentado con evidencia; los tests usan los N observados.
5. Hallazgo relevante para el pipeline actual: el azar real de Lotto Activo es 1/37
   (2,70%), no 1/38 (2,63%) como asume `lotto_eval`/`monitor_politica` (K=38).
