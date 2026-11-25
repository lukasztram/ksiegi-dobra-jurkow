#!/usr/bin/env python3
"""Sprawdza tłumaczenia strony względem polskich oryginałów (struktura, znaczniki, cytaty z ksiąg, resztki polszczyzny).

Użycie:
  python3 narzedzia/sprawdz_tlumaczenia.py <jęz> [id ...]   historie (bez id: wszystkie przetłumaczone)
  python3 narzedzia/sprawdz_tlumaczenia.py <jęz> --reszta     ui.json, spis.json, o-stronie.html, wykresy/*.html
Języki: en de fr es zh. Kod wyjścia 1, gdy są błędy (ostrzeżenia nie psują wyniku).
"""
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

KAT = Path(__file__).resolve().parent.parent
T = KAT / 'tresci'
SCISLE = ('figure', 'blockquote', 'a', 'table', 'thead', 'tbody', 'tr', 'td', 'th', 'li', 'ul', 'ol', 'h2', 'h3',
          'div', 'details', 'summary', 'img', 'figcaption', 'section')
LUZNE = ('span', 'em', 'i', 'b', 'strong', 'br', 'sup', 'small', 'abbr', 'cite', 'p')
ZNACZNIKI = re.compile(r'\{\{(?:historia|plik|strona):[^}]+\}\}|<!--WYKRES:[a-z0-9-]+-->')
POLSKIE = re.compile(r'(?<![\w])(się|oraz|który|która|które|było|była|jest|że|ale|przez|przy|już|tylko|kiedy|gdzie|więc|także|jego|jej|ich|roku|lat)(?![\w])', re.I)
ZLE_CUDZ = {'en': '„', 'de': '”', 'fr': '„', 'es': '„', 'zh': '„'}


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.n = Counter(); self.w_cyt = 0; self.cytaty = []; self.poza = []; self.hrefy = Counter(); self.lang_cyt = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.n[tag] += 1
        if tag == 'blockquote':
            self.w_cyt += 1; self.cytaty.append(''); self.lang_cyt.append(a.get('lang'))
        if tag == 'a' and a.get('href') and not a['href'].startswith('{{'):
            self.hrefy[a['href']] += 1

    def handle_endtag(self, tag):
        if tag == 'blockquote':
            self.w_cyt -= 1

    def handle_data(self, d):
        if self.w_cyt > 0:
            self.cytaty[-1] += d
        else:
            self.poza.append(d)


def rozbierz(tekst):
    p = Parser(); p.feed(tekst); p.close(); return p


def porownaj(nazwa, pl_tekst, tl_tekst, jez, ids):
    bledy, ostrz = [], []
    a, b = rozbierz(pl_tekst), rozbierz(tl_tekst)
    for t in SCISLE:
        if a.n[t] != b.n[t]:
            bledy.append(f'<{t}>: oryginał {a.n[t]}, tłumaczenie {b.n[t]}')
    for t in LUZNE:
        if t == 'p':
            dod = b.n['p'] - a.n['p']
            if not 0 <= dod <= a.n['figure']:
                bledy.append(f'<p>: oryginał {a.n["p"]}, tłumaczenie {b.n["p"]} (wolno dodać tylko p.pl-t w wypisach)')
        elif a.n[t] != b.n[t]:
            ostrz.append(f'<{t}>: oryginał {a.n[t]}, tłumaczenie {b.n[t]}')
    za, zb = Counter(ZNACZNIKI.findall(pl_tekst)), Counter(ZNACZNIKI.findall(tl_tekst))
    if za != zb:
        bledy.append(f'znaczniki {{{{…}}}}/WYKRES różne: brak {sorted((za - zb).elements())}, nadmiar {sorted((zb - za).elements())}')
    for m in re.findall(r'\{\{tytul:([^}]+)\}\}', tl_tekst):
        if m not in ids:
            bledy.append(f'nieznany id w {{{{tytul:{m}}}}}')
    if a.hrefy != b.hrefy:
        bledy.append(f'adresy zewnętrzne różne: brak {sorted((a.hrefy - b.hrefy).elements())}, nadmiar {sorted((b.hrefy - a.hrefy).elements())}')
    norm = lambda s: re.sub(r'\s+', ' ', s).strip()
    if [norm(c) for c in a.cytaty] != [norm(c) for c in b.cytaty]:
        for i, (x, y) in enumerate(zip(a.cytaty, b.cytaty)):
            if norm(x) != norm(y):
                bledy.append(f'cytat z księgi nr {i + 1} zmieniony (ma zostać w oryginale): {norm(y)[:80]!r}')
    for i, (x, l) in enumerate(zip(a.cytaty, b.lang_cyt)):
        if not l:
            ostrz.append(f'cytat nr {i + 1} bez atrybutu lang (polski oryginał → lang="pl")')
    poza = ' '.join(b.poza)
    pol = [w for w in POLSKIE.findall(poza) if not (jez == 'de' and w.lower() == 'ich')]   # niem. „ich” = ja
    if jez != 'pl' and len(pol) >= 3:
        bledy.append(f'możliwe resztki polskiego tekstu poza cytatami: {Counter(w.lower() for w in pol).most_common(6)}')
    zly = ZLE_CUDZ.get(jez)
    if zly and zly in poza:
        ostrz.append(f'znak {zly} poza cytatami (cudzysłów niewłaściwy dla języka {jez}?)')
    if jez == 'zh' and len(re.findall(r'[一-鿿]', poza)) < 0.2 * len(re.sub(r'\s', '', poza)):
        bledy.append('mało znaków chińskich poza cytatami — czy tekst jest przetłumaczony?')
    return bledy, ostrz


