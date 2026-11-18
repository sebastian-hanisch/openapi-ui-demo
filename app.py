"""OpenAPI-YAML → Swagger UI (Demo): vier mitgelieferte Beispiele, geprüft und als Oberfläche angezeigt."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

import oa_parse
import oa_render

ORDNER = Path(__file__).parent
BEISPIELE = {
    "Sendungsverfolgung (OpenAPI 3.0)": "sendungen-3.0.yaml",
    "Lagerbestand (OpenAPI 3.1, mit Webhooks)": "lagerbestand-3.1.yaml",
    "Fuhrpark (Swagger 2.0)": "fahrzeuge-2.0.yaml",
    "Absichtlich fehlerhaft (zeigt die Prüfung)": "mit-fehlern.yaml",
}
BEISPIEL_HINWEISE = {
    "Sendungsverfolgung (OpenAPI 3.0)": "Gruppen, Parameter mit Grenzen, Anfragekörper mit Beispiel, `$ref` auf Schemas, `allOf`, Anmeldung per Token, eine veraltete Operation.",
    "Lagerbestand (OpenAPI 3.1, mit Webhooks)": "Neu in 3.1: `webhooks` und Typlisten wie `[integer, \"null\"]`.",
    "Fuhrpark (Swagger 2.0)": "Das ältere Format mit `swagger: \"2.0\"`, `host` und `definitions`.",
    "Absichtlich fehlerhaft (zeigt die Prüfung)": "Zwei Fehler und sieben Warnungen: fehlende Version, kaputter `$ref`, doppelte `operationId`, nicht beschriebener Pfadparameter, …",
}
DOC_EXPANSION_TEXT = {
    "list": "Operationen einer Gruppe sichtbar, Details zugeklappt",
    "full": "Alles aufgeklappt",
    "none": "Alles zugeklappt",
}
HOEHE_MIN, HOEHE_MAX, HOEHE_STANDARD = 400, 2000, 900
BEFUND_SPALTEN = {
    "Stufe": st.column_config.TextColumn(width="small"),
    "Ort": st.column_config.TextColumn(width="medium"),
    "Meldung": st.column_config.TextColumn(width="large"),
}

st.set_page_config(page_title="OpenAPI-UI – Sebastian Hanisch", layout="wide")

st.title("📘 OpenAPI-YAML als Oberfläche")
st.markdown(
    """
