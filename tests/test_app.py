"""AppTest-Rauchtests der Demo (nur Beispiele). Die Oberfläche selbst (Swagger UI im Rahmen) prüft nur der Browser."""
import base64
import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
BEISPIELE = {
    "Sendungsverfolgung (OpenAPI 3.0)": ("3.0.3", "5"),
    "Lagerbestand (OpenAPI 3.1, mit Webhooks)": ("3.1.0", "2"),
    "Fuhrpark (Swagger 2.0)": ("2.0", "2"),
}
FEHLERHAFT = "Absichtlich fehlerhaft (zeigt die Prüfung)"


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def _metriken(at: AppTest) -> dict[str, str]:
    return {m.label: m.value for m in at.metric}


def _rahmen(at: AppTest) -> list:
    return at.get("iframe")


def _konfig_im_rahmen(at: AppTest) -> dict:
    """Die Swagger-UI-Konfiguration aus der data:-Adresse des Rahmens."""
    url = _rahmen(at)[0].proto.src
    seite = base64.b64decode(url.split(",", 1)[1]).decode("utf-8")
    return json.loads(re.search(r"var konfig = (.*);\n", seite).group(1))


def test_standard_zeigt_beispiel_mit_kennzahlen_und_einem_rahmen():
    at = _app()
    assert _metriken(at) == {"Version": "3.0.3", "Operationen": "5", "Pfade": "3", "Gruppen (Tags)": "2", "Schemas": "6"}
    assert len(_rahmen(at)) == 1
    assert not at.error
    assert any("keine Fehler" in s.value for s in at.success)


def test_demo_hat_keine_eingabe_fuer_eigene_dateien():
    at = _app()
    assert at.get("file_uploader") == [] and len(at.text_area) == 0 and len(at.radio) == 0
    assert [s.key for s in at.selectbox] == ["beispiel", "doc_expansion"]


def test_demo_sendet_keine_anfragen():
    assert _konfig_im_rahmen(_app())["supportedSubmitMethods"] == []


@pytest.mark.parametrize("name,erwartet", BEISPIELE.items())
def test_jedes_beispiel_laeuft(name, erwartet):
    at = _app()
    at.selectbox(key="beispiel").set_value(name).run()
    assert not at.exception and not at.error
    m = _metriken(at)
    assert (m["Version"], m["Operationen"]) == erwartet
    assert len(_rahmen(at)) == 1
    assert _konfig_im_rahmen(at)["spec"]["info"]["title"] == at.subheader[0].value


def test_fehlerhaftes_beispiel_zeigt_fehler_und_zeichnet_trotzdem():
    at = _app()
    at.selectbox(key="beispiel").set_value(FEHLERHAFT).run()
    assert not at.exception
    assert len(at.error) == 1 and "2 Fehler" in at.error[0].value
    assert len(_rahmen(at)) == 1
    pruefung = next(e for e in at.expander if e.label.startswith("🔎 Prüfung"))
    assert pruefung.label == "🔎 Prüfung: 2 Fehler, 7 Warnungen"


def test_jeder_beispielhinweis_gehoert_zu_einem_beispiel():
    import app  # noqa: PLC0415  (Modulebene von app.py zeichnet Streamlit-Elemente; hier nur die Wörterbücher lesen)

    assert set(app.BEISPIEL_HINWEISE) == set(app.BEISPIELE)
    for datei in app.BEISPIELE.values():
        assert (Path(app.ORDNER) / "examples" / datei).is_file()


@pytest.mark.parametrize("hoehe", [400, 2000])
def test_hoehe_am_rand_laeuft(hoehe):
    at = _app()
    at.slider(key="hoehe").set_value(hoehe).run()
    assert not at.exception and len(_rahmen(at)) == 1


@pytest.mark.parametrize("schluessel,wert", [("doc_expansion", "full"), ("doc_expansion", "none"), ("filter_leiste", False)])
def test_darstellungsschalter_kommen_in_der_oberflaeche_an(schluessel, wert):
    at = _app()
    if isinstance(wert, bool):
        at.checkbox(key=schluessel).set_value(wert).run()
    else:
        at.selectbox(key=schluessel).set_value(wert).run()
    assert not at.exception and len(_rahmen(at)) == 1
    konfig = _konfig_im_rahmen(at)
    assert konfig["docExpansion"] == (wert if schluessel == "doc_expansion" else "list")
    assert konfig["filter"] is (wert if schluessel == "filter_leiste" else True)


def test_typ_tiefe_ist_standardmaessig_3_und_der_regler_kommt_in_der_oberflaeche_an():
    at = _app()
    assert at.slider(key="typ_tiefe").value == 3
    assert _konfig_im_rahmen(at)["defaultModelExpandDepth"] == 3
    at.slider(key="typ_tiefe").set_value(5).run()
    assert not at.exception
    konfig = _konfig_im_rahmen(at)
    assert konfig["defaultModelExpandDepth"] == 5 and konfig["defaultModelsExpandDepth"] == 5
