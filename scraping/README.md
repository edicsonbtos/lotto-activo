# scraping/ — datos de animalitos (2026-04-11 a 2026-10-07)

## Cómo se regeneran
Desde `scraping/`, con el Python de `.venv_scrape` (orden importa):
1. `scripts/descargar_animalitos.py`: Tuazar, una página por semana (todos los juegos que muestra).
2. `scripts/complementar_selvaplus.py`: completa Selva Plus con la API de lotterly.co (días que Tuazar no tiene). Debe ir después del paso 1, porque sobrescribe `resultados/selvaplus_*.csv`.
3. `scripts/descargar_loteriadehoy.py`: juegos que Tuazar no tiene o tiene solo desde septiembre (solo dan el animal, sin número).
4. `scripts/consolidar_y_copia.py`: reconstruye `resultados/consolidado_todos.csv` y corre la prueba exploratoria de copia contra Lotto Activo.

Los HTML y JSON crudos quedan en `crudos/` (cache: si existen, no se vuelven a bajar).
Los CSV de datos previos siguen en `datos_multiloteria/`; no se tocaron.

## Formato de los CSV
`fecha,hora,slot,animal_numero,animal_nombre,operador,timestamp_publicacion`
- `timestamp_publicacion` queda vacío: ninguna fuente muestra la hora de publicación.
- `animal_numero` vacío en los juegos de Lotería de Hoy (no publican número).
- `00` y `0`: el número 0 aparece como Ballena o Delfín según la fuente (conflicto ya conocido).

## Cobertura real (ver `logs/resumen_descarga.txt`)
Cubren los 180 días (≈176-180 con datos) : Lotto Activo, Guácharo, La Granjita, Lotto Chaima, Gatazo, Lotto Gato, Chance Animalitos A y B, Animalitos del Oriente (3), Tropi Gana, Triple Popular, Ruleta Royal, Mega Animal 40, El Guacharito Millonario, El Arrejuntao (parcial), La Ricachona, Cazalotón, Centena Plus, Centena Animalitos, Ruleta Activa, Lotto Activo Dominicana, Lotto Activo RD, Monje Millonario, Granja Millonaria y Granjazo (parciales, ≈171 sorteos cada uno).
Selva Plus: 2055 sorteos; faltan 2026-06-25 a 06-28 y 2026-08-31 a 09-06 (ninguna fuente los tiene).
Jungla Millonaria: sin resultados en la semana del 2026-09-28; se excluye.

## Prueba de copia (exploratoria)
`logs/copia_exploratoria.txt`: coincidencia de animal con Lotto Activo en la misma hora, comparada con un control de la misma hora 37 días después.
- Selva Plus: 3,02 % vs control 2,74 %. Granja: 3,22 % vs 3,03 %. Ninguno copia a Lotto Activo.
- Lotto Activo RD (08:30..19:30) y Lotto Activo 2 (Monje): 0,5 % y 0,1 % vs control 3,3 % y 1,1 %. Evitan el animal que sale en Lotto Activo en la misma hora. Coincide con el hallazgo previo (hilo 7).
- Línea base de azar: ≈2,6 % (1/38).
Esto es una mirada exploratoria sobre datos que se solapan con el tramo de prueba de LA; no es una prueba ciega ni una ventaja para apostar.

## Decisiones pendientes
1. "Máximo 4 animales por sorteo": sin definir; hoy no se excluye nada.
2. Lista de operadores "vigentes": la búsqueda web de 2026 no dio una lista verificada. Aquí "vigente" = publicó resultados hasta 2026-10-07 en Tuazar o Lotería de Hoy.
