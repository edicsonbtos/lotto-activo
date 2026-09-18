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

# Jornada y etiquetas deben correr en hora de Caracas (UTC-4, sin DST),
# no en la hora del contenedor. FUERZA el valor: la imagen de Railway ya
# trae TZ (sfo -> America/Los_Angeles, UTC-8); setdefault quedaba corto.
# tzdata (requirements.txt) garantiza que la zona exista en imagenes slim.
os.environ["TZ"] = "America/Caracas"
try:
    time.tzset()
except AttributeError:
    pass

RUTA = os.path.dirname(os.path.abspath(__file__))
DATOS = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or RUTA
HIST = os.path.join(DATOS, "historial.txt")
LOG  = os.path.join(DATOS, "predicciones.json")
HERR = os.path.join(RUTA, "herramientas")
PUERTO = 8000  # local; en Railway se usa PORT
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
select{padding:10px;font-size:14px;border:1px solid #d7d2c8;border-radius:8px;background:#fbfaf7}
table.hist{width:100%;border-collapse:collapse;font-size:13px}
table.hist th{text-align:left;color:var(--muted);font-weight:600;padding:6px 8px;border-bottom:1px solid var(--line)}
table.hist td{padding:6px 8px;border-bottom:1px solid var(--line)}
table.hist td.ok{color:var(--ok);font-weight:600}table.hist td.no{color:var(--soft)}
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

def html_tripleta(e, tri_actual, d, filas, calculando=False, sin_modelo=False):
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
                  '(error del modelo). <b>Fallback manual</b>:</div>' + form_manual)
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