def wypisz(nazwa, bledy, ostrz):
    if not bledy and not ostrz:
        print(f'OK    {nazwa}')
    for x in bledy:
        print(f'BŁĄD  {nazwa}: {x}')
    for x in ostrz:
        print(f'uwaga {nazwa}: {x}')
    return not bledy


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    jez = sys.argv[1]
    spis = json.loads((T / 'spis.json').read_text(encoding='utf-8'))
    ids = {h['id'] for h in spis['historie']}
    ok = True
    if '--reszta' in sys.argv:
        ui_pl = json.loads((T / 'ui.json').read_text(encoding='utf-8'))
        p = T / jez / 'ui.json'
        if p.exists():
            ui = json.loads(p.read_text(encoding='utf-8'))
            b = [f'brak klucza {k}' for k in ui_pl if k not in ui] + [f'nadmiarowy klucz {k}' for k in ui if k not in ui_pl]
            for k, v in ui_pl.items():
                w = ui.get(k)
                if isinstance(v, list) and (not isinstance(w, list) or len(w) != len(v)):
                    b.append(f'{k}: lista ma mieć {len(v)} elementów')
                if isinstance(v, str) and isinstance(w, str) and v and not k.startswith('_'):   # puste po polsku (nota tłumaczenia) i _opis — bez porównania
                    if set(re.findall(r'\{\w+\}', v)) != set(re.findall(r'\{\w+\}', w)):
                        b.append(f'{k}: inne {{pola}} niż w oryginale')
            if ui.get('nota_tlumaczenia_html') and '{oryginal}' not in ui['nota_tlumaczenia_html']:
                b.append('nota_tlumaczenia_html: brak pola {oryginal} (link do polskiego oryginału)')
            ok &= wypisz('ui.json', b, [])
        else:
            ok &= wypisz('ui.json', ['brak pliku'], [])
        p = T / jez / 'spis.json'
        if p.exists():
            s = json.loads(p.read_text(encoding='utf-8'))
            b = []
            for k in ('nazwa', 'opis', 'tematy', 'historie'):
                if k not in s:
                    b.append(f'brak pola {k}')
            for t in spis['tematy']:
                if not s.get('tematy', {}).get(t['id']):
                    b.append(f'brak tematu {t["id"]}')
            for h in spis['historie']:
                x = s.get('historie', {}).get(h['id'])
                if not x:
                    b.append(f'brak historii {h["id"]}'); continue
                for pole in ('tytul', 'zajawka', 'znacznik', 'lead', 'miejsce', 'rok_tekst'):
                    if not x.get(pole):
                        b.append(f'{h["id"]}: brak pola {pole}')
            ok &= wypisz('spis.json', b, [])
        else:
            ok &= wypisz('spis.json', ['brak pliku'], [])
        p = T / jez / 'o-stronie.html'
        if p.exists():
            ok &= wypisz('o-stronie.html', *porownaj('o-stronie', (T / 'o-stronie.html').read_text(encoding='utf-8'),
                                                       p.read_text(encoding='utf-8'), jez, ids))
        else:
            ok &= wypisz('o-stronie.html', ['brak pliku'], [])
        for w in sorted((T / 'wykresy').glob('*.html')):
            p = T / jez / 'wykresy' / w.name
            if p.exists():
                bl, os_ = porownaj(w.name, w.read_text(encoding='utf-8'), p.read_text(encoding='utf-8'), jez, ids)
                bl = [x for x in bl if 'mało znaków chińskich' not in x]     # wykresy to głównie liczby
                ok &= wypisz(f'wykresy/{w.name}', bl, [x for x in os_ if 'lang' not in x])
            else:
                ok &= wypisz(f'wykresy/{w.name}', ['brak pliku'], [])
    else:
        wybrane = [a for a in sys.argv[2:] if not a.startswith('-')] or \
                  sorted(p.stem for p in (T / jez / 'historie').glob('*.html'))
        for hid in wybrane:
            p = T / jez / 'historie' / f'{hid}.html'
            if not p.exists():
                ok &= wypisz(hid, ['brak pliku'], []); continue
            ok &= wypisz(hid, *porownaj(hid, (T / 'historie' / f'{hid}.html').read_text(encoding='utf-8'),
                                         p.read_text(encoding='utf-8'), jez, ids))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
