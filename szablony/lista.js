/* Filtr tematów na liście historii. Bez JavaScriptu lista działa normalnie, tylko bez filtrów. */
(function () {
  var lista = document.getElementById('wiersze');
  var filtry = document.getElementById('filtry');
  if (!lista || !filtry) return;
  var tematy = JSON.parse(filtry.getAttribute('data-tematy'));
  var wiersze = Array.prototype.slice.call(lista.querySelectorAll('.row'));
  var pusto = document.getElementById('pusto');
  var temat = 'wszystkie';
  try {
    var z = localStorage.getItem('ksiegi-temat');
    if (z && (z === 'wszystkie' || tematy.some(function (t) { return t.id === z; }))) temat = z;
  } catch (e) {}

  function ma(w, t) { return (' ' + w.getAttribute('data-tematy') + ' ').indexOf(' ' + t + ' ') >= 0; }

  function rysuj() {
    var widac = 0;
    wiersze.forEach(function (w) {
      var ok = temat === 'wszystkie' || ma(w, temat);
      w.hidden = !ok;
      if (ok) widac++;
    });
    Array.prototype.forEach.call(filtry.querySelectorAll('button'), function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-t') === temat));
    });
    if (pusto) pusto.hidden = widac > 0;
  }

  var wszystkie = [{ id: 'wszystkie', nazwa: 'Wszystkie' }].concat(tematy);
  filtry.innerHTML = wszystkie.map(function (t) {
    var ile = t.id === 'wszystkie' ? wiersze.length : wiersze.filter(function (w) { return ma(w, t.id); }).length;
    return '<li><button type="button" id="f-' + t.id + '" data-t="' + t.id + '" aria-pressed="false">' +
      t.nazwa + '<span class="ile">' + ile + '</span></button></li>';
  }).join('');
  filtry.addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    temat = b.getAttribute('data-t');
    try { localStorage.setItem('ksiegi-temat', temat); } catch (e) {}
    rysuj();
  });
  rysuj();
})();
