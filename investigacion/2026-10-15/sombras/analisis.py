# -*- coding: utf-8 -*-
"""Análisis secuencial, plata y regla RD15 sobre reg.json (salida de reconstruir.py). Solo lectura.
Semilla fija. Uso: python analisis.py > salida_analisis.txt"""
import json, math, os, random, sys
from collections import defaultdict
from statistics import NormalDist
AQUI = os.path.dirname(os.path.abspath(__file__))
N = NormalDist()
rnd = random.Random(20261015)
R_all = json.load(open(os.path.join(AQUI, "reg.json")))
# mismos sorteos que /api/sombra: producción no tiene sombra para 2026-10-02 8:00
R = [r for r in R_all if (r["f"], r["h"]) != ("2026-10-02", 0)]
DEC = json.load(open(os.path.join(AQUI, "sombra_decision.json"), encoding="utf-8"))
SOM = json.load(open(os.path.join(AQUI, "sombra.json"), encoding="utf-8"))

def jornadas(rows):
    d = defaultdict(list)
    for r in rows: d[r["f"]].append(r)
    return [d[k] for k in sorted(d)]

def boot(rows, fn, B=10000):
    """fn(lista de sorteos) -> número. IC por bootstrap de jornadas (90 % y 95 %)."""
    J = jornadas(rows); est = fn(rows); v = []
    for _ in range(B):
        s = [x for j in (rnd.choice(J) for _ in J) for x in j]
        v.append(fn(s))
    v.sort()
    q = lambda a: v[int(a * B)]
    return est, (q(0.05), q(0.95)), (q(0.025), q(0.975))

FX5 = {1: 2, 2: 2, 3: 2, 4: 1, 5: 1}
FX15 = {1: 3, 2: 3, 3: 3, 4: 2, 5: 2, **{k: 1 for k in range(6, 16)}}
neto5 = lambda rk: 30 * FX5.get(rk, 0) - 8
neto15 = lambda rk: 30 * FX15.get(rk, 0) - 23
print("=" * 70); print("1. SECUENCIAL ag12 (regla: n=931, IC90 inferior de Δmbits > 0, Top-5 pp/ficha punto >= -3)")
d = DEC["mbits_ag12_menos_ensamble"]; n0 = d["n"]; m0 = d["media"]
se0 = (d["ic90"][1] - d["ic90"][0]) / (2 * 1.645); sig = se0 * math.sqrt(n0)
print(f"producción: n={n0} media={m0} IC90={d['ic90']} -> EE={se0:.2f}, σ efectiva por sorteo (con jornadas)={sig:.1f}")
z0 = m0 / se0; print(f"z actual = {z0:.2f}  (p unilateral {1 - N.cdf(z0):.3f})")
NF = 931; nr = NF - n0; ser = sig / math.sqrt(nr); umbral = 1.645 * sig / math.sqrt(NF)
need = (NF * umbral - n0 * m0) / nr
print(f"a n=931 pasa si media final > {umbral:.2f} mbits; los {nr} sorteos restantes deben promediar > {need:.2f}")
print("Potencia condicional (efecto verdadero fijo):")
for dl in (0, 5, 10, m0, 19.4):
    print(f"  δ={dl:5.1f}: P(pasar a 931) = {1 - N.cdf((need - dl) / ser):.2f}")
print("Predictiva bayesiana (prior normal sobre δ; verosimilitud = lo observado):")
priors = {"plano": None, "escéptico N(0,10²)": (0, 10), "planificación N(10,10²)": (10, 10),
          "evidencia previa N(6,8²) (sellada −1,2 / ciega +19,4 / réplica +20)": (6, 8)}
for nom, pr in priors.items():
    if pr is None: mu, v = m0, se0 ** 2
    else:
        w0, w1 = 1 / pr[1] ** 2, 1 / se0 ** 2; v = 1 / (w0 + w1); mu = v * (w0 * pr[0] + w1 * m0)
    p = 1 - N.cdf((need - mu) / math.sqrt(v + ser ** 2))
    print(f"  {nom}: posterior δ ~ N({mu:.1f}, {math.sqrt(v):.1f}²) -> P(pasar a 931) = {p:.2f}")
