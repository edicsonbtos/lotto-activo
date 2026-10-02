# -*- coding: utf-8 -*-
"""Prueba ciega por hora (PREREGISTRO_hora_8am_ciega.md): ¿las 8:00 aciertan más? ¿la tarde, con más
resultados del día, acierta más? Y, descriptivo, por qué el Top-15 pasó de ~53 % a ~49 %.

Uso (desde la raíz): python herramientas/exploracion/hora_8am_ciega.py
  1. Arma el historial: verificacion/hilo9/datos/historial.txt + corrección de fechas 2026-09-29
     + API oficial (juego 1) hasta el 2026-09-22 + oficial_extra.csv del enjambre (09-23..09-29).
     Comprueba que coinciden donde se solapan.
  2. Walk-forward del ensamble_v2 de producción (~70 s; se guarda en hora_cache.npz, fuera del repo).
  3. Tablas por hora y trimestre, H8, H8-cal y H-día. La primera corrida anota la mirada en registro_final.jsonl.
"""
import csv, hashlib, json, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
sys.path.insert(0, os.path.join(RAIZ, "herramientas", "modelos"))
import lotto_eval as LE  # noqa: E402

HIST_EXT = os.path.join(AQUI, "hora_historial_ext.txt")
CACHE = os.path.join(AQUI, "hora_cache.npz")
PRE = os.path.join(AQUI, "PREREGISTRO_hora_8am_ciega.md")
SALIDA = os.path.join(AQUI, "hora_8am_ciega_salida.txt")
FIN_PRUEBA = "2026-09-14"          # el vivo arranca aquí; lo anterior (>= fila 9357) es el tramo de prueba
SEMILLA, B = 20261002, 10000
F15P = np.array([3, 3, 3, 2, 2] + [1] * 10, float)   # Top-15 ponderado 3-2-1 (23 fichas)
LINEAS = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LINEAS.append(s)


def armar_historial():
    lin = [l.strip() for l in open(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt"),
                                   encoding="utf-8") if l.strip()]
    cam = {c["antes"]: c["despues"] for c in json.load(open(os.path.join(
        RAIZ, "herramientas", "correccion_historial_2026-09-29.json"), encoding="utf-8"))["cambios"]}
    assert sum(l in cam for l in lin) == len(cam), "la corrección de fechas no aplica entera"
    H = {}
    for l in lin:
        f, h, a = cam.get(l, l).split(); H[(f, int(h))] = a
    O = {}
    for ruta in (os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"),
                 os.path.join(AQUI, "enjambre_2026-09-30", "reentreno", "oficial_extra.csv")):
        for r in csv.DictReader(open(ruta, encoding="utf-8")):
            if r["juego"] == "1":
                k = (r["fecha"], int(r["hora"][:2]) - 8)
                assert O.get(k, r["codigo"]) == r["codigo"], k
                O[k] = r["codigo"]
    comun = set(H) & set(O)
    dif = [k for k in comun if H[k] != O[k]]
    log(f"Historial congelado {len(H)} + corrección de fechas ({len(cam)}); API oficial LA {len(O)}; "
        f"solapan {len(comun)}, difieren {len(dif)}")
    assert not dif, dif[:10]
    ult = max(H)
    todo = dict(H); todo.update({k: v for k, v in O.items() if k > ult})
    with open(HIST_EXT, "w", encoding="utf-8") as f:
        for k in sorted(todo):
            f.write(f"{k[0]} {k[1]} {todo[k]}\n")
    log(f"Historial extendido: {len(todo)} sorteos, hasta {max(todo)}")


