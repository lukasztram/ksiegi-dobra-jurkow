#!/usr/bin/env python3
"""Buduje stronę „Co mówią księgi parafii Dobra i Jurków”.

Wynik:
  docs/                  gotowa strona do internetu (GitHub Pages: gałąź main, folder /docs)
  _podglad/podglad.html  cała strona w jednym pliku, do podglądu na telefonie

Treści:   tresci/spis.json (lista historii), tresci/historie/<id>.html, tresci/o-stronie.html
Wygląd:   szablony/styl.css, szablony/lista.js

Tylko biblioteka standardowa Pythona.  Użycie:  python3 buduj.py
"""
import html
import json
import shutil
import sys
from pathlib import Path

KAT = Path(__file__).resolve().parent
TRESCI = KAT / 'tresci'
SZABLONY = KAT / 'szablony'
DOCS = KAT / 'docs'
PODGLAD = KAT / '_podglad'

FONTY = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..700;'
         '1,6..96,400..700&amp;family=IBM+Plex+Mono:wght@400;500&amp;family=Source+Serif+4:ital,opsz,wght@0,8..60,400..650;'
         '1,8..60,400..650&amp;display=swap">')

IKONA = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
         '<rect width="64" height="64" rx="12" fill="#2C5A4B"/>'
         '<path d="M18 14h22a6 6 0 0 1 6 6v30H24a6 6 0 0 1-6-6z" fill="#EDF0EB"/>'
         '<path d="M24 24h16M24 31h16M24 38h11" stroke="#7A5430" stroke-width="2.5" stroke-linecap="round"/>'
         '</svg>\n')


def e(s):
    return html.escape(s, quote=True)


SPIS = json.loads((TRESCI / 'spis.json').read_text(encoding='utf-8'))
NAZWA = SPIS['nazwa']
ADRES = SPIS.get('adres', '').rstrip('/')
TEMATY = SPIS['tematy']
HIST = sorted(SPIS['historie'], key=lambda h: h['rok'])
PELNE = [h for h in HIST if h['gotowa']]
ZRODLA = {
    'nowa': ('t-nowa', 'Nowa'),
    'ksiazka': ('t-ksiazka', 'Z publikacji'),
    'rodzina': ('t-rodzina', 'Moja rodzina'),
}


def sprawdz():
    """Zatrzymuje budowę przy brakach, zanim cokolwiek zostanie nadpisane."""
    bledy = []
    znane = {t['id'] for t in TEMATY}
    ids = set()
    for h in HIST:
        if h['id'] in ids:
            bledy.append(f'powtórzony id: {h["id"]}')
        ids.add(h['id'])
        for t in h['tematy']:
            if t not in znane:
                bledy.append(f'{h["id"]}: nieznany temat {t}')
        if h['zrodlo'] not in ZRODLA:
            bledy.append(f'{h["id"]}: nieznane źródło {h["zrodlo"]}')
        if h['gotowa']:
            if not (TRESCI / 'historie' / f'{h["id"]}.html').exists():
                bledy.append(f'{h["id"]}: brak pliku tresci/historie/{h["id"]}.html')
            for pole in ('znacznik', 'lead'):
                if not h.get(pole):
                    bledy.append(f'{h["id"]}: brak pola {pole}')
    if bledy:
        sys.exit('Błędy w treściach:\n  ' + '\n  '.join(bledy))


class LinkiStrona:
    """Linki między plikami strony (root = '' albo '../')."""
    def __init__(self, root):
        self.root = root

    def start(self):
        return f'{self.root}index.html'

    def o(self):
        return f'{self.root}o-stronie.html'

    def historia(self, hid):
        return f'{self.root}historie/{hid}.html'


class LinkiPodglad:
    """Linki w podglądzie jednoplikowym (widoki przełączane po #)."""
    root = ''

    def start(self):
        return '#'

    def o(self):
        return '#o-stronie'

    def historia(self, hid):
        return f'#{hid}'


def naglowek(L, aktywna, skok=True):
    a_h = ' aria-current="page"' if aktywna == 'historie' else ''
    a_o = ' aria-current="page"' if aktywna == 'o' else ''
    skip = '<a class="skip" href="#tresc">Przejdź do treści</a>\n' if skok else ''
    return f'''{skip}<header class="wrap top">
  <a class="brand" href="{L.start()}">Co mówią księgi <i>parafii Dobra i Jurków</i></a>
  <nav class="nav" aria-label="Główne">
    <a href="{L.start()}"{a_h}>Historie</a>
    <a href="{L.o()}"{a_o}>O stronie</a>
  </nav>
</header>'''