# simulación con bloques de jornada (incluye la condición Top-5) y la segunda mirada a 3.500
J = jornadas(R)
blk = [([x["mb_ag"] - x["mb_ens"] for x in j], [100 * (neto5(x["r_ag"]) - neto5(x["r_ens"])) / 8 for x in j]) for j in J]
mm = sum(sum(a) for a, _ in blk) / sum(len(a) for a, _ in blk)
def sim(dl, S=4000):
    p931 = p3500 = 0; t5f = 0
    for _ in range(S):
        A, T = [], []
        for a, t in blk: A += a; T += t
        while len(A) < 3500:
            a, t = rnd.choice(blk); A += [x - mm + dl for x in a]; T += t
        def pasa(n):
            x = A[:n]; mu = sum(x) / n
            # EE por jornadas aprox. con 12 por jornada
            g = [sum(x[i:i + 12]) for i in range(0, n, 12)]; k = len(g); mg = sum(g) / k
            se = math.sqrt(sum((gi - mg) ** 2 for gi in g) / (k - 1) * k) / n
            return mu - 1.645 * se > 0, mu > 0
        ok, pos = pasa(931); t5 = sum(T[:931]) / 931 >= -3
        if ok and t5: p931 += 1
        elif ok and not t5: t5f += 1
        elif pos:
            ok2, _ = pasa(3500)
            p3500 += ok2
    return p931 / S, p3500 / S, t5f / S
print("Simulación por bloques de jornada (observados, re-centrados a δ; Top-5 tal cual se observó):")
for dl in (0, 5, 10, round(mm, 1)):
    a, b, c = sim(dl, 1500)
    print(f"  δ={dl:5.1f}: pasa a 931 = {a:.2f}; pasa luego a 3.500 = {b:.2f}; total = {a + b:.2f}; frenado por Top-5 = {c:.2f}")
t = n0 / NF
z_obf = N.inv_cdf(1 - 2 * (1 - N.cdf(N.inv_cdf(0.975) / math.sqrt(t))) / 2)
print(f"O'Brien-Fleming (Lan-DeMets, α=0,05 unilateral) en t={t:.3f}: frontera z ≈ {z_obf:.2f} (hoy z = {z0:.2f}); Pocock ≈ 2,2")
dia = lambda n_falta: n_falta / 12
print(f"Fecha n=931: faltan {nr} -> {dia(nr):.1f} días desde 2026-10-14 (cierre) -> ~2026-12-12; preregistro: 2026-12-14")

print("=" * 70); print("2. ensamble_exp (freno a 930 si n>=600 y Δ<−5; decide a 6.000 con IC90 inf > 0 y Top-5 IC90 inf > −3 pp)")
e = SOM["exposicion"]["diferencias"]["ensamble_exp_vs_ensamble"]["mbits"]; ne, me = e["n"], e["media"]
see = (e["ic90"][1] - e["ic90"][0]) / 3.29; sge = see * math.sqrt(ne)
print(f"n={ne} media={me} EE={see:.2f} σ efectiva={sge:.1f} (preregistro suponía ~78)")
for NF2, lab in ((930, "freno 930"), (6000, "decisión 6.000")):
    nr2 = NF2 - ne; s2 = sge / math.sqrt(nr2)
    if NF2 == 930:
        # P(media final < −5)
        for dl in (0, 2.3, me):
            th = (NF2 * -5 - ne * me) / nr2
            print(f"  {lab}, δ={dl}: P(se apaga) = {N.cdf((th - dl) / s2):.3f}")
    else:
        u = 1.645 * sge / math.sqrt(NF2); th = (NF2 * u - ne * me) / nr2
        for dl in (0, 2.3, me):
            print(f"  {lab}, δ={dl}: P(pasa mbits) = {1 - N.cdf((th - dl) / s2):.2f}")
        for nom, pr in (("plano", None), ("preregistro N(2,3; 2,6²)", (2.3, 2.6))):
            if pr is None: mu, v = me, see ** 2
            else:
                w0, w1 = 1 / pr[1] ** 2, 1 / see ** 2; v = 1 / (w0 + w1); mu = v * (w0 * pr[0] + w1 * me)
            print(f"  {lab}, predictiva {nom}: δ~N({mu:.1f},{math.sqrt(v):.1f}²) -> P(pasa mbits) = {1 - N.cdf((th - mu) / math.sqrt(v + s2 ** 2)):.2f}")