def html_historico(d, limite=100):
    vistos = [r for r in d["registros"] if vigente(r) and r.get("salio") is not None]
    filas_h = ""
    for r in reversed(vistos[-limite:]):
        top3 = " ".join(POS[i] for i in r["top3"])
        salio = POS[r["salio"]]
        if r["salio"] == r["top3"][0]: marca, clase = "Top-1", "ok"
        elif r["salio"] in r["top3"]: marca, clase = "Top-3", "ok"
        else: marca, clase = "fallo", "no"
        filas_h += (f'<tr><td>{esc(fecha_corta(r["fecha"]))} {HORAS[r["hora"]]}</td><td>{esc(top3)}</td>'
                    f'<td>{esc(salio)}</td><td class="{clase}">{marca}</td></tr>')
    if not filas_h:
        cuerpo = '<p class="note">Sin predicciones resueltas todavía.</p>'
    else:
        nota = (f'<p class="note">Mostrando las últimas {min(limite, len(vistos))} de {len(vistos)}.</p>'
                if len(vistos) > limite else "")
        cuerpo = (f'{nota}<table class="hist"><thead><tr><th>Sorteo</th><th>Top-3</th>'
                  f'<th>Salió</th><th>Resultado</th></tr></thead><tbody>{filas_h}</tbody></table>')
    return f'<section class="card" id="historico"><div class="hh"><h2>Histórico de predicciones</h2></div>{cuerpo}</section>'

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
        if PRED is not None and PRED.error:
            aviso_modelo += f'<div class="msg bad">Último error del modelo: {esc(PRED.error[-300:])}</div>'
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
                    "scores": [round(float(x), 6) for x in e["sc"]],
                    "creado": ahora(), "modelo": modelo}
            d["registros"].append(pend); cambio = True

    tri_actual = None
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
        '<a href="#mesa">Mesa</a><a href="#marcadores">Marcadores</a><a href="#historico">Histórico</a><a href="#herramientas">Herramientas</a></nav>'
        f'{aviso}{html_resumen(e, d, modelo, calculando)}<div class="strip">{ultimos}</div>'
        f'<div class="grid"><div>{html_prediccion(e, calculando, pend, aviso_modelo)}<div style="height:14px"></div>{html_registro()}</div>'
        f'<div>{html_tripleta(e, tri_actual, d, filas, calculando, PRED is None)}</div></div>'
        f'<div style="height:14px"></div>{html_mesa()}{html_marcadores(d)}{html_historico(d)}{html_herramientas()}'
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
    # Cerrar el hueco del sorteo sin pronóstico: si aún no hay «pend» para este
    # slot pero la predicción ya estaba en caché (calculada en un render previo
    # a que saliera el resultado), se registra ahora: el pronóstico es anterior
    # al resultado, sigue siendo honesto. Si no hay caché, no hubo pronóstico.
    pend = None
    for r in d["registros"]:
        if vigente(r) and r.get("salio") is None and r["fecha"] == e["pf"] and r["hora"] == e["ph"]:
            pend = r
            break
    if pend is None and PRED is not None and [e["pf"], e["ph"]] not in d["sorteos_conocidos"]:
        res = PRED.obtener(HIST, e["pf"], e["ph"])
        if res is not None:
            p, _info = res
            sc = [float(x) for x in p]
            orden = sorted(range(K), key=lambda i: (-sc[i], i))
            pend = {"fecha": e["pf"], "hora": e["ph"], "top3": orden[:3],
                    "orden_completo": orden, "salio": None,
                    "scores": [round(float(x), 6) for x in sc],
                    "creado": ahora(), "modelo": prediccion.MODELO_ENSAMBLE}
            d["registros"].append(pend)
    if pend is not None:
        pend["salio"] = IDX[num]; pend["resuelto"] = ahora()
        if IDX[num] == pend["top3"][0]: estado_txt, clase = "¡ACIERTO Top-1!", "ok"
        elif IDX[num] in pend["top3"]: estado_txt, clase = "acierto Top-3", "ok"
        else: estado_txt = "fallo"
    try:
        with open(HIST, "a", encoding="utf-8") as fh:
            fh.write(f"{e['pf']} {e['ph']} {num}\n")
    except OSError as ex:
        log_guardar(d)
        return (f"ERROR al guardar en el volumen: {ex}. NO se registró el resultado; "
                f"reintenta. Si persiste, el contenedor está sin escritura.", "bad")
    _, cerradas = resolver_tripletas(d, cargar())
    log_guardar(d)
    texto = f'{HORAS[e["ph"]]} → <b>{num} {ANIM[num].title()}</b> · {estado_txt}'
    for t in cerradas:
        gan = sum(t["aciertos"])
        texto += (f'<br>Tripleta de {esc(fecha_corta(t["inicio_fecha"]))} {HORAS[t["inicio_hora"]]} cerrada: '
                  + (f"<b>¡{gan} ganadora{'s' if gan > 1 else ''}!</b>" if gan else "sin acierto"))
        if gan: clase = "ok"
    return texto, clase

def registrar_tripleta(pf, ph, n, codigos):
    filas = cargar(); e = estado(filas)
    if (pf, ph) != (e["pf"], e["ph"]) or n != len(filas):
        return "La ventana cambió, actualiza la página e inténtalo de nuevo.", "bad"
    for c in codigos:
        if c not in IDX:
            return f'«{c or "vacío"}» no es un animal válido.', "bad"
    if len(set(codigos)) != 6:
        return "Los 6 animales deben ser distintos.", "bad"
    d = log_cargar()
    for t in d["tripletas"]:
        if vigente(t) and (t["inicio_fecha"], t["inicio_hora"]) == (pf, ph) and t["n_inicio"] == n:
            return "Ya hay una tripleta guardada para esta ventana.", "bad"
    o = [IDX[c] for c in codigos]
    d["tripletas"].append({"inicio_fecha": pf, "inicio_hora": ph, "n_inicio": n,
                            "jugadas": [o[0:3], o[3:6]], "estado": "pendiente",
                            "creado": ahora(), "modelo": "manual"})
    log_guardar(d)
    return "Tripleta guardada.", "ok"


