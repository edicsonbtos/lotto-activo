# REPORTE — OPERACIÓN TURING (Lotto Activo)

Fecha: 2026-09-20 · Repo: `lotto-activo` · Todo el trabajo en `investigacion/2026-09-18/`.

**Integridad (antes = después, verificado):**
- `pesos_ensamble.json` MD5 `078394faf4d909b3be62cfbad5746e55` — sin cambios.
- Composite `modelos/*.py + pesos_ensamble.json` MD5 `b27765f5fe6e5cb3b4645b1919d0ad69` — sin cambios.
- `registro_final.jsonl` = **4 líneas** (el tramo de prueba `>=9357` no se miró).
- `git status` limpio salvo `investigacion/`, este reporte y la `mesa_consejo.txt` ya modificada antes de esta sesión.
- Nada desplegado. Producción, modelo, pesos, lógica y split de prueba intactos.

---

## ENJAMBRE A — LA BOMBA ESTADÍSTICA

### Método (reproducible)
- Base congelada **una vez**: salida walk-forward de `ensamble_v2` (log-prob por
  sorteo×animal) en desarrollo `[2000, 9357)`. Cache `baseline_dev_full.npz`.
- **308 hipótesis** (≥300 exigidas): 18 covariables base (gap exacto/binned, g2,
  veces-hoy, salió-hoy, k, día-semana, borde de jornada, dd, ganó-anterior,
  vecino-de-tablero, conteos móviles 12/24/38/76/150/300, régimen de repetición)
  + todas las interacciones de pares sobre 17 de ellas × 2 suavizados (a=1, a=8).
- Cada hipótesis = feature causal (log-rate empírico con cuentas estrictas `<t`)
  añadida al logit congelado con **un peso escalar** ajustado por ML (sonda directa).
- Métrica principal = **mbits** (log-loss), no Top-3. IC95 por bootstrap de
  bloque-día (2000 remuestreos). p-valor una cola, **corrección Benjamini-Hochberg
  a nivel familia** (308 pruebas).
- **Compuerta de supervivencia**: aporte OOF **> 0 en 4/4 cuartos** (peso ajustado
  con 3 cuartos, se puntúa el 4º) **Y** `q(BH) < 0.05`. Nada se integra al modelo.

> **Aclaración obligada sobre "+90 mbits".** Esos +90/+120 mbits son la ventaja del
> ensamble **entero** sobre uniforme. El oráculo walk-forward de la política medible
> es 10.38 % Top-3, **por debajo** del ensamble (12.89 %): por construcción ninguna
> feature residual puede acercarse a +90 mbits. Ese número es la vara de "¿vale la
> pena integrarlo?", NO el filtro de la compuerta. El filtro real es 4/4 + BH.

### Resultado
- **308 hipótesis** evaluadas sobre 7.357 sorteos de desarrollo (semilla 20260918).
- **Señales (4/4 OOF>0 Y q_BH<0.05): 0 / 308.**
- Aporte máximo de cualquier hipótesis: **+1.68 mbits** (`win_last*cnt150_bin`),
  frente a **+120 mbits** del ensamble. Ninguna llega ni al 1,5 % de su margen.
- **0 hipótesis significativas** tras Benjamini-Hochberg: el `q_BH` mínimo de toda
  la familia es **0.523**. Sin corrección, ninguna baja de p≈0.02.
- Sólo **5** hipótesis pasan el heurístico "OOF>0 en 4/4 cuartos", y **todas** son
  ruido: aporte ≤ +0.60 mbits, IC95 cruzando 0, q_BH=0.523.

### Tabla (extracto — completa en `investigacion/2026-09-18/a_estadistica/tabla_full.md` y `barrido_full.json`)

**Top-6 por aporte (los más grandes de las 308):**

| hipótesis | a | mbits | IC95 | OOF cuartos | 4/4 | q_BH | veredicto |
|---|---|---|---|---|---|---|---|
| win_last×cnt150 | 8 | +1.68 | [+0.12,+3.20] | [−1.6, +1.9, +2.7, +2.7] | no | 0.523 | RUIDO |
| win_last×cnt150 | 1 | +1.55 | [−0.08,+3.02] | [−1.0, +1.6, +2.6, +2.2] | no | 0.523 | RUIDO |
| dow×dd | 8 | +1.13 | [−0.17,+2.48] | [−1.4, +1.7, +1.9, +1.5] | no | 0.523 | RUIDO |
| vhoy×k | 1 | +1.02 | [−0.14,+2.03] | [−1.1, +0.4, −0.2, +2.2] | no | 0.523 | RUIDO |
| cnt150 | 1 | +0.97 | [−0.11,+2.12] | [−2.2, +1.3, +2.0, +1.6] | no | 0.523 | RUIDO |
| vhoy×k_borde | 1 | +0.97 | [−0.12,+2.00] | [−1.2, +0.2, +0.4, +2.1] | no | 0.523 | RUIDO |

**Las únicas 5 que pasan 4/4 OOF>0 (ninguna pasa BH):**

| hipótesis | a | mbits | IC95 | OOF cuartos | q_BH | veredicto |
|---|---|---|---|---|---|---|
| neigh_last | 1 | +0.60 | [−0.33,+1.53] | [+0.5, +1.2, +0.3, +0.1] | 0.523 | RUIDO |
| neigh_last | 8 | +0.60 | [−0.34,+1.58] | [+0.5, +1.2, +0.3, +0.1] | 0.523 | RUIDO |
| neigh_last×regimen_rep | 1 | +0.51 | [−0.30,+1.32] | [+0.3, +0.8, +0.5, +0.2] | 0.523 | RUIDO |
| neigh_last×regimen_rep | 8 | +0.51 | [−0.33,+1.31] | [+0.3, +0.8, +0.5, +0.2] | 0.523 | RUIDO |
| cnt76 | 1 | +0.09 | [−0.26,+0.47] | [+0.1, +0.0, +0.1, +0.1] | 0.523 | RUIDO |

