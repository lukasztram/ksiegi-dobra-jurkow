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
            fokus=True, os_x=None, wiersze=None):
    """Wykres kolumnowy. kroki: wartości linii siatki (ostatnia = góra skali).
    os_x: krótsze podpisy pod osią (np. rzymskie miesiące); wiersze: własne wiersze tabeli."""
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
                  for i, e in enumerate(os_x or etykiety))
    tresc = (f'<figure class="wykres">\n<p class="wk-tyt">{html.escape(tytul)}</p>\n'
             f'<div class="wk-plot"><div class="wk-siatka" aria-hidden="true">{siatka}</div>'
             f'<div class="wk-slupki">{"".join(sl)}</div></div>\n'
             f'<div class="wk-osx" aria-hidden="true">{osx}</div>\n'
             f'<figcaption>{opis}</figcaption>\n'
             f'{_tabela(nagl, wiersze or zip(etykiety, wartosci))}\n</figure>\n')
    (WYJ / f'{nazwa}.html').write_text(tresc, encoding='utf-8')


def kratki(nazwa, tytul, grupy, opis, nagl, wiersze):
    """Sto kratek (10 × 10) dla „ze stu dzieci…”. grupy: [(liczba, klasa, podpis)], razem 100."""
    assert sum(g[0] for g in grupy) == 100
    kr = ''.join(f'<i class="{k}"></i>' * n for n, k, _ in grupy)
    opis_aria = '; '.join(f'{n} {p}' for n, _, p in grupy)
    leg = ''.join(f'<li><i class="{k}"></i><b>{n}</b><span>{html.escape(p)}</span></li>' for n, k, p in grupy)
    tresc = (f'<figure class="wykres">\n<p class="wk-tyt">{html.escape(tytul)}</p>\n'
             f'<div class="wk-kr-uklad"><div class="wk-kratki" role="img" aria-label="{html.escape(opis_aria)}">{kr}</div>'
             f'<ul class="wk-leg">{leg}</ul></div>\n'
             f'<figcaption>{opis}</figcaption>\n'
             f'{_tabela(nagl, wiersze)}\n</figure>\n')
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

    # Pierwszy rok życia: Dobra 1840–1879, Jurków, Chyszówki, Półrzeczki 1840–1889; księgi główne.
    # 5110 chrztów (bez martwo urodzonych), 1043 zgony przed 1. urodzinami, 618 w wieku 1–4 lat.
    kratki('pierwszy-rok-sto-dzieci', 'Ze stu dzieci urodzonych w latach 1840–1889',
           [(20, 'k1', 'zmarło przed pierwszymi urodzinami'), (12, 'k2', 'zmarło w wieku od roku do pięciu lat'),
            (68, 'k3', 'dożyło piątych urodzin')],
           'Dobra, Jurków, Chyszówki i Półrzeczki: 5110 ochrzczonych dzieci i zgony dzieci zapisane w tych samych '
           'latach w księgach zmarłych tych wsi.',
           ['Grupa', 'Dzieci', 'Na 100 urodzonych'],
           [('ochrzczone (urodzone żywe)', 5110, '100'), ('zmarłe przed 1. urodzinami', 1043, '20,4'),
            ('zmarłe w wieku od roku do 5 lat', 618, '12,1'), ('martwo urodzone (osobno)', 237, '4,6')])
    poziome('pierwszy-rok-wiek', 'W jakim wieku umierały niemowlęta, 1840–1889',
            ['1. tydzień', '2.–4. tydzień', '2.–3. miesiąc', '4.–6. miesiąc', '7.–12. miesiąc'],
            [15.4, 27.2, 21.3, 14.5, 21.5], [160, 283, 222, 151, 224],
            'Na 100 zmarłych niemowląt (1040 zgonów z zapisanym wiekiem). Przedziały są różnej długości: '
            'pierwszy tydzień to siedem dni, ostatni przedział to pół roku.',
            ['Wiek', 'Zgony', 'Udział'])

    # Kalendarz narodzin: chrzty z ksiąg głównych 1678–1909 (19 295), data urodzenia, a gdy jej brak, data chrztu.
    ur = [1992, 1833, 1875, 1767, 1723, 1435, 1314, 1366, 1372, 1546, 1513, 1559]
    dni = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    srednio = sum(ur) / 365.25
    ind = [round(100 * u / d / srednio) for u, d in zip(ur, dni)]
    kolumny('narodziny-miesiace', 'Urodzenia według miesięcy, 1678–1909', nazwy, ind, [0, 50, 100, 150],
            'Ile dzieci rodziło się w danym miesiącu w porównaniu z przeciętnym miesiącem (100 = przeciętnie). '
            'Przeliczone na jednakową długość miesiąca; 19 295 dzieci z odczytanych ksiąg chrztów. '
            'Najedź na słupek albo go dotknij, żeby zobaczyć wartość.',
            ['Miesiąc', 'Urodzenia', 'Na 100 przeciętnie'], podpisz=(0, 1, 6), os_x=mies,
            wiersze=list(zip(nazwy, ur, ind)))

    # Wdowy i wdowcy: śluby z lat 1786–1899 ze znanym stanem cywilnym obojga (2840), księgi bez duplikatów.
    poziome('wdowy-pary', 'Kto brał ślub, 1786–1899',
            ['kawaler i panna', 'wdowiec i panna', 'kawaler i wdowa', 'wdowiec i wdowa'],
            [61.5, 18.8, 12.6, 7.1], [1747, 535, 357, 201],
            'Na 100 ślubów (2840 ślubów, przy których ksiądz zaznaczył stan cywilny obojga nowożeńców).',
            ['Para', 'Śluby', 'Udział'])

    # Śmierć przy porodzie: zamężne kobiety 20–44 lat, cztery wsie, lata objęte księgami chrztów i zmarłych, 1786–1896.
    kratki('porod-sto-kobiet', 'Ze stu zamężnych kobiet, które zmarły w wieku 20–44 lat',
           [(18, 'k1', 'zmarło przy porodzie albo w połogu'), (82, 'k3', 'zmarło z innych przyczyn')],
           'Dobra, Jurków, Chyszówki i Półrzeczki, 1786–1896: 314 zgonów zamężnych kobiet w tym wieku, '
           'z tego 56 przy porodzie albo w ciągu sześciu tygodni po nim.',
           ['Zgony', 'Liczba', 'Na 100'],
           [('zamężne kobiety, 20–44 lat', 314, '100'), ('przy porodzie albo w połogu', 56, '17,8')])
    print('Zapisano wykresy w', WYJ)


if __name__ == '__main__':
    main()
