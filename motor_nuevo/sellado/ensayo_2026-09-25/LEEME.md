# Ensayo en seco, NO es la prueba sellada
2026-09-25 ~22:25. Un error de prueba.py (el modo ENSAYO no saltaba el registro) hizo que el ensayo escribiera
registro_sellado.jsonl y resultado_sellado.json. Los datos del ensayo eran las primeras 2600 filas de desarrollo
(2023-09-04..2024-05-02, sha256 99c5d767...), evaluadas desde la fila 2000: n=600, DENTRO de la muestra de los pesos
congelados. Sus números (+33,1 / +19,3) no significan nada. El tramo sellado no se había descargado
(sellado_la.txt no existía). Detectado por el revisor de sesgo; se movió aquí y se corrigió prueba.py.
