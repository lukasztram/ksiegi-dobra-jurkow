#!/usr/bin/env python3
"""Buduje stronę „Co mówią księgi parafii Dobra i Jurków” — po polsku i w tłumaczeniach.

Wynik:
  docs/                  gotowa strona do internetu (GitHub Pages: gałąź main, folder /docs);
                         wersja polska w docs/, tłumaczenia w docs/en/, docs/de/, docs/fr/, docs/es/, docs/zh/
  _podglad/podglad.html  wersja polska w jednym pliku, do podglądu na telefonie

Treści:   tresci/spis.json (lista historii), tresci/historie/<id>.html, tresci/o-stronie.html,
          tresci/ui.json (napisy strony), tresci/dostepnosc.json (zakładka Księgi; tworzy go eksport_dostepnosci.py)
Tłumaczenia: tresci/<język>/ — spis.json, ui.json, o-stronie.html, historie/, wykresy/ (zasady: narzedzia/TLUMACZENIA.md).
          Język trafia na stronę, gdy ma ui.json i spis.json; historia — gdy ma plik w tresci/<język>/historie/.
Wygląd:   szablony/styl.css, szablony/lista.js

Tylko biblioteka standardowa Pythona.  Użycie:  python3 buduj.py
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

from dostepnosc import dostepnosc_html

KAT = Path(__file__).resolve().parent
TRESCI = KAT / 'tresci'
SZABLONY = KAT / 'szablony'
DOCS = KAT / 'docs'
PODGLAD = KAT / '_podglad'
JEZYKI = ('pl', 'en', 'de', 'fr', 'es', 'zh')        # kolejność w przełączniku języków
POLA_TLUMACZONE = ('tytul', 'zajawka', 'znacznik', 'lead', 'miejsce', 'rok_tekst')
EPIGRAF = 'Incipit Liber Metrices post combustionem Ecclesiae'

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
ADRES = SPIS.get('adres', '').rstrip('/')
HIST = sorted(SPIS['historie'], key=lambda h: h['rok'])
UI_PL = json.loads((TRESCI / 'ui.json').read_text(encoding='utf-8'))
ZRODLA = {
    'nowa': ('t-nowa', 'zrodlo_nowa'),
    'ksiazka': ('t-ksiazka', 'zrodlo_ksiazka'),
    'rodzina': ('t-rodzina', 'zrodlo_rodzina'),
}
PEWNOSC = (('c-pewne', 'pewne'), ('c-prawd', 'prawd'), ('c-mozliwe', 'mozliwe'), ('c-odczyt', 'odczyt'))


class Jezyk:
    """Napisy, spis historii i pliki treści jednej wersji językowej."""

    def __init__(self, kod):
        self.kod = kod
        self.pl = kod == 'pl'
        self.kat = TRESCI if self.pl else TRESCI / kod
        self.prefiks = '' if self.pl else f'{kod}/'
        if self.pl:
            self.ui = UI_PL
            self.nazwa, self.opis = SPIS['nazwa'], SPIS['opis']
            self.tematy = SPIS['tematy']
            self.hist = HIST
            przetl = {h['id'] for h in HIST}
        else:
            self.ui = {**UI_PL, **json.loads((self.kat / 'ui.json').read_text(encoding='utf-8'))}
            sp = json.loads((self.kat / 'spis.json').read_text(encoding='utf-8'))
            self.nazwa, self.opis = sp['nazwa'], sp['opis']
            self.tematy = [{'id': t['id'], 'nazwa': sp.get('tematy', {}).get(t['id']) or t['nazwa']} for t in SPIS['tematy']]
            tl = sp.get('historie', {})
            self.hist = [dict(h, **{k: v for k, v in tl.get(h['id'], {}).items() if k in POLA_TLUMACZONE and v})
                         for h in HIST]
            przetl = set(tl)
        self.pelne = [h for h in self.hist if h['gotowa'] and h['id'] in przetl
                      and (self.kat / 'historie' / f'{h["id"]}.html').exists()]
        self.ids = {h['id'] for h in self.pelne}
        self.tytuly = {h['id']: h['tytul'] for h in self.hist}

    @staticmethod
    def gotowy(kod):
        return kod == 'pl' or ((TRESCI / kod / 'ui.json').exists() and (TRESCI / kod / 'spis.json').exists())


JEZ = {}          # języki, które wchodzą na stronę: kod → Jezyk (wypełnia main)


def sprawdz():
    """Zatrzymuje budowę przy brakach, zanim cokolwiek zostanie nadpisane."""
    bledy, uwagi = [], []
    znane = {t['id'] for t in SPIS['tematy']}
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
    for kod in JEZYKI[1:]:
        if not (TRESCI / kod).exists():
            continue
        if not Jezyk.gotowy(kod):
            uwagi.append(f'{kod}: brak ui.json albo spis.json — język pominięty')
            continue
        brak_ui = [k for k in UI_PL if k not in json.loads((TRESCI / kod / 'ui.json').read_text(encoding='utf-8'))]
        if brak_ui:
            uwagi.append(f'{kod}: w ui.json brak {len(brak_ui)} kluczy (zostaną po polsku): {", ".join(brak_ui[:6])}')
        for p in sorted((TRESCI / kod / 'historie').glob('*.html')):
            for m in re.findall(r'\{\{(?:tytul|historia):([^}]+)\}\}', p.read_text(encoding='utf-8')):
                if m not in ids:
                    bledy.append(f'{kod}/historie/{p.name}: nieznana historia {m}')
    for u in uwagi:
        print('uwaga:', u)
    if bledy:
        sys.exit('Błędy w treściach:\n  ' + '\n  '.join(bledy))


class Linki:
    """Adresy między plikami strony.
    glebokosc: 0 dla stron w katalogu języka, 1 dla historie/<id>.html.
    baza: adres bezwzględny strony (dla 404.html, które GitHub Pages podaje pod dowolną ścieżką)."""

    def __init__(self, J, glebokosc=0, baza=None):
        self.J = J
        if baza:
            self.do_korzenia = baza
            self.do_jez = baza + J.prefiks
        else:
            self.do_jez = '../' * glebokosc
            self.do_korzenia = self.do_jez + ('' if J.pl else '../')

    def start(self):
        return f'{self.do_jez}index.html'

    def o(self):
        return f'{self.do_jez}o-stronie.html'

    def ksiegi(self):
        return f'{self.do_jez}ksiegi.html'

    def historia(self, hid):
        if hid in self.J.ids:
            return f'{self.do_jez}historie/{hid}.html'
        return f'{self.do_korzenia}historie/{hid}.html'      # historia jeszcze nieprzetłumaczona: wersja polska

    def plik(self, sciezka):
        return f'{self.do_korzenia}{sciezka}'

    def jezyk(self, kod, sciezka):
        """Ta sama strona w innym języku (albo jego strona główna, gdy tej strony tam nie ma)."""
        J2 = JEZ[kod]
        if sciezka in ('', '404.html') or (sciezka.startswith('historie/') and sciezka[9:-5] not in J2.ids):
            sciezka = 'index.html'
        return f'{self.do_korzenia}{J2.prefiks}{sciezka}'


class LinkiPodglad:
    """Linki w podglądzie jednoplikowym (widoki przełączane po #); tylko wersja polska."""

    def __init__(self, J):
        self.J = J

    def start(self):
        return '#'

    def o(self):
        return '#o-stronie'

    def ksiegi(self):
        return '#ksiegi'

    def historia(self, hid):
        return f'#{hid}'

    def plik(self, sciezka):
        # podgląd jednoplikowy nie ma folderów — obrazki z opublikowanej strony
        return f'{ADRES}/{sciezka}' if ADRES else sciezka


def pasek_jezykow(J, L, sciezka):
    if len(JEZ) < 2:
        return ''
    linki = []
    for kod, J2 in JEZ.items():
        u = J2.ui
        akt = ' aria-current="true"' if kod == J.kod else ''
        linki.append(f'<a href="{L.jezyk(kod, sciezka)}" hreflang="{u["html_lang"]}" lang="{u["html_lang"]}" '
                     f'title="{e(u["nazwa_jezyka"])}"{akt}>{e(u["skrot"])}</a>')
    return (f'<div class="wrap jezyki-pas"><nav class="jezyki" aria-label="{e(J.ui["jezyki_aria"])}">'
            f'{"".join(linki)}</nav></div>\n')


def naglowek(J, L, aktywna, sciezka=None, skok=True):
    ui = J.ui
    akt = lambda k: ' aria-current="page"' if aktywna == k else ''
    skip = f'<a class="skip" href="#tresc">{e(ui["skip"])}</a>\n' if skok else ''
    jez = pasek_jezykow(J, L, sciezka) if sciezka is not None else ''
    return f'''{skip}{jez}<header class="wrap top">
  <a class="brand" href="{L.start()}">{ui["brand_html"]}</a>
  <nav class="nav" aria-label="{e(ui["nav_aria"])}">
    <a href="{L.start()}"{akt("historie")}>{e(ui["nav_historie"])}</a>
    <a href="{L.ksiegi()}"{akt("ksiegi")}>{e(ui["nav_ksiegi"])}</a>
    <a href="{L.o()}"{akt("o")}>{e(ui["nav_o"])}</a>
  </nav>
</header>'''


def stopka(J):
    ui = J.ui
    tl = f'<br>\n  {e(ui["stopka_tlumaczenie"])}' if ui.get('stopka_tlumaczenie') else ''
    return f'''<footer class="wrap stopka">
  {e(J.nazwa)} · {e(ui["stopka_opis"])}<br>
  {e(ui["stopka_zrodla"])}{tl}
</footer>'''


def lista_pewnosci(ui, klasa='legenda', wciecie='      '):
    w = ''.join(f'{wciecie}  <li><span class="chip {c}">{e(ui[f"chip_{k}"])}</span><span>{e(ui[f"opis_{k}"])}</span></li>\n'
                for c, k in PEWNOSC)
    return f'<ul class="{klasa}">\n{w}{wciecie}</ul>'


def tresc_start(J, L):
    ui = J.ui
    wiersze = []
    for h in (J.hist if J.pl else J.pelne):
        kl, klucz = ZRODLA[h['zrodlo']]
        tag = f'<span class="tag {kl}">{e(ui[klucz])}</span>'
        srodek = (f'<span class="yr">{e(h["rok_tekst"])}</span><span class="pl">{e(h["miejsce"])}</span>'
                  f'<div class="tx"><span class="ttl" role="heading" aria-level="3">{e(h["tytul"])}</span>'
                  f'<p class="tsr">{e(h["zajawka"])}</p></div>')
        tem = ' '.join(h['tematy'])
        if h['id'] in J.ids:
            wiersze.append(f'<a class="row" href="{L.historia(h["id"])}" data-tematy="{tem}">{srodek}'
                           f'<span class="mt">{tag}<span class="go">{e(ui["czytaj"])}</span></span></a>')
        else:
            wiersze.append(f'<div class="row soon" data-tematy="{tem}">{srodek}'
                           f'<span class="mt">{tag}<span class="soon-l">{e(ui["w_przygotowaniu"])}</span></span></div>')
    tematy_json = e(json.dumps(J.tematy, ensure_ascii=False))
    nl = '\n      '
    dane = ''.join(f'\n    <span>{d}</span>' for d in ui['dane_html'])
    rubryki = ''.join(f'<span>{r}</span>' for r in ui['rubryki_html'])
    return f'''<section class="wrap" id="tresc">
  <div class="hero">
    <div>
      <p class="eyebrow">{e(ui["hero_eyebrow"])}</p>
      <h1>{ui["hero_h1_html"]}</h1>
      <p class="dek">{e(ui["hero_dek"])}</p>
    </div>
    <figure class="epigraf">
      <blockquote lang="la">{EPIGRAF}</blockquote>
      <p>{e(ui["epigraf_przeklad"])}</p>
      <cite>{e(ui["epigraf_cite"])}</cite>
    </figure>
  </div>
  <div class="dane">{dane}
  </div>
  <p class="odsylacz">{ui["odsylacz_ksiegi_html"].format(ksiegi=L.ksiegi())}</p>
  <div class="sekcja-tyt">
    <h2>{e(ui["historie_h2"])}</h2>
    <p>{e(ui["historie_p"])}</p>
  </div>
  <ul class="filtry" id="filtry" aria-label="{e(ui["tematy_aria"])}" data-tematy="{tematy_json}" data-wszystkie="{e(ui["wszystkie"])}"></ul>
  <div class="rejestr">
    <div class="rubryki" aria-hidden="true">{rubryki}</div>
    <div id="wiersze">
      {nl.join(wiersze)}
    </div>
    <p class="pusto" id="pusto" hidden>{e(ui["pusto"])}</p>
  </div>
  <div class="sekcja-tyt"><h2>{e(ui["jak_czytac_h2"])}</h2></div>
  <div class="dwie">
    <div>
      <h3>{e(ui["skad_h3"])}</h3>
      <ul class="legenda">
        <li><span class="tag t-nowa">{e(ui["zrodlo_nowa"])}</span><span>{e(ui["legenda_nowa"])}</span></li>
        <li><span class="tag t-ksiazka">{e(ui["zrodlo_ksiazka"])}</span><span>{e(ui["legenda_ksiazka"])}</span></li>
        <li><span class="tag t-rodzina">{e(ui["zrodlo_rodzina"])}</span><span>{e(ui["legenda_rodzina"])}</span></li>
      </ul>
    </div>
    <div>
      <h3>{e(ui["pewnosc_h3"])}</h3>
      {lista_pewnosci(ui)}
    </div>
  </div>
</section>'''


def wykres(J, nazwa):
    p = J.kat / 'wykresy' / f'{nazwa}.html'
    if not p.exists():
        p = TRESCI / 'wykresy' / f'{nazwa}.html'
    return p.read_text(encoding='utf-8')


def podstaw(tresc, J, L):
    """Znaczniki w plikach treści → adresy i teksty zależne od wersji (strona / podgląd) i języka."""
    q = J.ui['cudzyslow_tytul']
    # tytuł innej historii w cudzysłowie języka: {{tytul:id}} (tłumaczenia)
    tresc = re.sub(r'\{\{tytul:([a-z0-9-]+)\}\}', lambda m: f'{q[0]}{e(J.tytuly[m.group(1)])}{q[1]}', tresc)
    # odnośniki między historiami: {{historia:id}}
    tresc = re.sub(r'\{\{historia:([a-z0-9-]+)\}\}', lambda m: L.historia(m.group(1)), tresc)
    # pliki strony (ilustracje): {{plik:ilustracje/x.jpg}}
    tresc = re.sub(r'\{\{plik:([A-Za-z0-9_./-]+)\}\}', lambda m: L.plik(m.group(1)), tresc)
    # zakładki strony: {{strona:ksiegi}}, {{strona:o-stronie}}, {{strona:start}}
    strony = {'ksiegi': L.ksiegi, 'o-stronie': L.o, 'start': L.start}
    tresc = re.sub(r'\{\{strona:(ksiegi|o-stronie|start)\}\}', lambda m: strony[m.group(1)](), tresc)
    # wykresy: <!--WYKRES:nazwa--> → tresci/[<język>/]wykresy/nazwa.html (generuje narzedzia/wykresy.py)
    return re.sub(r'<!--WYKRES:([a-z0-9-]+)-->', lambda m: wykres(J, m.group(1)), tresc)


def artykul(J, h, L, kotwica=True):
    ui = J.ui
    tresc = podstaw((J.kat / 'historie' / f'{h["id"]}.html').read_text(encoding='utf-8'), J, L)
    i = J.pelne.index(h)
    pop, nast = J.pelne[i - 1], J.pelne[(i + 1) % len(J.pelne)]
    id_attr = ' id="tresc"' if kotwica else ''
    nota = ''
    if not J.pl and ui.get('nota_tlumaczenia_html'):
        oryg = L.jezyk('pl', f'historie/{h["id"]}.html')
        nota = f'\n  <p class="tl-nota">{ui["nota_tlumaczenia_html"].format(oryginal=oryg)}</p>'
    return f'''<article class="czyt"{id_attr}>
  <a class="wstecz" href="{L.start()}">{e(ui["wstecz"])}</a>
  <p class="eyebrow">{e(h["znacznik"])}</p>
  <h1 tabindex="-1">{e(h["tytul"])}</h1>
  <p class="lead">{e(h["lead"])}</p>{nota}
{tresc}
  <nav class="dalej" aria-label="{e(ui["inne_aria"])}">
    <a href="{L.historia(pop["id"])}"><small>{e(ui["poprzednia"])}</small>{e(pop["tytul"])}</a>
    <a href="{L.historia(nast["id"])}"><small>{e(ui["nastepna"])}</small>{e(nast["tytul"])}</a>
  </nav>
</article>'''


def artykul_o(J, L, kotwica=True):
    ui = J.ui
    p = J.kat / 'o-stronie.html'
    if not p.exists():
        p = TRESCI / 'o-stronie.html'
    tresc = podstaw(p.read_text(encoding='utf-8'), J, L)
    id_attr = ' id="tresc"' if kotwica else ''
    return f'''<article class="czyt"{id_attr}>
  <a class="wstecz" href="{L.start()}">{e(ui["wstecz"])}</a>
  <p class="eyebrow">{e(ui["o_eyebrow"])}</p>
  <h1 tabindex="-1">{e(ui["o_h1"])}</h1>
{tresc}
</article>'''


def artykul_ksiegi(J, L, kotwica=True):
    ui = J.ui
    id_attr = ' id="tresc"' if kotwica else ''
    return f'''<section class="wrap ks-strona"{id_attr}>
  <a class="wstecz" href="{L.start()}">{e(ui["wstecz"])}</a>
  <p class="eyebrow">{e(ui["ksiegi_eyebrow"])}</p>
  <h1 tabindex="-1">{e(ui["ksiegi_h1"])}</h1>
  {dostepnosc_html(ui)}
</section>'''


def adres_strony(J, sciezka):
    return f'{ADRES}/{J.prefiks}{sciezka}'


def glowa(J, tytul, opis, root, sciezka, typ='website', obraz='obrazki/start.png'):
    ui = J.ui
    w = ['<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         f'<title>{e(tytul)}</title>',
         f'<meta name="description" content="{e(opis)}">',
         f'<meta property="og:site_name" content="{e(J.nazwa)}">',
         f'<meta property="og:title" content="{e(tytul)}">',
         f'<meta property="og:description" content="{e(opis)}">',
         f'<meta property="og:type" content="{typ}">',
         f'<meta property="og:locale" content="{ui["og_locale"]}">',
         '<meta name="theme-color" content="#EDF0EB" media="(prefers-color-scheme: light)">',
         '<meta name="theme-color" content="#121614" media="(prefers-color-scheme: dark)">',
         f'<link rel="icon" href="{root}ikona.svg" type="image/svg+xml">']
    if ADRES:
        u = adres_strony(J, sciezka)
        w += [f'<link rel="canonical" href="{e(u)}">', f'<meta property="og:url" content="{e(u)}">']
        if sciezka != '404.html' and len(JEZ) > 1:
            for kod, J2 in JEZ.items():
                if sciezka.startswith('historie/') and sciezka[9:-5] not in J2.ids:
                    continue
                w.append(f'<link rel="alternate" hreflang="{J2.ui["html_lang"]}" href="{e(adres_strony(J2, sciezka))}">')
            w.append(f'<link rel="alternate" hreflang="x-default" href="{e(adres_strony(JEZ["pl"], sciezka))}">')
    if ADRES and (KAT / obraz).exists():
        u = f'{ADRES}/{obraz}'
        w += [f'<meta property="og:image" content="{e(u)}">', '<meta property="og:image:width" content="1200">',
              '<meta property="og:image:height" content="630">', f'<meta property="og:image:alt" content="{e(tytul)}">',
              '<meta name="twitter:card" content="summary_large_image">']
    # czcionki z własnego serwera strony (bez łączenia czytelników z Google)
    w += [f'<link rel="stylesheet" href="{root}fonty/fonty.css">', f'<link rel="stylesheet" href="{root}styl.css">']
    return '\n'.join(w)


def strona(J, tytul, opis, L, sciezka, aktywna, tresc, skrypt='', typ='website', obraz='obrazki/start.png'):
    return f'''<!doctype html>
<html lang="{J.ui["html_lang"]}">
<head>
{glowa(J, tytul, opis, L.plik(''), sciezka, typ, obraz)}
</head>
<body>
{naglowek(J, L, aktywna, sciezka)}
<main>
{tresc}
</main>
{stopka(J)}
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
    shutil.copytree(SZABLONY / 'fonty', DOCS / 'fonty')
    if (KAT / 'obrazki').exists():
        shutil.copytree(KAT / 'obrazki', DOCS / 'obrazki')
    if (KAT / 'ilustracje').exists():
        shutil.copytree(KAT / 'ilustracje', DOCS / 'ilustracje')
    zapisz(DOCS / 'ikona.svg', IKONA)
    zapisz(DOCS / '.nojekyll', '')
    adresy = []
    for J in JEZ.values():
        ui, kat = J.ui, DOCS / J.prefiks
        L0, L1 = Linki(J, 0), Linki(J, 1)
        zapisz(kat / 'index.html',
               strona(J, J.nazwa, J.opis, L0, '', 'historie', tresc_start(J, L0),
                      f'<script src="{L0.plik("lista.js")}"></script>'))
        for h in J.pelne:
            zapisz(kat / 'historie' / f'{h["id"]}.html',
                   strona(J, f'{h["tytul"]} · {J.nazwa}', h['zajawka'], L1, f'historie/{h["id"]}.html', 'historie',
                          artykul(J, h, L1), typ='article', obraz=f'obrazki/{h["id"]}.png'))
        zapisz(kat / 'ksiegi.html',
               strona(J, f'{ui["ksiegi_tytul"]} · {J.nazwa}', ui['ksiegi_opis'], L0, 'ksiegi.html', 'ksiegi',
                      artykul_ksiegi(J, L0)))
        zapisz(kat / 'o-stronie.html',
               strona(J, f'{ui["o_tytul"]} · {J.nazwa}', ui['o_opis'], L0, 'o-stronie.html', 'o', artykul_o(J, L0),
                      KONTAKT_JS))
        adresy += [adres_strony(J, s) for s in ('', 'ksiegi.html', 'o-stronie.html')]
        adresy += [adres_strony(J, f'historie/{h["id"]}.html') for h in J.pelne]
    J = JEZ['pl']
    L = Linki(J, baza=f'{ADRES}/') if ADRES else Linki(J, 0)
    zapisz(DOCS / '404.html',
           strona(J, f'{J.ui["e404_tytul"]} · {J.nazwa}', f'{J.ui["e404_tytul"]}.', L, '404.html', '',
                  f'<section class="wrap czyt" id="tresc"><h1 tabindex="-1">{e(J.ui["e404_tytul"])}</h1>'
                  f'<p>{J.ui["e404_tekst_html"].format(start=L.start())}</p></section>'))
    roboty = 'User-agent: *\nAllow: /\n'
    if ADRES:
        roboty += f'Sitemap: {ADRES}/sitemap.xml\n'
        zapisz(DOCS / 'sitemap.xml',
               '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + ''.join(f'  <url><loc>{e(a)}</loc></url>\n' for a in adresy) + '</urlset>\n')
    zapisz(DOCS / 'robots.txt', roboty)


KONTAKT_JS = '''<script>
/* adres e-mail składany dopiero w przeglądarce, żeby automaty zbierające adresy go nie znalazły */
document.querySelectorAll('.adres[data-u]').forEach(function (s) {
  var a = s.getAttribute('data-u') + '@' + s.getAttribute('data-d');
  var l = document.createElement('a');
  l.href = 'mailto:' + a;
  l.textContent = a;
  s.replaceChildren(l);
});
</script>'''


ROUTER = '''<script>
(function () {
  var PELNE = %s;
  var widoki = { start: document.getElementById('widok-start'), hist: document.getElementById('widok-historia'),
                 o: document.getElementById('widok-o'), ksiegi: document.getElementById('widok-ksiegi') };
  var nav = { historie: document.querySelector('.nav a[href="#"]'), o: document.querySelector('.nav a[href="#o-stronie"]'),
              ksiegi: document.querySelector('.nav a[href="#ksiegi"]') };
  function trasa() {
    var h = decodeURIComponent(location.hash.slice(1));
    Object.keys(widoki).forEach(function (k) { widoki[k].hidden = true; });
    var akt = 'historie';
    if (h === 'o-stronie') { widoki.o.hidden = false; akt = 'o'; }
    else if (h === 'ksiegi') { widoki.ksiegi.hidden = false; akt = 'ksiegi'; }
    else if (PELNE.indexOf(h) >= 0) {
      widoki.hist.replaceChildren(document.getElementById('t-' + h).content.cloneNode(true));
      widoki.hist.hidden = false;
    } else { widoki.start.hidden = false; }
    Object.keys(nav).forEach(function (k) {
      if (!nav[k]) return;
      if (k === akt) nav[k].setAttribute('aria-current', 'page'); else nav[k].removeAttribute('aria-current');
    });
    window.scrollTo(0, 0);
    var h1 = document.querySelector('main > :not([hidden]) h1[tabindex]');
    if (h1 && h) h1.focus({ preventScroll: true });
  }
  window.addEventListener('hashchange', trasa);
  trasa();
})();
</script>'''


def buduj_podglad():
    J = JEZ['pl']
    L = LinkiPodglad(J)
    css = (SZABLONY / 'styl.css').read_text(encoding='utf-8')
    lista_js = (SZABLONY / 'lista.js').read_text(encoding='utf-8')
    szablony = '\n'.join(f'<template id="t-{h["id"]}">\n{artykul(J, h, L, kotwica=False)}\n</template>' for h in J.pelne)
    tekst = f'''<title>{e(J.nazwa)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
{FONTY}
<style>
{css}
</style>
<div class="proto"><div class="wrap">Podgląd · strona nie jest jeszcze w internecie · teksty do przeczytania i poprawek</div></div>
{naglowek(J, L, 'historie', skok=False)}
<main>
<div id="widok-start">
{tresc_start(J, L)}
</div>
<section id="widok-historia" class="wrap" hidden></section>
<section id="widok-o" class="wrap" hidden>
{artykul_o(J, L, kotwica=False)}
</section>
<div id="widok-ksiegi" hidden>
{artykul_ksiegi(J, L, kotwica=False)}
</div>
</main>
{stopka(J)}
{szablony}
<script>
{lista_js}
</script>
{ROUTER % json.dumps([h['id'] for h in J.pelne])}
{KONTAKT_JS}
'''
    zapisz(PODGLAD / 'podglad.html', tekst)


if __name__ == '__main__':
    sprawdz()
    for kod in JEZYKI:
        if Jezyk.gotowy(kod):
            JEZ[kod] = Jezyk(kod)
    buduj_strone()
    buduj_podglad()
    J = JEZ['pl']
    print(f'Gotowe: {len(J.pelne)} historii, {len(J.hist) - len(J.pelne)} w przygotowaniu.')
    for kod, J2 in JEZ.items():
        if not J2.pl:
            print(f'  {kod}: {len(J2.pelne)} z {len(J.pelne)} historii przetłumaczonych')
    print(f'  strona:  {DOCS}')
    print(f'  podgląd: {PODGLAD / "podglad.html"}')
    if not ADRES:
        print('  uwaga: brak "adres" w tresci/spis.json, więc bez canonical, og:url i sitemap.xml')