print(f"  Fechas: 930 -> faltan {930 - ne} = {(930 - ne) / 12:.0f} días (~2026-12-18); 6.000 -> {(6000 - ne) / 12:.0f} días (~2028-02)")
v8 = SOM["ventana_8am"]; print(f"ventana_8am: n={v8['n']} mañanas, obs {v8['ventana_obs']} vs esp {v8['ventana_esp']}; 730 -> ~{(730 - v8['n'])} días más (~2028-10)")
print(f"  OJO: IC90 de mbits {v8['mbits_exp8_vs_exp']['ic90']} es artefacto: 0 aciertos en la ventana -> todas las mañanas suman lo mismo; un acierto en la ventana resta ~{1000*math.log2(0.59):.0f} mbits")

print("=" * 70); print("3. PLATA (mismos 226 sorteos desde 2026-09-26; IC por bootstrap de jornadas, 10.000)")
modelos = [("vivo congelado (con 8:00)", "r_vivo"), ("vivo como se juega (regla RD Top-5/Top-15)", None),
           ("ensamble sin 8:00 (base de la decisión)", "r_ens"), ("ag12", "r_ag"), ("ag12 + RD ×0,5/×0,75", "r_agrd"),
           ("ag12 + regla RD Top-15", "r_ag_rd15")]
def rk_juego(r, cual):
    if cual == 5: return r["r_vivo_rd5"]
    return r["r_vivo_rd15"] if r["f"] >= "2026-10-07" else r["r_vivo"]   # Top-15 con regla desde el 7-oct
res = {}
for nom, k in modelos:
    for plan, fn, fichas in (("Top-5 2-2-2-1-1", neto5, 8), ("Top-15 pond. 3-3-3-2-2+1x10", neto15, 23)):
        if k is None:
            cual = 5 if fichas == 8 else 15
            f = lambda rows, fn=fn, cual=cual: sum(fn(rk_juego(r, cual)) for r in rows)
        else:
            f = lambda rows, fn=fn, k=k: sum(fn(r[k]) for r in rows)
        est, i90, i95 = boot(R, f)
        res[(nom, plan)] = est
        print(f"  {nom:45s} {plan:28s} neto {est:+6.0f} u  ({100 * est / (fichas * len(R)):+5.1f} %)  IC90 [{i90[0]:+.0f}; {i90[1]:+.0f}]  IC95 [{i95[0]:+.0f}; {i95[1]:+.0f}]")
print("  Diferencias pareadas ag12 − vivo como se juega:")
for plan, fn, cual in (("Top-5", neto5, 5), ("Top-15 pond.", neto15, 15)):
    f = lambda rows, fn=fn, cual=cual: sum(fn(r["r_ag"]) - fn(rk_juego(r, cual)) for r in rows)
    est, i90, i95 = boot(R, f); print(f"    {plan}: {est:+.0f} u IC90 [{i90[0]:+.0f}; {i90[1]:+.0f}] IC95 [{i95[0]:+.0f}; {i95[1]:+.0f}]")
RX = [r for r in R if r["f"] >= "2026-10-02"]
print(f"  Exposición (desde 2026-10-02, n={len(RX)}):")
for nom, k in (("ensamble", "r_ens"), ("ensamble_exp", "r_ensexp"), ("ag12_rd", "r_agrd"), ("ag12_rd_exp", "r_agrdexp")):
    for plan, fn, fichas in (("Top-5", neto5, 8), ("Top-15 pond.", neto15, 23)):
        est, i90, _ = boot(RX, lambda rows, fn=fn, k=k: sum(fn(r[k]) for r in rows), 4000)
        print(f"    {nom:13s} {plan:13s} {est:+6.0f} u ({100 * est / (fichas * len(RX)):+5.1f} %) IC90 [{i90[0]:+.0f}; {i90[1]:+.0f}]")