# ============================================================ mesa de probabilidades
# Bloque ADITIVO (solo lectura sobre la lógica existente). No toca predicción,
# scoring, registro, tripletas ni marcador: lee lo que el pipeline ya calculó y
# lo muestra completo (38 animales) en vez de solo el top-3/top-15.

# Cuadrantes de membresía FIJA (no dependen de la probabilidad).
# El "00" no tiene decena propia: se agrupa con Q4 (30-36) por convención
# documentada, para que los 4 cuadrantes cubran los 38 códigos sin solapes.
MESA_CUADRANTES = [
    ("Q1", "0-9", [IDX[c] for c in ["0"] + [str(i) for i in range(1, 10)]]),
    ("Q2", "10-19", [IDX[str(i)] for i in range(10, 20)]),
    ("Q3", "20-29", [IDX[str(i)] for i in range(20, 30)]),
    ("Q4", "30-36 + 00", [IDX[str(i)] for i in range(30, 37)] + [IDX["00"]]),
]
# Segmentos de rank (de 8 en 8; el último queda de 6 porque K=38).
MESA_SEG_RANK = [(1, 8), (9, 16), (17, 24), (25, 32), (33, 38)]
# Bins de hueco en DÍAS sin salir. "hoy" = ya salió en esta misma jornada.
MESA_BINS_HUECO = [(0, 0, "hoy"), (1, 1, "1 día"), (2, 2, "2 días"), (3, 5, "3-5 días"),
                   (6, 10, "6-10 días"), (11, 20, "11-20 días"), (21, 40, "21-40 días"),
                   (41, 10**9, "más de 40 días")]

def mesa_seg_rank(rk):
    for j, (a, b) in enumerate(MESA_SEG_RANK):
        if a <= rk <= b: return j
    return len(MESA_SEG_RANK) - 1

def mesa_bin_hueco(g):
    """g = días sin salir; None (nunca salió) cae en el último bin."""
    if g is None: return len(MESA_BINS_HUECO) - 1
    for j, (a, b, _) in enumerate(MESA_BINS_HUECO):
        if a <= g <= b: return j
    return len(MESA_BINS_HUECO) - 1

def mesa_huecos(filas, fecha, hora):
    """Días sin salir por animal ANTES del slot (fecha,hora). None = nunca salió.
    Usa solo sorteos estrictamente anteriores: no mira el resultado del slot."""
    ult = {}
    for f, h, v in filas:
        if (f, h) >= (fecha, hora): break
        ult[v] = f
    base = date.fromisoformat(fecha)
    return [(base - date.fromisoformat(ult[i])).days if i in ult else None for i in range(K)]

def mesa_slots_hist(d, actual):
    """Registros navegables (sin el slot actual), del más reciente al más antiguo."""
    h = [r for r in d["registros"] if vigente(r) and (r["fecha"], r["hora"]) != actual]
    h.sort(key=lambda r: (r["fecha"], r["hora"]), reverse=True)
    return h