### Conclusión binaria del Enjambre A: **ESPACIO CERRADO**
Ninguna de las 308 hipótesis sobrevive la compuerta (4/4 OOF + BH). El mejor
negativo documentado es `win_last×cnt150` con **+1.68 mbits** (IC95 [+0.12,+3.20],
pero OOF negativo en el 1er cuarto y q_BH=0.523). El "candidato" más consistente
—`neigh_last` (vecino de tablero del ganador anterior), +0.60 mbits, IC95 cruza 0—
es ruido. **Certificado sólido**: con 308 features causales, walk-forward estricto,
OOF por cuartos y BH a nivel familia, no queda señal residual explotable sobre el
ensamble en desarrollo. Coherente con los hilos 1–3 ya muertos y con el oráculo de
la política (10.38 % < 12.89 %): el ensamble ya capturó todo lo medible.

**Reproducción:**
```powershell
$env:PYTHONIOENCODING="utf-8"
cd C:\Users\edics\Downloads\lotto-activo\lotto-activo
python investigacion\2026-09-18\a_estadistica\barrido.py      # semilla 20260918
```

---

## ENJAMBRE B — INTELIGENCIA DEL PRODUCTO

### Inventario (fuentes públicas únicamente)
| Ítem | Hallazgo |
|---|---|
| **Operador** | Corporación **Biglot 777 c.a.** |
| **Licencia** | **Malta Gaming Authority**, vigente desde 2019 |
| **Sorteo (público)** | "algoritmos digitales completamente aleatorios", certificado por funcionario |
| **`lotterly.co`** | Backend privado de `selvaplus.com` y `guacharoactivo.com.ve` (familia Biglot). **Sin docs públicas, sin marketing, sin endpoints documentados.** |
| **"Vector 3"** | **Cero huella pública** como software de sorteos. Codename interno, no producto documentado. |
| **Metadata por sorteo** (`api.lotterly.co/v1/results/<slug>/`, ~19.000 registros desde 2022-02-22) | **Exactamente 3 campos: `date`, `time`, `result`.** `time` = slot programado (`HH:15:00`/`HH:00:00`, segundos siempre `00`). **Sin** id de sorteo, delay, server-time, nonce ni semilla. |
| **Correlación de campos con el resultado** | Ninguna. El metadata público es inerte. |

### Veredicto binario del Enjambre B: **IMPLEMENTACIÓN CERRADA**
1. **Generador fuerte por evidencia**: licencia MGA ⇒ RNG bajo régimen de
   certificación (CSPRNG probado por laboratorio independiente). Coincide con el
   hecho ya establecido en el proyecto (choice ponderada sobre PRNG fuerte; V1–V3
   archivados como ruido).
2. **Nada público es explotable**: la única superficie que en principio serviría
   —timestamps finos de ejecución o material de semilla— **no está expuesta**. La
   API pública sólo devuelve fecha, slot y resultado.
3. **"Vector 3" no es un generador de debilidad conocida**: no existe públicamente.

> **Límite por diseño**: caractericé la superficie pública y di el veredicto de
> fortaleza. No construyo un procedimiento de recuperación de semilla ni de
> predicción contra el sistema en vivo del operador. "Documentar, no ejecutar"
> significa parar en la caracterización.

**Reproducción:**
```powershell
$env:PYTHONIOENCODING="utf-8"
python investigacion\2026-09-18\b_producto\inventario_api.py
```

---

## QUÉ HARÍA FALTA PARA REABRIR CADA FRENTE (10 líneas)

1. **A — datos**: ~4× el desarrollo actual (~29.000 sorteos, ~8 años más) para
   decidir con |z|≥5 el único residual vivo histórico (g=1 intradía, 0.685×).
2. **A — señal**: que el barrido arroje una hipótesis con aporte OOF > 0 en 4/4
   cuartos, q(BH) < 0.05 y magnitud ≳ 5 mbits sostenida en datos vivos frescos.
3. **A — régimen**: un cambio de política del operador (el monitor `|z|>3` en 2
   ventanas seguidas) que abra estructura nueva no capturada por el ensamble.
4. **A — validación**: cualquier candidata debe confirmarse en el marcador VIVO,
   no re-mirando el tramo de prueba (ya contaminado con 1 mirada).
5. **B — metadata**: que el operador exponga un timestamp de ejecución sub-slot,
   un id de sorteo secuencial o cualquier campo correlacionado con el resultado.
6. **B — generador**: evidencia pública de un PRNG débil (LCG/semilla temporal)
   en "Vector 3" o en Biglot 777 — hoy inexistente.
7. **B — certificación**: que caduque/retire la licencia MGA o aparezca un informe
   de laboratorio señalando un RNG no conforme.
8. **B — filtración**: documentación interna, repos o binarios del vendor
   públicamente accesibles (sin acceso no autorizado) que revelen el generador.
9. **B — canal lateral**: latencias/orden de publicación con estructura explotable
   medibles sólo con captura masiva propia y legítima (no contra su backend).
10. **Ambos**: cualquiera de lo anterior se documenta para evaluación interna; no
    se ejecuta nada contra sistemas del operador.
