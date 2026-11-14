#!/usr/bin/env python3
"""Spisuje, jakie księgi metrykalne parafii Dobra są w serwisie Metryki PTG i ile z nich jest już odczytane.

Czyta bazę Fototeki TYLKO DO ODCZYTU i zapisuje tresci/dostepnosc.json, z którego buduj.py
rysuje na stronie osie czasu „Jakie księgi się zachowały”. Uruchamiać, gdy przybędzie odczytów.

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
TYP = {'U': 'chrzty', 'M': 'śluby', 'Z': 'zgony'}


def status(skany, z_wpisami):
    """Odczytana, gdy wpisy są na większości skanów (okładki i puste karty ich nie mają)."""
    if skany == 0 or z_wpisami == 0:
        return 'nieodczytana'
    return 'odczytana' if z_wpisami / skany >= 0.6 else 'czesciowo'


def main():
    c = sqlite3.connect(f'file:{BAZA}?mode=ro', uri=True, timeout=30)
    jednostki = c.execute(f"""
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
        from metryki_jednostki j where j.zespol_id in ({','.join(map(str, ZESPOLY))})
        order by j.rok_od, j.zespol_id, j.sy""").fetchall()
    wspolne, wsie = [], {k: [] for k, _ in WSIE}
    for (_id, zesp, sy, opis, od, do, wies, rodz, skany, z_wp, wpisy, url) in jednostki:
        typy = [t for t in (rodz or '').split(',') if t in TYP]
        if not typy or od is None:
            continue
        ksiega = {'typy': typy, 'sygn': f'{zesp}/{sy}', 'od': od, 'do': do or od, 'opis': opis,
                  'odpis': zesp == 3402, 'skany': skany, 'wpisy': wpisy,
                  'status': status(skany, z_wp), 'url': url or ''}
        if wies in wsie:
            wsie[wies].append(ksiega)
        elif wies in WSPOLNE_DLA:
            for w in WSPOLNE_DLA[wies]:
                wsie[w].append(dict(ksiega, wspolna_z='Zadziele i Łostówka'))
        else:
            wspolne.append(ksiega)
    # ile wpisów z każdej wsi jest w bazie (wszystkie księgi, także wspólne sprzed 1786)
    ile = dict(c.execute("select wies_klucz, count(*) from metryki_wpisy where wies_klucz is not null group by wies_klucz"))
    wynik = {
        'stan_na': date.today().isoformat(),
        'wspolne': wspolne,
        'wsie': [{'klucz': k, 'nazwa': n, 'wpisy': ile.get(k, 0), 'ksiegi': wsie[k]} for k, n in WSIE],
    }
    WYNIK.write_text(json.dumps(wynik, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Zapisano {WYNIK}: {len(wspolne)} ksiąg wspólnych, '
          + ', '.join(f'{n} {len(wsie[k])}' for k, n in WSIE))


if __name__ == '__main__':
    main()