Aus einer **OpenAPI-Datei** (YAML; OpenAPI 3.0, 3.1 und Swagger 2.0) wird die bekannte **Swagger UI**:
Endpunkte nach Gruppen, Parameter, Schemas und Beispiele. Wählen Sie links eines der **vier Beispiele**. Die Datei wird vorher
**geprüft** (Pflichtfelder, `$ref`-Verweise, doppelte `operationId`, Pfadparameter), und die fertige Seite lässt sich als
**eigenständige HTML-Datei** laden. Darunter stehen die **Endpunktübersicht** und die gelesene Spezifikation als **JSON**.
"""
)


@st.cache_data(show_spinner=False)
def _beispiel(name: str) -> tuple[str, oa_parse.Ergebnis]:
    text = (ORDNER / "examples" / BEISPIELE[name]).read_text(encoding="utf-8")
    return text, oa_parse.lesen(text)


def _befund_zeilen(befunde: list[oa_parse.Befund]) -> list[dict[str, str]]:
    """Fehler vor Warnungen, sonst in der Reihenfolge des Fundes."""
    ordnung = sorted(befunde, key=lambda b: b.stufe != oa_parse.FEHLER)
    return [{"Stufe": b.stufe, "Ort": b.ort, "Meldung": b.text} for b in ordnung]


with st.sidebar:
    st.header("📥 Beispiel")
    name = st.selectbox("Beispiel", list(BEISPIELE), key="beispiel", label_visibility="collapsed")
    st.caption(BEISPIEL_HINWEISE[name])

    st.header("⚙️ Darstellung")
    doc_expansion = st.selectbox(
        "Aufklappen",
        list(DOC_EXPANSION_TEXT),
        format_func=DOC_EXPANSION_TEXT.get,
        key="doc_expansion",
    )
    filter_leiste = st.checkbox("Filterleiste anzeigen", value=True, key="filter_leiste")
    typ_tiefe = st.slider(
        "Typen aufklappen bis Tiefe",
        oa_render.TYP_TIEFE_MIN,
        oa_render.TYP_TIEFE_MAX,
        oa_render.TYP_TIEFE_STANDARD,
        key="typ_tiefe",
        help=(
            "Wie tief verschachtelte Typen in der Schema-Liste und in der Schema-Ansicht der Operationen von selbst aufgeklappt sind. "
            "Bei 1 erscheint ein Typ, der selbst ein benanntes Schema ist (z. B. `Status`), nur als zugeklappter Block."
        ),
    )
    hoehe =st.slider("Höhe der Ansicht (px)", HOEHE_MIN, HOEHE_MAX, HOEHE_STANDARD, step=50, key="hoehe")

text, erg = _beispiel(name)
spec = erg.spec
assert spec is not None  # alle mitgelieferten Beispiele sind lesbar (tests/test_parse.py)

if erg.fehler:
    st.error(f"Die Spezifikation hat {len(erg.fehler)} Fehler. Die Oberfläche wird trotzdem gezeichnet.")

kz = oa_parse.kennzahlen(spec)
st.subheader(kz["titel"] or "(ohne Titel)")
spalten = st.columns(5)
spalten[0].metric("Version", kz["version"])
spalten[1].metric("Operationen", kz["operationen"])
spalten[2].metric("Pfade", kz["pfade"])
spalten[3].metric("Gruppen (Tags)", kz["tags"])
spalten[4].metric("Schemas", kz["schemas"])

if erg.befunde:
    with st.expander(f"🔎 Prüfung: {len(erg.fehler)} Fehler, {len(erg.warnungen)} Warnungen", expanded=bool(erg.fehler)):
        st.dataframe(_befund_zeilen(erg.befunde), hide_index=True, width="stretch", column_config=BEFUND_SPALTEN)
else:
    st.success("Prüfung: keine Fehler und keine Warnungen gefunden.")

# Die Beispiele zeigen auf erfundene Server: die Demo sendet keine Anfragen („Try it out“ bleibt aus).
seite = oa_render.html_seite(
    spec,
    titel=kz["titel"] or "API-Dokumentation",
    doc_expansion=doc_expansion,
    filter_leiste=filter_leiste,
    try_it_out=False,
    typ_tiefe=typ_tiefe,
)
st.iframe(oa_render.als_data_url(seite), height=hoehe)
st.caption(
    f"Die Oberfläche lädt Swagger UI {oa_render.SWAGGER_UI_VERSION} vom CDN jsDelivr; ohne Internetzugang bleibt der Rahmen leer. "
    "Sie läuft in einem abgeschotteten Rahmen ohne Zugriff auf diese App und sendet keine Anfragen."
)
st.download_button(
    "⬇️ Als eigenständige HTML-Datei laden",
    data=seite,
    file_name=oa_render.html_dateiname(spec),
    mime="text/html",
    key="download_html",
)

with st.expander("📄 Die YAML-Datei dieses Beispiels"):
    st.code(text, language="yaml")

with st.expander("📋 Endpunktübersicht"):
    ops = oa_parse.operationen(spec)
    if ops:
        st.dataframe(
            [
                {
                    "Methode": o.methode,
                    "Pfad": o.pfad,
                    "Zusammenfassung": o.zusammenfassung,
                    "Tags": ", ".join(o.tags),
                    "operationId": o.operation_id,
                    "veraltet": "ja" if o.veraltet else "",
                }
                for o in ops
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("Die Spezifikation beschreibt keine Operationen unter `paths`.")

with st.expander("🧾 Gelesene Spezifikation als JSON"):
    st.caption(
        "So kommt die Datei in der Oberfläche an: YAML-Anker und -Aliase sind aufgelöst, `true`/`false` sind die einzigen Wahrheitswerte, "
        "Datumsangaben bleiben Text."
    )
    st.code(json.dumps(spec, ensure_ascii=False, indent=2), language="json")
