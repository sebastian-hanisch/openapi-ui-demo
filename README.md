# OpenAPI-YAML als Oberfläche (Demo)

Demo für die Webseite: Aus einer **OpenAPI-Datei** (OpenAPI 3.0, 3.1 und Swagger 2.0) wird die **Swagger UI**: Endpunkte nach
Gruppen, Parameter, Schemas und Beispiele. Die Demo arbeitet **nur mit vier mitgelieferten Beispielen**; eigene Dateien hochladen
geht im Schwesterprojekt `openapi-ui-werkzeug`.

Stand: 2026-11-18 lokal gebaut und im Browser geprüft; **nicht** in der Streamlit Community Cloud deployt oder dort geprüft, nicht in die Website eingebunden.

## Starten

```bash
python -m venv venv
venv/Scripts/python.exe -m pip install -r requirements-dev.txt
venv/Scripts/python.exe -m streamlit run app.py
```

Die App lädt die Swagger UI (Version 5.17.14) zur Laufzeit vom CDN jsDelivr. Ohne Internetzugang bleibt der Rahmen mit der
Oberfläche leer; Prüfung, Kennzahlen, Endpunktübersicht und JSON-Ansicht funktionieren weiter.

## Was die Demo zeigt

1. **Beispiel wählen** (Seitenleiste), mit je einem Satz, was es zeigt:
   * *Sendungsverfolgung* (OpenAPI 3.0): Gruppen, Parameter mit Grenzen, Anfragekörper mit Beispiel, `$ref`, `allOf`, Anmeldung per Token, eine veraltete Operation.
   * *Lagerbestand* (OpenAPI 3.1): `webhooks` und Typlisten wie `[integer, "null"]`.
   * *Fuhrpark* (Swagger 2.0): das ältere Format mit `host` und `definitions`.
   * *Absichtlich fehlerhaft*: zwei Fehler und sieben Warnungen, damit die Prüfung etwas zu melden hat.
2. **Prüfen** (Fehler und Warnungen, Fehler zuerst): Version (`openapi: 3.x` bzw. `swagger: "2.0"`), `info.title`, `info.version`, `paths`
   (bei 3.1 genügen `webhooks` oder `components`), Pfad beginnt mit `/`, `responses` je Operation, doppelte `operationId`,
   Pfadparameter `{x}` ohne Beschreibung, `$ref` auf nichts (Fehler) und `$ref` auf eine andere Datei oder URL (Warnung), doppelte YAML-Schlüssel mit Zeilennummer.
3. **Zeichnen:** Swagger UI in einem Rahmen mit `data:`-Adresse. Auch bei Fehlern wird gezeichnet.
4. **Laden:** die Seite als eigenständige HTML-Datei (`<Titel>.html`).
5. **Nachlesen:** die YAML-Datei des Beispiels, die Endpunktübersicht und die gelesene Spezifikation als JSON.

Darstellung (Seitenleiste): Aufklappen (`list`, `full`, `none`), Filterleiste, Typen aufklappen bis Tiefe (1 bis 6, Standard 3: wie tief verschachtelte Typen, die selbst benannte Schemas sind, von selbst aufgeklappt erscheinen; die Standardtiefe 1 der Swagger UI zeigt sie nur als zugeklappten Block `UUIDType[...]`, die Typdetails stünden dann erst nach dem Aufklappen da), Höhe des Rahmens (400 bis 2000 px). **„Try it out“ gibt es in der Demo nicht**:
die Beispiele zeigen auf erfundene Server (`example.org`), die Oberfläche sendet nichts.

## Grenzen und Annahmen

* **Die Prüfung ist kein vollständiger Validator.** Sie fängt die Fehler, die eine Oberfläche sichtbar kaputt machen. Ob eine Datei dem
  offiziellen JSON-Schema der OpenAPI-Spezifikation entspricht, sagt sie nicht.
* **Lesen mit PyYAML (`oa_parse.py`).** Abweichend vom Standard von PyYAML sind nur `true` und `false` Wahrheitswerte (ein Ländercode
  `no` bleibt Text), und Datumsangaben bleiben Text. Verschachtelte und zyklische YAML-Aliase werden abgefangen (höchstens 6.000.000 Zeichen JSON).