STOPKA = f'''<footer class="wrap stopka">
  {e(NAZWA)} · historie z ksiąg metrykalnych z lat 1678–1926<br>
  Skany ksiąg: serwis Metryki Polskiego Towarzystwa Genealogicznego, wyłącznie przez linki. Księgi czytam z pomocą Claude, asystenta sztucznej inteligencji.
</footer>'''


def tresc_start(L):
    wiersze = []
    for h in HIST:
        kl, et = ZRODLA[h['zrodlo']]
        tag = f'<span class="tag {kl}">{et}</span>'
        srodek = (f'<span class="yr">{e(h["rok_tekst"])}</span><span class="pl">{e(h["miejsce"])}</span>'
                  f'<div class="tx"><span class="ttl" role="heading" aria-level="3">{e(h["tytul"])}</span>'
                  f'<p class="tsr">{e(h["zajawka"])}</p></div>')
        tem = ' '.join(h['tematy'])
        if h['gotowa']:
            wiersze.append(f'<a class="row" href="{L.historia(h["id"])}" data-tematy="{tem}">{srodek}'
                           f'<span class="mt">{tag}<span class="go">Czytaj →</span></span></a>')
        else:
            wiersze.append(f'<div class="row soon" data-tematy="{tem}">{srodek}'
                           f'<span class="mt">{tag}<span class="soon-l">w przygotowaniu</span></span></div>')
    tematy_json = e(json.dumps(TEMATY, ensure_ascii=False))
    nl = '\n      '
    return f'''<section class="wrap" id="tresc">
  <div class="hero">
    <div>
      <p class="eyebrow">Dobra · Jurków · Chyszówki · Półrzeczki · Gruszowiec · Porąbka</p>
      <h1>Co mówią księgi <em>parafii Dobra i Jurków</em></h1>
      <p class="dek">Prawdziwe historie ludzi z naszych wsi, odczytane z ksiąg chrztów, ślubów i pogrzebów z lat 1678–1926. Także to, co księża dopisywali na marginesach.</p>
    </div>
    <figure class="epigraf">
      <blockquote lang="la">Incipit Liber Metrices post combustionem Ecclesiae</blockquote>
      <p>Zaczyna się księga metrykalna po spaleniu kościoła.</p>
      <cite>Dobra, 1678 · pierwsza strona najstarszej zachowanej księgi</cite>
    </figure>
  </div>
  <div class="dane">
    <span><b>prawie 40 tysięcy</b> wpisów w bazie</span>
    <span>księgi z lat <b>1678–1944</b></span>
    <span>historie do roku <b>1926</b></span>
    <span>każda z <b>sygnaturą i skanem</b></span>
  </div>
  <div class="sekcja-tyt">
    <h2>Historie</h2>
    <p>Po kolei, jak w księdze. Kliknij historię, żeby przeczytać. Szare czekają na opracowanie.</p>
  </div>
  <ul class="filtry" id="filtry" aria-label="Tematy" data-tematy="{tematy_json}"></ul>
  <div class="rejestr">
    <div class="rubryki" aria-hidden="true"><span>Rok <i>annus</i></span><span>Miejsce <i>pagus</i></span><span>Historia</span><span>Skąd</span></div>
    <div id="wiersze">
      {nl.join(wiersze)}
    </div>
    <p class="pusto" id="pusto" hidden>Brak historii w tym temacie.</p>
  </div>
  <div class="sekcja-tyt"><h2>Jak czytać te historie</h2></div>
  <div class="dwie">
    <div>
      <h3>Skąd pochodzą</h3>
      <ul class="legenda">
        <li><span class="tag t-nowa">Nowa</span><span>Powstała wprost z ksiąg i nie było jej w żadnej książce.</span></li>
        <li><span class="tag t-ksiazka">Z publikacji</span><span>Z publikacji dla mieszkańców: „Trzy stulecia Jurkowa”, „Chyszówki w księgach zmarłych 1786–1926” i „Umierali w Jurkowie”.</span></li>
        <li><span class="tag t-rodzina">Moja rodzina</span><span>Z moich książek rodzinnych. Te historie piszę w pierwszej osobie.</span></li>
      </ul>
    </div>
    <div>
      <h3>Na ile to pewne</h3>
      <ul class="legenda">
        <li><span class="chip c-pewne">Pewne</span><span>Odczyt porównany ze skanem albo fakt potwierdzony w kilku aktach.</span></li>
        <li><span class="chip c-prawd">Prawdopodobne</span><span>Jeden wiarygodny ślad, bez sprzecznych.</span></li>
        <li><span class="chip c-mozliwe">Możliwe</span><span>Przypuszczenie, które pasuje do faktów, ale nie ma dowodu.</span></li>
        <li><span class="chip c-odczyt">Do sprawdzenia</span><span>Odczyt maszynowy, który nie był jeszcze porównany ze skanem.</span></li>
      </ul>
    </div>
  </div>
</section>'''


