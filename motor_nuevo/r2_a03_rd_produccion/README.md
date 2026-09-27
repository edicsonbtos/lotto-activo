# r2_a03_rd_produccion — ag12 V1 + RD Internacional (para producción)

Prerregistro: `PREREGISTRO.md` (escrito antes de correr). Reproducir (unos 6 s, poca RAM):

    cd C:\Users\edics\Downloads\lotto-activo\lotto-activo-motor
    $env:PYTHONIOENCODING="utf-8"; python motor_nuevo/r2_a03_rd_produccion/experimento.py
    python motor_nuevo/r2_a03_rd_produccion/placebo.py      # control

Salidas: `salida_experimento.txt`, `consola.txt`, `resultados.json`, `P_VA.npy`, `salida_placebo.txt`, `resultados_placebo.json`.
Datos: solo desarrollo LA [2000, 9357) = 2024-03-07..2025-12-17 (7.357 filas) y RD Int h:30 hasta 2025-12-17.
Nada >= 9357 y nada del sellado.

## Variables (fila t = LA h:00; solo RD de horas previas del mismo día y pares de jornadas anteriores)
L1 = [i == RD (h−1):30] · L3 = [i == RD (h−2):30] · PF = pares RD (h'−1):30 → LA h':00 vistos hace 1-30 días ·
PR = par inverso LA h':00 → RD h':30 visto hace 1-30 días. RD (h−1):30 disponible en 6.930 de 7.357 filas.

## Resultados (Δ mbits frente a ag12 V1, IC95 bootstrap por jornada; ag12 V1 = +141,78 mbits, Top-15 54,78 %)
| Variante | Δ mbits [IC95] | Mitad 1 | Mitad 2 | Top-3 | Top-5 | Top-15 | Top-5 esc./ficha |
|---|---|---|---|---|---|---|---|
| **VA (primaria)** offset V1 + L1,L3,PF,PR | **+10,51 [+7,89 ; +13,17]** | +11,87 | +9,16 | 14,24 % | 22,59 % | **55,59 %** | +38,13 % (vs +34,92; Δ +3,2 pp [+1 ; +5]) |
| VA forward informativo | +7,63 [+5,56 ; +9,62] | +6,24 | +9,03 | 14,19 % | 22,50 % | 55,55 % | +37,57 % |
| VB offset V1 + solo L1,L3 | +10,32 [+7,79 ; +12,88] | +11,82 | +8,81 | 14,14 % | 22,35 % | 55,73 % | +36,81 % |
| VB forward informativo | +7,44 [+5,41 ; +9,38] | +6,18 | +8,70 | 14,12 % | 22,40 % | 55,66 % | +36,96 % |
| VC conjunto 37 var desde el ensamble | +10,52 [+7,88 ; +13,19] | +11,87 | +9,17 | 14,29 % | 22,58 % | 55,57 % | +38,24 % |
| VC forward (bloque 0 = ensamble, no comparable) | +1,98 [−1,74 ; +5,71] | −3,83 | +7,79 | | | 55,24 % | |

Forward justo de VC frente al forward de ag12 (mismo procedimiento, 33 contra 37 variables):
**+7,65 [+5,58 ; +9,65]**, mitades +6,24 / +9,06, sin el bloque 0 +9,45 [+6,91 ; +11,92]. Es la cifra honesta.

Pesos VA (media [mín, máx] de los 5 bloques): L1 −0,685 [−0,718 ; −0,633] (×0,50), L3 −0,289 [−0,336 ; −0,239] (×0,75),
PF −0,059, PR +0,035. Estables en los 5 bloques.

Diagnóstico frente a ag12 V1 (O/E):
- L1: antes de 2025-07-01 49 vs 139,4 (O/E 0,351, z −7,66); desde 2025-07-01 21 vs 46,3 (0,453, z −3,72); total 70 vs 185,8 (0,377, z −8,49).
- L3: 88 vs 129,0 (0,682) · 33 vs 43,2 (0,764) · total 121 vs 172,2 (0,703, z −3,90).
- PF 1.372 vs 1.416,4 (0,969, z −1,18); PR 1.518 vs 1.477,2 (1,028, z +1,06) → los pares RD→LA NO aportan (como ya decía sondeo_rd).
- Δ VA antes de 2025-07-01 +11,25 [+8,04 ; +14,19]; desde 2025-07-01 +8,43 [+2,69 ; +13,65].
- Placebo (RD de la misma hora 7 días antes): Δ −0,41 [−1,03 ; +0,26] → sin fuga ni artefacto de la tubería.

## Veredicto
**VA PASA la barra de desarrollo** (Δ +10,51 ≥ 3, IC inferior +7,89 > 0, mitades +11,87 / +9,16, forward +7,63; forward
justo de VC +7,65). Top-15 sube de 54,78 % a 55,59 % (+0,8 pp); Top-5 22,13 → 22,59 %.

Lectura honesta:
1. Toda la ganancia es L1 + L3 (VB = +10,32 de +10,51). Los pares RD→LA (la parte nueva del ángulo) no hacen nada.
   Para producción basta VB: dos multiplicadores, animal de RD (h−1):30 ×~0,50 y de RD (h−2):30 ×~0,75, sobre ag12 V1.
2. NO es un descubrimiento nuevo: es H4/H4b y la regla de cambio RD→Top-5 que ya está en vivo. H4 falló en su prueba ciega
   (2025-07-01..2026-04-12), que se solapa con la cola de este desarrollo; aquí, sobre ag12, ese mismo solape
   (2025-07-01..2025-12-17) sigue dando O/E 0,45 y Δ +8,43 [+2,69 ; +13,65]. El desarrollo es reutilizado.
3. El efecto es aditivo a ag12 (VC conjunto = VA), no se solapa con las transiciones LA→LA.
4. Muy lejos del 60 % de Top-15. Solo se confirma con sorteos FUTUROS (marcador en vivo, en sombra); tocar producción
   requiere el OK del usuario. Variantes probadas: 3 (VA, VB, VC); el placebo y el forward de ag12 son controles.
