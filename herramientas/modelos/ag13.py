# -*- coding: utf-8 -*-
"""ag13 en sombra (PREREGISTRO_ag13.md): ag12 -> regla RD -> exposición (todas las horas) -> pronosticadores.

Este módulo solo tiene lo puro: leer lo que publican lotoven y loteriadehoy, y las dos multiplicaciones nuevas.
La regla RD (experimentos.con_rd) y la exposición (exposicion.aplicar) se reutilizan tal cual.
Constantes CONGELADAS: no se reajustan mirando el marcador de ag13.
"""
import hashlib
import os
import re
import sys
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.append(AQUI)
import exposicion  # noqa: E402

IDX = exposicion.IDX
K = len(exposicion.POS)
PRON_X = 0.862          # confirmación 1 de investigacion/2026-10-15/pronosticadores (O/E de U); CONGELADO
PRON_X_ND = 0.924       # O/E de U sin lo explicado por la fecha (solo el diagnóstico ag13_nd); CONGELADO
FUENTES = ("lotoven", "loteriadehoy")
_MESES = {m: i + 1 for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July",
                                          "August", "September", "October", "November", "December"])}


def _lotoven(h):
    """(fecha de la página o None, [códigos]) del bloque 'Datos Lotto Activo' (sin RD Int)."""
    for b in re.split(r'<h3 class="text-center pb-3" title="Datos ', h)[1:]:
        juego = re.sub(r"\s+", " ", b.split('"', 1)[0]).strip()
        if juego != "Lotto Activo":
            continue
        m = re.search(r'title three[^>]*>\s*\w+,\s*(\d+)\s+de\s+(\w+)\s+de\s+(\d{4})', b)
        fd = None
        if m and m.group(2) in _MESES:
            try:
                fd = date(int(m.group(3)), _MESES[m.group(2)], int(m.group(1))).isoformat()
            except ValueError:
                fd = None
        return fd, re.findall(r'<span class="info">Numero</span><span class="result">\s*(\d+)\s*</span>', b)
    return None, []


def _loteriadehoy(h):
    m = re.search(r'id="datepicker" value="([\d-]+)"', h)
    fd = m.group(1) if m else None
    nums = []
    for card in h.split('class="card"')[1:]:
        g = re.search(r'<h6 class="h7">([^<]+)</h6>', card)
        n = re.search(r'<h6>\s*(\d+)\s+([^<]+?)\s*</h6>', card)
        if g and n and g.group(1).strip() == "Lotto Activo":
            nums.append(n.group(1))
    return fd, nums


_PARSE = {"lotoven": _lotoven, "loteriadehoy": _loteriadehoy}


def conjunto_fuente(html, fuente, fecha):
    """(índices, motivo_de_falta). La fecha de la página tiene que ser la del día: si no, no vale."""
    fd, nums = _PARSE[fuente](html)
    if fd != fecha:
        return None, f"{fuente}: la página es del {fd}, no del {fecha}"
    idx = {IDX[n] for n in nums if n in IDX}
    if not idx:
        return None, f"{fuente}: sin animales"
    return idx, None


def conjunto_del_dia(carpeta, fecha):
    """Lee las páginas guardadas por scraping/datos_publicados.py. Devuelve el dict que se guarda en el registro:
    {"u": [...], "fuentes": {...}} o {"falta": motivo}. Hacen falta las DOS fuentes."""
    u, info, faltas = set(), {}, []
    for f in FUENTES:
        ruta = os.path.join(carpeta, f"{f}_datos.html")
        try:
            with open(ruta, "rb") as fh:
                crudo = fh.read()
        except OSError as ex:
            faltas.append(f"{f}: no se pudo leer ({ex.__class__.__name__})")
            continue
        s, motivo = conjunto_fuente(crudo.decode("utf-8", "replace"), f, fecha)
        if s is None:
            faltas.append(motivo)
            continue
        u |= s
        info[f] = {"n": len(s), "bytes": len(crudo), "sha256": hashlib.sha256(crudo).hexdigest()[:16]}
    if faltas:
        return {"falta": "; ".join(faltas)}
    return {"u": sorted(u), "fuentes": info}


def aplicar_pron(p, u, x=PRON_X):
    """p × x a los animales de U y se renormaliza."""
    q = [float(v) for v in p]
    for i in u:
        q[i] *= x
    s = sum(q)
    return [v / s for v in q]


def aplicar_pron_nd(p, u, fecha, hora, x=PRON_X_ND):
    """Diagnóstico: solo a los de U que la exposición no tocó (día−1..día+2, hora en 12 h y mes quedan fuera)."""
    tocados = {IDX[str(n)] for n, _ in exposicion.numeros(fecha, int(hora)) if 1 <= n <= 36}
    return aplicar_pron(p, [i for i in u if i not in tocados], x)


def cadena(q_rd, fecha, hora, u):
    """q_rd = ag12 ya con la regla RD. Devuelve (ag12_rd_exp, ag13, ag13_nd)."""
    q_exp = exposicion.aplicar(q_rd, fecha, int(hora))
    return q_exp, aplicar_pron(q_exp, u), aplicar_pron_nd(q_exp, u, fecha, hora)