def artykul(h, L, kotwica=True):
    tresc = (TRESCI / 'historie' / f'{h["id"]}.html').read_text(encoding='utf-8')
    i = PELNE.index(h)
    pop, nast = PELNE[i - 1], PELNE[(i + 1) % len(PELNE)]
    id_attr = ' id="tresc"' if kotwica else ''
    return f'''<article class="czyt"{id_attr}>
  <a class="wstecz" href="{L.start()}">← Wszystkie historie</a>
  <p class="eyebrow">{e(h["znacznik"])}</p>
  <h1 tabindex="-1">{e(h["tytul"])}</h1>
  <p class="lead">{e(h["lead"])}</p>
{tresc}
  <nav class="dalej" aria-label="Inne historie">
    <a href="{L.historia(pop["id"])}"><small>← Poprzednia</small>{e(pop["tytul"])}</a>
    <a href="{L.historia(nast["id"])}"><small>Następna →</small>{e(nast["tytul"])}</a>
  </nav>
</article>'''


def artykul_o(L, kotwica=True):
    tresc = (TRESCI / 'o-stronie.html').read_text(encoding='utf-8')
    id_attr = ' id="tresc"' if kotwica else ''
    return f'''<article class="czyt"{id_attr}>
  <a class="wstecz" href="{L.start()}">← Wszystkie historie</a>
  <p class="eyebrow">O stronie</p>
  <h1 tabindex="-1">Jak powstają te historie</h1>
{tresc}
</article>'''


def glowa(tytul, opis, root, sciezka, typ='website'):
    w = ['<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         f'<title>{e(tytul)}</title>',
         f'<meta name="description" content="{e(opis)}">',
         f'<meta property="og:site_name" content="{e(NAZWA)}">',
         f'<meta property="og:title" content="{e(tytul)}">',
         f'<meta property="og:description" content="{e(opis)}">',
         f'<meta property="og:type" content="{typ}">',
         '<meta property="og:locale" content="pl_PL">',
         '<meta name="theme-color" content="#EDF0EB" media="(prefers-color-scheme: light)">',
         '<meta name="theme-color" content="#121614" media="(prefers-color-scheme: dark)">',
         f'<link rel="icon" href="{root}ikona.svg" type="image/svg+xml">']
    if ADRES:
        u = f'{ADRES}/{sciezka}'
        w += [f'<link rel="canonical" href="{e(u)}">', f'<meta property="og:url" content="{e(u)}">']
    w += [FONTY, f'<link rel="stylesheet" href="{root}styl.css">']
    return '\n'.join(w)


def strona(tytul, opis, root, sciezka, aktywna, tresc, skrypt='', typ='website'):
    L = LinkiStrona(root)
    return f'''<!doctype html>
<html lang="pl">
<head>
{glowa(tytul, opis, root, sciezka, typ)}
</head>
<body>
{naglowek(L, aktywna)}
<main>
{tresc}
</main>
{STOPKA}
{skrypt}
</body>
</html>
'''


def zapisz(sciezka, tekst):
    sciezka.parent.mkdir(parents=True, exist_ok=True)
    sciezka.write_text(tekst, encoding='utf-8')


