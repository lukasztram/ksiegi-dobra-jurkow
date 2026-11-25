# Wersje językowe strony — zasady tłumaczenia

Strona „Co mówią księgi parafii Dobra i Jurków” ma wersję polską (oryginał) i tłumaczenia:
`en` (angielski, pisownia amerykańska), `de` (niemiecki), `fr` (francuski), `es` (hiszpański),
`zh` (chiński uproszczony, zh-Hans). Tłumaczenia buduje `buduj.py` do `docs/<język>/`.

## Pliki

| Oryginał (polski) | Tłumaczenie |
|---|---|
| `tresci/historie/<id>.html` | `tresci/<jęz>/historie/<id>.html` |
| `tresci/spis.json` (tylko pola tekstowe) | `tresci/<jęz>/spis.json` (format niżej) |
| `tresci/ui.json` (napisy strony) | `tresci/<jęz>/ui.json` (te same klucze) |
| `tresci/o-stronie.html` | `tresci/<jęz>/o-stronie.html` |
| `tresci/wykresy/<nazwa>.html` | `tresci/<jęz>/wykresy/<nazwa>.html` |

Tłumacz pisze tylko swoje pliki wynikowe. Nie zmienia plików polskich, nie uruchamia `buduj.py` ani gita.

Sprawdzenie (z katalogu repo):
`python3 narzedzia/sprawdz_tlumaczenia.py <jęz> <id> [<id> …]` — historie;
`python3 narzedzia/sprawdz_tlumaczenia.py <jęz> --reszta` — ui.json, spis.json, o-stronie.html, wykresy.
BŁĄD trzeba poprawić; „uwaga” przejrzeć i poprawić, jeśli ma sens.

### Format `tresci/<jęz>/spis.json`

```json
{
 "nazwa": "<nazwa strony>",
 "opis": "<opis strony>",
 "tematy": {"zaraza": "…", "zywioly": "…", "dwor": "…", "daleko": "…", "slowa": "…", "ludzie": "…"},
 "historie": {
  "<id>": {"tytul": "…", "zajawka": "…", "znacznik": "…", "lead": "…", "miejsce": "…", "rok_tekst": "…"}
 }
}
```
Wszystkie 63 historie z `tresci/spis.json`. Pozostałe pola (rok, tematy, zrodlo, gotowa) zostają w polskim spisie.
`rok_tekst`: „XVI wiek – 1973” → np. “16th century – 1973”, „od 1679” → “since 1679”, zakresy lat bez zmian.
`miejsce`: „Dobra, dom nr 202” → “Dobra, house no. 202”; „cała parafia” → “the whole parish”;
„Mszana Dolna, sąsiednia parafia” → “Mszana Dolna, neighboring parish”.

### `tresci/<jęz>/ui.json`

Te same klucze co `tresci/ui.json`, przetłumaczone wartości. Pola w `{nawiasach}` i znaczniki HTML zostają.
`_opis` przetłumacz albo zostaw. Klucze stałe ustaw tak:

| klucz | en | de | fr | es | zh |
|---|---|---|---|---|---|
| jezyk | en | de | fr | es | zh |
| html_lang | en | de | fr | es | zh-Hans |
| og_locale | en_US | de_DE | fr_FR | es_ES | zh_CN |
| skrot | EN | DE | FR | ES | 中文 |
| nazwa_jezyka | English | Deutsch | Français | Español | 中文 |
| cudzyslow | “ ” | „ “ | «   » | « » | “ ” |
| cudzyslow_tytul | “ ” | „ “ | «   » | « » | 《 》 |
| separator_tysiecy | , | . |   | . | , |
| data | {m} {d}, {r} | {d}. {m} {r} | {d} {m} {r} | {d} de {m} de {r} | {r}年{m}月{d}日 |
| miesiace | January … | Januar … | janvier … | enero … | "1" … "12" |

(`cudzyslow` i `cudzyslow_tytul` to listy dwóch napisów: otwierający i zamykający; ` ` = twarda spacja.)
`hero_eyebrow` to nazwy wsi — zostają. `stopka_tlumaczenie` i `nota_tlumaczenia_html` są w polskim puste;
w tłumaczeniu wpisz:
- `stopka_tlumaczenie`: jedno zdanie, że wersję przetłumaczono z polskiego z pomocą Claude i że w razie różnic
  rozstrzyga tekst polski;
- `nota_tlumaczenia_html`: „Przetłumaczone z <a href=\"{oryginal}\">polskiego oryginału</a> z pomocą Claude.
  Cytaty z ksiąg podaję w oryginale, z przekładem.” (w języku docelowym; `{oryginal}` zostaje).
`legenda_ksiazka`: tytuły publikacji zostają po polsku, z przekładem w nawiasie.

## Historie i strona „O stronie” — HTML

