# -*- coding: utf-8 -*-
"""Reconstruye servidor.py solo-infra a partir del final (revierte los 3 hunks
de tripletas). Byte-fiel (UTF-8, conserva finales de linea del archivo final)."""
import shutil, sys

FINAL = sys.argv[1]
DEST = sys.argv[2]

with open(FINAL, encoding="utf-8") as f:
    s = f.read()

# --- Hunk C: call site ---
new_c = """        f'<div>{html_tripleta(e, tri_actual, d, filas, calculando, PRED is None)}</div></div>'"""
old_c = """        f'<div>{html_tripleta(e, tri_actual, d, filas)}</div></div>'"""
assert new_c in s, "hunk C no encontrado"
s = s.replace(new_c, old_c, 1)

# --- Hunk A: auto-creacion en render ---
new_a = """    tri_actual = None
    for t in d["tripletas"]:
        if vigente(t) and (t["inicio_fecha"], t["inicio_hora"]) == (e["pf"], e["ph"]) and t["n_inicio"] == len(filas):
            tri_actual = t
    # Generación automática (diseño original, previo a c23792f): una tripleta
    # nueva por slot, en cuanto la predicción del modelo está lista. El ingreso
    # manual queda como fallback (ver html_tripleta), no como sustituto.
    if tri_actual is None and not calculando and not conocido and "tripleta" in info:
        pt = info["tripleta"]
        o = sorted(range(K), key=lambda i: (-pt[i], i))
        tri_actual = {"inicio_fecha": e["pf"], "inicio_hora": e["ph"], "n_inicio": len(filas),
                      "jugadas": [o[0:3], o[3:6]], "prob": [round(float(pt[i]), 4) for i in o[:6]],
                      "estado": "pendiente", "creado": ahora(), "modelo": "tripleta_ventana_A"}
        d["tripletas"].append(tri_actual); cambio = True
        print(f"[tripleta] {ahora()} slot={e['pf']} h{e['ph']} n={len(filas)} "
              f"auto 2 tripletas: {[ [POS[i] for i in jug] for jug in tri_actual['jugadas'] ]}",
              file=sys.stderr, flush=True)
    if cambio:
        log_guardar(d)"""
old_a = """    tri_actual = None
    for t in d["tripletas"]:
        if vigente(t) and (t["inicio_fecha"], t["inicio_hora"]) == (e["pf"], e["ph"]) and t["n_inicio"] == len(filas):
            tri_actual = t
    if cambio:
        log_guardar(d)"""
assert new_a in s, "hunk A no encontrado"
s = s.replace(new_a, old_a, 1)

# --- Hunk B: html_tripleta (firma + fallback manual) ---
new_b = '''def html_tripleta(e, tri_actual, d, filas, calculando=False, sin_modelo=False):
    ff, fh = fin_ventana(e["pf"], e["ph"])
    cab = (f'<div class="hh"><h2>Tripleta · paga {PAGO_TRIPLETA}x</h2>'
           f'<span>{esc(fecha_corta(e["pf"]))} {HORAS[e["ph"]]} → {esc(fecha_corta(ff))} {HORAS[fh]}</span></div>')
    # Formulario manual: FALLBACK documentado. Solo se ofrece cuando la vía
    # automática no puede producir la tripleta (modelo caído o cálculo fallido).
    opciones = "".join(f'<option value="{POS[i]}">{POS[i]} · {ANIM[POS[i]].title()}</option>' for i in range(K))
    campos = "".join(
        f'<select name="{nom}" required><option value="">Animal {j}</option>{opciones}</select>'
        for j, nom in enumerate(["a1", "a2", "a3", "b1", "b2", "b3"], 1))
    form_manual = (
        f'<form class="reg" method="post" action="/tripleta/registrar" style="flex-wrap:wrap;gap:6px">'
        f'<input type="hidden" name="pf" value="{esc(e["pf"])}"><input type="hidden" name="ph" value="{e["ph"]}">'
        f'<input type="hidden" name="n" value="{len(filas)}">{campos}'
        '<button type="submit">Guardar tripleta</button></form>')
    if sin_modelo:
        cuerpo = ('<div class="tip">La tripleta automática necesita el modelo nuevo (numpy/scipy), que ahora no '
                  'está disponible. <b>Fallback manual</b> (la vía normal es la generación automática):</div>'
                  + form_manual)
    elif calculando:
        cuerpo = '<div class="tip">Calculando las tripletas para esta ventana…</div>'
    elif tri_actual is None:
        cuerpo = ('<div class="tip">No se pudo calcular la tripleta automática para esta ventana '
                  '(error del modelo). <b>Fallback manual</b>:</div>' + form_manual)'''
old_b = '''def html_tripleta(e, tri_actual, d, filas):
    ff, fh = fin_ventana(e["pf"], e["ph"])
    cab = (f'<div class="hh"><h2>Tripleta · paga {PAGO_TRIPLETA}x</h2>'
           f'<span>{esc(fecha_corta(e["pf"]))} {HORAS[e["ph"]]} → {esc(fecha_corta(ff))} {HORAS[fh]}</span></div>')
    if tri_actual is None:
        opciones = "".join(f'<option value="{POS[i]}">{POS[i]} · {ANIM[POS[i]].title()}</option>' for i in range(K))
        campos = "".join(
            f'<select name="{nom}" required><option value="">Animal {j}</option>{opciones}</select>'
            for j, nom in enumerate(["a1", "a2", "a3", "b1", "b2", "b3"], 1))
        cuerpo = (
            '<div class="tip">Ingresa tú la tripleta (2 grupos de 3 animales) calculada aparte.</div>'
            f'<form class="reg" method="post" action="/tripleta/registrar" style="flex-wrap:wrap;gap:6px">'
            f'<input type="hidden" name="pf" value="{esc(e["pf"])}"><input type="hidden" name="ph" value="{e["ph"]}">'
            f'<input type="hidden" name="n" value="{len(filas)}">{campos}'
            '<button type="submit">Guardar tripleta</button></form>')'''
assert new_b in s, "hunk B no encontrado"
s = s.replace(new_b, old_b, 1)

with open(DEST, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("OK: servidor.py solo-infra reconstruido en", DEST)
