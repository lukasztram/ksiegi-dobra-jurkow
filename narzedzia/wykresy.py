#!/usr/bin/env python3
"""Wykresy do historii: proste słupki w HTML/CSS (bez bibliotek, bez obrazków).

Zapisuje gotowe fragmenty HTML do tresci/wykresy/<nazwa>.html. W treści historii
wstawia się je znacznikiem <!--WYKRES:nazwa-->, który podmienia buduj.py.
Liczby policzono z bazy Metryk (odczyty ksiąg parafii Dobra), stan na listopad 2026.

Użycie:  python3 narzedzia/wykresy.py
"""
import html
from pathlib import Path

WYJ = Path(__file__).resolve().parent.parent / 'tresci' / 'wykresy'


def _tabela(nagl, wiersze):
    th = ''.join(f'<th>{html.escape(n)}</th>' for n in nagl)
    tr = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(c))}</td>' for c in w) + '</tr>' for w in wiersze)
    return (f'<details class="wk-tab"><summary>Liczby w tabeli</summary><div class="tab-wrap">'
            f'<table class="tabela"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></details>')


def kolumny(nazwa, tytul, etykiety, wartosci, kroki, opis, nagl, pokaz_x=None, podpisz=(), sufiks='',
            fokus=True):
    """Wykres kolumnowy. kroki: wartości linii siatki (ostatnia = góra skali)."""
    gora = kroki[-1]
    siatka = ''.join(f'<span style="bottom:{100 * k / gora:.2f}%"><em>{k}</em></span>' for k in kroki)
    sl = []
    for i, (e, v) in enumerate(zip(etykiety, wartosci)):
        brzeg = max(2, round(len(etykiety) * 0.15))   # dymki przy brzegach wyrównane do środka wykresu
        kl = 'wk-k' + (' l' if i < brzeg else ' p' if i >= len(etykiety) - brzeg else '')
        opis_v = f'{e}{sufiks}: {v}'
        tab = ' tabindex="0"' if fokus else ''
        b = f'<b>{v}</b>' if i in podpisz else ''
        sl.append(f'<span class="{kl}"{tab} style="--h:{100 * v / gora:.2f}%" data-v="{html.escape(opis_v)}" '
                  f'aria-label="{html.escape(opis_v)}"><i></i>{b}</span>')
    osx = ''.join(f'<span>{html.escape(e) if (pokaz_x is None or i in pokaz_x) else ""}</span>'
                  for i, e in enumerate(etykiety))
    tresc = (f'<figure class="wykres">\n<p class="wk-tyt">{html.escape(tytul)}</p>\n'
             f'<div class="wk-plot"><div class="wk-siatka" aria-hidden="true">{siatka}</div>'
             f'<div class="wk-slupki">{"".join(sl)}</div></div>\n'
             f'<div class="wk-osx" aria-hidden="true">{osx}</div>\n'
             f'<figcaption>{opis}</figcaption>\n'
             f'{_tabela(nagl, zip(etykiety, wartosci))}\n</figure>\n')
    (WYJ / f'{nazwa}.html').write_text(tresc, encoding='utf-8')


def _proc(p):
    """Procent po polsku: całe liczby, poniżej 1% z jednym miejscem po przecinku."""
    return f'{p:.1f}%'.replace('.', ',') if p < 1 else f'{p:.0f}%'


def poziome(nazwa, tytul, etykiety, procenty, liczby, opis, nagl):
    """Poziome słupki z procentem przy końcu słupka."""
    wiersze = ''.join(
        f'<div class="wk-w"><span class="wk-n">{html.escape(e)}</span>'
        f'<span class="wk-b"><i style="--w:{p / 100:.4f}"></i><b>{_proc(p)}</b></span></div>'
        for e, p in zip(etykiety, procenty))
    tresc = (f'<figure class="wykres">\n<p class="wk-tyt">{html.escape(tytul)}</p>\n'
             f'<div class="wk-poz">{wiersze}</div>\n<figcaption>{opis}</figcaption>\n'
             f'{_tabela(nagl, [(e, n, f"{p:.1f}%") for e, n, p in zip(etykiety, liczby, procenty)])}\n</figure>\n')
    (WYJ / f'{nazwa}.html').write_text(tresc, encoding='utf-8')


def main():
    WYJ.mkdir(exist_ok=True)
    mies = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
    nazwy = ['styczeń', 'luty', 'marzec', 'kwiecień', 'maj', 'czerwiec', 'lipiec', 'sierpień', 'wrzesień',
             'październik', 'listopad', 'grudzień']
    sluby = [488, 1538, 71, 22, 214, 225, 241, 188, 198, 232, 705, 7]   # 1682–1943, 4129 ślubów z datą
    kolumny('wesela-miesiace', 'Śluby według miesięcy, 1682–1943', nazwy, sluby, [0, 400, 800, 1200, 1600],
            'Liczba ślubów w każdym miesiącu, z odczytanych ksiąg parafii (4129 ślubów z pełną datą). '
            'Najedź na słupek albo go dotknij, żeby zobaczyć liczbę.',
            ['Miesiąc', 'Śluby'], podpisz=(1, 10, 11))
    # podpisy pod osią: rzymskie numery miesięcy
    p = WYJ / 'wesela-miesiace.html'
    t = p.read_text(encoding='utf-8')
    for n, r in zip(nazwy, mies):
        t = t.replace(f'<span>{n}</span>', f'<span>{r}</span>', 1)
    p.write_text(t, encoding='utf-8')

    wiek = [114, 16, 37, 20, 23, 64, 52, 10, 32, 13, 160, 9, 31, 35, 10, 92, 51, 19, 36, 16, 191, 12, 26, 29, 41,
            31, 67, 27, 46, 17, 269, 24, 42, 41, 39, 54, 33, 30, 55, 25, 245, 14, 22, 23, 12, 29, 25, 6, 9, 10,
            120, 9, 7, 5, 8, 16, 6, 3, 0, 7, 30, 1, 3, 2, 0, 4, 4, 1, 1, 1, 2]   # zgony 1779–1849, wiek 30–100
    lata = [str(a) for a in range(30, 101)]
    kolumny('wiek-na-oko', 'Wiek zmarłych dorosłych zapisany w księgach, 1779–1849', lata, wiek,
            [0, 100, 200, 300],
            'Ilu zmarłych w wieku od 30 do 100 lat ksiądz zapisał z danym wiekiem (2564 osoby). '
            'Wysokie słupki to lata okrągłe: 40, 50, 60, 70, 80.',
            ['Wiek', 'Zmarli'], pokaz_x={0, 10, 20, 30, 40, 50, 60}, podpisz=(30, 40), sufiks=' lat',
            fokus=False)

    poziome('cwierc-roli', 'Kim byli ojcowie ochrzczonych dzieci, 1820–1879',
            ['¼ kmiecia', '½ kmiecia', '⅛ kmiecia', 'komornik', '⅓ kmiecia', '⅙ kmiecia', 'zagrodnik',
             'cały kmieć'],
            [63.7, 13.6, 9.3, 8.1, 2.6, 1.2, 1.1, 0.3], [3102, 661, 452, 394, 128, 60, 54, 17],
            'Jak ksiądz zapisał stan ojca przy chrzcie (4868 chrztów z takim dopiskiem).',
            ['Stan ojca', 'Chrzty', 'Udział'])
    print('Zapisano wykresy w', WYJ)


if __name__ == '__main__':
    main()