- Zachowaj strukturę: te same znaczniki, klasy, atrybuty i kolejność. Tłumaczysz tekst widoczny dla czytelnika
  oraz atrybuty `alt`, `title`, `aria-label`.
- `{{historia:id}}`, `{{plik:…}}`, `{{strona:…}}`, `<!--WYKRES:…-->` przepisz bez zmian.
- Odnośnik do innej historii, którego tekstem jest jej polski tytuł w cudzysłowie, np.
  `<a href="{{historia:las-trak-woda}}">„Las, trak i woda”</a>`, zamień na
  `<a href="{{historia:las-trak-woda}}">{{tytul:las-trak-woda}}</a>` — bez cudzysłowów. `buduj.py` wstawi tam
  przetłumaczony tytuł we właściwym cudzysłowie. Słowa wokół („historia”, „opowiada historia”) tłumacz normalnie.
  Inny tekst odnośnika (nie tytuł) tłumacz zwyczajnie.
- Adresy zewnętrzne (`href="https://…"`) bez zmian.
- Wypis z księgi `<figure class="wypis">`:
  - `p.k` (podpis: z jakiej księgi i z kiedy) — przetłumacz;
  - `blockquote` — to ORYGINAŁ z księgi. Zostaw go dokładnie jak jest (łacina, polski, niemiecki), znak w znak.
    Jeśli nie ma atrybutu `lang`: oryginał polski → dodaj `lang="pl"`, niemiecki → `lang="de"`, łaciński → `lang="la"`;
  - `p.pl-t` — przekład oryginału: przełóż na język docelowy (z oryginału; polski przekład pomaga). Klasa zostaje
    `pl-t`. Gdy wypis nie ma `p.pl-t` (oryginał był po polsku albo po niemiecku), DODAJ
    `<p class="pl-t">…</p>` zaraz po `blockquote`. Tylko w tym miejscu wolno dodać akapit;
  - `p.sy` (sygnatura) — przetłumacz opis, numery bez zmian, „zobacz skan ↗” według słownika.
- `figure.ilustracja`: przetłumacz `figcaption` i `alt`.
- Tabele: przetłumacz nagłówki i tekst; liczby bez zmian.
- Bloki „Na ile to pewne”, „Czego nie wiemy”, „Źródła” i etykiety pewności (chip) — według słownika.

## Treść

- Wiernie, bez dodawania faktów, bez skracania i bez upiększania. Styl jak w oryginale: prosty, rzeczowy,
  krótkie zdania. Autor pisze w pierwszej osobie liczby pojedynczej („porównałem ze skanem”) — zachowaj.
- Krótkie objaśnienie w nawiasie wolno dodać tylko tam, gdzie obcy czytelnik nie zrozumie pojęcia
  (np. Galicja, morga, pańszczyzna, przednówek, Wigilia) — raz w historii, bez nowych faktów.
- Imiona i nazwiska w formie polskiej (Jan, Józef, Wojciech, Agnieszka) — nie zamieniaj na John, Joseph, Josef.
  Formy łacińskie w cytatach bez zmian.
- Nazwiska kobiet podawaj w formie podstawowej, bez polskiej odmiany i form żeńskich: „Anna z Kuczajów”,
  „Węglarzowa”, „Potaczkówna” → Anna Kuczaj; Anna Węglarz, née Kuczaj (de: geb. Kuczaj; fr: née Kuczaj;
  es: de soltera Kuczaj; zh: 娘家姓 Kuczaj). Formę żeńską zostaw tylko wtedy, gdy tekst mówi o samej formie.
- Nazwy miejscowości po polsku, z polskimi znakami, zawsze w MIANOWNIKU: „w Łętowem” → in Łętowe,
  „z Kasinki Małej” → from Kasinka Mała, „pod Mszaną” → near Mszana. Mianowniki: Dobra, Jurków, Chyszówki,
  Półrzeczki, Gruszowiec, Porąbka, Wilczyce, Zadziele, Łostówka, Mszana Dolna, Mszana Górna, Kasinka Mała,
  Kasina Wielka, Łętowe, Słomka, Glisne, Niedźwiedź, Słopnice, Szczyrzyc, Limanowa, Tymbark, Podobin,
  Poręba Wielka, Chabówka, Nowy Sącz, Szerszenie, Szyrszenie, Lubomierz, Rabka; góra Mogielica; rzeki Raba, Mszanka.
- Miasta, kraje i krainy z utartą nazwą w języku docelowym — w tej nazwie: Kraków (de Krakau, fr Cracovie,
  es Cracovia, zh 克拉科夫), Warszawa (Warsaw, Warschau, Varsovie, Varsovia, 华沙), Wiedeń (Vienna, Wien, Vienne,
  Viena, 维也纳), Budapeszt, Chicago, Węgry, Austria, Słowacja; Galicja: en Galicia, de Galizien, fr Galicie,
  es **Galitzia** (nie „Galicia”), zh 加利西亚. Mniejsze miasta (Tarnów, Nowy Sącz, Limanowa) — po polsku.