def mesa_datos(offset=0):
    """Distribución completa del slot en offset (0 = actual). Solo lectura."""
    filas = cargar(); e = estado(filas); d = log_cargar()
    actual = (e["pf"], e["ph"])
    hist = mesa_slots_hist(d, actual)
    total = 1 + len(hist)
    try: offset = int(offset)
    except (TypeError, ValueError): offset = 0
    offset = max(0, min(offset, total - 1))

    if offset == 0:
        fecha, hora = actual
        winner = None
        pend = next((r for r in d["registros"]
                     if vigente(r) and (r["fecha"], r["hora"]) == actual), None)
        modelo = (pend or {}).get("modelo", "—")
        scores = (pend or {}).get("scores")
        orden = (pend or {}).get("orden_completo")
        top3 = (pend or {}).get("top3") or []
        if scores is None and PRED is not None:
            res = PRED.obtener(HIST, fecha, hora)   # mismo cálculo (cacheado) que render()
            if res is not None:
                p, _i = res
                scores = [float(x) for x in p]
                if modelo == "—": modelo = prediccion.MODELO_ENSAMBLE
        if scores is None and orden is None:
            scores = list(e["sc"])
            if modelo == "—": modelo = "hazard_actual"
    else:
        r = hist[offset - 1]
        fecha, hora = r["fecha"], r["hora"]
        winner = r.get("salio")
        modelo = r.get("modelo", "—")
        scores = r.get("scores")
        orden = r.get("orden_completo")
        top3 = r.get("top3") or []

    if orden is None and scores is not None:
        orden = sorted(range(K), key=lambda i: (-scores[i], i))
    rank = {}
    if orden:
        for pos, i in enumerate(orden, 1): rank[i] = pos

    gaps = mesa_huecos(filas, fecha, hora)
    probs = None
    if scores is not None:
        tot = sum(scores) or 1.0
        probs = [s / tot for s in scores]

    animales = []
    for i in range(K):
        rk = rank.get(i)
        animales.append({
            "idx": i, "num": POS[i], "nombre": ANIM[POS[i]].title(),
            "prob": (probs[i] if probs else None),
            "rank": rk,
            "gap_dias": gaps[i],
            "salio_hoy": gaps[i] == 0,
            "en_top15": (rk <= 15) if rk is not None else (i in top3),
            "es_top3": i in top3,
        })
    if scores is None and not orden:
        vista = "top3"       # registro viejo: solo se guardó el top-3
    elif probs is None:
        vista = "rank"       # registro viejo: orden completo, sin puntajes
    else:
        vista = "prob"
    return {
        "offset": offset, "total": total, "fecha": fecha, "hora": hora,
        "hora_txt": HORAS[hora], "fecha_txt": fecha_corta(fecha),
        "modelo": modelo, "vista": vista,
        "winner": winner,
        "winner_num": (POS[winner] if winner is not None else None),
        "winner_nombre": (ANIM[POS[winner]].title() if winner is not None else None),
        "winner_rank": (rank.get(winner) if winner is not None else None),
        "animales": animales,
        "cuadrantes": [{"clave": c, "etiqueta": et, "idx": ix} for c, et, ix in MESA_CUADRANTES],
        "seg_rank": [{"desde": a, "hasta": b} for a, b in MESA_SEG_RANK],
        "bins_hueco": [{"desde": a, "hasta": b, "etiqueta": t} for a, b, t in MESA_BINS_HUECO],
    }

def mesa_stats():
    """Dónde cayó el ganador, sobre TODOS los registros resueltos. Solo lectura.
    Muestra en vivo y pequeña: NO es validación (para eso, walk-forward en desarrollo)."""
    filas = cargar(); d = log_cargar()
    res = [r for r in d["registros"] if vigente(r) and r.get("salio") is not None]
    quiero = {(r["fecha"], r["hora"]) for r in res}
    snap = {}; ult = {}
    for f, h, v in filas:
        if (f, h) in quiero and (f, h) not in snap:
            base = date.fromisoformat(f)
            snap[(f, h)] = [(base - date.fromisoformat(ult[i])).days if i in ult else None
                            for i in range(K)]
        ult[v] = f

    nr = len(MESA_SEG_RANK); nh = len(MESA_BINS_HUECO)
    rank_n = 0; rank_seg = [0] * nr
    hue_n = 0; hue_seg = [0] * nh; hue_ocup = [0.0] * nh
    sin_orden = 0; sin_hist = 0
    for r in res:
        o = r.get("orden_completo")
        if o and r["salio"] in o:
            rank_seg[mesa_seg_rank(o.index(r["salio"]) + 1)] += 1; rank_n += 1
        else:
            sin_orden += 1
        g = snap.get((r["fecha"], r["hora"]))
        if g is None:
            sin_hist += 1; continue
        hue_seg[mesa_bin_hueco(g[r["salio"]])] += 1; hue_n += 1
        for i in range(K): hue_ocup[mesa_bin_hueco(g[i])] += 1

    return {
        "resueltos": len(res), "sin_orden_completo": sin_orden, "sin_historial": sin_hist,
        "rank": {"n": rank_n,
                 "segmentos": [{"etiqueta": "%d-%d" % (a, b), "n": rank_seg[j],
                                "pct": (rank_seg[j] / rank_n * 100 if rank_n else None),
                                "esperado": (b - a + 1) / K * 100}
                               for j, (a, b) in enumerate(MESA_SEG_RANK)]},
        "hueco": {"n": hue_n,
                  "segmentos": [{"etiqueta": MESA_BINS_HUECO[j][2], "n": hue_seg[j],
                                 "pct": (hue_seg[j] / hue_n * 100 if hue_n else None),
                                 "esperado": (hue_ocup[j] / (hue_n * K) * 100 if hue_n else None)}
                                for j in range(nh)]},
    }

