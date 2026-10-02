# PRE-REGISTRO — Tripleta inteligente (cuándo comprarla, cuántas combinaciones, lista negra)

Escrito el 2026-10-02 ANTES de medir. Script: `medir.py` (misma carpeta).

## Regla de la tripleta (como la usa la web)
3 animales; se cobra 45x si los 3 salen en los 12 sorteos que empiezan en el siguiente. La web genera
2 tripletas (puestos 1-2-3 y 4-5-6 del modelo `herramientas/tripleta_ventana.py`) cada 24 h.

## Datos y tramos
- `verificacion/hilo9/datos/historial.txt` cortado en la fila 9357: **solo desarrollo**. Los inicios van de
  2000 a 9345, para que ninguna ventana use sorteos del tramo de prueba.
- Modelo: `tripleta_ventana.Modelo()` con sus parámetros de producción, walk-forward (se reajusta cada 250
  inicios con ventanas ya terminadas).
- **dev-A** = inicios < 5688 (elige); **dev-B** = inicios en [5688, 9345] (mide una vez).
- IC por bootstrap de jornadas (las ventanas se solapan), 3.000 réplicas, semilla 20261002.

## Preguntas
- **Q1. ¿A qué hora conviene comprarla?** EV por ficha de la estrategia A según la hora del primer sorteo de
  la ventana. Candidata a priori: **8:00** (ventana = el día entero; el "no repetir" del día da más animales
  distintos y sube la base). También la mejor hora de dev-A. En dev-B, cada una frente a "cualquier hora".
- **Q2. ¿Cuántas combinaciones?** Todas las tripletas de los k primeros, C(k,3), con k = 3, 4, 5 y 6; además A
  (123 + 456) y B (123 + 124). Se reporta EV por ficha y la probabilidad de cobrar algo en la ventana. Se elige
  en dev-A la de mayor EV y se mide en dev-B.
- **Q3. Lista negra.** A, pero saltándose los animales con número = día o día+1 de la fecha del primer sorteo
  (se toma el siguiente de la lista). Diferencia de EV en dev-B.

## Criterio
- **MEJORA** sobre A a cualquier hora: diferencia de EV por ficha > 0 en dev-B y su IC 95 % no incluye 0.
- La tripleta tiene muchas menos jugadas que la apuesta simple. Si el IC cruza 0, se dice "no se distingue" y
  no se cambia nada de la web.
- La confirmación final es el marcador de tripletas en vivo.
