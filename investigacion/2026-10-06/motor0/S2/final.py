"""S2 final congelado (C, vida 90; mezcla w = 0,75 por la regla). AJUSTE/ELECCION, selector S1 y UNA mirada a PRUEBA26."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import eval_s2 as E
A = E.A; SP = E.SP
z = np.load(SP + "/motor0_S2.npz"); S2 = z["P"]; MIX = z["P_mezcla075"]
C = {"PROD": A.PROD, "S2 (w=1)": S2, "S2+PROD w=0.75": MIX, "S2+PROD w=0.5 (info)": E.mezcla(S2, 0.5),
     "M4 final (con RD)": np.load(SP + "/motor2_M4.npz")["P"], "M4 V1 sin RD": np.load(SP + "/m4_V1noRD.npz")["P"]}
TR = ("AJUSTE", "ELECCION", "PRUEBA26")
res = {}
print("== evaluar del arnés (PRUEBA26 contaminada; una sola mirada, registrada) ==")
for k in ("S2 (w=1)", "S2+PROD w=0.75"):
    A.evaluar(C[k], "S2-" + k.replace(" ", ""), tramos=TR, extra="motor0 S2 congelado; PRUEBA26 contaminada")
print("\n== Top-15 y plata con regla RD (pareado contra PROD) ==")
for tr in TR:
    for k, P in C.items():
        o = E.resumen(P, k, tr); res[f"{k}|{tr}"] = o; print(E.linea(o))
        print(f"{'':26}netas/día: T15plano {o['T15plano_netodia']:+.1f} (PROD {o['T15plano_netodia_ref']:+.1f}) "
              f"T15pond {o['T15pond_netodia']:+.1f} ({o['T15pond_netodia_ref']:+.1f}) T5esc {o['T5esc_netodia']:+.1f} "
              f"({o['T5esc_netodia_ref']:+.1f}) | ΔT15plano {o['T15plano_d']:+.1f} [{o['T15plano_dic'][0]:+.1f};{o['T15plano_dic'][1]:+.1f}] "
              f"ΔT15pond {o['T15pond_d']:+.1f} [{o['T15pond_dic'][0]:+.1f};{o['T15pond_dic'][1]:+.1f}]")
print("\n== Top-15 por régimen (mié-vie contra resto), S2 w=1 y mezcla ==")
for tr in TR:
    for nmk in ("S2 (w=1)", "S2+PROD w=0.75"):
        for lab, sel in (("mié-vie", np.isin(A.DOW, [2, 3, 4])), ("resto", ~np.isin(A.DOW, [2, 3, 4]))):
            o = E.resumen(C[nmk], nmk, tr, sel=sel)
            print(f"  {tr:8} {nmk:16} {lab:8} n={o['n']:4d} Top15 {o['top15']:.1f} (PROD {o['top15_ref']:.1f}) Δ {o['d15']:+.2f} "
                  f"[{o['d15_ic'][0]:+.2f};{o['d15_ic'][1]:+.2f}] Δmbits {o['dmb']:+.1f}")
print("\n== Selector S1 (sin reajustar): jugar solo si P̂ ≥ 0,50 ==")
s1 = np.load(SP + "/selector_S1.npz")
assert (s1["t"] == A.T).all()
for tr in TR:
    nd = len(np.unique(A.F[A.TRAMOS[tr]]))
    ref = E.resumen(A.PROD, "REF", tr)  # Top-5 esc PROD con cambio, todos
    print(f"  {tr}: REF Top-5 esc PROD todos {ref['T5esc_ref']:+.1f}%/ficha, netas/día {ref['T5esc_netodia_ref']:+.1f}")
    for sk in ("jugar_PROD", "jugar_M4"):
        sel = s1[sk].astype(bool)
        for k in ("PROD", "S2 (w=1)", "S2+PROD w=0.75"):
            o = E.resumen(C[k], k, tr, sel=sel)
            fr = 100 * o["n"] / A.TRAMOS[tr].sum()
            # netas por día sobre TODOS los días del tramo
            idx = np.where(A.TRAMOS[tr] & sel)[0]; rk = E.rango_rd(E.norm(C[k]), idx)
            net = {pl: (E.ganancia(rk, pl)[0] - E.PLANES[pl].sum()).sum() / nd for pl in ("T15plano", "T15pond")}
            print(f"    {sk:10} {k:16} jugado {fr:4.1f}% Top15 {o['top15']:.1f} T15plano {o['T15plano']:+.1f}% "
                  f"[{o['T15plano_ic'][0]:+.0f};{o['T15plano_ic'][1]:+.0f}] netas/día {net['T15plano']:+.1f} | "
                  f"T15pond {o['T15pond']:+.1f}% [{o['T15pond_ic'][0]:+.0f};{o['T15pond_ic'][1]:+.0f}] netas/día {net['T15pond']:+.1f}")
json.dump(res, open("/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2/final.json", "w"), default=float, indent=0)