def _api(fn, *args):
    """Envoltorio de las rutas /api/: nunca deja que un fallo de la mesa
    (funcion puramente de lectura) tumbe el servidor ni la pagina."""
    try:
        return fn(*args)
    except Exception as ex:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"error": "%s: %s" % (type(ex).__name__, ex)}

def html_mesa():
    return (
        '<section class="card" id="mesa">'
        '<div class="hh"><h2>Mesa de probabilidades</h2>'
        '<span id="mesa-slot">cargando…</span></div>'
        '<div class="mesa-bar">'
        '<div class="mesa-nav"><button type="button" class="sec" id="mesa-prev">←</button>'
        '<span id="mesa-pos" class="st"></span>'
        '<button type="button" class="sec" id="mesa-next">→</button></div>'
        '<div class="mesa-modos">'
        '<button type="button" class="sec on" data-modo="rango">Por rango</button>'
        '<button type="button" class="sec" data-modo="rank">Por rank</button>'
        '<button type="button" class="sec" data-modo="hueco">Por hueco</button>'
        '</div></div>'
        '<div id="mesa-aviso"></div>'
        '<div id="mesa-cuerpo" class="mesa-cuerpo"></div>'
        '<details style="margin-top:14px"><summary>Dónde cayó el ganador (muestra en vivo)</summary>'
        '<div id="mesa-stats" class="mesa-stats">cargando…</div>'
        '<p class="tip" style="margin-top:10px"><b>Muestra en vivo, n pequeño — esto NO es '
        'validación.</b> Es un termómetro de lo que está pasando ahora, no evidencia. '
        'Cualquier cambio de apuesta necesita validación walk-forward en desarrollo.</p>'
        '</details>'
        '<p class="note">La mesa no mejora la predicción: muestra completa la distribución que el '
        'modelo ya calculaba. Solo lectura — no altera pronósticos, marcador ni tripletas.</p>'
        '</section>')

