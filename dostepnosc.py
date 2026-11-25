"""Zakładka „Księgi”: osie czasu ksiąg dla każdej wsi parafii Dobra i Jurków oraz dla sąsiednich parafii.

Dane: tresci/dostepnosc.json (tworzy go eksport_dostepnosci.py z bazy Fototeki).
Napisy: słownik ui z tresci/ui.json albo tresci/<język>/ui.json. Używa go buduj.py. Tylko biblioteka standardowa.
"""
import html
import json
from pathlib import Path

PLIK = Path(__file__).resolve().parent / 'tresci' / 'dostepnosc.json'
OS_OD, OS_DO = 1610, 1945          # od najstarszej księgi Słopnic (1618) do najmłodszych ksiąg Dobrej (1944)
ZNACZNIKI_LAT = (1650, 1700, 1750, 1800, 1850, 1900)
TYPY = ('U', 'M', 'Z')
KLASA = {'odczytana': 's-odcz', 'czesciowo': 's-czes', 'nieodczytana': 's-nie'}
KOLEJ = {'nieodczytana': 0, 'czesciowo': 1, 'odczytana': 2}     # odczytane rysowane na wierzchu


def e(s):
    return html.escape(str(s), quote=True)


def _x(rok):
    return (rok - OS_OD) / (OS_DO - OS_OD) * 100


def liczba(n, ui):
    return f'{n:,}'.replace(',', ui['separator_tysiecy'])


def data(iso, ui):
    r, m, d = (int(x) for x in iso.split('-'))
    return ui['data'].format(d=d, m=ui['miesiace'][m - 1], r=r)


def _lata(k):
    return f'{k["od"]}–{k["do"]}' if k['do'] != k['od'] else str(k['od'])


def _stan(status, ui):
    return ui[{'odczytana': 'stan_odczytana', 'czesciowo': 'stan_czesciowo', 'nieodczytana': 'stan_nieodczytana'}[status]]


def _pasek(ksiegi, typ, ui):
    out = []
    nazwa_typu = ui[f'typ_{typ}']
    for k in sorted((k for k in ksiegi if typ in k['typy']), key=lambda k: KOLEJ[k['status']]):
        lewa = _x(k['od'])
        szer = max(_x(k['do'] + 1) - lewa, 0.7)
        tyt = f'{nazwa_typu} {_lata(k)} · {ui["sygn"]} {k["sygn"]}'
        if k['odpis']:
            tyt += f' ({ui["odpis"]})'
        tyt += f' · {_stan(k["status"], ui)}'
        if k['wpisy']:
            tyt += ', ' + ui['wpisow'].format(n=liczba(k['wpisy'], ui))
        href = k['url'] or 'https://metryki.genealodzy.pl/'
        out.append(f'<a class="seg {KLASA[k["status"]]}" style="left:{lewa:.2f}%;width:{szer:.2f}%" href="{e(href)}" '
                   f'target="_blank" rel="noopener" title="{e(tyt)}" aria-label="{e(tyt)}"></a>')
    return ''.join(out)


def _blok(nazwa, podpis, ksiegi, ui):
    ticks = ''.join(f'<span class="tick" style="left:{_x(r):.2f}%">{r}</span>' for r in ZNACZNIKI_LAT)
    pasy = ''.join(f'<div class="pas"><span class="pas-l">{e(ui[f"typ_{t}"])}</span><div class="tor">{_pasek(ksiegi, t, ui)}</div></div>'
                   for t in TYPY)
    return (f'<div class="wies"><div class="wies-n"><h3>{e(nazwa)}</h3><span>{e(podpis)}</span></div>'
            f'<div class="os" aria-hidden="true"><span></span><div class="tor">{ticks}</div></div>{pasy}</div>')


def _siatka():
    czesci = []
    for rok in ZNACZNIKI_LAT:
        p = f'{_x(rok):.2f}%'
        czesci.append(f'linear-gradient(to right, transparent calc({p} - .5px), var(--siatka-kolor) calc({p} - .5px), '
                      f'var(--siatka-kolor) calc({p} + .5px), transparent calc({p} + .5px))')
    return ', '.join(czesci)


