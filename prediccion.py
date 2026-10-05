# -*- coding: utf-8 -*-
"""Puente entre servidor.py y el ensamble evaluado en herramientas/.

Predice el próximo sorteo con EXACTAMENTE el mismo código que midió
herramientas/lotto_eval.py (mismos submodelos, misma cadencia de reajuste):

* Cada submodelo reajusta sus parámetros en fronteras de bloque
  (ARRANQUE + k·R). Para el sorteo n se llama a predecir(datos+fila_ficticia, T)
  con T = última frontera <= n; la fila ficticia no influye en la fila n
  (lo garantiza la prueba de fuga).
* Los pesos del ensamble se reajustan cada R_ENS sorteos con predicciones
  walk-forward pasadas. Ese cálculo completo tarda varios minutos, así que se
  guarda en pesos_ensamble.json y se rehace en segundo plano cuando cambia de
  bloque; mientras tanto se usan los pesos del bloque anterior.

Si numpy/scipy no están instalados, servidor.py sigue con su modelo antiguo.
"""
import hashlib, json, os, sys, threading, time, traceback

RUTA = os.path.dirname(os.path.abspath(__file__))
DATOS = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or RUTA
HERR = os.path.join(RUTA, "herramientas")
PESOS = os.path.join(DATOS, "pesos_ensamble.json")
MODELO_ENSAMBLE = "ensamble_v2"
sys.path.insert(0, HERR)

import numpy as np                      # noqa: E402  (ImportError -> servidor usa el modelo antiguo)
import lotto_eval as LE                 # noqa: E402
import tripleta_ventana as TV           # noqa: E402

K = 38

# Ajuste del PRIMER sorteo del día (investigacion/2026-10-03/primer_sorteo_ayer/).
# El operador casi nunca repite en el primer sorteo el ganador del primer
# sorteo de ayer (3 veces en 1.082 días; contra el ensamble O/E 0,12 dev, 0,19
# prueba) y repite de más el del primer sorteo de hace 3 días (O/E 1,45-1,89 en
# las dos eras). El ensamble lo diluye porque su "retraso exacto" es común a
# las 12 horas. Multiplicadores ajustados SOLO en dev [2000, 9357) con L2.
AJUSTE_PRIMER = {1: 0.272, 3: 1.736}     # días atrás -> multiplicador

# Corrección de FECHA a las 8:00 (investigacion/2026-10-05/ocho_am/INFORME.md). El operador
# esquiva el número de la fecha (día−1, día, día+1) en el primer sorteo: en prueba, 9 aciertos
# contra 17,1 esperados; +24 mbits por mañana [no significativo al 95 %]. Se ENCIENDE antes de
# que la sombra llegue a n = 730, por decisión del usuario (rompe ese pre-registro). Multiplicadores
# congelados de herramientas/modelos/exposicion.aplicar_8am (ajustados solo en dev). Freno: con
# n ≥ 180 mañanas desde ENCENDIDO_8AM, si la ventana sale O/E ≥ 1,0 (/api/sombra) se apaga.
ENCENDIDO_8AM = "2026-10-06"


def ajuste_8am(p, fecha_sig, hora_sig):
    """Probabilidades con la corrección de fecha a las 8:00, o None si no aplica (otra hora o antes del encendido)."""
    if int(hora_sig) != 0 or fecha_sig < ENCENDIDO_8AM:
        return None
    ruta = os.path.join(HERR, "modelos")
    if ruta not in sys.path:
        sys.path.append(ruta)
    import exposicion
    q = np.array(exposicion.aplicar_8am([float(x) for x in p], fecha_sig, 0))
    return q / q.sum()


def ajuste_primer_sorteo(datos, fecha_sig, hora_sig):
    """Multiplicadores (K,) para el próximo sorteo y detalle; (None, None) si no aplica.

    Solo usa datos ya registrados (filas < n): el ganador del primer sorteo de
    hace k días, si ese sorteo fue a la misma hora que el que viene.
    """
    from datetime import date, timedelta
    if datos.fecha and datos.fecha[-1] >= fecha_sig:
        return None, None                       # no es el primero del día
    f0 = date.fromisoformat(fecha_sig)
    primero = {}
    for f, h, s in zip(datos.fecha, datos.hora, datos.seq):
        primero.setdefault(f, (int(h), int(s)))
    m = np.ones(K); detalle = {}
    for k, mult in AJUSTE_PRIMER.items():
        x = primero.get((f0 - timedelta(days=k)).isoformat())
        if x is not None and x[0] == int(hora_sig):
            m[x[1]] *= mult; detalle[str(k)] = x[1]
    return (m, detalle) if detalle else (None, None)


