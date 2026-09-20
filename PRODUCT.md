# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Un solo usuario: el dueño del proyecto, que juega Lotto Activo en Venezuela. No
es programador: lee la interfaz en español llano y no quiere jerga estadística
(confirmado). Lo consulta **sobre todo desde el teléfono** (confirmado), en la
calle o en cualquier sitio, en ratos cortos entre sorteo y sorteo.

Nadie más lo usa hoy. No hay cuentas, ni sesiones, ni roles: la web es de una
sola persona y no se ha pedido que deje de serlo.

## Product Purpose

Decidir, antes de cada sorteo, **qué jugar y si vale la pena jugar**, y saber
con números honestos si el modelo está funcionando o no.

Al entrar, el usuario hace tres cosas (confirmado, en este orden de frecuencia):

1. **Ver qué jugar ahora**: los 3 animales del próximo sorteo.
2. **Ver cómo va**: el marcador — si el modelo acierta y si va ganando o
   perdiendo plata.
3. **Estudiar los números**: mesa de probabilidades, histórico y herramientas de
   validación, cuando quiere mirar a fondo.

Éxito no es "acertar": es que el usuario pueda confiar en lo que la pantalla le
dice, incluso cuando le dice que no conviene jugar.

## Positioning

Lo que ningún otro sitio de "predicciones de animalitos" puede copiar de verdad
es la **contabilidad honesta del propio pronóstico**:

- cada pronóstico se congela y se guarda **antes** de conocer el resultado, y el
  marcador solo cuenta esos;
- todo se mide walk-forward (el modelo nunca ve el futuro), con intervalos de
  confianza y contra el umbral de rentabilidad del pago, no contra el aplauso;
- el tramo de prueba se miró una sola vez, y está registrado que fue una sola
  vez;
- la interfaz dice explícitamente cuándo **no** hay evidencia suficiente.

## Operating Context

- **El juego**: 38 animales, 12 sorteos al día, de 8:00 AM a 7:00 PM, hora de
  Caracas (UTC-4, sin horario de verano). Pago 30x por sorteo acertado y 45x por
  tripleta (3 animales dentro de una ventana de 12 sorteos).
- **El ritmo de uso**: una consulta corta antes de cada sorteo, casi siempre en
  el teléfono; sesiones largas de estudio solo de vez en cuando.
- **El resultado se anota solo**: la app lo busca en la fuente pública unos 10
  minutos después de cada sorteo y lo registra con el mismo código que el botón
  manual; el usuario ya no teclea resultados. El botón manual queda como atajo.
- **Dónde vive**: desplegado en Railway (dominio público), con el historial real
  en un volumen persistente. La copia local del repositorio es secundaria y se
  queda atrás; el marcador de verdad es el desplegado.
- **La máquina local** tiene poca memoria: las herramientas pesadas se corren a
  mano y pueden fallar por RAM, no por el código.

## Capabilities and Constraints

- Pronóstico por sorteo con un ensamble de modelos (top-3 y orden completo de los
  38), tripleta automática por ventana, mesa de probabilidades (solo lectura),
  histórico de pronósticos, marcadores y herramientas de validación que corren
  bajo demanda.
- **Archivos de datos protegidos**: el historial y los pronósticos solo los
  escribe la app. Un hook bloquea cualquier otra escritura.
- **El tramo de prueba ya se usó una vez.** Volver a elegir modelo mirándolo
  contaminaría la evidencia; lo nuevo se valida en desarrollo o con datos vivos.
- Sin cuentas, sin pagos, sin notificaciones push. No hay ningún mecanismo para
  apostar desde la web: la web informa, el usuario juega por fuera.

## Brand Commitments

- Nombre: **Lotto Activo**. Los animales se nombran como en el juego (Delfín,
  Ballena, Perico…), nunca como categorías abstractas.
- Voz: español venezolano llano, directo, sin jerga y sin promesas. La pantalla
  puede decir "vas en negativo" o "todavía no se distingue del azar" sin
  suavizarlo.
- Compromiso innegociable: **nunca presentar como demostrado algo que no lo
  está**, ni insinuar que el sistema garantiza ganar.

## Evidence on Hand

Real, medido y ya escrito en el repositorio:

- Histórico propio de ~12.500 sorteos (`historial.txt` en el volumen desplegado).
- Prueba ciega sobre 3.122 sorteos: Top-1 **4,00 %** (IC 95 % 3,37–4,75) y Top-3
  **12,27 %**, contra 2,63 % de azar puro; el umbral de rentabilidad con pago 30x
  es 3,33 %.
- Tripleta: umbral 2,22 % con pago 45x; la estrategia preelegida dio 3,07 %
  (p = 0,064, **no significativa**).
- Informes reproducibles en `herramientas/resultados/` y
  `REPORTE_OPERACION_TURING.md` (barrido de 308 hipótesis sin señal).

Lo que **no** existe y no debe inventarse: testimonios, otros usuarios, cifras de
ganancias, clientes, precios, respaldos, premios y cualquier afirmación sobre el
operador del sorteo que no esté en esos informes.

## Product Principles

1. **La honestidad es el producto.** Si el dato no alcanza para afirmar algo, la
   pantalla lo dice; un número prometedor sin evidencia es un fallo de diseño.
2. **Primero la decisión, después el detalle.** Lo que se juega ahora manda; el
   estudio a fondo existe pero no estorba.
3. **El teléfono es el escenario real**, en ratos de un minuto y con una mano.
4. **Ningún paso manual que la máquina pueda hacer sola.** El resultado ya se
   anota solo; lo demás debería seguir ese camino.
5. **Nada de emoción falsa.** Ni celebraciones de un acierto aislado ni alarmas
   por una racha: la escala de tiempo honesta son cientos de sorteos.

## Accessibility & Inclusion

Sin requisito formal externo, pero con dos necesidades reales del usuario:
lectura cómoda en pantalla de teléfono a la luz del día (contraste alto, modo
oscuro, objetivos grandes para el pulgar) y **lenguaje no técnico**: cada número
va acompañado de su lectura en palabras.

<!-- Nota de init: "solo yo", "sobre todo el teléfono" y los tres trabajos al
     entrar son respuestas del usuario. Todo lo demás está tomado del código, el
     historial y los informes del propio repositorio; no se preguntó por
     estética, colores ni tipografía, que no pertenecen a este archivo. -->
