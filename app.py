from pathlib import Path
from html import escape
import json

import streamlit as st


DATA_FILE = Path("data/modelle.json")
ERSATZTEILE_FILE = Path("data/ersatzteile.json")


# -----------------------------------------------------------------------------
# Daten laden
# -----------------------------------------------------------------------------

def lade_ersatzteile():
    """Lädt die Ersatzteildaten aus der separaten JSON-Datei."""
    with open(ERSATZTEILE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def lade_modelle():
    """Lädt die Gerätedaten aus der JSON-Datei."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# -----------------------------------------------------------------------------
# Such- und Vergleichsfunktionen
# -----------------------------------------------------------------------------

def normalisiere_key(text):
    """
    Macht Modellnamen vergleichbar.

    Beispiele:
    'TASKalfa 5054ci' -> '5054ci'
    'ECOSYS PA6000x' -> 'pa6000x'
    """
    if not text:
        return ""

    return (
        str(text)
        .lower()
        .replace("taskalfa", "")
        .replace("ecosys", "")
        .replace("kyocera", "")
        .replace(" ", "")
        .replace("-", "")
        .strip()
    )


def normalisiere_text(text):
    """
    Vereinheitlicht Text für die Suche.

    Beispiel:
    "P-6034DN" wird zu "p6034dn"
    "TASKalfa 5054ci" wird zu "taskalfa5054ci"
    """
    if text is None:
        return ""

    return (
        str(text)
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def feld_passt(suchbegriff, feldinhalt):
    """
    Prüft, ob ein Suchbegriff zu einem bestimmten Feld passt.
    """
    if not feldinhalt:
        return False

    suchbegriff_klein = suchbegriff.lower().strip()
    feldinhalt_klein = str(feldinhalt).lower()

    suchbegriff_normalisiert = normalisiere_text(suchbegriff)
    feldinhalt_normalisiert = normalisiere_text(feldinhalt)

    return (
        suchbegriff_klein in feldinhalt_klein
        or suchbegriff_normalisiert in feldinhalt_normalisiert
    )


def baue_suchtext(eintrag):
    """
    Baut aus einem Geräteeintrag einen großen Suchtext.
    """
    teile = []

    teile.append(eintrag.get("id", ""))
    teile.append(eintrag.get("produktname", ""))
    teile.append(eintrag.get("code", ""))
    teile.append(eintrag.get("bemerkung", ""))

    marken = eintrag.get("marken", {})

    for modellbezeichnung in marken.values():
        if modellbezeichnung:
            teile.append(modellbezeichnung)

    for alias in eintrag.get("aliases", []):
        teile.append(alias)

    return " ".join(teile)


def suche_modelle(modelle, suchbegriff):
    """
    Durchsucht alle Modelle und gibt passende Treffer zurück.
    """
    suchbegriff = suchbegriff.strip()

    if suchbegriff == "":
        return []

    treffer = []

    for eintrag in modelle:
        suchtext = baue_suchtext(eintrag)

        if feld_passt(suchbegriff, suchtext):
            treffer.append(eintrag)

    return treffer


def erkenne_eingabe_marke(eintrag, suchbegriff):
    """
    Erkennt, zu welcher Marke die Eingabe gehört.

    Beispiel:
    Suche: "TASKalfa 5054ci" -> kyocera
    Suche: "5008ci" -> utax
    """
    marken = eintrag.get("marken", {})

    for marke, modellbezeichnung in marken.items():
        if feld_passt(suchbegriff, modellbezeichnung):
            return marke

    return None


def markenname_schoen(marke):
    """
    Wandelt interne Markennamen in schöne Anzeigenamen um.
    """
    namen = {
        "kyocera": "Kyocera",
        "utax": "UTAX"
    }

    return namen.get(marke, marke)


def bestimme_hauptanzeige(eintrag, suchbegriff):
    """
    Bestimmt, was groß in der Trefferkarte angezeigt wird.

    Regel:
    - Eingabe Kyocera -> zeige UTAX
    - Eingabe UTAX -> zeige Kyocera
    - Eingabe unklar -> zeige beide
    """
    marken = eintrag.get("marken", {})
    eingabe_marke = erkenne_eingabe_marke(eintrag, suchbegriff)

    kyocera = marken.get("kyocera")
    utax = marken.get("utax")

    if eingabe_marke == "kyocera":
        return {
            "titel": "UTAX",
            "modell": utax or "Keine UTAX-Zuordnung hinterlegt",
            "hinweis": f"Gefunden über: Kyocera {kyocera}"
        }

    if eingabe_marke == "utax":
        return {
            "titel": "Kyocera",
            "modell": kyocera or "Keine Kyocera-Zuordnung hinterlegt",
            "hinweis": f"Gefunden über: UTAX {utax}"
        }

    return {
        "titel": "Zuordnung",
        "modell": f"Kyocera: {kyocera or '-'} | UTAX: {utax or '-'}",
        "hinweis": "Eingabe konnte keiner eindeutigen Marke zugeordnet werden."
    }


def finde_ersatzteile(eintrag, ersatzteile_db):
    """
    Sucht die passenden Ersatzteile zu einem Modell-Eintrag.
    """
    modelle = ersatzteile_db.get("modelle", {})
    marken = eintrag.get("marken", {})

    moegliche_keys = [
        eintrag.get("id"),
        marken.get("kyocera"),
        marken.get("utax")
    ]

    for key in moegliche_keys:
        normalisiert = normalisiere_key(key)

        if normalisiert in modelle:
            return modelle[normalisiert]

    return None


# -----------------------------------------------------------------------------
# Anzeige-Helfer
# -----------------------------------------------------------------------------

def sicherer_text(wert):
    """
    Wandelt Werte sicher in Text um.
    None oder leere Werte werden als '-' angezeigt.
    """
    if wert is None or wert == "":
        return "-"

    return escape(str(wert))


def markenfarbe(marke):
    """
    Gibt die passende Hintergrundfarbe für Hersteller-Labels zurück.
    """
    farben = {
        "Kyocera": "#c00000",
        "UTAX": "#f28c00"
    }

    return farben.get(marke, "#4b5563")


def zeige_hauptanzeige(titel, modell):
    """
    Zeigt das direkte Suchergebnis kompakt als Chip-Zeile an.
    """
    if titel in ["Kyocera", "UTAX"]:
        st.markdown(
            f"""
            <div class="chip-row main-row">
                <span class="chip-label" style="background-color: {markenfarbe(titel)};">{sicherer_text(titel)}</span>
                <span class="chip-value">{sicherer_text(modell)}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="chip-row main-row">
                <span class="chip-label info-label-compact">{sicherer_text(titel)}</span>
                <span class="chip-value">{sicherer_text(modell)}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


def zeige_marken_zeile(name, wert):
    """
    Zeigt eine Modellbezeichnung kompakt im gleichen Chip-Stil wie Ersatzteile an.
    """
    st.markdown(
        f"""
        <div class="chip-row">
            <span class="chip-label" style="background-color: {markenfarbe(name)};">{sicherer_text(name)}</span>
            <span class="chip-value">{sicherer_text(wert)}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def zeige_info_zeile(label, wert):
    """
    Zeigt technische Informationen kompakt mit blauem Label und grünem Wert an.
    """
    st.markdown(
        f"""
        <div class="chip-row">
            <span class="chip-label info-label-compact">{sicherer_text(label)}</span>
            <span class="chip-value">{sicherer_text(wert)}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def formatiere_teil(teil):
    """
    Formatiert eine Ersatzteilnummer.
    Später kann hier ein echter Link zur Knowledgebase genutzt werden.
    """
    nummer = teil.get("nummer", "-")
    url = teil.get("url", "")

    if url:
        return f"[{nummer}]({url})"

    return f"`{nummer}`"


def zeige_ersatzteile(ersatzteil_daten):
    """
    Zeigt Ersatzteile im Stil der KyoceraCommunity-Struktur an:
    Main Parts und Toner/WTB.
    """
    if not ersatzteil_daten:
        st.info("Noch keine Ersatzteile hinterlegt.")
        return

    gruppen = ersatzteil_daten.get("gruppen", [])

    if not gruppen:
        st.info("Noch keine Ersatzteile hinterlegt.")
        return

    for gruppe in gruppen:
        name = gruppe.get("name", "Ersatzteile")
        teile = gruppe.get("teile", [])

        st.markdown(
            f"<span style='color: orange; font-weight: bold;'>{sicherer_text(name)}:</span>",
            unsafe_allow_html=True
        )

        if not teile:
            st.caption("Keine Teile in dieser Gruppe hinterlegt.")
            continue

        teile_ausgabe = " ".join(formatiere_teil(teil) for teil in teile)
        st.markdown(teile_ausgabe)


# -----------------------------------------------------------------------------
# Streamlit-Seite
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Kyocera / UTAX Modellfinder",
    page_icon="🔎",
    layout="centered"
)

st.markdown(
    """
    <style>
        .section-title {
            font-weight: 700;
            margin-top: 0.65rem;
            margin-bottom: 0.25rem;
            font-size: 0.95rem;
        }

        .chip-row {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            margin: 0.22rem 0;
            flex-wrap: wrap;
        }

        .main-row {
            margin-top: 0.1rem;
            margin-bottom: 0.05rem;
        }

        .chip-label {
            color: white;
            font-weight: 700;
            padding: 0.10rem 0.42rem;
            border-radius: 0.28rem;
            min-width: 68px;
            text-align: center;
            display: inline-block;
            font-size: 0.78rem;
            line-height: 1.45;
        }

        .chip-value {
            color: #22c55e;
            background-color: rgba(17, 24, 39, 0.65);
            border: 1px solid rgba(75, 85, 99, 0.55);
            border-radius: 0.28rem;
            padding: 0.08rem 0.35rem;
            font-weight: 700;
            font-size: 0.78rem;
            line-height: 1.45;
            display: inline-block;
        }

        .main-row .chip-label,
        .main-row .chip-value {
            font-size: 0.88rem;
            padding: 0.12rem 0.48rem;
        }

        .info-label-compact {
            background-color: #2563eb;
            min-width: 88px;
        }

        .stCaptionContainer {
            margin-top: -0.1rem;
            margin-bottom: 0.6rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Kyocera / UTAX Modellfinder")

st.write(
    "Gib ein Kyocera- oder UTAX-Modell ein. "
    "Die passende Gegenbezeichnung wird direkt angezeigt."
)


modelle = lade_modelle()
ersatzteile_db = lade_ersatzteile()

suchbegriff = st.text_input(
    "Modell suchen",
    placeholder="z. B. TASKalfa 5054ci, 5008ci, PA6000x, P-6034DN ..."
)


if suchbegriff.strip() == "":
    st.info("Gib ein Modell ein, um die passende Bezeichnung zu finden.")
    st.stop()


treffer = suche_modelle(modelle, suchbegriff)


st.write(f"Gefundene Treffer: {len(treffer)}")


if len(treffer) == 0:
    st.warning("Kein passendes Modell gefunden.")


for eintrag in treffer:
    marken = eintrag.get("marken", {})
    hauptanzeige = bestimme_hauptanzeige(eintrag, suchbegriff)

    with st.container(border=True):
        zeige_hauptanzeige(hauptanzeige["titel"], hauptanzeige["modell"])
        st.caption(hauptanzeige["hinweis"])

        st.markdown(
            '<div class="section-title">Modellbezeichnungen</div>',
            unsafe_allow_html=True
        )

        zeige_marken_zeile("Kyocera", marken.get("kyocera"))
        zeige_marken_zeile("UTAX", marken.get("utax"))

        with st.expander("Ersatzteile"):
            ersatzteil_daten = finde_ersatzteile(eintrag, ersatzteile_db)
            zeige_ersatzteile(ersatzteil_daten)

        with st.expander("Technische Informationen"):
            zeige_info_zeile("Produktname", eintrag.get("produktname", "-"))
            zeige_info_zeile("Code", eintrag.get("code", "-"))
            zeige_info_zeile("Beginn", eintrag.get("beginn", "-"))

            if eintrag.get("vertrieb_eingestellt"):
                vertrieb = "eingestellt"
            else:
                vertrieb = "aktiv / nicht als eingestellt markiert"

            zeige_info_zeile("Vertrieb", vertrieb)

            bemerkung = eintrag.get("bemerkung")

            if bemerkung:
                zeige_info_zeile("Bemerkung", bemerkung)
