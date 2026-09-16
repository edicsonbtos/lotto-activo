#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lotto Activo — servidor local. Solo librería estándar de Python."""
import os, sys, json, math, webbrowser, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from datetime import date, timedelta

RUTA = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(RUTA, "historial.txt")
LOG  = os.path.join(RUTA, "predicciones.json")
PUERTO = 8000
PAGO = 30

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K = len(POS); P0 = 1.0 / K
ANIM = {"0":"DELFÍN","00":"BALLENA","1":"CARNERO","2":"TORO","3":"CIEMPIÉS","4":"ALACRÁN",
 "5":"LEÓN","6":"RANA","7":"PERICO","8":"RATÓN","9":"ÁGUILA","10":"TIGRE","11":"GATO",
 "12":"CABALLO","13":"MONO","14":"PALOMA","15":"ZORRO","16":"OSO","17":"PAVO","18":"BURRO",
 "19":"CHIVO","20":"COCHINO","21":"GALLO","22":"CAMELLO","23":"CEBRA","24":"IGUANA",
 "25":"GALLINA","26":"VACA","27":"PERRO","28":"ZAMURO","29":"ELEFANTE","30":"CAIMÁN",
 "31":"LAPA","32":"ARDILLA","33":"PESCADO","34":"VENADO","35":"JIRAFA","36":"CULEBRA"}
HORAS = ["8:00 AM","9:00 AM","10:00 AM","11:00 AM","12:00 PM","1:00 PM",
         "2:00 PM","3:00 PM","4:00 PM","5:00 PM","6:00 PM","7:00 PM"]
BINS = [0,1,2,3,4,5,6,8,10,13,17,22,28,36,46,60,80,10**9]
P_MOD_T3, P_AZAR_T3 = 0.1100, 3.0/K
P_MOD_T1 = 0.0358

def bidx(g):
    i = 0
    for j, b in enumerate(BINS):
        if g >= b: i = j
        else: break
    return i

def cargar():
    filas = []
    for ln in open(HIST, encoding="utf-8"):
        p = ln.split()
        if len(p) == 3 and p[2] in IDX:
            filas.append((p[0], int(p[1]), IDX[p[2]]))
    filas.sort(key=lambda r: (r[0], r[1]))
    return filas

def hazard(seq):
    nb = len(BINS); hit = [0.0]*nb; tot = [0.0]*nb; last = {}
    for t, v in enumerate(seq):
        if t > 0:
            b = [bidx((t - last[s]) if s in last else 10**6) for s in range(K)]
            for s in range(K): tot[b[s]] += 1
            hit[b[v]] += 1
        last[v] = t
    return [hit[i]/tot[i] if tot[i] >= 30 else P0 for i in range(nb)]

def estado(filas):
    seq = [v for _, _, v in filas]
    n = len(seq); last = {}
    for t, v in enumerate(seq): last[v] = t
    g = [n - 1 - last[s] if s in last else 10**6 for s in range(K)]
    hz = hazard(seq)
    sc = [hz[bidx(x + 1)] for x in g]
    orden = sorted(range(K), key=lambda i: -sc[i])
    top = max(sc); emp = [i for i in range(K) if sc[i] == top]
    f, h, v = filas[-1]
    if h < 11: nf, nh = f, h + 1
    else:
        nf = (date.fromisoformat(f) + timedelta(days=1)).isoformat(); nh = 0
    return dict(sc=sc, gaps=g, orden=orden, emp=emp, n=n,
                ult=(f, HORAS[h], POS[v], ANIM[POS[v]]), prox=(nf, HORAS[nh]),
                pf=nf, ph=nh)

def log_cargar():
    if os.path.exists(LOG): return json.load(open(LOG, encoding="utf-8"))
    return {"registros": []}