def walk_forward():
    import ensamble as E
    D = LE.cargar(HIST_EXT)
    ens = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py"))
    huella = hashlib.sha256(open(HIST_EXT, "rb").read()).hexdigest()
    if os.path.exists(CACHE):
        c = np.load(CACHE)
        if str(c["huella"]) == huella:
            return D, c["P"]
    t0 = time.time()
    n = len(D); a = min(ens.arranque, LE.W)
    L = np.stack([np.log(np.clip(E._cargar(b).predecir(D, a), 1e-9, None)) for b in ens.base], axis=1)
    L -= np.log(np.exp(L).sum(2, keepdims=True))
    y = np.asarray(D.seq)[a:]
    w = np.full(len(ens.base), 1 / len(ens.base)); P = np.empty((n - LE.W, 38))
    for T in range(LE.W, n, ens.R):               # misma cadencia que ensamble.Modelo.predecir
        j = T - a
        if j >= 200:
            w = E.ajustar_pesos(L[:j], y[:j], w, ens.lam, np.exp(-(j - 1 - np.arange(j)) / ens.tau))
        b = min(T + ens.R, n)
        z = np.einsum("nmk,m->nk", L[T - a:b - a], w); z -= z.max(1, keepdims=True); p = np.exp(z)
        P[T - LE.W:b - LE.W] = p / p.sum(1, keepdims=True)
    np.savez_compressed(CACHE, P=P, huella=huella)
    log(f"Walk-forward del ensamble_v2: {time.time() - t0:.0f} s")
    return D, P


def boot_dias(dias, *cols, f, B=B, semilla=SEMILLA):
    """Bootstrap por jornada: remuestrea días y aplica f a las columnas concatenadas."""
    u, inv = np.unique(dias, return_inverse=True)
    grupos = [np.nonzero(inv == g)[0] for g in range(len(u))]
    rng = np.random.default_rng(semilla); out = np.empty(B)
    for b in range(B):
        idx = np.concatenate([grupos[g] for g in rng.integers(0, len(u), len(u))])
        out[b] = f(*(c[idx] for c in cols))
    return out


def tabla_horas(nombre, sel, pos, q15, q5, mb, emb, hora):
    log(f"\n--- {nombre}: por hora (Top-15 observado / esperado por el motor, z; Top-5; mbits obs / esperado) ---")
    for h in range(12):
        m = sel & (hora == h)
        if m.sum() < 5:
            continue
        o15 = (pos[m] < 15).mean(); e15 = q15[m].mean()
        z = ((pos[m] < 15).sum() - q15[m].sum()) / np.sqrt((q15[m] * (1 - q15[m])).sum())
        log(f"  {8 + h:2d}:00  n={m.sum():4d}  Top-15 {o15 * 100:5.1f} % / {e15 * 100:5.1f} %  z={z:+5.2f}   "
            f"Top-5 {(pos[m] < 5).mean() * 100:5.1f} / {q5[m].mean() * 100:5.1f}   "
            f"mbits {mb[m].mean():+6.0f} / {emb[m].mean():+5.0f}")
    m = sel
    log(f"  TODAS  n={m.sum():4d}  Top-15 {(pos[m] < 15).mean() * 100:5.1f} % / {q15[m].mean() * 100:5.1f} %"
        f"            Top-5 {(pos[m] < 5).mean() * 100:5.1f} / {q5[m].mean() * 100:5.1f}   "
        f"mbits {mb[m].mean():+6.0f} / {emb[m].mean():+5.0f}")


