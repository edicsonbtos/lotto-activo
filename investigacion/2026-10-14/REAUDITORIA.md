# Reauditoría y días buenos/malos — 2026-10-14

Datos: pronósticos congelados en Railway (`/api/mesa`, offsets 1–374, descargados el 14-oct después del sorteo de las 7:00 p. m.), más `/api/rdint`, `/api/sombra`, `/api/sombra_decision`, `/api/cambio_rd`, `/api/cambio_rd15`, `/api/salud`. No se usó la copia local del histórico.
Scripts: `dias.py` y `an.py` en esta carpeta (leen los JSON bajados en `rw/mesa/<offset>.json`). Tests locales: 97 pasan.

## 1. Estado de avance

| Frente | Estado |
|---|---|
| Railway | Vivo, responde en ~0,6 s. Último deploy: `f2f1769` (8-oct). `RESPALDO_CLAVE` sin definir → `/respaldo.zip` cerrado. |
| Repo local | Cambios sin commit en `servidor.py`, `static/`, `tests/oro_css_js.json`, `datos_multiloteria/` y varias carpetas nuevas (scraping, otras_lotos, reciclaje_k). |
| Lotto Activo (h:00) | 349 sorteos puntuados desde el 15-sep. |
| RD Internacional (h:30) | 255 sorteos puntuados. |
| ag12 en sombra | 226 sorteos de 931 preregistrados (24 %). Aún no decide. |

### Lotto Activo — 349 sorteos

| Jugada | Aciertos | Azar | Plata (pago 30) |
|---|---:|---:|---:|
| Top-3 | 37 (10,6 %) | 7,9 % | Top-3 plano: **+63 u (+6,0 %)** |
| Top-5 | 59 (16,9 %) | 13,2 % | Top-5 escalonado 2-2-2-1-1: **+88 u (+3,2 %)** |
| Top-15 | 163 (46,7 %) | 39,5 % | Top-15 ponderado: **−257 u (−3,2 %)**; plano: **−345 u (−6,6 %)** |

El modelo le gana al azar en las tres medidas. Pero el Top-15 **pierde plata**: para cubrir apuesta plana necesita 50 % de aciertos, y va en 46,7 %. Solo 9 de 30 días cerraron en ganancia con Top-15 plano.

Calibración: con orden completo (310 sorteos) el modelo esperaba 159 aciertos Top-15 y hubo 149. Es algo optimista, cerca de un 6 %.

### RD Internacional — 255 sorteos
Top-3 24, Top-5 47 (18,4 %), Top-15 125 (49,0 %). Top-5 escalonado **+90 u (+4,4 %)**, Top-15 ponderado **+15 u (+0,3 %)**, Top-3 plano −45, Top-15 plano −75.

### Reglas y modelo en sombra
- **Regla RD→Top-5** (en vivo desde el 23-sep): 241 sorteos, 42 cambios, **+60 u** frente a no aplicarla. Sigue sumando.
- **Regla RD en Top-15** (`cambio_rd15`, desde el 7-oct): 88 sorteos, **−30 u**. Va en contra; muestra chica.
- **ag12 vs ensamble** (226 sorteos): Top-15 52,2 % vs 46,9 %; Top-5 20,4 % vs 16,8 %. Δ mbits +16,9 con IC90 [−7,6; +41,4], **todavía cruza cero**. El Top-5 sin la regla RD ya tiene el IC90 por encima de cero ([+3,8; +42,6]), pero la regla preregistrada decide por mbits. Sigue en sombra hasta 931.
- **Exposición** (`ensamble_exp`, 155 sorteos): +7,7 mbits, IC90 [+0,6; +14,9]. Primera señal positiva, pero se decide con 6.000 sorteos.

## 2. Días buenos y días malos (Top-15, Lotto Activo)

Bueno = 7 o más aciertos de 12 (≥58 %). Malo = 4 o menos (≤33 %).

- **Buenos (7):** 15-sep, 22-sep, 3-oct, 5-oct, 10-oct (9/12, el mejor), 11-oct y 13-oct.
- **Malos (5):** 16-sep (1/11, el peor), 23-sep, 28-sep, 8-oct y 9-oct.

### Por qué fue bueno o malo: qué animal salió

| Tipo de ganador | Veces que quedó en Top-15 |
|---|---:|
| Salió hace 1 día | 64/98 = **65 %** |
| Salió hace 2–5 días | 93/174 = **53 %** |
| Frío, 6 días o más | 6/57 = **11 %** |
| Repetido el mismo día | 0/20 = **0 %** |

| Tipo de día | Ganador de hace 1 día | Repetido el mismo día | Frío ≥6 días |
|---|---:|---:|---:|
| Buenos | 36 % | 2 % | 16 % |
| Medios | 26 % | 5 % | 18 % |
| Malos | 25 % | **12 %** | 12 % |

Lo que explica los días es el tipo de animal que salió. En un día bueno salieron animales que habían salido hace 1–5 días, que es justo donde el modelo apuesta. En un día malo hubo más repetidos del mismo día, que el modelo deja siempre fuera del Top-15, y fríos. El modelo tiene razón en dejarlos fuera la mayoría de las veces: los repetidos del mismo día salen solo el 5,6 % de las veces.

### ¿Se puede saber antes si el día será bueno? No.

| Prueba | Resultado | Lectura |
|---|---|---|
| ¿Los días varían más que el azar? | Varianza 2,21 vs 2,90 esperada; p = 0,80 | No. Los días buenos y malos tienen el tamaño que da la suerte. |
| ¿Un día bueno trae otro bueno? | Correlación entre un día y el siguiente: +0,04 | No hay rachas. |
| ¿La confianza del modelo anuncia el día? | Correlación −0,02 (26 días) | No. |
| ¿La mañana anuncia la tarde? | Correlación −0,20, no significativa | No. Coincide con «día sin reciclaje». |
| ¿Hay un día de la semana mejor? | Martes 56 %, miércoles 34 %; p = 0,14 | No pasa. Es ruido, igual que el domingo. |
| ¿Hay una hora mejor? | 8 a. m. 20/29; p = 0,16 para todas las horas | No pasa. La ventana de las 8 ya se descartó a ciegas. |

## 3. Qué replicar y qué evitar

1. **Los días buenos no se pueden replicar porque no hay régimen.** Cada día es una muestra del mismo motor. Elegir qué días jugar mirando el día anterior, la confianza del modelo, la mañana o el día de la semana no tiene base.
2. **Lo que pierde de forma sostenida es el Top-15 a pago 30**, sobre todo el plano. Lo que gana poco pero de forma sostenida es el Top-5 escalonado o el Top-3, en LA y en RD. Para evitar días malos en plata, hay que bajar el Top-15 y no buscar otro filtro.
3. **No meter a la fuerza los repetidos del mismo día ni los fríos.** Eso es lo que hunde los días malos, pero ya se probó (reciclaje k, día sin reciclaje, fríos >7 d en la tarde) y no pasó a ciegas.
4. **La mejora real en camino es ag12.** Rinde mejor en Top-5 y Top-15 en vivo y está al 24 % del corte preregistrado. Hay que dejarlo correr y no adelantar el cambio.
5. **Vigilar `cambio_rd15`.** Va −30 u. Si sigue negativo al llegar a unos 300 sorteos, conviene quitarla.

## 4. Pendientes técnicos
- Definir `RESPALDO_CLAVE` en Railway para poder bajar `/respaldo.zip` (el marcador vive solo en `/data`).
- Hacer commit/push de los cambios locales sin subir.
- Revisar la facturación de Railway: hoy el servicio responde, pero si se suspende se pierde el registro de sorteos en vivo.
