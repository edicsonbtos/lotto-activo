# Ingenieria inversa de la politica f

Generado por `herramientas/exploracion/politica_f.py`.

- Historial completo **12502 sorteos**; tramo de prueba (>= 9357) **intacto**.
- Analizado: **desarrollo** `[2000, 9357)` = **7357 sorteos** = 279566 pares (sorteo, animal).
- Azar puro por animal: 1/38 = **2.632%**.

---

## Tarea 1 - Mapa fino de f(hueco)

### 1.1 Tasa por hueco individual (1 a 60, mas 61+)

| hueco | n pares | aciertos | tasa | IC95 | vs azar |
|---|---|---|---|---|---|
| 1 | 7357 | 47 | 0.639% | 0.481-0.848% | **0.24x** |
| 2 | 7310 | 95 | 1.300% | 1.064-1.586% | **0.49x** |
| 3 | 7215 | 113 | 1.566% | 1.304-1.880% | **0.60x** |
| 4 | 7102 | 98 | 1.380% | 1.134-1.679% | **0.52x** |
| 5 | 7004 | 130 | 1.856% | 1.565-2.200% | **0.71x** |
| 6 | 6874 | 130 | 1.891% | 1.595-2.241% | **0.72x** |
| 7 | 6744 | 146 | 2.165% | 1.844-2.540% | **0.82x** |
| 8 | 6598 | 165 | 2.501% | 2.151-2.906% | **0.95x** |
| 9 | 6433 | 201 | 3.125% | 2.727-3.578% | **1.19x** |
| 10 | 6232 | 172 | 2.760% | 2.381-3.197% | **1.05x** |
| 11 | 6060 | 143 | 2.360% | 2.007-2.773% | **0.90x** |
| 12 | 5917 | 153 | 2.586% | 2.211-3.022% | **0.98x** |
| 15 | 5369 | 193 | 3.595% | 3.129-4.127% | **1.37x** |
| 18 | 4842 | 181 | 3.738% | 3.239-4.310% | **1.42x** |
| 20 | 4473 | 177 | 3.957% | 3.424-4.569% | **1.50x** |
| 25 | 3757 | 128 | 3.407% | 2.873-4.036% | **1.29x** |
| 30 | 3221 | 96 | 2.980% | 2.447-3.626% | **1.13x** |
| 40 | 2418 | 61 | 2.523% | 1.969-3.227% | **0.96x** |
| 50 | 1825 | 39 | 2.137% | 1.567-2.908% | **0.81x** |
| 60 | 1436 | 31 | 2.159% | 1.525-3.048% | **0.82x** |
| 61+ | 56223 | 1408 | 2.504% | 2.378-2.637% | **0.95x** |

(Tabla completa 1..60 en el JSON adjunto; aqui van los puntos de referencia.)

### Curva (cada linea es un hueco; `|` marca el azar 2.632%)

```
g= 1  0.24x ######.................|........................
g= 2  0.49x ###########............|........................
g= 3  0.60x ##############.........|........................
g= 4  0.52x ############...........|........................
g= 5  0.71x ################.......|........................
g= 6  0.72x #################......|........................
g= 7  0.82x ###################....|........................
g= 8  0.95x ######################.|........................
g= 9  1.19x #######################|###.....................
g=10  1.05x #######################|........................
g=11  0.90x #####################..|........................
g=12  0.98x #######################|........................
g=13  1.37x #######################|########................
g=14  1.28x #######################|#####...................
g=15  1.37x #######################|#######.................
g=16  1.29x #######################|######..................
g=17  1.21x #######################|####....................
g=18  1.42x #######################|#########...............
g=19  1.53x #######################|###########.............
g=20  1.50x #######################|###########.............
g=21  1.29x #######################|######..................
g=22  1.37x #######################|########................
g=23  1.19x #######################|###.....................
g=24  1.15x #######################|##......................
g=25  1.29x #######################|######..................
g=26  1.19x #######################|###.....................
g=27  1.15x #######################|##......................
g=28  1.06x #######################|........................
g=29  1.07x #######################|#.......................
g=30  1.13x #######################|##......................
```

### 1.3 Multiplicadores DESNORMALIZADOS (logit condicional)

La tasa observada es `w_i / suma_j w_j` y esa suma cambia en cada sorteo. Para recuperar el peso `w` que usa el script hay que resolver el sistema. Se ajusta por maxima verosimilitud