f = lambda rows: sum(neto5(r["r_ensexp"]) - neto5(r["r_ens"]) for r in rows); print("    exp − ens Top-5:", boot(RX, f, 4000))
f = lambda rows: sum(neto15(r["r_ensexp"]) - neto15(r["r_ens"]) for r in rows); print("    exp − ens Top-15 pond.:", boot(RX, f, 4000))

print("=" * 70); print("4. REGLA RD EN TOP-15 (desde 2026-10-07, h>0, RD (h−1):30 conocido)")
R15 = [r for r in R_all if r["f"] >= "2026-10-07" and r["h"] > 0 and r["rd_prev"] is not None]
camb = [r for r in R15 if r["r_vivo_rd15"] != r["r_vivo"]]
sin = sum(neto15(r["r_vivo"]) for r in R15); con = sum(neto15(r["r_vivo_rd15"]) for r in R15)
print(f"n={len(R15)} cambios (orden distinto donde cayó el ganador) = {len(camb)}; sin {sin:+} con {con:+} dif {con - sin:+}  (API: n=88 sin −194 con −224 dif −30)")
for r in camb:
    print(f"   {r['f']} h{r['h']}: ganador puesto {r['r_vivo']} -> {r['r_vivo_rd15']}  Δ {neto15(r['r_vivo_rd15']) - neto15(r['r_vivo']):+}  (RD previo={r['rd_prev']}, ganó el de RD: {r['r_vivo_rd15'] == 16 and r['r_vivo'] <= 15})")
f = lambda rows: sum(neto15(r["r_vivo_rd15"]) - neto15(r["r_vivo"]) for r in rows)
est, i90, i95 = boot(R15, f); print(f"dif con−sin: {est:+} u = {100 * est / (23 * len(R15)):+.2f} pp/ficha  IC90 [{i90[0]:+}; {i90[1]:+}]  IC95 [{i95[0]:+}; {i95[1]:+}]")
# separar: Top-5 (regla vieja, ya validada) vs puestos 6-15 (lo nuevo)
f6 = lambda rows: sum(neto15(r["r_vivo_rd15"]) - neto15(r["r_vivo_rd5"]) for r in rows)
print("  parte nueva (6º-16º) frente a solo regla Top-5:", boot(R15, f6))
# Esperado bajo la hipótesis de la prueba (+1,57 pp/ficha fresco, +2,47 réplica): en u
for pp in (1.57, 2.47):
    print(f"  esperado con +{pp} pp/ficha en {len(R15)} sorteos: {pp / 100 * 23 * len(R15):+.0f} u")
# mismo efecto aplicado a ag12 y al ensamble sin 8:00 desde 26-sep (más n)
RB = [r for r in R_all if r["h"] > 0 and r["rd_prev"] is not None]
for nom, a, b in (("ensamble sin 8:00", "r_ens", "r_ens_rd15"), ("ag12", "r_ag", "r_ag_rd15")):
    f = lambda rows, a=a, b=b: sum(neto15(r[b]) - neto15(r[a]) for r in rows)
    est, i90, i95 = boot(RB, f)
    print(f"  desde 26-sep, {nom}: n={len(RB)} dif {est:+} u = {100 * est / (23 * len(RB)):+.2f} pp/ficha IC90 [{i90[0]:+}; {i90[1]:+}]")
# ¿con qué frecuencia repite en LA h el animal de RD (h−1):30 cuando estaba en el Top-15?
en15 = [r for r in RB if r["r_vivo_rd15"] != r["r_vivo"] or True]
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..", "..")))
from comun import IDX
rep = sum(1 for r in RB if r["w"] == IDX[r["rd_prev"]])
print(f"  LA h repite el animal de RD (h−1):30: {rep}/{len(RB)} = {100 * rep / len(RB):.2f} % (azar 2,63 %)")
