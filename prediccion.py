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
