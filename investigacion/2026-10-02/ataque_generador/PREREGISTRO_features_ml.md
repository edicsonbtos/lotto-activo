# PRERREGISTRO — Dieharder, LSTM, autoencoder, clustering de firmas (2026-10-02)

Solo desarrollo, filas [2000, 9357). Semilla 20261002. Bootstrap por jornada, 5000 réplicas. Familia de 4 pruebas -> IC 98,75 %.
Referencia: P del ensamble en `herramientas/exploracion/calor_cache.npz` (P 7357x38, y), alineada a las filas 2000..9356.
Partición interna: entrenamiento = historia hasta la fila 5678 (mitad del desarrollo); evaluación = filas 5678..9356, partida en E1 (primera mitad) y E2 (segunda). Nada se ajusta mirando E1+E2 a la vez: el peso de mezcla se elige en E1 y se mide en E2.

## D. Dieharder
Dieharder necesita decenas de millones de bits; hay ~31.000 (5 bits x 6.200 sorteos válidos). No existe binario para Windows. Se hace lo que cabe: las pruebas de Dieharder aplicables a esa longitud (birthday spacings sobre los 38 símbolos, gaps, poker/chi2 de 5 símbolos, craps no) con la batería ya corrida; y se declara que una prueba con 31k bits solo detecta sesgos > ~1 %. Si no se puede instalar, se dice tal cual.

## F1. LSTM (100 sorteos previos, one-hot + hora) -> softmax de 38
Métrica: mbits/sorteo de la mezcla log-lineal (LSTM + ensamble, peso elegido en E1) contra el ensamble solo, medido en E2, con IC bootstrap por jornada. También entropía cruzada del LSTM solo. PASA si el IC 98,75 % de la ganancia en E2 queda entero >0 y el LSTM mejora la entropía cruzada >5 % (criterio del texto; muy improbable: el ensamble ya está cerca del techo).
## F2. Autoencoder de anomalías
Entrada: conteos de los 38 animales en los últimos 38 sorteos; cuello de 16. Anómalo = error de reconstrucción > media+3σ (media y σ del entrenamiento). Métrica: O/E del ensamble en los sorteos anómalos de E1+E2 contra el resto (estratificado por hora, Mantel-Haenszel) y retorno por ficha del Top-5 escalonado. PASA si el IC del O/E o del retorno excluye 1 / 0 en E1 y E2 por separado.
## F4. Clustering de firmas espectrales
Ventanas de 200 sorteos (paso 50): magnitud de la FFT de los 38 indicadores (promedio). KMeans k=3 ajustado en el entrenamiento, asignado en E. Métrica: retorno por ficha del Top-5 escalonado y acierto Top-5 por cluster; chi2 de homogeneidad por permutación (5000). PASA si p<0,0125 y la diferencia de retorno entre clusters mantiene signo en E1 y E2.

Veredicto global: ninguna pasa sola sin replicar en E1 y E2. Sin ganancia en mbits sobre el ensamble no hay "+2 % ROI". Todo lo que no pase se archiva.
