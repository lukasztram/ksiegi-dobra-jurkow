#!/usr/bin/env python3
"""Spisuje, jakie księgi metrykalne parafii Dobra są w serwisie Metryki PTG i ile z nich jest już odczytane.

Czyta bazę Fototeki TYLKO DO ODCZYTU i zapisuje tresci/dostepnosc.json, z którego buduj.py
rysuje na stronie osie czasu „Jakie księgi się zachowały” (zakładka Księgi),
razem z księgami sąsiednich parafii (Mszana Dolna, Niedźwiedź, Słopnice) pobranymi do bazy. Uruchamiać, gdy przybędzie odczytów.

Użycie:  python3 eksport_dostepnosci.py [ścieżka do baza.db]
"""
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

BAZA = sys.argv[1] if len(sys.argv) > 1 else '/home/lukasz/fototeka/fototeka_dane/baza.db'
WYNIK = Path(__file__).resolve().parent / 'tresci' / 'dostepnosc.json'
ZESPOLY = (4268, 4269, 3402)          # Dobra — księgi główne, księgi wsi (Jurków), duplikaty
WSIE = [('dobra', 'Dobra'), ('jurkow', 'Jurków'), ('chyszowki', 'Chyszówki'), ('polrzeczki', 'Półrzeczki'),
        ('gruszowiec', 'Gruszowiec'), ('porabka', 'Porąbka'), ('wilczyce', 'Wilczyce'),
        ('zadziele', 'Zadziele'), ('lostowka', 'Łostówka')]
WSPOLNE_DLA = {'zadzielelostowka': ('zadziele', 'lostowka')}   # jedna księga dla dwóch wsi
# sąsiednie parafie: tylko księgi pobrane do bazy (w serwisie PTG może być ich więcej)
SASIEDNIE = [('mszana', 'Mszana Dolna', (2582, 4888)), ('niedzwiedz', 'Niedźwiedź', (4889,)),
             ('slopnice', 'Słopnice', (4275, 5321))]
ODPISY = {3402, 2582, 4888, 4889, 5321}   # duplikaty i roczne odpisy akt
TYP = {'U': 'chrzty', 'M': 'śluby', 'Z': 'zgony'}


def status(skany, z_wpisami):
    """Odczytana, gdy wpisy są na większości skanów (okładki i puste karty ich nie mają)."""
    if skany == 0 or z_wpisami == 0:
        return 'nieodczytana'
    return 'odczytana' if z_wpisami / skany >= 0.6 else 'czesciowo'


def jednostki(c, zespoly):
    return c.execute(f"""
        select j.id, j.zespol_id, j.sy, j.opis, j.rok_od, j.rok_do, j.wies_klucz,
               (select group_concat(distinct k.rodzaj) from metryki_katalogi k where k.jednostka_id=j.id),
               (select count(*) from metryki_katalogi k join metryki_skany s on s.katalog_id=k.id
                 where k.jednostka_id=j.id and s.powtorka_id is null),
               (select count(distinct s.id) from metryki_katalogi k join metryki_skany s on s.katalog_id=k.id
                 join metryki_wpisy w on w.skan_id=s.id where k.jednostka_id=j.id),
               (select count(*) from metryki_katalogi k join metryki_skany s on s.katalog_id=k.id
                 join metryki_wpisy w on w.skan_id=s.id where k.jednostka_id=j.id),
               (select s.url from metryki_katalogi k join metryki_skany s on s.katalog_id=k.id
                 where k.jednostka_id=j.id order by k.kt, s.plik limit 1)
        from metryki_jednostki j where j.zespol_id in ({','.join(map(str, zespoly))})
        order by j.rok_od, j.zespol_id, j.sy""").fetchall()


def ksiegi(wiersze):
    for (_id, zesp, sy, opis, od, do, wies, rodz, skany, z_wp, wpisy, url) in wiersze:
        typy = [t for t in (rodz or '').split(',') if t in TYP]
        if not typy or od is None:
            continue
        yield wies, {'typy': typy, 'sygn': f'{zesp}/{sy}', 'od': od, 'do': do or od, 'opis': opis,
                     'odpis': zesp in ODPISY, 'skany': skany, 'wpisy': wpisy,
                     'status': status(skany, z_wp), 'url': url or ''}


def main():
    c = sqlite3.connect(f'file:{BAZA}?mode=ro', uri=True, timeout=30)
    wspolne, wsie = [], {k: [] for k, _ in WSIE}
    for wies, ksiega in ksiegi(jednostki(c, ZESPOLY)):
        if wies in wsie:
            wsie[wies].append(ksiega)
        elif wies in WSPOLNE_DLA:
            for w in WSPOLNE_DLA[wies]:
                wsie[w].append(dict(ksiega, wspolna_z='Zadziele i Łostówka'))
        else:
            wspolne.append(ksiega)
    # ile wpisów z każdej wsi jest w bazie — tylko księgi parafii Dobra (także wspólne sprzed 1786);
    # bez duplikatów i akt cywilnych sąsiednich parafii (np. Mszana Dolna, gdzie należała część Łostówki)
    ile = dict(c.execute(f"""
        select w.wies_klucz, count(*) from metryki_wpisy w join metryki_skany s on s.id=w.skan_id
        join metryki_katalogi k on k.id=s.katalog_id join metryki_jednostki j on j.id=k.jednostka_id
        where w.wies_klucz is not null and j.zespol_id in ({','.join(map(str, ZESPOLY))})
        group by w.wies_klucz"""))
    wynik = {
        'stan_na': date.today().isoformat(),
        'wspolne': wspolne,
        'wsie': [{'klucz': k, 'nazwa': n, 'wpisy': ile.get(k, 0), 'ksiegi': wsie[k]} for k, n in WSIE],
        'sasiednie': [],
    }
    for klucz, nazwa, zespoly in SASIEDNIE:
        lista = [k for _, k in ksiegi(jednostki(c, zespoly))]
        wynik['sasiednie'].append({'klucz': klucz, 'nazwa': nazwa, 'zespoly': list(zespoly),
                                   'wpisy': sum(k['wpisy'] for k in lista), 'ksiegi': lista})
    WYNIK.write_text(json.dumps(wynik, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Zapisano {WYNIK}: {len(wspolne)} ksiąg wspólnych, '
          + ', '.join(f'{n} {len(wsie[k])}' for k, n in WSIE) + '; sąsiednie parafie: '
          + ', '.join(f'{p["nazwa"]} {len(p["ksiegi"])} ksiąg, {p["wpisy"]} wpisów' for p in wynik['sasiednie']))


if __name__ == '__main__':
    main()