* **Abgeschotteter Rahmen.** Die Seite steht als `data:`-Adresse im Rahmen. Dessen Herkunft ist von der App getrennt (im Browser geprüft:
  `contentDocument` des Rahmens ist von der App aus nicht lesbar). Die Spezifikation steht als maskiertes JSON in der Seite (`<`, `>`, `&`
  und die Zeilentrenner U+2028/2029 sind ersetzt) und kann den Skriptblock nicht beenden.
* **Feste Basisadresse (`oa_render.BASIS_ADRESSE`).** Die Swagger UI löst die `$ref` einer Operation oder eines Schemas erst beim Aufklappen auf,
  und zwar gegen die Adresse des Dokuments. Im `data:`-Rahmen ist die Adresse die ganze Seite in Base64: Ohne Korrektur drehte sich beim Aufklappen
  jeder Operation ein endloser Ladekreis (das fiel zunächst nicht auf, weil nur die zugeklappte Oberfläche angesehen worden war). Die Seite setzt
  deshalb nach dem Start eine feste Adresse mit der reservierten Endung `.invalid`, die nie geladen wird; ein Stil blendet den Link aus, den die
  Swagger UI daraus unter dem Titel macht. Die Python-Tests sichern nur, dass die Zeilen in der Seite stehen; das Verhalten prüft allein der Browser.
* **Nicht geprüft:** Verhalten in der Streamlit Community Cloud (ob die dortige Seite den `data:`-Rahmen zulässt) und die Darstellung im
  dunklen Design (die Swagger UI ist hell und steht auf weißem Grund). Die Swagger UI selbst (Zeichnen, Aufklappen von Operationen und Schemas) prüft kein Test, nur der Blick im Browser; das Aufklappen im `data:`-Rahmen ist am 2026-11-18 im Browser nachgeprüft (an einer Beschreibung mit 48 Dateien im Werkzeug und an „POST /sendungen“ in dieser Demo; Hinweis zu `BASIS_ADRESSE` oben).
* `st.iframe` setzt eine neuere Streamlit-Version voraus (geprüft mit 1.64, deshalb `streamlit>=1.64`).
* **Nur eine Datei je Beispiel.** Verweist ein `$ref` auf eine andere Datei, warnt die Prüfung nur. Beschreibungen, die auf einen Ordner verteilt sind, bündelt `openapi-ui-werkzeug`.
* **Doppelter Code:** `oa_parse.py` und `oa_render.py` stehen gleich in `openapi-ui-werkzeug`. Änderungen an einem Ort in beiden nachziehen.

## Dateien

```
app.py                   Oberfläche der Demo
oa_parse.py              Lesen, Prüfen, Kennzahlen (ohne Streamlit)
oa_render.py             HTML-Seite mit Swagger UI, data:-Adresse, Dateiname
examples/                vier Beispiele (3.0, 3.1, 2.0, absichtlich fehlerhaft)
tests/                   81 Tests (Parser, Renderer, AppTest, Laufzeit-Imports)
requirements.txt         streamlit, pyyaml (ungepinnt)
requirements-dev.txt     dazu pytest
```

Die Beispiel-APIs sind erfunden; Namen, Pfade und Server gehören zu keinem echten Dienst.

## Tests

```bash
venv/Scripts/python.exe -m pytest tests -q
```

81 Tests; die Laufzeit schwankt mit der Rechnerlast. Die Kennzahlen der Beispiele (Operationen, Pfade, Schemas) sind von Hand aus den Dateien gezählt; die
Gegenprobe zum Lesen ist die Standardbibliothek (`json`): das als JSON ausgegebene Ergebnis ergibt beim erneuten Lesen dieselbe Spezifikation.
Die AppTests lesen die Konfiguration der Swagger UI aus der Adresse des Rahmens und prüfen, dass jeder Schalter dort ankommt und die Demo nichts sendet.

## Lizenz

MIT, siehe [LICENSE](LICENSE). Die Swagger UI (Apache-2.0) wird zur Laufzeit vom CDN jsDelivr geladen und ist nicht Teil dieses Repos.