CSS_MESA = """
.mesa-bar{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px}
.mesa-nav{display:flex;align-items:center;gap:8px}
.mesa-nav button{padding:6px 13px;font-size:15px;line-height:1}
.mesa-nav button[disabled]{opacity:.35;cursor:default}
.mesa-modos{display:flex;gap:6px;flex-wrap:wrap}
.mesa-modos button{padding:6px 12px;font-size:13px;font-weight:600}
.mesa-modos button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.mesa-cuerpo{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media (max-width:820px){.mesa-cuerpo{grid-template-columns:1fr}}
.mseg{border:1px solid var(--line);border-radius:9px;padding:10px 12px}
.mseg h4{margin:0 0 3px;font-size:13px;font-weight:600}
.mseg .masa{font-size:12px;color:var(--muted);margin:0 0 8px;font-variant-numeric:tabular-nums}
.mrow{display:grid;grid-template-columns:38px 1fr 46px;align-items:center;gap:8px;padding:3px 0;font-size:13px}
.mrow .mn{font-weight:700;color:var(--brand);font-variant-numeric:tabular-nums;font-size:15px}
.mrow .mb{height:15px;background:#f0ede6;border-radius:4px;position:relative;overflow:hidden}
.mrow .mb i{display:block;height:100%;border-radius:4px;min-width:1px;background:#c9c4b8}
.mrow .mb span{position:absolute;left:6px;top:0;line-height:15px;font-size:11px;color:var(--ink);white-space:nowrap}
.mrow .mp{text-align:right;font-variant-numeric:tabular-nums;color:var(--soft);font-size:11px}
.mrow.t15 .mb i{background:var(--brand)}
.mrow.gana{background:var(--ok-soft);border-radius:5px}
.mrow.gana .mn{color:var(--ok)}
.mrow.gana .mb i{background:var(--ok)}
.mrow .tag{font-style:normal;color:var(--soft);font-size:10px;margin-left:4px}
.mesa-stats table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
.mesa-stats th{text-align:left;color:var(--muted);font-weight:600;padding:5px 7px;border-bottom:1px solid var(--line)}
.mesa-stats td{padding:5px 7px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
.mesa-stats h4{margin:14px 0 0;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
"""