def descriptivo_extra(P, Ps, pos, y, hora, dev, prueba, vivo, mb, dia):
    """Descriptivo (no decide nada): dónde está la información y si el motor promete de más."""
    bandas = ((0, 5, "1-5"), (5, 15, "6-15"), (15, 25, "16-25"), (25, 38, "26-38"))
    log("\n--- Calibración por bandas de puesto: % de ganadores observado / esperado por el motor (azar) ---")
    for nom, s in (("desarrollo", dev), ("prueba", prueba), ("vivo", vivo)):
        cel = []
        for a, b, et in bandas:
            o = ((pos[s] >= a) & (pos[s] < b)).mean(); e = Ps[s][:, a:b].sum(1).mean()
            cel.append(f"{et} {o * 100:4.1f}/{e * 100:4.1f} ({(b - a) / 38 * 100:4.1f})")
        log(f"  {nom:<10} " + "   ".join(cel))
    log("\n--- Por hora en prueba: ganadores en el fondo (puestos 26-38) y en la cabeza (1-15); azar 34,2 % y 39,5 % ---")
    for h in range(12):
        m = prueba & (hora == h)
        log(f"  {8 + h:2d}:00  fondo {(pos[m] >= 25).mean() * 100:4.1f} % (esperaba {Ps[m][:, 25:].sum(1).mean() * 100:4.1f})"
            f"   cabeza {(pos[m] < 15).mean() * 100:4.1f} % (esperaba {Ps[m][:, :15].sum(1).mean() * 100:4.1f})")
    # Temperatura: P^b normalizado, b ajustado en una ventana móvil de los 1.500 sorteos anteriores (sin futuro).
    lp = np.log(P)
    def mbits_b(sel, b):
        z = b * lp[sel]; z -= z.max(1, keepdims=True); q = np.exp(z); q /= q.sum(1, keepdims=True)
        return 1000 * np.log2(q[np.arange(sel.sum()), y[sel]] * 38)
    rejilla = np.round(np.arange(0.50, 1.31, 0.05), 2)
    idx = np.arange(len(y)); bwf = np.ones(len(y))
    for T in range(1500, len(y), 250):
        v = np.zeros(len(y), bool); v[T - 1500:T] = True
        bwf[T:T + 250] = rejilla[np.argmax([mbits_b(v, b).mean() for b in rejilla])]
    log("\n--- Temperatura (motor más o menos seguro): b < 1 = el motor estaba sobreconfiado ---")
    for nom, s in (("desarrollo", dev), ("prueba", prueba), ("vivo", vivo)):
        mejor = rejilla[np.argmax([mbits_b(s, b).mean() for b in rejilla])]
        g = np.zeros(s.sum()); sub = idx[s]
        for b in np.unique(bwf[s]):
            mm = bwf[sub] == b; selb = np.zeros(len(y), bool); selb[sub[mm]] = True
            g[mm] = mbits_b(selb, b) - mb[selb]
        bb = boot_dias(dia[s], g, f=lambda a: a.mean(), B=2000)
        log(f"  {nom:<10} b óptimo a posteriori {mejor:.2f}; b móvil (sin futuro) medio {bwf[s].mean():.2f}, "
            f"ganancia {g.mean():+.1f} mbits [IC95 {np.percentile(bb, 2.5):+.1f}; {np.percentile(bb, 97.5):+.1f}]")


