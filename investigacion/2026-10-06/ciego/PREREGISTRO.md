# Pruebas ciegas del motor nuevo S2 (2026-10-06), pre-registradas ANTES de correrlas
Candidato congelado: S2 = mezcla de expertos LightGBM C-90 (`../motor0/S2/`), y S2+PROD con w = 0,75. Nada se reajusta.

## Ya corrida (resultado de orientación, con reentreno trimestral): ANTIGUO 2024-03..2025-06
S2 solo −11,1 mbits [−19,1; −3,0]; mezcla +0,8 [−5,3; +6,8]; Top-5 con la mezcla +15,1 % contra +20,4 % de PROD.

## C1 (T1): ANTIGUO con la configuración EXACTA (reentreno mensual)
Pasa si la mezcla da Δ mbits con IC 90 % > 0 Y no pierde en plata (Top-5 escalonado con la regla de RD: diferencia
pareada ≥ 0). Si no pasa, la ganancia de 2026 se considera específica del régimen.
## C2 (T1): transferencia a RD Internacional (juego nunca usado para diseñar S2)
La misma arquitectura y los mismos hiperparámetros, entrenados con RD, contra el motor de RD (`herramientas/rdint/`) en
2025-07..2026-09. Pasa si Δ mbits tiene IC 90 % > 0.
## C3 (T2): batería Turing de controles
- Etiquetas barajadas entre jornadas (el modelo entrena con días permutados): Δ contra PROD ≈ el de "S2 sin información";
  si sale > 0, hay fuga.
- Retraso artificial: entrenar sin el mes previo al que predice; la caída debe ser pequeña.
- Semillas (5) y bootstrap del entrenamiento: dispersión del Δ.
- Rasgo aleatorio de control: importancia ≈ 0.
- Fuga temporal: alterar todo lo posterior a t y comprobar que P[t] no cambia (con reentreno real).
## Veredicto global
S2 se considera REAL solo si pasan C1 y C3 (C2 es un apoyo). Si no, queda como "mejora del régimen 2026, no confirmada".