> `P(gana a | sorteo t) = exp(b[bin(hueco)]) / suma_a' exp(b[bin(hueco_a')])`

y el multiplicador es `exp(b)` normalizado a 1 en el bin de referencia.

| hueco | multiplicador exp(b) | tasa cruda (tasa/azar) |
|---|---|---|
| 1 | **0.238** | 0.243 |
| 2 | **0.484** | 0.494 |
| 3 | **0.583** | 0.595 |
| 4 | **0.513** | 0.524 |
| 5 | **0.690** | 0.705 |
| 6 | **0.703** | 0.719 |
| 7 | **0.805** | 0.823 |
| 8 | **0.930** | 0.950 |
| 9 | **1.163** | 1.187 |
| 10 | **1.027** | 1.049 |
| 11 | **0.877** | 0.897 |
| 12 | **0.962** | 0.983 |
| 15 | **1.340** | 1.366 |
| 20 | **1.479** | 1.504 |
| 25 | **1.271** | 1.295 |
| 30 | **1.110** | 1.133 |
| 40 | **0.937** | 0.959 |
| 50 | **0.792** | 0.812 |
| 60 | **0.800** | 0.820 |
| 61+ | **0.931** | 0.952 |

El multiplicador desnormalizado y la tasa cruda casi coinciden: la suma de pesos `S_t` varia poco entre sorteos, asi que la lectura ingenua no estaba lejos. Diferencia media absoluta: **0.0208**.

### 1.2 Forma funcional: suave o escalones?

Comparacion por AIC (verosimilitud binomial exacta por bin, 60 bins con n>=50):

| forma | parametros | logver | AIC | delta AIC |
|---|---|---|---|---|
| escalones (segmentacion BIC) | 5 | -27191.4 | 54392.9 | +0.0 |
| exponencial saturante x decaimiento | 4 | -27193.0 | 54394.0 | +1.1 |
| exponencial saturante | 3 | -27229.7 | 54465.3 | +72.4 |
| logistica en log(hueco) | 3 | -27242.9 | 54491.8 | +98.9 |
| potencia | 2 | -27330.0 | 54664.0 | +271.1 |
| constante (nula) | 1 | -27437.1 | 54876.1 | +483.3 |

**Forma ganadora: escalones (segmentacion BIC).**

Puntos de corte detectados por segmentacion binaria (penalizacion BIC): **hueco 3, hueco 7, hueco 13, hueco 28**.

| regimen | huecos | n | tasa | IC95 | multiplicador |
|---|---|---|---|---|---|
| 1 | 1-2 | 14667 | 0.968% | 0.822-1.140% | **0.37x** |
| 2 | 3-6 | 28195 | 1.671% | 1.527-1.827% | **0.63x** |
| 3 | 7-12 | 37984 | 2.580% | 2.425-2.744% | **0.98x** |
| 4 | 13-27 | 68061 | 3.460% | 3.325-3.600% | **1.31x** |
| 5 | 28-60 | 74436 | 2.688% | 2.574-2.807% | **1.02x** |

---

## Tarea 2 - Interacciones de f

Metodo: se compara por razon de verosimilitudes el logit condicional con **efectos principales** (f depende solo del hueco) contra el que permite que los multiplicadores **cambien** segun la variable. Regimenes de hueco tomados de los cortes de la Tarea 1. Se exige p < 0.01 tras FDR **y** tamano de efecto relativo > 10%.

Regimenes usados: R1 = huecos 1-2, R2 = huecos 3-6, R3 = huecos 7-12, R4 = huecos 13-27, R5 = huecos 28-inf.

| interaccion | razon de verosim. | gl | p | pasa FDR |
|---|---|---|---|---|
| hora del sorteo | 344.3 | 44 | 1.90e-44 | SI |
| veces que ya salio hoy (0,1,2+) | 206.1 | 8 | 6.92e-33 | SI |
| dia de semana | 48.7 | 24 | 0.0021 | SI |
| posicion en la jornada (0-11) | 296.7 | 44 | 1.30e-36 | SI |

Interacciones que pasan el filtro estadistico. Ahora el filtro de **tamano de efecto**:

- **hora del sorteo**: variacion relativa maxima del multiplicador entre niveles = **245%** -> **INTERACCION REAL**

  | nivel | R1 | R2 | R3 | R4 | R5 |
  |---|---|---|---|---|---|
  | 0 | 0.63 | 0.50 | 0.47 | 1.74 | 1.00 |
  | 1 | 1.03 | 1.46 | 1.29 | 1.58 | 1.00 |
  | 2 | 0.34 | 1.01 | 0.85 | 1.39 | 1.00 |
  | 3 | 0.16 | 1.04 | 1.25 | 1.26 | 1.00 |
  | 4 | 0.09 | 0.67 | 0.90 | 1.25 | 1.00 |
  | 5 | 0.26 | 0.68 | 1.24 | 1.48 | 1.00 |
  | 6 | 0.22 | 0.21 | 1.20 | 0.99 | 1.00 |
  | 7 | 0.02 | 0.13 | 0.87 | 0.93 | 1.00 |
  | 8 | 0.11 | 0.19 | 0.86 | 1.18 | 1.00 |
  | 9 | 0.32 | 0.33 | 0.81 | 1.35 | 1.00 |
  | 10 | 0.83 | 0.99 | 0.95 | 1.48 | 1.00 |
  | 11 | 0.95 | 0.99 | 1.12 | 1.80 | 1.00 |

- **veces que ya salio hoy (0,1,2+)**: variacion relativa maxima del multiplicador entre niveles = **266%** -> **INTERACCION REAL**

  | nivel | R1 | R2 | R3 | R4 | R5 |
  |---|---|---|---|---|---|
  | 0 | 1.08 | 1.08 | 1.11 | 1.33 | 1.00 |
  | 1 | 4.28 | 6.17 | 8.80 | 1.00 | 1.00 |
  | 2 | 1.38 | 0.00 | 0.00 | 1.00 | 1.00 |

- **dia de semana**: variacion relativa maxima del multiplicador entre niveles = **88%** -> **INTERACCION REAL**

  | nivel | R1 | R2 | R3 | R4 | R5 |
  |---|---|---|---|---|---|
  | 0 | 0.35 | 0.44 | 0.77 | 1.22 | 1.00 |
  | 1 | 0.24 | 0.64 | 0.93 | 1.25 | 1.00 |
  | 2 | 0.57 | 0.71 | 0.94 | 1.36 | 1.00 |
  | 3 | 0.37 | 0.69 | 1.06 | 1.54 | 1.00 |
  | 4 | 0.42 | 0.69 | 1.10 | 1.48 | 1.00 |
  | 5 | 0.24 | 0.61 | 1.08 | 1.42 | 1.00 |
  | 6 | 0.41 | 0.74 | 1.08 | 1.06 | 1.00 |

- **posicion en la jornada (0-11)**: variacion relativa maxima del multiplicador entre niveles = **230%** -> **INTERACCION REAL**

  | nivel | R1 | R2 | R3 | R4 | R5 |
  |---|---|---|---|---|---|
  | 0 | 0.78 | 0.79 | 0.63 | 1.53 | 1.00 |
  | 1 | 0.80 | 1.10 | 1.10 | 1.40 | 1.00 |
  | 2 | 0.13 | 1.15 | 1.15 | 1.42 | 1.00 |
  | 3 | 0.15 | 0.87 | 1.05 | 1.31 | 1.00 |
  | 4 | 0.09 | 0.81 | 0.99 | 1.34 | 1.00 |
  | 5 | 0.27 | 0.54 | 1.49 | 1.52 | 1.00 |
  | 6 | 0.15 | 0.09 | 0.98 | 0.84 | 1.00 |
  | 7 | 0.08 | 0.16 | 0.88 | 1.09 | 1.00 |
  | 8 | 0.25 | 0.28 | 0.84 | 1.23 | 1.00 |
  | 9 | 0.38 | 0.64 | 0.82 | 1.32 | 1.00 |
  | 10 | 0.87 | 0.90 | 1.07 | 1.65 | 1.00 |
  | 11 | 1.03 | 0.91 | 1.05 | 1.76 | 1.00 |


### 2.4 Pesos BASE: el primer sorteo del dia

El primer sorteo de la jornada es el momento con menos estado intradia. n=635, chi2=24.5 (gl=37), **p=0.9424**.

**Los pesos BASE por animal son uniformes.** No hay animal con peso propio: toda la politica vive en el hueco, no en la identidad.

