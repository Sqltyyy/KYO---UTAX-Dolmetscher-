from pathlib import Path
import json

import streamlit as st


DATA_FILE = Path("data/modelle.json")

ERSATZTEILE_FILE = Path("data/ersatzteile.json")

def lade_ersatzteile():
    """Lädt die Ersatzteildaten aus der separaten JSON-Datei."""
    with open(ERSATZTEILE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


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
            f"<span style='color: orange; font-weight: bold;'>{name}:</span>",
            unsafe_allow_html=True
        )

        if not teile:
            st.caption("Keine Teile in dieser Gruppe hinterlegt.")
            continue

        teile_ausgabe = " ".join(formatiere_teil(teil) for teil in teile)

        st.markdown(teile_ausgabe)

def lade_modelle():
    """Lädt die Gerätedaten aus der JSON-Datei."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def normalisiere_text(text):
    """
    Vereinheitlicht Text für die Suche.

    Beispiel:
    "P-6034DN" wird zu "p6034dn"
    "TASKalfa 5054ci" wird zu "taskalfa5054ci"

    Dadurch findet die Suche auch Begriffe trotz Leerzeichen oder Bindestrichen.
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

    Beispiel:
    suchbegriff = "5054ci"
    feldinhalt = "TASKalfa 5054ci"
    → passt
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

    Dieser Suchtext wird nur für die allgemeine Suche benutzt.
    Die Hersteller-Erkennung passiert später separat über 'marken'.
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
    Suche: "TASKalfa 5054ci"
    → kyocera

    Suche: "5008ci"
    → utax
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
    - Eingabe Kyocera → zeige UTAX
    - Eingabe UTAX oder Triumph-Adler → zeige Kyocera
    - Eingabe unklar → zeige Kyocera und UTAX
    """
    marken = eintrag.get("marken", {})
    eingabe_marke = erkenne_eingabe_marke(eintrag, suchbegriff)

    kyocera = marken.get("kyocera")
    utax = marken.get("utax")
    triumph_adler = marken.get("triumph_adler")

    if eingabe_marke == "kyocera":
        return {
            "titel": "UTAX",
            "modell": utax or "Keine UTAX-Zuordnung hinterlegt",
            "hinweis": f"Gefunden über: Kyocera {kyocera}"
        }

    if eingabe_marke in ["utax", "triumph_adler", "olivetti"]:
        return {
            "titel": "Kyocera",
            "modell": kyocera or "Keine Kyocera-Zuordnung hinterlegt",
            "hinweis": f"Gefunden über: {markenname_schoen(eingabe_marke)} {marken.get(eingabe_marke)}"
        }

    return {
        "titel": "Zuordnung",
        "modell": f"Kyocera: {kyocera or '-'} | UTAX: {utax or '-'}",
        "hinweis": "Eingabe konnte keiner eindeutigen Marke zugeordnet werden."
    }


st.set_page_config(
    page_title="Kyocera / UTAX Modellfinder",
    page_icon="🔎",
    layout="centered"
)


st.title("Kyocera / UTAX Modellfinder")

st.write(
    "Gib ein Kyocera-, UTAX- oder Triumph-Adler-Modell ein. "
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
        st.subheader(f"{hauptanzeige['titel']}: {hauptanzeige['modell']}")
        st.caption(hauptanzeige["hinweis"])

        # Modellbezeichnungen direkt sichtbar
        st.write("**Modellbezeichnungen:**")
        st.write(f"- Kyocera: {marken.get('kyocera') or '-'}")
        st.write(f"- UTAX: {marken.get('utax') or '-'}")

        # Ersatzteile als eigener aufklappbarer Bereich
        with st.expander("Ersatzteile"):
            ersatzteil_daten = finde_ersatzteile(eintrag, ersatzteile_db)
            zeige_ersatzteile(ersatzteil_daten)

        # Technische Informationen als eigener aufklappbarer Bereich
        with st.expander("Technische Informationen"):
            st.write(f"- Produktname: {eintrag.get('produktname', '-')}")
            st.write(f"- Code: {eintrag.get('code', '-')}")
            st.write(f"- Beginn: {eintrag.get('beginn', '-')}")

            if eintrag.get("vertrieb_eingestellt"):
                st.write("- Vertrieb: eingestellt")
            else:
                st.write("- Vertrieb: aktiv / nicht als eingestellt markiert")

            bemerkung = eintrag.get("bemerkung")

            if bemerkung:
                st.write(f"**Bemerkung:** {bemerkung}")