
<script>
(function(){
  var calc = %CALC%;
  function tareas(){
    fetch('/tareas.json').then(r=>r.json()).then(function(t){
      var alguna=false;
      var a=t._auto;
      if(a){
        var el=document.getElementById('auto-est');
        if(el){ el.textContent=a.txt; el.className='auto '+a.clase; }
        // Si el resultado acaba de anotarse solo, la página que estás viendo ya
        // es vieja (hay sorteo nuevo y otra predicción): se recarga sola.
        if(window.__autoSeq===undefined) window.__autoSeq=a.seq;
        else if(a.seq>window.__autoSeq){ location.replace(location.pathname + location.search); return; }
        if(a.corriendo) alguna=true;
      }
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
  // Pestañas: ?tab=la|rd manda; si no viene, la última que abriste.
  var tabs = [].slice.call(document.querySelectorAll('.tabs [role=tab]'));
  function ver(t, guardar){
    if(t !== 'la' && t !== 'rd') return;
    tabs.forEach(function(a){
      var on = a.getAttribute('data-tab') === t;
      a.setAttribute('aria-selected', on ? 'true' : 'false');
      a.tabIndex = on ? 0 : -1;
      var p = document.getElementById(a.getAttribute('aria-controls'));
      if(p) p.hidden = !on;
    });
    if(guardar){
      try{ localStorage.setItem('lotto.tab', t); }catch(e){}
      try{ var u = new URL(location.href); u.searchParams.set('tab', t);
           history.replaceState(null, '', u.pathname + u.search + u.hash); }catch(e){}
    }
  }
  tabs.forEach(function(a, i){
    a.addEventListener('click', function(ev){ ev.preventDefault(); ver(a.getAttribute('data-tab'), true); });
    a.addEventListener('keydown', function(ev){
      if(ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
      ev.preventDefault();
      var n = tabs[(i + (ev.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      n.focus(); ver(n.getAttribute('data-tab'), true);
    });
  });
  var qtab = null;
  try{ qtab = new URLSearchParams(location.search).get('tab'); }catch(e){}
  if(qtab){ try{ localStorage.setItem('lotto.tab', qtab); }catch(e){} }
  else { var s = null; try{ s = localStorage.getItem('lotto.tab'); }catch(e){} if(s) ver(s, false); }
  // Desplegables: recuerda cuáles dejaste abiertos.
  [].forEach.call(document.querySelectorAll('details[data-rec]'), function(d){
    var k = 'lotto.sec.' + d.id;
    try{ var v = localStorage.getItem(k); if(v === '1') d.open = true; else if(v === '0') d.open = false; }catch(e){}
    d.addEventListener('toggle', function(){ try{ localStorage.setItem(k, d.open ? '1' : '0'); }catch(e){} });
  });
  if(calc){
    (function listo(){
      fetch('/listo.json').then(r=>r.json()).then(function(j){
        var inp=document.getElementById('num');
        if(j.listo && !(inp && inp.value)) location.replace(location.pathname + location.search);
        else setTimeout(listo, 2500);
      }).catch(function(){setTimeout(listo,4000);});
    })();
  }
})();
</script>

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
    var dentro = a.prob !== null ? pct(a.prob) : (a.rank !== null ? 'rank ' + a.rank : '\u2014');
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
    var cab = hay ? ('masa ' + pct(masa) + ' \u00b7 ' + orden.length + ' animales')
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
        ? ' \u00b7 sali\u00f3 <b>' + esc(j.winner_num) + ' ' + esc(j.winner_nombre) + '</b>' +
          (j.winner_rank ? ' (rank ' + j.winner_rank + ')' : '')
        : ' \u00b7 pendiente';
      slotEl.innerHTML = esc(j.fecha_txt) + ' ' + esc(j.hora_txt) + gan;
      posEl.textContent = (j.offset === 0 ? 'slot actual' : 'hace ' + j.offset) +
                          ' \u00b7 ' + (j.offset + 1) + '/' + j.total;
      prev.disabled = (j.offset >= j.total - 1);
      next.disabled = (j.offset <= 0);
      avisoEl.innerHTML = j.vista === 'prob' ? '' :
        '<div class="tip">' + (j.vista === 'rank'
          ? 'Registro antiguo: se guard\u00f3 el orden completo pero no los puntajes. Vista <b>solo rank</b>, sin barras de probabilidad.'
          : 'Registro antiguo: solo se guard\u00f3 el Top-3. No hay ranks ni puntajes para los 38.') +
        '</div>';
      pinta();
    }).catch(function(){ cuerpo.innerHTML = '<p class="note">No se pudo cargar la mesa.</p>'; });
  }

  prev.onclick = function(){ off += 1; carga(); };
  next.onclick = function(){ if(off > 0){ off -= 1; carga(); } };
  Array.prototype.forEach.call(document.querySelectorAll('.mesa-modos button'), function(b){
    b.onclick = function(){
      Array.prototype.forEach.call(document.querySelectorAll('.mesa-modos button'), function(x){
        x.classList.remove('on'); x.setAttribute('aria-pressed', 'false'); });
      b.classList.add('on'); b.setAttribute('aria-pressed', 'true'); modo = b.getAttribute('data-modo'); pinta();
    };
  });

  function tabla(t, titulo, nota){
    var h = '<h4>' + titulo + '</h4><p class="note">' + nota + ' \u00b7 n = ' + t.n + '</p>' +
      '<table><tr><th>segmento</th><th>ganadores</th><th>%</th><th>esperado</th></tr>';
    t.segmentos.forEach(function(s){
      h += '<tr><td>' + esc(s.etiqueta) + '</td><td>' + s.n + '</td><td>' +
           (s.pct === null ? '\u2014' : s.pct.toFixed(1) + '%') + '</td><td>' +
           (s.esperado === null ? '\u2014' : s.esperado.toFixed(1) + '%') + '</td></tr>';
    });
    return h + '</table>';
  }
  fetch('/api/mesa_stats').then(function(r){ return r.json(); }).then(function(j){
    var el = document.getElementById('mesa-stats');
    el.innerHTML =
      tabla(j.rank, 'Por segmento de rank', 'solo registros con orden completo guardado') +
      tabla(j.hueco, 'Por bin de hueco', 'esperado = ocupaci\u00f3n media del bin bajo azar') +
      '<p class="note">' + j.resueltos + ' sorteos resueltos \u00b7 ' + j.sin_orden_completo +
      ' sin orden completo \u00b7 ' + j.sin_historial + ' sin fila en el historial.</p>';
  }).catch(function(){});

  carga();
})();
</script>

<script>
document.addEventListener('click', function(ev){
  var b = ev.target.closest('.compartir button'); if(!b) return;
  var c = b.parentNode, v = c.querySelector('select').value;
  var m = parseFloat(c.querySelector('input').value.replace(',', '.')) || 0;
  // Formato para WhatsApp: cabecera en negrita y bloques de 5 separados por una línea en blanco.
  function lista(a, monto, desde){
    var filas = a.map(function(x, k){
      var n = (desde || 0) + k + 1;
      return (n < 10 ? '0' : '') + n + '.  ' + x + (monto ? '  →  $' + monto : '');
    });
    var bl = [];
    for(var i = 0; i < filas.length; i += 5) bl.push(filas.slice(i, i + 5).join('\n'));
    return bl.join('\n\n');
  }
  var top = c.dataset.a.split('|'), anti = c.dataset.x ? c.dataset.x.split('|') : [];
  var t = '*' + c.dataset.t.toUpperCase() + '*\n' + '📅 ' + c.dataset.f + '\n';
  if(v === 'anti'){
    t += '🚫 Anti Top 15 (del 16 al 30, para descartar)\n\n' + lista(anti, 0, 15);
  } else {
    var n = v === 'ambos' ? 15 : +v, a = top.slice(0, n);
    t += '🎯 Top ' + n + (m ? '  ·  $' + m + ' por animal' : '') + '\n\n' + lista(a, m)
       + (m ? '\n\n💰 *Total: $' + (m * a.length) + '*' : '');
    if(v === 'ambos') t += '\n\n🚫 Anti Top 15 (del 16 al 30, para descartar)\n\n' + lista(anti, 0, 15);
  }
  if(navigator.share) navigator.share({text: t}).catch(function(){});
  else navigator.clipboard.writeText(t).then(function(){ b.textContent = 'Copiado'; setTimeout(function(){ b.textContent = 'Compartir'; }, 1500); });
});
</script>
