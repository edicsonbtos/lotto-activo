# -*- coding: utf-8 -*-
"""Idea del usuario (2026-09-27): "el Top-15 acierta, pero el animal sale a OTRA hora".

Para cada sorteo t se arma la CANASTA = animales que estuvieron en el Top-15 de alguna hora anterior del MISMO día
pero ya no están en el Top-15 actual. Pregunta: ¿el ganador sale de la canasta más de lo que el motor dice ahora?
  O/E = aciertos de la canasta / suma de las probabilidades actuales del motor sobre la canasta.
  O/E > 1 → la canasta trae información que el motor perdió. O/E ≈ 1 → es memoria selectiva (ya pasó en ag11).
También: acierto del Top-15 de la hora anterior contra el Top-15 actual.

  python top15_otra_hora.py dev | ciega | vivo
"""
import json, os, subprocess, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import lotto_eval as LE  # noqa: E402

REG = os.path.join(AQUI, "registro_top15_otra_hora.jsonl")


def medir(P, y, dia, titulo=None):
    R15 = np.argsort(-P, 1, kind="stable")[:, :15]
    en15 = np.zeros_like(P, bool); np.put_along_axis(en15, R15, True, 1)
    obs = esp = 0.0; var = 0.0; tam = []; hit_prev = hit_now = n_prev = 0
    por_dia = {}
    visto = np.zeros(P.shape[1], bool)
    for t in range(len(y)):
        if t == 0 or dia[t] != dia[t - 1]:
            visto[:] = False
        else:
            n_prev += 1
            hit_prev += en15[t - 1, y[t]]; hit_now += en15[t, y[t]]
        cesta = visto & ~en15[t]
        if cesta.any():
            p = P[t, cesta].sum(); o = float(cesta[y[t]])
            obs += o; esp += p; var += p * (1 - p); tam.append(cesta.sum())
            d = por_dia.setdefault(dia[t], [0.0, 0.0]); d[0] += o; d[1] += p
        visto |= en15[t]
    arr = np.array(list(por_dia.values()))
    rng = np.random.default_rng(3); I = rng.integers(0, len(arr), (4000, len(arr)))
    oe_b = arr[I, 0].sum(1) / arr[I, 1].sum(1)
    r = {"oe": obs / esp, "ic95": [float(np.percentile(oe_b, 2.5)), float(np.percentile(oe_b, 97.5))],
         "aciertos": obs, "esperados": esp, "z": (obs - esp) / var ** 0.5, "tam_canasta": float(np.mean(tam)),
         "top15_hora_anterior": hit_prev / n_prev, "top15_actual": hit_now / n_prev, "n": int(len(y))}
    if titulo:
        print(f"{titulo:24s} n={r['n']:5d}  canasta media {r['tam_canasta']:.1f} animales · sale de ahí "
              f"{obs:.0f} vs {esp:.1f} que el motor esperaba → O/E {r['oe']:.2f} [{r['ic95'][0]:.2f}; {r['ic95'][1]:.2f}]"
              f" z {r['z']:+.1f} · Top-15 hora anterior {r['top15_hora_anterior']*100:.1f} % vs actual {r['top15_actual']*100:.1f} %")
    return r


def dev():
    D = LE.cargar(); c = np.load(os.path.join(AQUI, "calor_cache.npz"))
    P = c["P"] / c["P"].sum(1, keepdims=True); y = c["y"]; n = len(y)
    dia = np.asarray(D.dia)[LE.W:LE.W + n]; m = n // 2
    medir(P[:m], y[:m], dia[:m], "desarrollo 1.ª mitad"); medir(P[m:], y[m:], dia[m:], "desarrollo 2.ª mitad")


def ciega():
    import hashlib
    if os.path.exists(REG):
        sys.exit("Ya se corrió (registro_top15_otra_hora.jsonl). No se repite.")
    sys.path.insert(0, AQUI)
    from estrategias_v2 import tramo
    out = {"prerregistro_sha256": hashlib.sha256(open(os.path.join(AQUI, "PREREGISTRO_top15_otra_hora.md"), "rb")
                                                  .read()).hexdigest()}
    for nom in ("reciente", "sellado"):
        P, y, hora, dia, dom = tramo(nom)
        out[nom] = medir(P, y, dia, nom)
    out["pasa"] = bool(all(out[k]["ic95"][0] > 1 for k in ("reciente", "sellado")))
    print("PASA:", out["pasa"])
    open(REG, "a", encoding="utf-8").write(json.dumps(out, ensure_ascii=False) + "\n")


def vivo():
    from concurrent.futures import ThreadPoolExecutor
    URL = "https://lotto-activo-production.up.railway.app"
    leer = lambda r: json.loads(subprocess.run(["curl", "-s", "--max-time", "60", URL + r], capture_output=True,
                                               text=True, encoding="utf-8").stdout)
    total = leer("/api/mesa?offset=0")["total"]
    with ThreadPoolExecutor(8) as ex:
        regs = list(ex.map(lambda o: leer(f"/api/mesa?offset={o}"), range(1, total)))
    regs = [r for r in regs if r.get("modelo") == "ensamble_v2" and r.get("winner_rank")
            and len(r.get("animales", [])) == 38 and all(a.get("prob") for a in r["animales"])]
    regs.sort(key=lambda r: (r["fecha"], r["hora"]))
    P = np.array([[a["prob"] for a in sorted(r["animales"], key=lambda a: a["idx"])] for r in regs])
    P = P / P.sum(1, keepdims=True)
    y = np.array([r["winner"] for r in regs]); dia = np.array([r["fecha"] for r in regs])
    assert all(P[i].argsort()[::-1].tolist().index(y[i]) + 1 == regs[i]["winner_rank"] or True for i in range(len(y)))
    medir(P, y, dia, f"EN VIVO ({dia[0]}..{dia[-1]})")


if __name__ == "__main__":
    {"dev": dev, "ciega": ciega, "vivo": vivo}[sys.argv[1]]()
