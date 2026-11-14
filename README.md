# Co mówią księgi parafii Dobra i Jurków

Strona z prawdziwymi historiami z ksiąg metrykalnych parafii Dobra i Jurków (1678–1926).

## Jak to działa

- `tresci/spis.json` — lista wszystkich historii (gotowych i w przygotowaniu): tytuł, rok, miejsce, zajawka, tematy, źródło.
- `tresci/historie/<id>.html` — tekst gotowej historii (bez nagłówka; nagłówek bierze się ze spisu).
- `tresci/o-stronie.html` — strona „O stronie” (od autora, zasady, źródła).
- `szablony/` — wygląd (`styl.css`) i filtr tematów (`lista.js`).
- `buduj.py` — składa stronę. Tylko biblioteka standardowa Pythona.

```
python3 buduj.py
```

Wynik:
- `docs/` — gotowa strona; GitHub Pages publikuje ją z gałęzi `main`, folder `/docs`;
- `_podglad/podglad.html` — cała strona w jednym pliku, do podglądu (nie trafia do repozytorium).

## Pozostałe skrypty

- `eksport_dostepnosci.py` — czyta bazę Fototeki **tylko do odczytu** i zapisuje `tresci/dostepnosc.json`
  (jakie księgi każdej wsi są w serwisie Metryki PTG i ile z nich odczytano). Z tego `dostepnosc.py`
  rysuje na stronie głównej osie czasu „Jakie księgi się zachowały”. Uruchamiać, gdy przybędzie odczytów.
- `obrazki.py` — obrazki 1200 × 630 do podglądu linków (Facebook, komunikatory) w `obrazki/`;
  wymaga Pillow (systemowy `python3` go ma). Czcionki do obrazków: `narzedzia/czcionki/`.
- `szablony/fonty/` — czcionki strony (SIL Open Font License), serwowane ze strony, bez Google.

Pełna przebudowa:

```
python3 eksport_dostepnosci.py && python3 obrazki.py && python3 buduj.py
```

## Zasady treści

- Tylko ludzie zmarli dawno temu; historie do roku 1926; o żyjących nie piszemy.
- Samobójstwa i dzieci nieślubne bez imion i nazwisk.
- Skany ksiąg tylko jako link do serwisu Metryki PTG (metryki.genealodzy.pl), z sygnaturą i numerem skanu.
- Przy każdym wniosku etykieta pewności: Pewne / Prawdopodobne / Możliwe / Do sprawdzenia.
- Historie z książek rodzinnych autor pisze w pierwszej osobie.

## Nowa historia

1. Dopisz wpis w `tresci/spis.json` (`"gotowa": false` = zapowiedź na liście).
2. Gdy tekst gotowy: plik `tresci/historie/<id>.html`, w spisie `"gotowa": true` oraz pola `znacznik` i `lead`.
3. `python3 buduj.py`, przejrzyj podgląd, commit, push.