- Daty, liczebniki i liczby w zwyczaju języka docelowego.
- Słowa gwarowe i polskie wyrazy, o które chodzi w tekście („sipka”, „zawalnica”, „trak”, „ława”), zostaw po polsku
  w cudzysłowie i objaśnij, jeśli polski tekst sam ich nie objaśnia.
- Tytuły polskich książek, artykułów i stron: oryginał w cudzysłowie, przy pierwszym użyciu przekład w nawiasie,
  np. “Trzy stulecia Jurkowa” (Three Centuries of Jurków). Skróty języka („ang.”, „węg.”, „pol.”) przetłumacz.
- Zasady wrażliwe: samobójstwa i dzieci nieślubne są w oryginale bez imion, nazwisk i linków do skanów.
  Nie dodawaj ich. Nie dopisuj niczego o osobach żyjących.

## Typografia

- en: “…”, wewnątrz ‘…’; myślnik — bez spacji; zakresy lat z półpauzą 1890–1916.
- de: „…“, wewnątrz ‚…‘.
- fr: « … » z twardą spacją (U+00A0) po « i przed », także przed : ; ? ! (U+202F lub U+00A0).
- es: «…», wewnątrz “…”; znaki ¿ ¡.
- zh: “…”; tytuły historii i publikacji 《…》; interpunkcja pełnej szerokości（，。：；？！）; imiona, nazwiska
  i nazwy wsi alfabetem łacińskim (z polskimi znakami); lata cyframi; wiek: 36岁; daty: 1907年8月20日.

## Słownik — stałe formy

| polski | en | de | fr | es | zh |
|---|---|---|---|---|---|
| Pewne (etykieta) | Certain | Sicher | Certain | Seguro | 确定 |
| Prawdopodobne | Probable | Wahrscheinlich | Probable | Probable | 很可能 |
| Możliwe | Possible | Möglich | Possible | Posible | 可能 |
| Do sprawdzenia | To be checked | Noch zu prüfen | À vérifier | Por comprobar | 待核实 |
| Na ile to pewne (nagłówek bloku) | How certain is this | Wie sicher ist das | Degré de certitude | Grado de certeza | 可信程度 |
| Czego nie wiemy | What we don’t know | Was wir nicht wissen | Ce que nous ne savons pas | Lo que no sabemos | 尚不清楚的事 |
| Źródła | Sources | Quellen | Sources | Fuentes | 资料来源 |
| zobacz skan ↗ | view scan ↗ | Scan ansehen ↗ | voir le scan ↗ | ver el escaneo ↗ | 查看扫描件 ↗ |
| sygn. | ref. | Sign. | cote | sign. | 档号 |
| skan 002 | scan 002 | Scan 002 | scan 002 | escaneo 002 | 扫描件 002 |
| serwis Metryki PTG (pierwsze użycie) | the Metryki website of the Polish Genealogical Society (PTG) | die Website Metryki der Polnischen Genealogischen Gesellschaft (PTG) | le site Metryki de la Société généalogique polonaise (PTG) | el sitio Metryki de la Sociedad Genealógica Polaca (PTG) | 波兰家谱学会（PTG）的 Metryki 网站 |
| księga chrztów | baptism register | Taufbuch | registre des baptêmes | libro de bautismos | 洗礼登记簿 |
| księga ślubów | marriage register | Traubuch | registre des mariages | libro de matrimonios | 婚姻登记簿 |
| księga zmarłych | death register | Sterbebuch | registre des décès | libro de defunciones | 死亡登记簿 |
| odpis roczny, duplikat | annual copy | Jahresabschrift (Duplikat) | copie annuelle | copia anual | 年度副本 |
| proboszcz | parish priest | Pfarrer | curé | párroco | 本堂神父 |
| wikary | curate | Kaplan | vicaire | vicario | 助理神父 |
| parafia | parish | Pfarrei | paroisse | parroquia | 堂区 |
| dwór; dziedzic | manor; lord of the manor | Gutshof; Gutsherr | manoir; seigneur | casa señorial; señor | 庄园；庄园主 |
| przysiółek | hamlet | Weiler | hameau | caserío | 小村落 |
| gospodarz (rolnik) | farmer | Bauer | paysan | campesino | 农户 |
| akuszerka, położna | midwife | Hebamme | sage-femme | partera | 接生婆 |
| chrzestni | godparents | Paten | parrain et marraine | padrinos | 教父母 |
| ochrzczony z wody | baptized at home (emergency baptism) | nottgetauft | ondoyé | bautizado de socorro | 紧急洗礼 |
