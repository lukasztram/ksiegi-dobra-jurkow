"""Sekcja „Jakie księgi się zachowały”: osie czasu ksiąg dla każdej wsi.

Dane: tresci/dostepnosc.json (tworzy go eksport_dostepnosci.py z bazy Fototeki).
Używa go buduj.py. Tylko biblioteka standardowa.
"""
import html
import json
from pathlib import Path

PLIK = Path(__file__).resolve().parent / 'tresci' / 'dostepnosc.json'
OS_OD, OS_DO = 1675, 1945
ZNACZNIKI_LAT = (1700, 1750, 1800, 1850, 1900)
TYPY = [('U', 'Chrzty'), ('M', 'Śluby'), ('Z', 'Zgony')]
STAN = {'odczytana': ('s-odcz', 'odczytana'), 'czesciowo': ('s-czes', 'odczytana częściowo'),
        'nieodczytana': ('s-nie', 'czeka na odczyt')}
KOLEJ = {'nieodczytana': 0, 'czesciowo': 1, 'odczytana': 2}     # odczytane rysowane na wierzchu
MIESIACE = ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia',
            'września', 'października', 'listopada', 'grudnia']


def e(s):
    return html.escape(str(s), quote=True)


def _x(rok):
    return (rok - OS_OD) / (OS_DO - OS_OD) * 100


def _liczba(n):
    return f'{n:,}'.replace(',', ' ')


def _lata(k):
    return f'{k["od"]}–{k["do"]}' if k['do'] != k['od'] else str(k['od'])


def _pasek(ksiegi, typ, nazwa_typu):
    out = []
    for k in sorted((k for k in ksiegi if typ in k['typy']), key=lambda k: KOLEJ[k['status']]):
        lewa = _x(k['od'])
        szer = max(_x(k['do'] + 1) - lewa, 0.7)
        kl, opis = STAN[k['status']]
        tyt = f'{nazwa_typu} {_lata(k)} · sygn. {k["sygn"]}'
        if k['odpis']:
            tyt += ' (odpis)'
        tyt += f' · {opis}'
        if k['wpisy']:
            tyt += f', {_liczba(k["wpisy"])} wpisów'
        href = k['url'] or 'https://metryki.genealodzy.pl/'
        out.append(f'<a class="seg {kl}" style="left:{lewa:.2f}%;width:{szer:.2f}%" href="{e(href)}" '
                   f'target="_blank" rel="noopener" title="{e(tyt)}" aria-label="{e(tyt)}"></a>')
    return ''.join(out)


def _blok(nazwa, podpis, ksiegi):
    ticks = ''.join(f'<span class="tick" style="left:{_x(r):.2f}%">{r}</span>' for r in ZNACZNIKI_LAT)
    pasy = ''.join(f'<div class="pas"><span class="pas-l">{n}</span><div class="tor">{_pasek(ksiegi, t, n)}</div></div>'
                   for t, n in TYPY)
    return (f'<div class="wies"><div class="wies-n"><h3>{e(nazwa)}</h3><span>{e(podpis)}</span></div>'
            f'<div class="os" aria-hidden="true"><span></span><div class="tor">{ticks}</div></div>{pasy}</div>')


def _siatka():
    czesci = []
    for rok in ZNACZNIKI_LAT:
        p = f'{_x(rok):.2f}%'
        czesci.append(f'linear-gradient(to right, transparent calc({p} - .5px), var(--siatka-kolor) calc({p} - .5px), '
                      f'var(--siatka-kolor) calc({p} + .5px), transparent calc({p} + .5px))')
    return ', '.join(czesci)


def dostepnosc_html():
    if not PLIK.exists():
        return ''
    d = json.loads(PLIK.read_text(encoding='utf-8'))
    r, m, dz = (int(x) for x in d['stan_na'].split('-'))
    stan = f'{dz} {MIESIACE[m - 1]} {r}'
    grupy = [('Cała parafia', 'księgi wspólne do 1786 i odpisy roczne', d['wspolne'])]
    grupy += [(w['nazwa'], f'{_liczba(w["wpisy"])} wpisów w bazie', w['ksiegi']) for w in d['wsie']]
    bloki = ''.join(_blok(n, p, k) for n, p, k in grupy)
    wiersze = []
    for nazwa, _, ksiegi in grupy:
        for k in sorted(ksiegi, key=lambda k: (k['od'], k['sygn'])):
            rodzaj = ', '.join(n.lower() for t, n in TYPY if t in k['typy'])
            if k['odpis']:
                rodzaj += ' (odpis)'
            kl, opis = STAN[k['status']]
            syg = (f'<a href="{e(k["url"])}" target="_blank" rel="noopener">{e(k["sygn"])}</a>'
                   if k['url'] else e(k['sygn']))
            wiersze.append(f'<tr><td>{e(nazwa)}</td><td>{e(rodzaj)}</td><td class="num">{_lata(k)}</td>'
                           f'<td>{syg}</td><td><span class="lg {kl}"></span>{opis}</td></tr>')
    return (
        f'<section class="dost" id="ksiegi" style="--siatka: {_siatka()}">\n'
        '  <div class="sekcja-tyt">\n'
        '    <h2>Jakie księgi się zachowały</h2>\n'
        '    <p>Księgi chrztów, ślubów i zgonów każdej wsi w serwisie Metryki PTG i to, ile z nich jest już odczytane. '
        'Puste miejsca na osi to lata bez skanów w sieci. Takie księgi mogą jeszcze leżeć w kancelarii parafii albo w archiwum.</p>\n'
        '  </div>\n'
        '  <ul class="legenda-ks">\n'
        '    <li><span class="lg s-odcz"></span>odczytane</li>\n'
        '    <li><span class="lg s-czes"></span>odczytane częściowo</li>\n'
        '    <li><span class="lg s-nie"></span>skany w sieci, czekają na odczyt</li>\n'
        '    <li><span class="lg s-brak"></span>brak skanów w sieci</li>\n'
        '  </ul>\n'
        f'  <div class="wiesy">{bloki}</div>\n'
        '  <details class="spis-ksiag">\n'
        '    <summary>Spis wszystkich ksiąg z sygnaturami</summary>\n'
        '    <div class="tab-wrap"><table>\n'
        '      <thead><tr><th>Miejscowość</th><th>Księga</th><th>Lata</th><th>Sygnatura i skany</th><th>Stan</th></tr></thead>\n'
        f'      <tbody>{"".join(wiersze)}</tbody>\n'
        '    </table></div>\n'
        '  </details>\n'
        f'  <p class="stan-na">Stan na {stan}. Kliknij odcinek na osi albo sygnaturę w spisie, żeby otworzyć skany księgi.</p>\n'
        '</section>'
    )