JS_MESA = """
<script>
(function(){
  var off = 0, modo = 'rango', datos = null;
  var cuerpo = document.getElementById('mesa-cuerpo');
  if(!cuerpo) return;
  var slotEl = document.getElementById('mesa-slot'), posEl = document.getElementById('mesa-pos');
  var avisoEl = document.getElementById('mesa-aviso');
  var prev = document.getElementById('mesa-prev'), next = document.getElementById('mesa-next');

  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function pct(x){ return (x*100).toFixed(2)+'%'; }

  function fila(a, maxp){
    var cls = 'mrow' + (a.en_top15 ? ' t15' : '') +
              (datos.winner !== null && a.idx === datos.winner ? ' gana' : '');
    var ancho = (a.prob !== null && maxp > 0) ? Math.max(1, a.prob/maxp*100) : 0;
    var dentro = a.prob !== null ? pct(a.prob) : (a.rank !== null ? 'rank ' + a.rank : '\\u2014');
    var gap = a.gap_dias === null ? 'nunca' : (a.gap_dias === 0 ? 'hoy' : a.gap_dias + 'd');
    return '<div class="' + cls + '"><span class="mn">' + esc(a.num) + '</span>' +
      '<span class="mb"><i style="width:' + ancho.toFixed(1) + '%"></i><span>' + dentro +
      ' <em class="tag">' + esc(a.nombre) + '</em></span></span>' +
      '<span class="mp">' + gap + '</span></div>';
  }

  function bloque(titulo, sub, lista, maxp){
    var masa = 0, hay = false;
    lista.forEach(function(a){ if(a.prob !== null){ masa += a.prob; hay = true; } });
    var orden = lista.slice().sort(function(x, y){
      if(x.prob !== null && y.prob !== null) return y.prob - x.prob;
      if(x.rank !== null && y.rank !== null) return x.rank - y.rank;
      return x.idx - y.idx;
    });
    var cab = hay ? ('masa ' + pct(masa) + ' \\u00b7 ' + orden.length + ' animales')
                  : (orden.length + ' animales');
    return '<div class="mseg"><h4>' + esc(titulo) + (sub ? ' <em class="tag">' + esc(sub) +
      '</em>' : '') + '</h4><p class="masa">' + cab + '</p>' +
      orden.map(function(a){ return fila(a, maxp); }).join('') + '</div>';
  }

  function pinta(){
    if(!datos) return;
    var A = datos.animales, maxp = 0;
    A.forEach(function(a){ if(a.prob !== null && a.prob > maxp) maxp = a.prob; });
    var out = '';
    if(modo === 'rango'){
      datos.cuadrantes.forEach(function(q){
        out += bloque(q.clave, q.etiqueta, q.idx.map(function(i){ return A[i]; }), maxp);
      });
    } else if(modo === 'rank'){
      datos.seg_rank.forEach(function(s){
        var l = A.filter(function(a){ return a.rank !== null && a.rank >= s.desde && a.rank <= s.hasta; });
        if(l.length) out += bloque('Ranks ' + s.desde + '-' + s.hasta, '', l, maxp);
      });
      var sinr = A.filter(function(a){ return a.rank === null; });
      if(sinr.length) out += bloque('Sin rank guardado', '', sinr, maxp);
    } else {
      datos.bins_hueco.forEach(function(b){
        var l = A.filter(function(a){
          var g = a.gap_dias === null ? 99999 : a.gap_dias;
          return g >= b.desde && g <= b.hasta;
        });
        if(l.length) out += bloque(b.etiqueta, '', l, maxp);
      });
    }
    cuerpo.innerHTML = out || '<p class="note">Sin datos para este modo.</p>';
  }

  function carga(){
    fetch('/api/mesa?offset=' + off).then(function(r){ return r.json(); }).then(function(j){
      if(j.error){ cuerpo.innerHTML = '<p class="note">' + esc(j.error) + '</p>'; return; }
      datos = j; off = j.offset;
      var gan = j.winner !== null
        ? ' \\u00b7 sali\\u00f3 <b>' + esc(j.winner_num) + ' ' + esc(j.winner_nombre) + '</b>' +
          (j.winner_rank ? ' (rank ' + j.winner_rank + ')' : '')
        : ' \\u00b7 pendiente';
      slotEl.innerHTML = esc(j.fecha_txt) + ' ' + esc(j.hora_txt) + gan;
      posEl.textContent = (j.offset === 0 ? 'slot actual' : 'hace ' + j.offset) +
                          ' \\u00b7 ' + (j.offset + 1) + '/' + j.total;
      prev.disabled = (j.offset >= j.total - 1);
      next.disabled = (j.offset <= 0);
      avisoEl.innerHTML = j.vista === 'prob' ? '' :
        '<div class="tip">' + (j.vista === 'rank'
          ? 'Registro antiguo: se guard\\u00f3 el orden completo pero no los puntajes. Vista <b>solo rank</b>, sin barras de probabilidad.'
          : 'Registro antiguo: solo se guard\\u00f3 el Top-3. No hay ranks ni puntajes para los 38.') +
        '</div>';
      pinta();
    }).catch(function(){ cuerpo.innerHTML = '<p class="note">No se pudo cargar la mesa.</p>'; });
  }

  prev.onclick = function(){ off += 1; carga(); };
  next.onclick = function(){ if(off > 0){ off -= 1; carga(); } };
  Array.prototype.forEach.call(document.querySelectorAll('.mesa-modos button'), function(b){
    b.onclick = function(){
      Array.prototype.forEach.call(document.querySelectorAll('.mesa-modos button'), function(x){
        x.classList.remove('on'); });
      b.classList.add('on'); modo = b.getAttribute('data-modo'); pinta();
    };
  });

  function tabla(t, titulo, nota){
    var h = '<h4>' + titulo + '</h4><p class="note">' + nota + ' \\u00b7 n = ' + t.n + '</p>' +
      '<table><tr><th>segmento</th><th>ganadores</th><th>%</th><th>esperado</th></tr>';
    t.segmentos.forEach(function(s){
      h += '<tr><td>' + esc(s.etiqueta) + '</td><td>' + s.n + '</td><td>' +
           (s.pct === null ? '\\u2014' : s.pct.toFixed(1) + '%') + '</td><td>' +
           (s.esperado === null ? '\\u2014' : s.esperado.toFixed(1) + '%') + '</td></tr>';
    });
    return h + '</table>';
  }
  fetch('/api/mesa_stats').then(function(r){ return r.json(); }).then(function(j){
    var el = document.getElementById('mesa-stats');
    el.innerHTML =
      tabla(j.rank, 'Por segmento de rank', 'solo registros con orden completo guardado') +
      tabla(j.hueco, 'Por bin de hueco', 'esperado = ocupaci\\u00f3n media del bin bajo azar') +
      '<p class="note">' + j.resueltos + ' sorteos resueltos \\u00b7 ' + j.sin_orden_completo +
      ' sin orden completo \\u00b7 ' + j.sin_historial + ' sin fila en el historial.</p>';
  }).catch(function(){});

  carga();
})();
</script>
"""

