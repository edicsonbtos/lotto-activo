# -*- coding: utf-8 -*-
"""Piezas que comparten la pestaña Lotto Activo (servidor.py) y RD Internacional (rdint_vivo.py).

Solo vive aquí lo que ambos escribían igual, byte a byte (lo fija tests/test_comun.py).
Lo que difiere a propósito (fecha_corta/«ayer», log_cargar, anti Top-15) sigue en cada módulo.
"""
import html as _html
import io
import json
import os


PAGO = 30                                   # cada ficha acertada paga 30
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K = len(POS)


def esc(s):
    return _html.escape(str(s))


def guardar_json(ruta, d, indent=None):
    """Escritura atómica: un corte a mitad no deja el archivo a medias."""
    tmp = ruta + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, ruta)


def fx(n, clase):
    """Casilla de fichas: número relleno si se juega, raya tenue si no."""
    if not n:
        return '<span class="fx z" aria-label="sin fichas">–</span>'
    return f'<span class="fx {clase}" aria-label="{n} ficha{"s" if n != 1 else ""}">{n}</span>'


COLS = ('<li class="cols" aria-hidden="true"><span></span><span></span><span>Animal</span>'
        '<span>Top-5</span><span>Ponde&shy;rado</span></li>')


def fila(r, num_, nombre, sub, f5, fp):
    return (f'<li><span class="rk">{r}</span><span class="n">{esc(num_)}</span>'
            f'<span class="nm">{esc(nombre)}<small>{sub}</small></span>'
            f'{fx(f5, "a")}{fx(fp, "b")}</li>')


def nav(tab, atras, total):
    """Flechas para ver el Top congelado de sorteos anteriores (atras=0: el próximo)."""
    def enlace(n, txt):
        return f'<a href="/?tab={tab}' + (f'&amp;atras={n}' if n else '') + f'">{txt}</a>'
    ant = enlace(atras + 1, "‹ Anterior") if atras < total else '<span class="off">‹ Anterior</span>'
    sig = enlace(atras - 1, "Siguiente ›") if atras > 0 else '<span class="off">Siguiente ›</span>'
    pos = "próximo sorteo" if atras == 0 else f"hace {atras} sorteo{'s' if atras > 1 else ''}"
    return f'<nav class="histnav" aria-label="Sorteos anteriores">{ant}<span class="pos">{pos}</span>{sig}</nav>'


def sec(id_, titulo, meta, cuerpo, abierto=False):
    """Desplegable de la página (se recuerda abierto/cerrado en el navegador)."""
    return (f'<details class="sec" id="{id_}" data-rec{" open" if abierto else ""}>'
            f'<summary><span class="st"><h2>{titulo}</h2><span class="meta">{meta}</span></span>'
            f'<span class="chev" aria-hidden="true"></span></summary>'
            f'<div class="cuerpo">{cuerpo}</div></details>')


def compartir(juego, animales, anti=(), cuando=None):
    """Bloque «Compartir» (el JS vive en static/app.js). `cuando` es opcional: RD no lo lleva."""
    op_anti = ('<option value="anti">Anti Top 15</option><option value="ambos">Top 15 + Anti 15</option>'
               if anti else "")
    f = f' data-f="{esc(cuando)}"' if cuando is not None else ""
    return (f'<div class="compartir" data-t="{esc(juego)}"{f} data-a="{esc("|".join(animales[:15]))}"'
            f' data-x="{esc("|".join(anti))}">'
            '<select aria-label="Qué compartir"><option value="5">Top 5</option><option value="15">Top 15</option>'
            f'{op_anti}</select>'
            '<input type="text" inputmode="decimal" placeholder="$ por animal" aria-label="Monto por animal">'
            '<button type="button" class="sec">Compartir</button></div>')


def respaldo_zip(carpeta, archivos):
    """Zip en memoria con los archivos de datos vivos que existan en `carpeta` (el marcador y los historiales)."""
    import io as _io, zipfile
    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre in archivos:
            ruta = os.path.join(carpeta, nombre)
            if os.path.isfile(ruta):
                z.write(ruta, nombre)
    return buf.getvalue()