def estructura_por_trimestre(D):
    """Descriptivo sobre los resultados crudos (sin modelo): ¿cuánto evita repetir y cuánto recicla el operador?
    O/E de 'repite un animal que ya salió HOY' y de 'sale un animal de AYER', contra el azar exacto de cada sorteo."""
    seq = np.asarray(D.seq); dia = np.asarray(D.dia); F = D.fecha
    hoy, ayer, d_ant, acum = set(), set(), None, {}
    for t in range(len(seq)):
        if dia[t] != d_ant:
            ayer = hoy if d_ant is not None and dia[t] - d_ant == 1 else set()
            hoy, d_ant = set(), dia[t]
        k = F[t][:4] + "-T" + str((int(F[t][5:7]) - 1) // 3 + 1)
        a = acum.setdefault(k, [0, 0.0, 0, 0.0, 0])
        a[0] += seq[t] in hoy; a[1] += len(hoy) / 38
        if ayer:
            a[2] += seq[t] in ayer; a[3] += len(ayer) / 38
        a[4] += 1
        hoy.add(seq[t])
    log("\n--- Estructura del operador por trimestre (resultados crudos): O/E de repetir HOY y de sacar uno de AYER ---")
    log("    (azar = 1,00; el motor gana cuando 'repite hoy' es bajo y 'sale de ayer' se aparta de 1)")
    for k in sorted(acum):
        o1, e1, o2, e2, n = acum[k]
        if n >= 200:
            log(f"  {k}  n={n:4d}  repite hoy {o1 / e1:4.2f} ({o1}/{e1:.0f})   sale de ayer {o2 / e2:4.2f} ({o2}/{e2:.0f})")


def main():
    armar_historial()
    D, P = walk_forward()
    n0 = LE.W
    y = np.asarray(D.seq)[n0:]; hora = np.asarray(D.hora)[n0:]; dia = np.asarray(D.dia)[n0:]
    fecha = np.array(D.fecha[n0:]); fila = np.arange(n0, len(D))
    orden = LE.rankings(P); pos = np.argmax(orden == y[:, None], axis=1)
    Ps = np.take_along_axis(P, orden, 1)
    q15 = Ps[:, :15].sum(1); q5 = Ps[:, :5].sum(1)
    mb = 1000 * np.log2(P[np.arange(len(y)), y] * 38)
    emb = 1000 * (P * np.log2(P * 38)).sum(1)               # mbits que el propio motor espera
    dev = fila < LE.CORTE_FIJO
    prueba = (fila >= LE.CORTE_FIJO) & (fecha < FIN_PRUEBA)
    vivo = fecha >= FIN_PRUEBA
    mitad = n0 + (LE.CORTE_FIJO - n0) // 2
    log(f"Tramos: desarrollo {fecha[dev][0]}..{fecha[dev][-1]} ({dev.sum()}), prueba {fecha[prueba][0]}.."
        f"{fecha[prueba][-1]} ({prueba.sum()}), vivo reconstruido {fecha[vivo][0]}..{fecha[vivo][-1]} ({vivo.sum()})")
    log(f"Comprobación: desarrollo Top-15 {(pos[dev] < 15).mean() * 100:.2f} % (publicado 53,07); prueba Top-3 "
        f"{(pos[prueba] < 3).mean() * 100:.2f} % (12,27), mbits {mb[prueba].mean():.1f} (90)")

    # ------------------------------------------------------------------ descriptivo: trimestres
    log("\n--- Top-15 por trimestre: observado / esperado por el motor; mbits observado / esperado ---")
    tri = np.array([f[:4] + "-T" + str((int(f[5:7]) - 1) // 3 + 1) for f in fecha])
    for t in sorted(set(tri)):
        m = tri == t
        tag = "dev" if dev[m].all() else ("prueba" if prueba[m].all() else ("vivo" if vivo[m].all() else "mixto"))
        log(f"  {t}  {tag:<6} n={m.sum():4d}  Top-15 {(pos[m] < 15).mean() * 100:5.1f} / {q15[m].mean() * 100:5.1f}"
            f"   mbits {mb[m].mean():+5.0f} / {emb[m].mean():+5.0f}   8:00 n={(m & (hora == 0)).sum()}")

    # ------------------------------------------------------------------ descriptivo: horas
    tabla_horas("Desarrollo (ya mirado)", dev, pos, q15, q5, mb, emb, hora)
    tabla_horas("dev-A (2.000..mitad)", dev & (fila < mitad), pos, q15, q5, mb, emb, hora)
    tabla_horas("dev-B (mitad..9357)", dev & (fila >= mitad), pos, q15, q5, mb, emb, hora)

    # ------------------------------------------------------------------ PRUEBA (ciega por hora)
    tabla_horas("PRUEBA 2025-12-19..2026-09-13 (ciega por hora)", prueba, pos, q15, q5, mb, emb, hora)
    s = prueba
    hit = (pos[s] < 15).astype(float); h8 = (hora[s] == 0).astype(float); dd = dia[s]
    dif = hit[h8 == 1].mean() - hit[h8 == 0].mean()
    bd = boot_dias(dd, hit, h8, f=lambda a, b: a[b == 1].mean() - a[b == 0].mean())
    p_dif = float(np.mean(bd <= 0))
    b8 = boot_dias(dd[h8 == 1], hit[h8 == 1], f=lambda a: a.mean())
    lo8, hi8 = np.percentile(b8, [2.5, 97.5])
    r8 = hit[h8 == 1].mean()
    pasa = dif > 0 and p_dif < 0.01 and lo8 > 0.5
    ver = "PASA" if pasa else ("FALSADA" if dif < 0.03 else "SIN CONCLUIR")
    log(f"\nH8: Top-15 8:00 {r8 * 100:.1f} % [IC95 {lo8 * 100:.1f}; {hi8 * 100:.1f}] (n={int(h8.sum())}) vs resto "
        f"{hit[h8 == 0].mean() * 100:.1f} % (n={int((1 - h8).sum())}); dif {dif * 100:+.1f} pp "
        f"[IC95 {np.percentile(bd, 2.5) * 100:+.1f}; {np.percentile(bd, 97.5) * 100:+.1f}], p={p_dif:.4f}  => {ver}")

    m8 = s & (hora == 0)
    zc = ((pos[m8] < 15).sum() - q15[m8].sum()) / np.sqrt((q15[m8] * (1 - q15[m8])).sum())
    mr = s & (hora != 0)
    zr = ((pos[mr] < 15).sum() - q15[mr].sum()) / np.sqrt((q15[mr] * (1 - q15[mr])).sum())
    log(f"H8-cal: a las 8:00 el motor esperaba {q15[m8].mean() * 100:.1f} % y salió {(pos[m8] < 15).mean() * 100:.1f} % "
        f"(z={zc:+.2f}); resto esperaba {q15[mr].mean() * 100:.1f} % y salió {(pos[mr] < 15).mean() * 100:.1f} % (z={zr:+.2f})"
        f"  => {'el motor YA lo sabe (calibrado)' if abs(zc) < 2 else ('estructura NO capturada a las 8:00' if zc >= 2 else 'el motor exagera a las 8:00')}")

    hh = hora[s].astype(float)
    def pend(a, x):
        xc = x - x.mean(); return (xc * (a - a.mean())).sum() / (xc ** 2).sum()
    sl = pend(hit, hh); bs = boot_dias(dd, hit, hh, f=pend)
    p_sl = float(np.mean(bs <= 0))
    log(f"H-día: pendiente Top-15 por sorteo del día {sl * 100:+.2f} pp/sorteo [IC95 {np.percentile(bs, 2.5) * 100:+.2f}; "
        f"{np.percentile(bs, 97.5) * 100:+.2f}], p={p_sl:.4f}  => "
        f"{'PASA' if sl > 0 and p_sl < 0.01 else ('FALSADA' if sl <= 0 else 'SIN CONCLUIR')}")
    log(f"       (esperado por el motor: pendiente {pend(q15[s], hh) * 100:+.2f} pp/sorteo; mbits 8:00 {emb[m8].mean():.0f}, "
        f"19:00 {emb[s & (hora == 11)].mean():.0f})")

    if pasa:
        for nombre, w in (("Top-15 plano", np.ones(15)), ("Top-15 ponderado 3-2-1", F15P)):
            g = np.where(pos[m8] < 15, 30 * w[np.minimum(pos[m8], 14)], 0) - w.sum()
            bb = boot_dias(dia[m8], g, f=lambda a: a.mean() / w.sum())
            log(f"  Solo 8:00, {nombre}: retorno/ficha {g.mean() / w.sum() * 100:+.1f} % "
                f"[IC95 {np.percentile(bb, 2.5) * 100:+.1f}; {np.percentile(bb, 97.5) * 100:+.1f}]")

    # ------------------------------------------------------------------ vivo reconstruido (no es evidencia)
    tabla_horas(f"Vivo reconstruido {fecha[vivo][0]}..{fecha[vivo][-1]} (originó la idea; no es evidencia)",
                vivo, pos, q15, q5, mb, emb, hora)
    log("\n--- Vivo reconstruido, sorteo de las 8:00 día por día (puesto del ganador; Top-15 que esperaba el motor) ---")
    m8v = np.nonzero(vivo & (hora == 0))[0]
    for i in m8v:
        log(f"  {fecha[i]}  ganador {LE.POS[y[i]]:>2}  puesto {pos[i] + 1:2d}  {'Top-15' if pos[i] < 15 else 'fuera '}"
            f"  esperaba {q15[i] * 100:4.1f} %")
    log(f"  8:00 en vivo: {(pos[m8v] < 15).sum()}/{len(m8v)} en el Top-15; resto de horas "
        f"{(pos[vivo & (hora != 0)] < 15).mean() * 100:.1f} %")

    descriptivo_extra(P, Ps, pos, y, hora, dev, prueba, vivo, mb, dia)
    estructura_por_trimestre(D)

    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(LINEAS) + "\n")
    reg = os.path.join(RAIZ, "herramientas", "registro_final.jsonl")
    sha = hashlib.sha256(open(PRE, "rb").read()).hexdigest()
    if not any(sha in l for l in open(reg, encoding="utf-8")):
        with open(reg, "a", encoding="utf-8") as f:
            f.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": "ensamble_v2 por hora (8:00 y H-día)",
                                "preregistro": "herramientas/exploracion/PREREGISTRO_hora_8am_ciega.md", "sha256": sha,
                                "h8": {"top15_8": round(r8, 4), "ic95": [round(lo8, 4), round(hi8, 4)], "dif": round(dif, 4),
                                       "p": p_dif, "veredicto": ver},
                                "h8_cal_z": round(float(zc), 2), "h_dia": {"pendiente": round(float(sl), 5), "p": p_sl}},
                               ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