CSS = CSS + CSS_MESA
JS = JS + JS_MESA

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
        elif ruta == "/api/mesa":
            q = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            self._send(json.dumps(_api(mesa_datos, q.get("offset", ["0"])[0]),
                                  ensure_ascii=False), "application/json; charset=utf-8")
        elif ruta == "/api/mesa_stats":
            self._send(json.dumps(_api(mesa_stats), ensure_ascii=False),
                       "application/json; charset=utf-8")
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
        if ruta == "/tripleta/registrar":
            q = parse_qs(datos)
            pf = (q.get("pf", [""])[0]).strip()
            try: ph = int(q.get("ph", [""])[0])
            except ValueError: ph = -1
            try: n = int(q.get("n", [""])[0])
            except ValueError: n = -1
            codigos = [(q.get(k, [""])[0]).strip() for k in ("a1", "a2", "a3", "b1", "b2", "b3")]
            texto, clase = registrar_tripleta(pf, ph, n, codigos)
            AVISO.update(texto=esc(texto), clase=clase)
            return self._volver("#tripleta")
        if ruta.startswith("/herramienta/"):
            partes = ruta.strip("/").split("/")
            if len(partes) == 3 and partes[2] == "detener":
                detener_tarea(partes[1])
            elif len(partes) == 2:
                iniciar_tarea(partes[1])
            return self._volver("#herramientas")
        self._send("No encontrado", "text/plain; charset=utf-8", 404)

    def log_message(self, fmt, *a):
        # Silenciado antes: el servidor corría sordo y un traceback en
        # /registrar o en el recálculo de pesos dejaba rastro solo en la
        # consola. Railway captura stderr: ahora queda en los logs.
        sys.stderr.write("%s %s\n" % (datetime.now().isoformat(timespec="seconds"),
                                       fmt % a if a else fmt))

if __name__ == "__main__":
    if DATOS != RUTA and not os.path.exists(HIST):
        # Volumen recién creado (vacío): lo sembramos una vez con los datos del repo.
        import shutil
        for nombre in ("historial.txt", "predicciones.json", "pesos_ensamble.json"):
            origen = os.path.join(RUTA, nombre)
            if os.path.exists(origen):
                shutil.copy2(origen, os.path.join(DATOS, nombre))
    if not os.path.exists(HIST):
        sys.exit("Falta historial.txt en esta carpeta.")
    PUERTO = int(os.environ.get("PORT", PUERTO))
    EN_NUBE = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT"))
    HOST = "0.0.0.0" if EN_NUBE else "127.0.0.1"
    url = f"http://localhost:{PUERTO}"
    print(f"\n  Lotto Activo corriendo en  {url}")
    print("  Modelo:", "ensamble (numpy/scipy OK)" if PRED else f"antiguo ({PRED_ERR})")
    print("  Hora local:", datetime.now().isoformat(timespec="seconds"),
          f"({time.tzname[0]}, UTC{time.timezone/-3600:+.0f})")
    if time.timezone != 4 * 3600:
        print("  AVISO: la zona horaria no quedo en UTC-4 (Caracas); "
              "las etiquetas hoy/ayer saldran desplazadas.", file=sys.stderr)
    print("  Para detenerlo: Ctrl + C\n")
    if not EN_NUBE:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        HTTPServer((HOST, PUERTO), H).serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.\n")