def _frontera(n, inicio, R):
    return inicio + ((n - inicio) // R) * R


def _extender(datos, fecha_sig, hora_sig):
    from datetime import date
    d0 = date.fromisoformat(datos.fecha[0])
    f = date.fromisoformat(fecha_sig)
    return LE.Datos(np.r_[datos.seq, 0], np.r_[datos.hora, hora_sig], np.r_[datos.dow, f.weekday()],
                    np.r_[datos.dia, (f - d0).days], list(datos.fecha) + [fecha_sig])


class Predictor:
    def __init__(self):
        self.ens = LE.cargar_modelo(os.path.join(HERR, "modelos", MODELO_ENSAMBLE + ".py"))
        self._lock = threading.Lock()
        self._cache = {}                 # clave historial -> (probs, info)
        self._calculando = None
        self._hilo_pesos = None
        self.error = None

    # ------------------------------------------------------------------ pesos
    def _pesos_guardados(self):
        # Primero el volumen (si existe); si falta, la copia del repo.
        # Así un despliegue con volumen vacío no cae en pesos uniformes.
        for ruta in (PESOS, os.path.join(RUTA, "pesos_ensamble.json")):
            try:
                with open(ruta, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
        return None

    def _recalcular_pesos(self, hist):
        try:
            datos = LE.cargar(hist)
            n = len(datos)
            T = _frontera(n, LE.W, self.ens.R)
            m = LE.cargar_modelo(os.path.join(HERR, "modelos", MODELO_ENSAMBLE + ".py"))
            m.predecir(datos.prefijo(T + 1), T)          # ajusta pesos con filas < T
            w = [float(x) for x in m.historial_pesos[-1][1]]
            with open(PESOS + ".tmp", "w", encoding="utf-8") as f:
                json.dump({"frontera": T, "base": m.base, "pesos": w,
                           "calculado": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=1)
            os.replace(PESOS + ".tmp", PESOS)
        except Exception:
            self.error = traceback.format_exc()

    def _pesos(self, n, hist):
        g = self._pesos_guardados()
        T = _frontera(n, LE.W, self.ens.R)
        vigentes = g is not None and g.get("base") == self.ens.base and g.get("frontera") == T
        if not vigentes and (self._hilo_pesos is None or not self._hilo_pesos.is_alive()):
            self._hilo_pesos = threading.Thread(target=self._recalcular_pesos, args=(hist,), daemon=True)
            self._hilo_pesos.start()
        # Los pesos de un bloque ANTERIOR valen (solo usan pasado); los de un
        # bloque POSTERIOR no: se calcularon con sorteos que, para la fila n,
        # todavía no habían ocurrido. Eso pasa tras un «deshacer», que baja n
        # por debajo de la frontera ya guardada. En ese caso se usan pesos
        # uniformes hasta que el recálculo en segundo plano termine.
        if (g is not None and g.get("base") == self.ens.base
                and g.get("frontera") is not None and g["frontera"] <= T):
            return np.array(g["pesos"]), g["frontera"], vigentes
        return np.full(len(self.ens.base), 1.0 / len(self.ens.base)), None, False

    # ------------------------------------------------------------ predicción
    def calcular(self, hist, fecha_sig, hora_sig):
        datos = LE.cargar(hist)
        n = len(datos)
        ext = _extender(datos, fecha_sig, hora_sig)
        logs = []
        for nombre in self.ens.base:
            sub = LE.cargar_modelo(os.path.join(HERR, "modelos", nombre + ".py"))
            R = getattr(sub, "R", None) or 250
            T = _frontera(n, self.ens.arranque, R)
            P = LE.normalizar(sub.predecir(ext, T))[-1]
            logs.append(np.log(np.clip(P, 1e-9, None)))
        L = np.stack(logs)
        L -= np.log(np.exp(L).sum(1, keepdims=True))
        w, fw, vigentes = self._pesos(n, hist)
        z = w @ L
        p = np.exp(z - z.max()); p /= p.sum()
        info = {"pesos": [round(float(x), 3) for x in w], "frontera_pesos": fw, "pesos_vigentes": vigentes}
        m, detalle = ajuste_primer_sorteo(datos, fecha_sig, hora_sig)
        if m is not None:
            info["scores_base"] = [round(float(x), 6) for x in p]   # sin ajuste, para auditar
            info["ajuste_primer"] = detalle
            p = p * m; p /= p.sum()
        q = ajuste_8am(p, fecha_sig, hora_sig)
        if q is not None:
            info["scores_sin_8am"] = [round(float(x), 6) for x in p]   # = producción hasta el 5-oct; las sombras lo usan
            info["ajuste_8am"] = "exposicion.aplicar_8am"
            p = q
        try:
            info["tripleta"] = [float(x) for x in self.calcular_tripleta(ext, n)]
        except Exception:
            info["tripleta_error"] = traceback.format_exc()[-400:]
        return p, info

    def calcular_tripleta(self, ext, n):
        """P(animal sale en los 12 sorteos que empiezan en n), mismo código que tripleta_ventana.py."""
        X, Y, _ = TV.construir(ext)
        m = TV.Modelo()
        th = m.pesos(X, Y, TV.frontera(n, m.reaj))
        z = X[n].astype(np.float64) @ th[1:] + th[0]
        return 1 / (1 + np.exp(-z))

    def obtener(self, hist, fecha_sig, hora_sig):
        """Devuelve (probs, info) o None si todavía se está calculando."""
        with open(hist, "rb") as f:
            crudo = f.read()
        huella = hashlib.sha1(crudo).hexdigest()
        clave = huella + f"|{fecha_sig}|{hora_sig}"
        with self._lock:
            if clave in self._cache:
                return self._cache[clave]
            if self._calculando == clave:
                return None
            self._calculando = clave

        def trabajo():
            try:
                t0 = time.time()
                p, info = self.calcular(hist, fecha_sig, hora_sig)
                # calcular() vuelve a leer el archivo: si alguien anotó o
                # deshizo entre medias, lo calculado no corresponde a la huella
                # y se descarta (el próximo render lo rehace).
                with open(hist, "rb") as f:
                    if hashlib.sha1(f.read()).hexdigest() != huella:
                        return
                info["segundos"] = round(time.time() - t0, 1)
                # Huella del historial con que se calculó: el pronóstico solo
                # depende de ese contenido, así que quien tenga el historial
                # puede comprobar que el resultado NO estaba dentro (H2).
                info["hist_sha1"] = huella
                info["hist_n"] = sum(1 for l in crudo.splitlines() if l.strip())
                info["calculado"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                with self._lock:
                    self._cache = {clave: (p, info)}
            except Exception:
                self.error = traceback.format_exc()
            finally:
                with self._lock:
                    if self._calculando == clave:
                        self._calculando = None

        threading.Thread(target=trabajo, daemon=True).start()
        return None
