#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lotto Activo — servidor local, todo en una sola página.

  * Próximo sorteo: Top-3 del ensamble (herramientas/modelos/ensamble_v2.py).
  * Tripleta: 2 tripletas para los 12 sorteos que empiezan en el siguiente
    (herramientas/tripleta_ventana.py). Paga 45x.
  * Registro de resultados, marcadores honestos (solo pronósticos hechos antes
    del resultado) y panel de herramientas de validación.

Sin numpy/scipy funciona con el modelo antiguo (solo librería estándar).
"""
import os, sys, json, math, webbrowser, threading, subprocess, time, html
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from datetime import date, datetime, timedelta
from math import comb

RUTA = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(RUTA, "historial.txt")
LOG  = os.path.join(RUTA, "predicciones.json")
HERR = os.path.join(RUTA, "herramientas")
PUERTO = 8000
PAGO = 30
PAGO_TRIPLETA = 45
VENTANA = 12

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
DIAS_SEM = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
BINS = [0,1,2,3,4,5,6,8,10,13,17,22,28,36,46,60,80,10**9]
# Tasas medidas en prueba ciega (3.122 sorteos no vistos, herramientas/resultados/final.txt)
P_MOD_T3, P_AZAR_T3 = 0.1227, 3.0/K     # ensamble_v2 (el antiguo: 0,1060)
P_MOD_T1 = 0.0400

# Modelo nuevo. Necesita numpy y scipy; si faltan, se usa el antiguo.
try:
    import prediccion
    PRED = prediccion.Predictor(); PRED_ERR = None
except Exception as _ex:
    PRED = None; PRED_ERR = f"{type(_ex).__name__}: {_ex}"

AVISO = {"texto": "", "clase": ""}      # mensaje que se muestra una vez tras un POST

# ----------------------------------------------------------------- datos
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

def siguiente(f, h):
    if h < 11: return f, h + 1
    return (date.fromisoformat(f) + timedelta(days=1)).isoformat(), 0

def estado(filas):
    """Modelo antiguo (tramos de retraso) + datos del próximo sorteo."""
    seq = [v for _, _, v in filas]
    n = len(seq); last = {}
    for t, v in enumerate(seq): last[v] = t
    g = [n - 1 - last[s] if s in last else 10**6 for s in range(K)]
    hz = hazard(seq)
    sc = [hz[bidx(x + 1)] for x in g]
    orden = sorted(range(K), key=lambda i: -sc[i])
    f, h, v = filas[-1]
    nf, nh = siguiente(f, h)
    return dict(sc=sc, gaps=g, orden=orden, n=n, ult=(f, h, v), pf=nf, ph=nh)

def log_cargar():
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            d = json.load(f)
    else:
        d = {"registros": []}
    d.setdefault("registros", []); d.setdefault("tripletas", []); d.setdefault("sorteos_conocidos", [])
    return d

def log_guardar(d):
    with open(LOG + ".tmp", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(LOG + ".tmp", LOG)

def ahora():
    return datetime.now().isoformat(timespec="seconds")

def vigente(r):
    return not r.get("anulado")

def fecha_corta(f):
    d = date.fromisoformat(f)
    hoy = date.today()
    if d == hoy: return "hoy"
    if d == hoy + timedelta(days=1): return "mañana"
    if d == hoy - timedelta(days=1): return "ayer"
    return f"{DIAS_SEM[d.weekday()]} {d.day} {MESES[d.month-1]}"

def fin_ventana(f, h):
    for _ in range(VENTANA - 1):
        f, h = siguiente(f, h)
    return f, h

# -------------------------------------------------------------- marcadores
MODELO_MARCADOR = "ensamble_v2"

def marcador(d):
    """Marcador del modelo EN USO. Las predicciones del modelo antiguo
    (hazard, sin campo «modelo») no se mezclan: el factor de Bayes y el SPRT
    tienen que medir el modelo que se está jugando, no una mezcla de dos."""
    res = [r for r in d["registros"] if vigente(r) and r.get("salio") is not None
           and r.get("modelo") == MODELO_MARCADOR]
    n = len(res)
    if n == 0: return dict(n=0)
    t3 = sum(1 for r in res if r["salio"] in r["top3"])
    t1 = sum(1 for r in res if r["salio"] == r["top3"][0])
    lo = 0.0
    for r in res:
        lo += math.log(P_MOD_T3/P_AZAR_T3) if r["salio"] in r["top3"] else math.log((1-P_MOD_T3)/(1-P_AZAR_T3))
    return dict(n=n, t3=t3, t1=t1, tasa3=t3/n*100, tasa1=t1/n*100, factor=math.exp(lo))

def resolver_tripletas(d, filas):
    """Cierra las tripletas cuya ventana de 12 sorteos ya está completa."""
    cambio = False; cerradas = []
    for t in d["tripletas"]:
        if not vigente(t) or t.get("estado") != "pendiente":
            continue
        i = t["n_inicio"]
        if i < len(filas) and (filas[i][0], filas[i][1]) != (t["inicio_fecha"], t["inicio_hora"]):
            t["anulado"] = {"cuando": ahora(), "motivo": "el historial no coincide con el inicio"}; cambio = True
            continue
        if len(filas) >= i + VENTANA:
            salieron = [filas[j][2] for j in range(i, i + VENTANA)]
            s = set(salieron)
            t["salieron"] = salieron
            t["aciertos"] = [all(a in s for a in jug) for jug in t["jugadas"]]
            t["base"] = comb(len(s), 3) / comb(K, 3)
            t["estado"] = "resuelta"; t["resuelto"] = ahora()
            cambio = True; cerradas.append(t)
    return cambio, cerradas

def marcador_tripleta(d):
    res = [t for t in d["tripletas"] if vigente(t) and t.get("estado") == "resuelta"]
    if not res: return dict(n=0)
    jug = sum(len(t["jugadas"]) for t in res)
    ac = sum(sum(t["aciertos"]) for t in res)
    esp = sum(t["base"] * len(t["jugadas"]) for t in res)
    return dict(n=len(res), jugadas=jug, aciertos=ac, tasa=ac/jug*100, azar=esp/jug*100,
                ganancia=ac * PAGO_TRIPLETA - jug)

# ---------------------------------------------------------------- deshacer
def deshacer():
    """Quita la última línea del historial.

    Registro de solo-añadir: la predicción de ese sorteo NO vuelve a quedar
    pendiente (su resultado ya se conoce). Se anula conservando lo registrado y
    deja de contar. También se anulan los pendientes calculados con el dato
    erróneo y las tripletas cuya ventana contenía ese sorteo."""
    if not os.path.exists(HIST):
        return "No hay historial.", False
    with open(HIST, encoding="utf-8") as f:
        lineas = [l for l in f.readlines() if l.strip()]
    if not lineas:
        return "El historial está vacío.", False
    p = lineas[-1].split()
    if len(p) != 3:
        return "La última línea no tiene formato válido, no se tocó nada.", False
    fecha, hora_txt, num = p
    try:
        hora_idx = int(hora_txt)
    except ValueError:
        return "La última línea no tiene formato válido, no se tocó nada.", False
    idx_quitado = len(cargar()) - 1
    with open(HIST, "w", encoding="utf-8") as f:
        f.writelines(lineas[:-1])
    d = log_cargar()
    for r in d["registros"]:
        if not vigente(r):
            continue
        mismo = r.get("fecha") == fecha and r.get("hora") == hora_idx
        if r.get("salio") is None or mismo:
            r["anulado"] = {"cuando": ahora(), "motivo": "deshacer" if mismo else "calculado con el dato deshecho"}
    for t in d["tripletas"]:
        if not vigente(t):
            continue
        dentro = t["n_inicio"] <= idx_quitado < t["n_inicio"] + VENTANA
        if t.get("estado") == "pendiente" or dentro:
            t["anulado"] = {"cuando": ahora(), "motivo": "ventana afectada por deshacer"}
    if [fecha, hora_idx] not in d["sorteos_conocidos"]:
        d["sorteos_conocidos"].append([fecha, hora_idx])
    log_guardar(d)
    hora_leg = HORAS[hora_idx] if 0 <= hora_idx < 12 else hora_txt
    return (f"Se deshizo {fecha_corta(fecha)} {hora_leg}: {num} {ANIM.get(num, '?')}. Escribe el número correcto. "
            f"Ese sorteo y las tripletas que lo incluían ya no cuentan en los marcadores."), True

# ------------------------------------------------------------- herramientas
HERRAMIENTAS = {
    "diagnostico": {
        "titulo": "Diagnóstico de aleatoriedad", "dura": "segundos",
        "cmd": ["diagnostico.py"],
        "que": "Comprueba si el sorteo es azar puro o tiene patrones.",
        "mirar": "En «1-1» un valor muy por debajo de 1,00x y más de 11 animales distintos por jornada "
                 "significan que el operador evita repetir. Compara el primer y el último tercio: si cambian "
                 "mucho, el mecanismo del operador cambió.",
    },
    "tripleta": {
        "titulo": "Validar tripleta de 12 sorteos", "dura": "1 a 3 min",
        "cmd": ["tripleta_ventana.py"],
        "que": "Mide en el histórico cuántas veces habrían ganado las tripletas sugeridas.",
        "mirar": "En la línea A_123_456: el % de aciertos debe superar 2,22% (umbral de 45x) y al «azar». "
                 "Si el primer número del intervalo [a-b] supera 2,22% y z(bloques) es mayor que +2, hay evidencia "
                 "real. Si «EV 45x» tiene el límite inferior negativo, todavía puede haber pérdida.",
    },
    "sorteo": {
        "titulo": "Validar predicción por sorteo", "dura": "5 a 10 min",
        "cmd": ["lotto_eval.py", "modelos/hazard_actual.py", "modelos/ensamble_v2.py", "--sin-fuga"],
        "que": "Compara el modelo antiguo con el ensamble en 7.357 sorteos de desarrollo.",
        "mirar": "El ensamble debe superar al antiguo en Top1, Top3 y mbits, y en los 4 «cuartos». "
                 "Top1 por encima de 3,33% es el umbral con pago 30x; mira el primer número del intervalo [a-b].",
    },
}
TAREAS = {}

def salida_tarea(clave):
    return os.path.join(HERR, "resultados", f"pagina_{clave}.txt")

def iniciar_tarea(clave):
    if clave not in HERRAMIENTAS: return
    t = TAREAS.get(clave)
    if t and t["proc"].poll() is None: return
    os.makedirs(os.path.join(HERR, "resultados"), exist_ok=True)
    out = open(salida_tarea(clave), "w", encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    proc = subprocess.Popen([sys.executable] + HERRAMIENTAS[clave]["cmd"], cwd=HERR, stdout=out,
                            stderr=subprocess.STDOUT, env=env)
    TAREAS[clave] = {"proc": proc, "inicio": time.time(), "out": out}

def detener_tarea(clave):
    t = TAREAS.get(clave)
    if t and t["proc"].poll() is None:
        t["proc"].terminate()

def estado_tareas():
    res = {}
    for clave in HERRAMIENTAS:
        t = TAREAS.get(clave); ruta = salida_tarea(clave)
        texto = ""
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8", errors="replace") as f:
                texto = f.read()[-12000:]
        if t is None:
            est = "lista" if not texto else "terminada (ejecución anterior)"
            seg = None
        else:
            rc = t["proc"].poll()
            seg = int(time.time() - t["inicio"]) if rc is None else t.get("seg")
            if rc is None:
                est = "corriendo"
            else:
                if "seg" not in t:
                    t["seg"] = int(time.time() - t["inicio"]); t["out"].close(); seg = t["seg"]
                est = "terminada" if rc == 0 else f"terminó con error ({rc})"
        res[clave] = {"estado": est, "segundos": seg, "salida": texto}
    return res

# ------------------------------------------------------------------ página
def esc(s):
    return html.escape(str(s))

def chip(i, extra=""):
    return f'<span class="chip {extra}"><b>{POS[i]}</b> {ANIM[POS[i]].title()}</span>'

CSS = """
:root{--bg:#f3f1ec;--card:#fff;--line:#e4e0d7;--ink:#1b1d22;--muted:#6c6f76;--soft:#9a9ca3;
--brand:#b5621b;--brand-soft:#fbf0e3;--ok:#1f6b4a;--ok-soft:#e5f3ec;--bad:#9b3b2a;--bad-soft:#f8e9e5}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Segoe UI",-apple-system,Roboto,sans-serif}
.w{max-width:1080px;margin:0 auto;padding:20px 16px 40px}
header{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:10px;margin-bottom:14px}
h1{font-size:24px;margin:0;font-weight:700;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:13px}
.pill{display:inline-block;font-size:12px;padding:3px 10px;border-radius:99px;background:var(--ok-soft);color:var(--ok);font-weight:600}
.pill.warn{background:var(--brand-soft);color:var(--brand)}
nav{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 14px}
nav a{font-size:13px;color:var(--muted);text-decoration:none;padding:5px 11px;border:1px solid var(--line);border-radius:99px;background:var(--card)}
nav a:hover{color:var(--ink);border-color:#cfc9bd}
.strip{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px;margin-bottom:14px}
.res{flex:0 0 auto;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 10px;text-align:center;min-width:78px}
.res small{display:block;color:var(--soft);font-size:11px}
.res b{font-size:17px}
.res span{display:block;font-size:11px;color:var(--muted)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:820px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin-bottom:14px}
.grid .card{margin-bottom:0}
.hh{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin:0 0 12px}
.hh h2{font-size:13px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:0;font-weight:600}
.hh span{font-size:13px;color:var(--ink);font-weight:600}
.pick{display:grid;grid-template-columns:18px 64px 1fr auto;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #f0ede6}
.pick:last-of-type{border-bottom:none}
.rk{font-size:12px;color:var(--soft)}
.num{font-size:32px;font-weight:800;color:var(--brand);font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.nm{font-size:16px;font-weight:600}
.bar{height:6px;background:#f0ede6;border-radius:9px;margin-top:5px;position:relative}
.bar i{display:block;height:100%;background:var(--brand);border-radius:9px}
.bar em{position:absolute;top:-3px;width:2px;height:12px;background:#8f8a80}
.pc{font-size:14px;font-weight:600;text-align:right;font-variant-numeric:tabular-nums}
.pc small{display:block;font-size:11px;color:var(--soft);font-weight:400}
.note{font-size:12px;color:var(--soft);margin:10px 0 0}
.tip{font-size:13px;color:#7c4c12;background:var(--brand-soft);padding:9px 12px;border-radius:7px;margin-top:12px}
.tri{border:1px solid var(--line);border-radius:9px;padding:10px 12px;margin-bottom:10px}
.tri h3{margin:0 0 8px;font-size:13px;color:var(--muted);font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:baseline;gap:5px;padding:5px 10px;border-radius:99px;background:var(--brand-soft);font-size:14px}
.chip b{color:var(--brand);font-size:16px}
.chip.si{background:var(--ok-soft)}.chip.si b{color:var(--ok)}
.chip small{color:var(--soft);font-size:11px}
form.reg{display:flex;gap:8px}
input[type=text]{flex:1;min-width:0;padding:12px 14px;font-size:18px;border:1px solid #d7d2c8;border-radius:8px;background:#fbfaf7}
input:focus{outline:2px solid var(--brand);outline-offset:1px}
button{padding:11px 18px;font-size:15px;font-weight:600;border:none;border-radius:8px;background:var(--ink);color:#fff;cursor:pointer}
button:hover{opacity:.88}
button.sec{background:#fff;color:var(--ink);border:1px solid var(--line)}
button.link{background:none;color:var(--bad);padding:0;font-size:13px;font-weight:400;text-decoration:underline}
.msg{font-size:14px;padding:11px 14px;border-radius:8px;margin-bottom:14px}
.msg.ok{background:var(--ok-soft);color:var(--ok)}.msg.no{background:#ecebe6;color:#55585e}.msg.bad{background:var(--bad-soft);color:var(--bad)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}
.kpi{border:1px solid var(--line);border-radius:8px;padding:9px 11px}
.kpi small{display:block;font-size:11px;color:var(--muted)}
.kpi b{font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{display:block;font-size:11px;color:var(--soft)}
.pend{font-size:13px;border-top:1px solid #f0ede6;padding:8px 0}
.pend b{font-weight:600}
.tool{border-top:1px solid #f0ede6;padding:14px 0}
.tool:first-of-type{border-top:none;padding-top:0}
.tool-h{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px}
.tool h3{margin:0;font-size:16px}
.tool p{margin:4px 0;font-size:13px;color:var(--muted)}
.tool .mirar{color:#4b4e55;background:#f7f5f0;border-radius:7px;padding:8px 10px}
.st{font-size:12px;font-weight:600;color:var(--muted)}
.st.corriendo{color:var(--brand)}
pre{background:#191b20;color:#e7e4dc;font-size:12px;line-height:1.45;padding:12px;border-radius:8px;overflow-x:auto;max-height:420px;white-space:pre}
details summary{cursor:pointer;font-size:13px;color:var(--muted);margin-top:6px}
footer{font-size:12px;color:var(--soft);line-height:1.6;margin-top:6px}
"""

JS = """
<script>
(function(){
  var calc = %CALC%;
  function tareas(){
    fetch('/tareas.json').then(r=>r.json()).then(function(t){
      var alguna=false;
      Object.keys(t).forEach(function(k){
        var s=document.getElementById('st-'+k), o=document.getElementById('out-'+k), b=document.getElementById('bt-'+k);
        if(!s) return;
        var e=t[k];
        s.textContent=e.estado+(e.segundos!=null?' · '+e.segundos+' s':'');
        s.className='st '+(e.estado==='corriendo'?'corriendo':'');
        if(o && e.salida){o.textContent=e.salida; o.parentNode.open = o.parentNode.open || e.estado==='corriendo';}
        if(b){b.textContent = e.estado==='corriendo' ? 'Detener' : 'Ejecutar';
              b.form.action = e.estado==='corriendo' ? '/herramienta/'+k+'/detener' : '/herramienta/'+k;}
        if(e.estado==='corriendo') alguna=true;
      });
      setTimeout(tareas, alguna?2000:8000);
    }).catch(function(){setTimeout(tareas,8000);});
  }
  tareas();
  if(calc){
    (function listo(){
      fetch('/listo.json').then(r=>r.json()).then(function(j){
        var inp=document.getElementById('num');
        if(j.listo && !(inp && inp.value)) location.replace('/');
        else setTimeout(listo, 2500);
      }).catch(function(){setTimeout(listo,4000);});
    })();
  }
})();
</script>
"""

def html_prediccion(e, calculando, pend, aviso_modelo):
    fecha, hora = fecha_corta(e["pf"]), HORAS[e["ph"]]
    cab = f'<div class="hh"><h2>Próximo sorteo</h2><span>{esc(fecha)} · {hora}</span></div>'
    if calculando:
        cuerpo = ('<div class="tip">Calculando la predicción con el ensamble (unos 10 segundos). '
                  'La página se actualiza sola.</div>')
        if PRED is not None and PRED.error:
            cuerpo += f'<div class="msg bad">Error: {esc(PRED.error[-400:])}</div>'
        return f'<section class="card" id="sorteo">{cab}{cuerpo}</section>'
    orden = e["orden"][:3]
    if pend is not None:
        orden = pend["top3"]
    maxp = 0.07
    filas = ""
    for r, i in enumerate(orden, 1):
        p = e["sc"][i]
        filas += (f'<div class="pick"><span class="rk">{r}</span><span class="num">{POS[i]}</span>'
                  f'<div><div class="nm">{ANIM[POS[i]].title()}</div>'
                  f'<div class="bar"><i style="width:{min(100, p/maxp*100):.0f}%"></i>'
                  f'<em style="left:{P0/maxp*100:.0f}%" title="azar"></em></div></div>'
                  f'<span class="pc">{p*100:.2f}%<small>salió hace {e["gaps"][i] + 1} sorteos</small></span></div>')
    nota = ('<p class="note">La raya gris marca el azar (2,63%). Top-3 acierta ~12% de las veces: '
            'es normal fallar 7 de cada 8.</p>')
    top15 = html_top15(e, pend)
    return f'<section class="card" id="sorteo">{cab}{filas}{nota}{aviso_modelo}{top15}</section>'

def html_top15(e, pend=None):
    # El orden que se muestra tiene que ser EL MISMO que se puntúa: si ya hay
    # un pronóstico guardado para este sorteo, se usa su orden congelado.
    orden = e["orden"]
    if pend is not None and pend.get("orden_completo"):
        orden = pend["orden_completo"]
    filas = ""
    for r, i in enumerate(orden[:15], 1):
        p = e["sc"][i]
        filas += (f'<div class="pick"><span class="rk">{r}</span><span class="num">{POS[i]}</span>'
                  f'<div><div class="nm">{ANIM[POS[i]].title()}</div></div>'
                  f'<span class="pc">{p*100:.2f}%<small>salió hace {e["gaps"][i] + 1}</small></span></div>')
    return (f'<details style="margin-top:12px"><summary>Ver Top-15 completo</summary>{filas}</details>')

def html_registro():
    return ('<section class="card" id="registrar"><div class="hh"><h2>¿Qué salió?</h2></div>'
            '<form class="reg" method="post" action="/registrar">'
            '<input type="text" id="num" name="num" placeholder="0, 00 o 1-36" autocomplete="off" '
            'inputmode="numeric" autofocus><button type="submit">Registrar</button></form>'
            '<p class="note">Regístralo solo cuando el sorteo ya haya ocurrido.</p>'
            '<form method="post" action="/deshacer" onsubmit="return confirm(\'¿Deshacer el último registro?\')">'
            '<button class="link" type="submit">Deshacer último registro</button></form></section>')

def html_tripleta(e, tri_actual, d, filas, calculando, sin_modelo):
    ff, fh = fin_ventana(e["pf"], e["ph"])
    cab = (f'<div class="hh"><h2>Tripleta · paga {PAGO_TRIPLETA}x</h2>'
           f'<span>{esc(fecha_corta(e["pf"]))} {HORAS[e["ph"]]} → {esc(fecha_corta(ff))} {HORAS[fh]}</span></div>')
    if sin_modelo:
        cuerpo = '<div class="tip">La tripleta necesita el modelo nuevo (instala numpy y scipy).</div>'
    elif calculando:
        cuerpo = '<div class="tip">Calculando las tripletas…</div>'
    elif tri_actual is None:
        cuerpo = '<div class="tip">No se pudo calcular la tripleta para esta ventana.</div>'
    else:
        cuerpo = ""
        for k, jug in enumerate(tri_actual["jugadas"], 1):
            cuerpo += (f'<div class="tri"><h3>Tripleta {k}</h3><div class="chips">'
                       + "".join(chip(i) for i in jug) + '</div></div>')
        probs = tri_actual.get("prob")
        if probs:
            cuerpo += ('<p class="note">Probabilidad de que cada uno salga en esos 12 sorteos: '
                       + ", ".join(f"{POS[i]} {p*100:.0f}%" for i, p in zip(sum(tri_actual['jugadas'], []), probs))
                       + ' (un animal cualquiera: ~30%).</p>')
    cuerpo += ('<p class="note">Vale para los 12 sorteos que empiezan en el próximo. Una tripleta al azar gana '
               '~2,2% de las veces y el umbral de 45x es 2,22%. Aún no está demostrada: juégala en papel y mira su marcador.</p>')
    # ventanas en curso
    curso = [t for t in d["tripletas"] if vigente(t) and t.get("estado") == "pendiente"
             and t["n_inicio"] < len(filas)][-4:]
    if curso:
        cuerpo += '<div style="margin-top:10px"><div class="hh"><h2>En curso</h2></div>'
        for t in reversed(curso):
            vistos = {filas[j][2] for j in range(t["n_inicio"], len(filas))}
            jugados = len(filas) - t["n_inicio"]
            cuerpo += (f'<div class="pend"><b>{esc(fecha_corta(t["inicio_fecha"]))} {HORAS[t["inicio_hora"]]}</b> · '
                       f'{jugados}/12 sorteos<div class="chips" style="margin-top:5px">'
                       + " ".join('<span style="margin-right:8px">' + "".join(chip(i, "si" if i in vistos else "") for i in jug) + '</span>'
                                  for jug in t["jugadas"]) + '</div></div>')
        cuerpo += '</div>'
    return f'<section class="card" id="tripleta">{cab}{cuerpo}</section>'

def html_marcadores(d):
    m = marcador(d)
    if m["n"] == 0:
        s1 = '<p class="note">Sin predicciones resueltas todavía.</p>'
    else:
        lect = ("evidencia fuerte a favor" if m["factor"] >= 20 else "evidencia moderada a favor" if m["factor"] >= 3
                else "todavía no distingue" if m["factor"] > 1/3 else "evidencia en contra")
        s1 = (f'<div class="kpis"><div class="kpi"><small>Predicciones</small><b>{m["n"]}</b></div>'
              f'<div class="kpi"><small>Top-3</small><b>{m["tasa3"]:.1f}%</b><span>{m["t3"]} aciertos · azar 7,9% · modelo 12,3%</span></div>'
              f'<div class="kpi"><small>Top-1</small><b>{m["tasa1"]:.1f}%</b><span>{m["t1"]} aciertos · umbral 30x 3,33%</span></div>'
              f'<div class="kpi"><small>Lectura</small><b style="font-size:14px">{lect}</b><span>factor {m["factor"]:.2f} : 1</span></div></div>')
        if m["n"] < 1000:
            s1 += f'<p class="note">Con {m["n"]} predicciones aún no se puede concluir: hacen falta 1.000 o más.</p>'
    mt = marcador_tripleta(d)
    if mt["n"] == 0:
        s2 = '<p class="note">Ninguna ventana de 12 sorteos cerrada todavía.</p>'
    else:
        s2 = (f'<div class="kpis"><div class="kpi"><small>Ventanas cerradas</small><b>{mt["n"]}</b><span>{mt["jugadas"]} tripletas</span></div>'
              f'<div class="kpi"><small>Aciertos</small><b>{mt["tasa"]:.1f}%</b><span>{mt["aciertos"]} · azar {mt["azar"]:.1f}% · umbral 2,22%</span></div>'
              f'<div class="kpi"><small>Resultado a 45x</small><b>{mt["ganancia"]:+d}</b><span>unidades si apostaras 1 por tripleta</span></div></div>')
        if mt["n"] < 300:
            s2 += f'<p class="note">Con {mt["n"]} ventanas es pura suerte: hacen falta varios cientos.</p>'
    return (f'<section class="card" id="marcadores"><div class="grid" style="gap:18px">'
            f'<div><div class="hh"><h2>Marcador sorteo</h2></div>{s1}</div>'
            f'<div><div class="hh"><h2>Marcador tripleta</h2></div>{s2}</div></div>'
            f'<p class="note">Solo cuentan pronósticos guardados antes de conocer el resultado.</p></section>')

def _leer_consejo():
    """Top-3 del consenso de la mesa nocturna (si el archivo es reciente)."""
    ruta = os.path.join(HERR, "resultados", "mesa_consejo.txt")
    try:
        if time.time() - os.path.getmtime(ruta) > 36 * 3600:
            return None
        raw = open(ruta, "rb").read()
        for enc in ("utf-8", "utf-16"):
            try:
                txt = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            return None
        if "CONSENSO" not in txt:
            return None
        picks = []
        for ln in txt.splitlines():
            p = ln.split()
            if len(p) >= 3 and p[0] == "#" and p[1].isdigit():
                picks.append(p[2])
            if len(picks) == 3:
                break
        return picks or None
    except OSError:
        return None

def html_resumen(e, d, modelo, calculando):
    """Panel 'En palabras claras': qué jugar, cómo vas y qué hacer, sin tecnicismos."""
    partes = []
    if calculando:
        partes.append("<p>⏳ Calculando la jugada del próximo sorteo; en unos segundos te la digo en claro.</p>")
    else:
        orden = e["orden"][:3]
        trio = ", ".join(f"<b>{POS[i]}</b> {ANIM[POS[i]].title()}" for i in orden)
        if modelo != "hazard_actual":
            s3 = sum(e["sc"][i] for i in orden)
            partes.append(
                f"<p>🎯 <b>La jugada de ahora:</b> {trio}. Juntos tienen <b>{s3*100:.1f}%</b> de salir: "
                f"aciertas más o menos <b>1 de cada {max(2, round(1/s3))}</b> sorteos. Si juegas los 3 y sale uno, "
                f"cobras {PAGO} por 3 jugadas: necesitas acertar más de 1 de cada 10 para no perder plata.</p>")
        else:
            partes.append(f"<p>🎯 <b>La jugada de ahora:</b> {trio} (modelo antiguo, sin porcentajes calibrados).</p>")
    m = marcador(d)
    if m["n"] == 0:
        partes.append("<p>📊 <b>Cómo vas:</b> todavía no hay predicciones resueltas. Registra cada resultado y aquí te diré si vas ganando o si es espejismo.</p>")
    else:
        roi = (PAGO * m["t3"] - 3 * m["n"]) / (3 * m["n"]) * 100
        equi = 3 / PAGO * 100
        if roi >= 0 and m["factor"] >= 3:
            cara = "✅ Vas en <b>positivo</b> y la evidencia empieza a favorecer al modelo."
        elif roi >= 0:
            cara = "🟡 Vas en <b>positivo</b>, pero todavía puede ser suerte."
        else:
            cara = "🔴 Vas en <b>negativo</b>: con estos números estarías perdiendo plata."
        partes.append(
            f"<p>📊 <b>Cómo vas (sorteo):</b> {m['t3']} aciertos Top-3 en {m['n']} sorteos ({m['tasa3']:.1f}%). "
            f"El azar da 7,9%, el punto de equilibrio es {equi:.1f}% y el modelo promete ~12,3%. "
            f"Si hubieras jugado el Top-3 plano: <b>{roi:+.0f}%</b>. {cara} "
            f"Para jurarlo de verdad hacen falta ~1.000 sorteos; llevas {m['n']}.</p>")
    mt = marcador_tripleta(d)
    pend = sum(1 for t in d["tripletas"] if vigente(t) and t.get("estado") == "pendiente")
    if mt["n"] == 0:
        partes.append(f"<p>🎲 <b>Tripleta:</b> ninguna ventana cerrada todavía ({pend} en curso). Sin evidencia de que gane: juégala en papel y mira su marcador.</p>")
    else:
        partes.append(
            f"<p>🎲 <b>Tripleta:</b> {mt['aciertos']} de {mt['jugadas']} ganadoras ({mt['tasa']:.1f}%; necesitas más de 2,22%). "
            f"A 45x habrías sacado <b>{mt['ganancia']:+d}</b> unidades. Con {mt['n']} ventanas cerradas aún es pura suerte.</p>")
    cons = _leer_consejo()
    if cons:
        partes.append(f"<p>🧠 <b>El consejo de las 5 estrategias</b> (corre solo cada noche) vota: <b>{', '.join(cons)}</b> para el próximo sorteo.</p>")
    partes.append('<p class="note">Reglas del consejo: apuesta plana en Top-3 · no amplíes a 5-10 (medido en tus propios datos: se pierde) · '
                  "no subas el monto cuando el porcentaje se vea alto (no acierta más) · registra todos los sorteos y evita «Deshacer» "
                  "(cada deshacer anula tripletas).</p>")
    return ('<section class="card" id="resumen"><div class="hh"><h2>En palabras claras</h2>'
            f"<span>{esc(fecha_corta(e['pf']))} · {HORAS[e['ph']]}</span></div>{''.join(partes)}</section>")

def html_herramientas():
    est = estado_tareas()
    cuerpo = ""
    for k, h in HERRAMIENTAS.items():
        e = est[k]
        corriendo = e["estado"] == "corriendo"
        accion = f"/herramienta/{k}/detener" if corriendo else f"/herramienta/{k}"
        cuerpo += (f'<div class="tool"><div class="tool-h"><div><h3>{esc(h["titulo"])}</h3>'
                   f'<p>{esc(h["que"])} Tarda {esc(h["dura"])}.</p></div>'
                   f'<form method="post" action="{accion}"><span class="st" id="st-{k}">{esc(e["estado"])}</span> '
                   f'<button class="sec" id="bt-{k}" type="submit">{"Detener" if corriendo else "Ejecutar"}</button></form></div>'
                   f'<p class="mirar"><b>Qué mirar:</b> {esc(h["mirar"])}</p>'
                   f'<details{" open" if corriendo else ""}><summary>Ver resultado</summary>'
                   f'<pre id="out-{k}">{esc(e["salida"] or "Todavía no se ha ejecutado.")}</pre></details></div>')
    return (f'<section class="card" id="herramientas"><div class="hh"><h2>Herramientas de validación</h2>'
            f'<span>corren en tu PC, sin tocar tus datos</span></div>{cuerpo}</section>')

def render():
    filas = cargar(); e = estado(filas)
    d = log_cargar()
    cambio, _ = resolver_tripletas(d, filas)
    calculando = False; info = {}; aviso_modelo = ""; modelo = "hazard_actual"
    if PRED is not None:
        res = PRED.obtener(HIST, e["pf"], e["ph"])
        if res is None:
            calculando = True
        else:
            p, info = res
            e["sc"] = [float(x) for x in p]
            e["orden"] = sorted(range(K), key=lambda i: (-e["sc"][i], i))
            modelo = prediccion.MODELO_ENSAMBLE
            if not info.get("pesos_vigentes"):
                aviso_modelo = ('<div class="tip">Recalculando en segundo plano los pesos del ensamble '
                                '(1 a 3 min); mientras, se usan los del bloque anterior.</div>')
    elif PRED_ERR:
        aviso_modelo = f'<div class="tip">Modelo antiguo: no se pudo cargar el ensamble ({esc(PRED_ERR)}).</div>'

    conocido = [e["pf"], e["ph"]] in d["sorteos_conocidos"]
    pend = None
    if not calculando:
        for r in d["registros"]:
            if vigente(r) and r.get("salio") is None:
                if (r["fecha"], r["hora"]) == (e["pf"], e["ph"]) and pend is None:
                    pend = r
                else:
                    r["anulado"] = {"cuando": ahora(), "motivo": "pendiente obsoleto"}; cambio = True
        if pend is None and not conocido:
            pend = {"fecha": e["pf"], "hora": e["ph"], "top3": e["orden"][:3],
                    "orden_completo": list(e["orden"]), "salio": None,
                    "creado": ahora(), "modelo": modelo}
            d["registros"].append(pend); cambio = True

    tri_actual = None
    if not calculando and "tripleta" in info:
        for t in d["tripletas"]:
            if vigente(t) and (t["inicio_fecha"], t["inicio_hora"]) == (e["pf"], e["ph"]) and t["n_inicio"] == len(filas):
                tri_actual = t
        if tri_actual is None and not conocido:
            pt = info["tripleta"]
            o = sorted(range(K), key=lambda i: (-pt[i], i))
            tri_actual = {"inicio_fecha": e["pf"], "inicio_hora": e["ph"], "n_inicio": len(filas),
                          "jugadas": [o[0:3], o[3:6]], "prob": [round(pt[i], 4) for i in o[:6]],
                          "estado": "pendiente", "creado": ahora(), "modelo": "tripleta_ventana_A"}
            d["tripletas"].append(tri_actual); cambio = True
    if cambio:
        log_guardar(d)

    f, h, v = e["ult"]
    ultimos = "".join(f'<div class="res"><small>{esc(fecha_corta(fl))} {HORAS[hl]}</small><b>{POS[vl]}</b>'
                      f'<span>{ANIM[POS[vl]].title()}</span></div>' for fl, hl, vl in reversed(filas[-12:]))
    if calculando:
        estado_pill = '<span class="pill warn">calculando…</span>'
    elif modelo == "hazard_actual":
        estado_pill = '<span class="pill warn">modelo antiguo</span>'
    else:
        estado_pill = '<span class="pill">ensamble activo</span>'
    aviso = ""
    if AVISO["texto"]:
        aviso = f'<div class="msg {AVISO["clase"]}">{AVISO["texto"]}</div>'
        AVISO["texto"] = ""

    cuerpo = (
        f'<div class="w"><header><div><h1>Lotto Activo</h1>'
        f'<div class="sub">Último: {esc(fecha_corta(f))} {HORAS[h]} → <b>{POS[v]} {ANIM[POS[v]].title()}</b> · '
        f'{e["n"]:,} sorteos en el histórico</div></div>{estado_pill}</header>'
        '<nav><a href="#resumen">En claro</a><a href="#sorteo">Próximo sorteo</a><a href="#tripleta">Tripleta</a><a href="#registrar">Registrar</a>'
        '<a href="#marcadores">Marcadores</a><a href="#herramientas">Herramientas</a></nav>'
        f'{aviso}{html_resumen(e, d, modelo, calculando)}<div class="strip">{ultimos}</div>'
        f'<div class="grid"><div>{html_prediccion(e, calculando, pend, aviso_modelo)}<div style="height:14px"></div>{html_registro()}</div>'
        f'<div>{html_tripleta(e, tri_actual, d, filas, calculando, PRED is None)}</div></div>'
        f'<div style="height:14px"></div>{html_marcadores(d)}{html_herramientas()}'
        '<footer>Azar puro: 2,63% por animal. En prueba ciega (3.122 sorteos) el ensamble acertó Top-1 4,00% '
        '(IC 95%: 3,37–4,75) y Top-3 12,27%; el umbral con pago 30x es 3,33%. Ningún modelo garantiza ganar y el '
        'operador puede cambiar su mecanismo. Tus datos: historial.txt y predicciones.json.</footer></div>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Lotto Activo</title><style>{CSS}</style></head><body>{cuerpo}'
            f'{JS.replace("%CALC%", "true" if calculando else "false")}</body></html>')

# ------------------------------------------------------------------ servidor
def registrar(num):
    filas = cargar(); e = estado(filas)
    d = log_cargar(); estado_txt = "sin pronóstico previo, no cuenta"; clase = "no"
    for r in d["registros"]:
        if vigente(r) and r.get("salio") is None and r["fecha"] == e["pf"] and r["hora"] == e["ph"]:
            r["salio"] = IDX[num]; r["resuelto"] = ahora()
            if IDX[num] == r["top3"][0]: estado_txt, clase = "¡ACIERTO Top-1!", "ok"
            elif IDX[num] in r["top3"]: estado_txt, clase = "acierto Top-3", "ok"
            else: estado_txt = "fallo"
            break
    with open(HIST, "a", encoding="utf-8") as fh:
        fh.write(f"{e['pf']} {e['ph']} {num}\n")
    _, cerradas = resolver_tripletas(d, cargar())
    log_guardar(d)
    texto = f'{HORAS[e["ph"]]} → <b>{num} {ANIM[num].title()}</b> · {estado_txt}'
    for t in cerradas:
        gan = sum(t["aciertos"])
        texto += (f'<br>Tripleta de {esc(fecha_corta(t["inicio_fecha"]))} {HORAS[t["inicio_hora"]]} cerrada: '
                  + (f"<b>¡{gan} ganadora{'s' if gan > 1 else ''}!</b>" if gan else "sin acierto"))
        if gan: clase = "ok"
    return texto, clase

class H(BaseHTTPRequestHandler):
    def _send(self, cuerpo, tipo="text/html; charset=utf-8", codigo=200):
        b = cuerpo.encode("utf-8")
        try:
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(b)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
            pass

    def _volver(self, ancla=""):
        try:
            self.send_response(303); self.send_header("Location", "/" + ancla); self.end_headers()
        except OSError:
            pass

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta in ("/", "/index.html"):
            self._send(render())
        elif ruta == "/tareas.json":
            self._send(json.dumps(estado_tareas(), ensure_ascii=False), "application/json; charset=utf-8")
        elif ruta == "/listo.json":
            listo = True
            if PRED is not None:
                filas = cargar(); e = estado(filas)
                listo = PRED.obtener(HIST, e["pf"], e["ph"]) is not None
            self._send(json.dumps({"listo": listo}), "application/json")
        else:
            self._send("No encontrado", "text/plain; charset=utf-8", 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        datos = self.rfile.read(n).decode("utf-8") if n else ""
        ruta = self.path.split("?")[0]
        if ruta == "/deshacer":
            texto, ok = deshacer()
            AVISO.update(texto=esc(texto), clase="ok" if ok else "no")
            return self._volver("#registrar")
        if ruta in ("/registrar", "/"):
            num = (parse_qs(datos).get("num", [""])[0]).strip()
            if num not in IDX:
                AVISO.update(texto=f'«{esc(num) or "vacío"}» no es válido. Usa 0, 00 o 1–36.', clase="bad")
            else:
                texto, clase = registrar(num)
                AVISO.update(texto=texto, clase=clase)
            return self._volver()
        if ruta.startswith("/herramienta/"):
            partes = ruta.strip("/").split("/")
            if len(partes) == 3 and partes[2] == "detener":
                detener_tarea(partes[1])
            elif len(partes) == 2:
                iniciar_tarea(partes[1])
            return self._volver("#herramientas")
        self._send("No encontrado", "text/plain; charset=utf-8", 404)

    def log_message(self, *a): pass

if __name__ == "__main__":
    if not os.path.exists(HIST):
        sys.exit("Falta historial.txt en esta carpeta.")
    PUERTO = int(os.environ.get("PORT", PUERTO))
    EN_NUBE = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT"))
    HOST = "0.0.0.0" if EN_NUBE else "127.0.0.1"
    url = f"http://localhost:{PUERTO}"
    print(f"\n  Lotto Activo corriendo en  {url}")
    print("  Modelo:", "ensamble (numpy/scipy OK)" if PRED else f"antiguo ({PRED_ERR})")
    print("  Para detenerlo: Ctrl + C\n")
    if not EN_NUBE:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        HTTPServer((HOST, PUERTO), H).serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.\n")