def buduj_strone():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    shutil.copy(SZABLONY / 'styl.css', DOCS / 'styl.css')
    shutil.copy(SZABLONY / 'lista.js', DOCS / 'lista.js')
    zapisz(DOCS / 'ikona.svg', IKONA)
    zapisz(DOCS / '.nojekyll', '')
    L0 = LinkiStrona('')
    zapisz(DOCS / 'index.html',
           strona(NAZWA, SPIS['opis'], '', '', 'historie', tresc_start(L0), '<script src="lista.js"></script>'))
    for h in PELNE:
        zapisz(DOCS / 'historie' / f'{h["id"]}.html',
               strona(f'{h["tytul"]} · {NAZWA}', h['zajawka'], '../', f'historie/{h["id"]}.html', 'historie',
                      artykul(h, LinkiStrona('../')), typ='article'))
    zapisz(DOCS / 'o-stronie.html',
           strona(f'O stronie · {NAZWA}', 'Skąd biorą się historie z ksiąg parafii Dobra i Jurków, kto je pisze i na ile są pewne.',
                  '', 'o-stronie.html', 'o', artykul_o(L0)))
    zapisz(DOCS / '404.html',
           strona(f'Nie ma takiej strony · {NAZWA}', 'Nie ma takiej strony.', '', '404.html', '',
                  '<section class="wrap czyt" id="tresc"><h1 tabindex="-1">Nie ma takiej strony</h1>'
                  '<p>Ta strona nie istnieje albo zmieniła adres. <a href="index.html">Wróć do listy historii</a>.</p></section>'))
    roboty = 'User-agent: *\nAllow: /\n'
    if ADRES:
        roboty += f'Sitemap: {ADRES}/sitemap.xml\n'
        adresy = [f'{ADRES}/', f'{ADRES}/o-stronie.html'] + [f'{ADRES}/historie/{h["id"]}.html' for h in PELNE]
        zapisz(DOCS / 'sitemap.xml',
               '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + ''.join(f'  <url><loc>{e(a)}</loc></url>\n' for a in adresy) + '</urlset>\n')
    zapisz(DOCS / 'robots.txt', roboty)


ROUTER = '''<script>
(function () {
  var PELNE = %s;
  var start = document.getElementById('widok-start');
  var hist = document.getElementById('widok-historia');
  var o = document.getElementById('widok-o');
  var navH = document.querySelector('.nav a[href="#"]');
  var navO = document.querySelector('.nav a[href="#o-stronie"]');
  function trasa() {
    var h = decodeURIComponent(location.hash.slice(1));
    start.hidden = hist.hidden = o.hidden = true;
    if (h === 'o-stronie') { o.hidden = false; }
    else if (PELNE.indexOf(h) >= 0) {
      hist.replaceChildren(document.getElementById('t-' + h).content.cloneNode(true));
      hist.hidden = false;
    } else { start.hidden = false; }
    var naO = h === 'o-stronie';
    (naO ? navO : navH).setAttribute('aria-current', 'page');
    (naO ? navH : navO).removeAttribute('aria-current');
    window.scrollTo(0, 0);
    var h1 = document.querySelector('main > :not([hidden]) h1[tabindex]');
    if (h1 && h) h1.focus({ preventScroll: true });
  }
  window.addEventListener('hashchange', trasa);
  trasa();
})();
</script>'''


def buduj_podglad():
    L = LinkiPodglad()
    css = (SZABLONY / 'styl.css').read_text(encoding='utf-8')
    lista_js = (SZABLONY / 'lista.js').read_text(encoding='utf-8')
    szablony = '\n'.join(f'<template id="t-{h["id"]}">\n{artykul(h, L, kotwica=False)}\n</template>' for h in PELNE)
    tekst = f'''<title>{e(NAZWA)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
{FONTY}
<style>
{css}
</style>
<div class="proto"><div class="wrap">Podgląd · strona nie jest jeszcze w internecie · teksty do przeczytania i poprawek</div></div>
{naglowek(L, 'historie', skok=False)}
<main>
<div id="widok-start">
{tresc_start(L)}
</div>
<section id="widok-historia" class="wrap" hidden></section>
<section id="widok-o" class="wrap" hidden>
{artykul_o(L, kotwica=False)}
</section>
</main>
{STOPKA}
{szablony}
<script>
{lista_js}
</script>
{ROUTER % json.dumps([h['id'] for h in PELNE])}
'''
    zapisz(PODGLAD / 'podglad.html', tekst)


if __name__ == '__main__':
    sprawdz()
    buduj_strone()
    buduj_podglad()
    print(f'Gotowe: {len(PELNE)} historii, {len(HIST) - len(PELNE)} w przygotowaniu.')
    print(f'  strona:  {DOCS}')
    print(f'  podgląd: {PODGLAD / "podglad.html"}')
    if not ADRES:
        print('  uwaga: brak "adres" w tresci/spis.json, więc bez canonical, og:url i sitemap.xml')
