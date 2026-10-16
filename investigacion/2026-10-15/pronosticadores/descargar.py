# -*- coding: utf-8 -*-
"""Descarga los "datos" archivados por fecha de lotoven.com y loteriadehoy.com (POST fecha=AAAA-MM-DD).
Guarda solo lo extraído (Lotto Activo y RD Int) en datos/publicados.jsonl; reanudable.
Uso: python descargar.py   (usa curl: urllib falla en estos sitios)"""
import json, os, re, subprocess, sys, time
from datetime import date, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(AQUI, "datos", "publicados.jsonl")
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Mobile Safari/537.36"
TRAMOS = [(date(2024, 3, 1), date(2025, 12, 14)), (date(2026, 9, 15), date(2026, 10, 14))]
URL = {"lotoven": "https://lotoven.com/datos/", "loteriadehoy": "https://loteriadehoy.com/datos/animalitos/"}
MESES = {m: i + 1 for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                          "September", "October", "November", "December"])}


def bajar(url, f):
    r = subprocess.run(["curl", "-s", "-L", "--max-time", "40", "-A", UA, "-d", "fecha=" + f, url],
                       capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def p_lotoven(h, f):
    out = {}
    partes = re.split(r'<h3 class="text-center pb-3" title="Datos ', h)
    for b in partes[1:]:
        juego = re.sub(r"\s+", " ", b.split('"', 1)[0]).strip()
        if juego not in ("Lotto Activo", "Lotto Activo RD Int"):
            continue
        m = re.search(r'title three[^>]*>\s*\w+,\s*(\d+)\s+de\s+(\w+)\s+de\s+(\d{4})', b)
        fd = date(int(m.group(3)), MESES.get(m.group(2), 0) or 1, int(m.group(1))).isoformat() if m else None
        nums = re.findall(r'<span class="info">Numero</span><span class="result">\s*(\d+)\s*</span>', b)
        out[juego] = {"fecha_pagina": fd, "nums": nums}
    return out


def p_ldh(h, f):
    out = {}
    m = re.search(r'id="datepicker" value="([\d-]+)"', h)
    fd = m.group(1) if m else None
    for card in h.split('class="card"')[1:]:
        g = re.search(r'<h6 class="h7">([^<]+)</h6>', card)
        n = re.search(r'<h6>\s*(\d+)\s+([^<]+?)\s*</h6>', card)
        if not g or not n:
            continue
        juego = g.group(1).strip()
        if juego not in ("Lotto Activo", "Lotto Activo Rd Int"):
            continue
        juego = "Lotto Activo RD Int" if juego.endswith("Int") else juego
        out.setdefault(juego, {"fecha_pagina": fd, "nums": []})["nums"].append(n.group(1))
    return out


def main():
    os.makedirs(os.path.dirname(SAL), exist_ok=True)
    hechos = set()
    if os.path.exists(SAL):
        for ln in open(SAL, encoding="utf-8"):
            r = json.loads(ln); hechos.add((r["fuente"], r["fecha"]))
    fechas = []
    for a, b in TRAMOS:
        d = a
        while d <= b:
            fechas.append(d.isoformat()); d += timedelta(days=1)
    with open(SAL, "a", encoding="utf-8") as fo:
        for f in fechas:
            for fuente, url in URL.items():
                if (fuente, f) in hechos:
                    continue
                for intento in range(3):
                    try:
                        h = bajar(url, f)
                        if len(h) < 2000:
                            raise OSError("página corta")
                        res = (p_lotoven if fuente == "lotoven" else p_ldh)(h, f)
                        break
                    except Exception as ex:  # noqa: BLE001
                        res = {"error": repr(ex)[:100]}; time.sleep(5)
                fo.write(json.dumps({"fuente": fuente, "fecha": f, "datos": res}, ensure_ascii=False) + "\n")
                fo.flush()
                time.sleep(0.7)
            print(f, flush=True)


if __name__ == "__main__":
    main()