def log_guardar(d): json.dump(d, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def marcador():
    res = [r for r in log_cargar()["registros"] if r.get("salio") is not None]
    n = len(res)
    if n == 0: return dict(n=0)
    t3 = sum(1 for r in res if r["salio"] in r["top3"])
    t1 = sum(1 for r in res if r["salio"] == r["top3"][0])
    lo = 0.0
    for r in res:
        lo += math.log(P_MOD_T3/P_AZAR_T3) if r["salio"] in r["top3"] else math.log((1-P_MOD_T3)/(1-P_AZAR_T3))
    return dict(n=n, t3=t3, t1=t1, tasa3=t3/n*100, tasa1=t1/n*100, factor=math.exp(lo))

def deshacer():
    """Quita la última línea del historial y, si tenía una predicción
    marcada como resuelta para ese mismo sorteo, la deja pendiente otra vez."""
    if not os.path.exists(HIST):
        return "No hay historial.", False
    with open(HIST, encoding="utf-8") as f:
        lineas = [l for l in f.readlines() if l.strip()]
    if not lineas:
        return "El historial está vacío.", False
    ultima = lineas[-1].strip()
    p = ultima.split()
    if len(p) != 3:
        return "La última línea no tiene formato válido, no se tocó nada.", False
    fecha, hora_txt, num = p[0], p[1], p[2]
    try:
        hora_idx = int(hora_txt)
    except ValueError:
        return "La última línea no tiene formato válido, no se tocó nada.", False
    with open(HIST, "w", encoding="utf-8") as f:
        f.writelines(lineas[:-1])
    d = log_cargar()
    for r in reversed(d["registros"]):
        if r.get("salio") is not None and r.get("fecha") == fecha and r.get("hora") == hora_idx:
            r["salio"] = None
            break
    log_guardar(d)
    animal = ANIM.get(num, "?")
    hora_leg = HORAS[hora_idx] if 0 <= hora_idx < 12 else hora_txt
    return f"Se deshizo: {fecha} {hora_leg} &rarr; {num} {animal}. Ese sorteo vuelve a quedar pendiente.", True

PAGINA = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lotto Activo</title><style>
*{box-sizing:border-box}
body{margin:0;padding:24px 16px;background:#f4f2ee;color:#1a1c20;
 font:16px/1.55 -apple-system,"Segoe UI",Roboto,sans-serif}
.w{max-width:620px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:600}
.sub{color:#6b6d73;font-size:13px;margin:0 0 24px}
.card{background:#fff;border:1px solid #e2dfd8;border-radius:6px;padding:18px;margin-bottom:14px}
.hh{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#8a8c92;margin:0 0 12px}
.pick{display:flex;align-items:center;gap:14px;padding:12px 0;border-bottom:1px solid #f0eee9}
.pick:last-child{border-bottom:none}
.rk{font-size:12px;color:#a5a7ad;width:14px}
.num{font-size:30px;font-weight:700;color:#b06a17;min-width:52px;
 font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.nm{font-size:17px;font-weight:500;flex:1}
.pc{font-size:13px;color:#6b6d73;text-align:right;font-variant-numeric:tabular-nums}
.pc small{display:block;color:#a5a7ad;font-size:11px}
form{display:flex;gap:8px;margin-top:4px}
input{flex:1;padding:12px 14px;font-size:17px;border:1px solid #d8d4cc;border-radius:5px;
 background:#faf9f6;font-variant-numeric:tabular-nums}
input:focus{outline:2px solid #b06a17;outline-offset:1px}
button{padding:12px 20px;font-size:15px;font-weight:500;border:none;border-radius:5px;
 background:#1a1c20;color:#fff;cursor:pointer}
button:hover{opacity:.88}
.warn{font-size:12px;color:#9a9ca2;margin:8px 0 0}
.undo{margin-top:10px}
.undo button{background:none;border:none;color:#9a5c1c;font-size:12px;
 text-decoration:underline;cursor:pointer;padding:0;font-weight:400}
.row{display:flex;justify-content:space-between;font-size:14px;padding:5px 0}
.row span:first-child{color:#6b6d73}
.row b{font-variant-numeric:tabular-nums}
.tie{font-size:13px;color:#8a5a10;background:#fdf4e6;padding:10px 12px;border-radius:4px;margin-top:12px}
.msg{font-size:14px;padding:10px 12px;border-radius:4px;margin-bottom:14px}
.ok{background:#e6f2ec;color:#1f5c42}.no{background:#f3f1ed;color:#6b6d73}
.foot{font-size:12px;color:#9a9ca2;margin-top:20px;line-height:1.6}
</style></head><body><div class="w">
<h1>Lotto Activo</h1>
<p class="sub">%(ult)s &middot; %(n)s sorteos en el histórico</p>
%(msg)s
<div class="card">
<p class="hh">Próximo &mdash; %(pf)s %(ph)s</p>
%(picks)s
%(tie)s
</div>
<div class="card">
<p class="hh">¿Qué salió?</p>
<form method="post" action="/">
<input name="num" placeholder="0, 00 o 1-36" autocomplete="off" autofocus>
<button type="submit">Registrar</button>
</form>
<p class="warn">Regístralo solo cuando el sorteo ya haya ocurrido de verdad.</p>
<form method="post" action="/deshacer" class="undo">
<button type="submit">Deshacer último registro</button>
</form>
</div>
<div class="card">
<p class="hh">Marcador</p>
%(score)s
</div>
<p class="foot">Azar puro: 2,63%% por animalito. El techo del modelo es 3,58%% y el umbral
de rentabilidad con pago %(pago)sx es 3,33%%. El marcador solo cuenta predicciones hechas
antes de conocer el resultado.</p>
</div></body></html>"""

def render(msg=""):
    filas = cargar(); e = estado(filas)
    # registrar pronóstico pendiente
    d = log_cargar()
    if not [r for r in d["registros"] if r.get("salio") is None]:
        d["registros"].append({"fecha": e["pf"], "hora": e["ph"],
                               "top3": e["orden"][:3], "salio": None})
        log_guardar(d)
    picks = ""
    for r, i in enumerate(e["orden"][:3], 1):
        picks += (f'<div class="pick"><span class="rk">{r}</span>'
                  f'<span class="num">{POS[i]}</span><span class="nm">{ANIM[POS[i]]}</span>'
                  f'<span class="pc">{e["sc"][i]*100:.2f}%<small>retraso {e["gaps"][i]}</small></span></div>')
    tie = ""
    if len(e["emp"]) > 3:
        fuera = ", ".join(POS[i] for i in e["emp"] if i not in e["orden"][:3])
        tie = (f'<div class="tie">Hay {len(e["emp"])} empatados en el nivel más alto. '
               f'El modelo no los distingue. Quedan fuera del corte: {fuera}</div>')
    m = marcador()
    if m["n"] == 0:
        score = '<div class="row"><span>Sin predicciones resueltas todavía</span></div>'
    else:
        lect = ("evidencia fuerte a favor" if m["factor"] >= 20 else
                "evidencia moderada a favor" if m["factor"] >= 3 else
                "no distingue nada" if m["factor"] > 1/3 else
                "evidencia en contra")
        score = (f'<div class="row"><span>Predicciones</span><b>{m["n"]}</b></div>'
                 f'<div class="row"><span>Aciertos Top-3</span><b>{m["t3"]} ({m["tasa3"]:.1f}%)</b></div>'
                 f'<div class="row"><span>Aciertos Top-1</span><b>{m["t1"]} ({m["tasa1"]:.1f}%)</b></div>'
                 f'<div class="row"><span>Factor acumulado</span><b>{m["factor"]:.2f} : 1</b></div>'
                 f'<div class="row"><span>Lectura</span><b>{lect}</b></div>')
        if m["n"] < 1000:
            score += f'<div class="tie">Con {m["n"]} predicciones esto no decide nada. Hacen falta 1.000 o más.</div>'
    u = e["ult"]
    return PAGINA % dict(ult=f"Último: {u[0]} {u[1]} &rarr; {u[2]} {u[3]}", n=e["n"],
                         pf=e["prox"][0], ph=e["prox"][1], picks=picks, tie=tie,
                         score=score, msg=msg, pago=PAGO)

class H(BaseHTTPRequestHandler):
    def _send(self, html):
        b = html.encode("utf-8")
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers(); self.wfile.write(b)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
            pass
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_response(404); self.end_headers(); return
        self._send(render())
    def do_POST(self):
        if self.path == "/deshacer":
            n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
            texto, ok = deshacer()
            cls = "ok" if ok else "no"
            self._send(render(f'<div class="msg {cls}">{texto}</div>'))
            return
        n = int(self.headers.get("Content-Length", 0))
        q = parse_qs(self.rfile.read(n).decode("utf-8"))
        num = (q.get("num", [""])[0]).strip()
        if num not in IDX:
            msg = f'<div class="msg no">«{num or "vacío"}» no es válido. Usa 0, 00 o 1&ndash;36.</div>'
        else:
            filas = cargar(); e = estado(filas)
            d = log_cargar(); estado_txt = "fallo"
            for r in d["registros"]:
                if r.get("salio") is None and r["fecha"] == e["pf"] and r["hora"] == e["ph"]:
                    r["salio"] = IDX[num]
                    estado_txt = ("ACIERTO Top-1" if IDX[num] == r["top3"][0]
                                  else "acierto Top-3" if IDX[num] in r["top3"] else "fallo")
                    break
            log_guardar(d)
            with open(HIST, "a", encoding="utf-8") as fh:
                fh.write(f"{e['pf']} {e['ph']} {num}\n")
            cls = "ok" if "cierto" in estado_txt else "no"
            msg = (f'<div class="msg {cls}">{e["prox"][1]} &rarr; {num} {ANIM[num]} '
                   f'&middot; {estado_txt}</div>')
        self._send(render(msg))
    def log_message(self, *a): pass

if __name__ == "__main__":
    if not os.path.exists(HIST):
        sys.exit("Falta historial.txt en esta carpeta.")
    url = f"http://localhost:{PUERTO}"
    print(f"\n  Lotto Activo corriendo en  {url}")
    print("  Para detenerlo: Ctrl + C\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        HTTPServer(("127.0.0.1", PUERTO), H).serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.\n")
