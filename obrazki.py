#!/usr/bin/env python3
"""Obrazki do podglądu linków (Facebook, komunikatory): 1200 × 630 px, po jednym na historię i na stronę główną.

Wynik: obrazki/<id>.png i obrazki/start.png — buduj.py kopiuje je do docs/obrazki/ i dopisuje og:image.
Wymaga Pillow (jest w systemowym python3). Użycie:  python3 obrazki.py
"""
import html
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KAT = Path(__file__).resolve().parent
CZ = KAT / 'narzedzia' / 'czcionki'
WYNIK = KAT / 'obrazki'
W, H, M = 1200, 630, 72
PAPIER, ATRAMENT, ATRAMENT2, SWIERK, GALAS = '#EDF0EB', '#1D2320', '#4E5751', '#2C5A4B', '#7A5430'


def f(nazwa, rozmiar):
    return ImageFont.truetype(str(CZ / nazwa), rozmiar)


def zawin(tekst, czcionka, szer):
    linie, biezaca = [], ''
    for slowo in tekst.split():
        proba = f'{biezaca} {slowo}'.strip()
        if czcionka.getlength(proba) <= szer or not biezaca:
            biezaca = proba
        else:
            linie.append(biezaca)
            biezaca = slowo
    if biezaca:
        linie.append(biezaca)
    return linie


def skroc(linie, ile, czcionka, szer):
    if len(linie) <= ile:
        return linie
    linie = linie[:ile]
    ost = linie[-1]
    while czcionka.getlength(ost + '…') > szer and ' ' in ost:
        ost = ost.rsplit(' ', 1)[0]
    linie[-1] = ost.rstrip(',;:') + '…'
    return linie


def rozstrzelony(d, xy, tekst, czcionka, kolor, odstep=2.2):
    x, y = xy
    for ch in tekst:
        d.text((x, y), ch, font=czcionka, fill=kolor)
        x += czcionka.getlength(ch) + odstep


def znak(d, x, y, s=64):
    """Ten sam znak co ikona strony: zielony kwadrat z kartą księgi."""
    k = s / 64
    d.rounded_rectangle([x, y, x + s, y + s], radius=12 * k, fill=SWIERK)
    d.rounded_rectangle([x + 18 * k, y + 14 * k, x + 46 * k, y + 50 * k], radius=6 * k, fill=PAPIER)
    for yy, dl in ((24, 16), (31, 16), (38, 11)):
        d.line([x + 24 * k, y + yy * k, x + (24 + dl) * k, y + yy * k], fill=GALAS, width=max(2, round(2.5 * k)))


def obrazek(sciezka, tytul, podtytul, meta, cytat):
    im = Image.new('RGB', (W, H), PAPIER)
    d = ImageDraw.Draw(im)
    rozstrzelony(d, (M, M - 6), 'CO MÓWIĄ KSIĘGI PARAFII DOBRA I JURKÓW', f('ibm-plex-mono-normal-500.ttf', 21), ATRAMENT2)
    znak(d, W - M - 64, M - 26)
    d.line([M, 122, W - M, 122], fill=ATRAMENT, width=2)
    szer = W - 2 * M
    # tytuł: największy rozmiar, przy którym mieści się w trzech liniach
    for rozm in range(96, 52, -4):
        ft = f('bodoni-moda-normal-500.ttf', rozm)
        linie = zawin(tytul, ft, szer)
        if len(linie) <= (2 if podtytul else 3):
            break
    y = 150
    for linia in linie:
        d.text((M - 3, y), linia, font=ft, fill=ATRAMENT)
        y += int(rozm * 1.08)
    if podtytul:
        fp = f('bodoni-moda-italic-400.ttf', int(rozm * 0.62))
        d.text((M - 2, y + 2), podtytul, font=fp, fill=SWIERK)
        y += int(rozm * 0.82)
    fm = f('ibm-plex-mono-normal-500.ttf', 23)
    d.text((M, y + 30), meta, font=fm, fill=ATRAMENT2)
    if cytat:
        fc = f('bodoni-moda-italic-400.ttf', 34)
        lc = skroc(zawin(cytat, fc, szer), 2, fc, szer)
        yc = H - M - 44 * len(lc) - 46
        d.line([M, yc - 18, W - M, yc - 18], fill=GALAS, width=1)
        for linia in lc:
            d.text((M, yc), linia, font=fc, fill=GALAS)
            yc += 44
    fa = f('ibm-plex-mono-normal-500.ttf', 19)
    adres = 'lukasztram.github.io/ksiegi-dobra-jurkow'
    d.text((W - M - fa.getlength(adres), H - M + 12), adres, font=fa, fill=ATRAMENT2)
    im.save(sciezka, optimize=True)


def pierwszy_cytat(plik):
    m = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', plik.read_text(encoding='utf-8'), re.S)
    if not m:
        return ''
    return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()


def main():
    spis = json.loads((KAT / 'tresci' / 'spis.json').read_text(encoding='utf-8'))
    WYNIK.mkdir(exist_ok=True)
    obrazek(WYNIK / 'start.png', 'Co mówią księgi', 'parafii Dobra i Jurków',
            'Prawdziwe historie z ksiąg metrykalnych · 1678–1926',
            'Incipit Liber Metrices post combustionem Ecclesiae')
    n = 1
    for h in spis['historie']:
        if not h['gotowa']:
            continue
        cytat = h.get('cytat_obrazek') or pierwszy_cytat(KAT / 'tresci' / 'historie' / f'{h["id"]}.html')
        obrazek(WYNIK / f'{h["id"]}.png', h['tytul'], '', f'{h["miejsce"]} · {h["rok_tekst"]}', cytat)
        n += 1
    print(f'Gotowe: {n} obrazków w {WYNIK}')


if __name__ == '__main__':
    main()