def _wiersze(grupy, ui, dopisek=''):
    out = []
    for nazwa, _, ksiegi in grupy:
        miejsce = f'{nazwa} ({dopisek})' if dopisek else nazwa
        for k in sorted(ksiegi, key=lambda k: (k['od'], k['sygn'])):
            # po niemiecku rzeczowniki zostają wielką literą
            rodzaj = ', '.join(ui[f'typ_{t}'] if ui.get('jezyk') == 'de' else ui[f'typ_{t}'].lower() for t in TYPY if t in k['typy'])
            if k['odpis']:
                rodzaj += f' ({ui["odpis"]})'
            syg = (f'<a href="{e(k["url"])}" target="_blank" rel="noopener">{e(k["sygn"])}</a>'
                   if k['url'] else e(k['sygn']))
            out.append(f'<tr><td>{e(miejsce)}</td><td>{e(rodzaj)}</td><td class="num">{_lata(k)}</td>'
                       f'<td>{syg}</td><td><span class="lg {KLASA[k["status"]]}"></span>{e(_stan(k["status"], ui))}</td></tr>')
    return out


def dane():
    return json.loads(PLIK.read_text(encoding='utf-8')) if PLIK.exists() else None


def dostepnosc_html(ui):
    d = dane()
    if not d:
        return ''
    dobra = [(ui['cala_parafia'], ui['cala_parafia_podpis'], d['wspolne'])]
    dobra += [(w['nazwa'], ui['wpisow_w_bazie'].format(n=liczba(w['wpisy'], ui)), w['ksiegi']) for w in d['wsie']]
    sas = [(p['nazwa'], ui['wpisow_w_bazie'].format(n=liczba(p['wpisy'], ui)), p['ksiegi']) for p in d.get('sasiednie', [])]
    wiersze = _wiersze(dobra, ui) + _wiersze(sas, ui, ui['sasiednia_parafia'])
    th = ''.join(f'<th>{e(t)}</th>' for t in ui['th'])
    sas_html = ''
    if sas:
        sas_html = (f'  <h2 class="ks-h2">{e(ui["ksiegi_sasiednie_h2"])}</h2>\n'
                    f'  <p class="ks-p">{e(ui["ksiegi_sasiednie_p"])}</p>\n'
                    f'  <div class="wiesy">{"".join(_blok(n, p, k, ui) for n, p, k in sas)}</div>\n')
    return (
        f'<section class="dost" id="ksiegi" style="--siatka: {_siatka()}">\n'
        f'  <p class="ks-p">{e(ui["ksiegi_wstep"])}</p>\n'
        '  <ul class="legenda-ks">\n'
        f'    <li><span class="lg s-odcz"></span>{e(ui["leg_odczytane"])}</li>\n'
        f'    <li><span class="lg s-czes"></span>{e(ui["leg_czesciowo"])}</li>\n'
        f'    <li><span class="lg s-nie"></span>{e(ui["leg_czeka"])}</li>\n'
        f'    <li><span class="lg s-brak"></span>{e(ui["leg_brak"])}</li>\n'
        '  </ul>\n'
        f'  <h2 class="ks-h2">{e(ui["ksiegi_dobra_h2"])}</h2>\n'
        f'  <div class="wiesy">{"".join(_blok(n, p, k, ui) for n, p, k in dobra)}</div>\n'
        f'{sas_html}'
        '  <details class="spis-ksiag">\n'
        f'    <summary>{e(ui["spis_summary"])}</summary>\n'
        '    <div class="tab-wrap"><table>\n'
        f'      <thead><tr>{th}</tr></thead>\n'
        f'      <tbody>{"".join(wiersze)}</tbody>\n'
        '    </table></div>\n'
        '  </details>\n'
        f'  <p class="stan-na">{e(ui["stan_na"].format(data=data(d["stan_na"], ui)))}</p>\n'
        '</section>'
    )
