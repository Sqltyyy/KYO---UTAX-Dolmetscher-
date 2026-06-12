from pathlib import Path
import json

import streamlit as st


DATA_FILE = Path("data/modelle.json")


def lade_modelle():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def baue_suchtext(eintrag):
    teile = []

    teile.append(eintrag.get("id", ""))
    teile.append(eintrag.get("kategorie", ""))
    teile.append(eintrag.get("geraetetyp", ""))
    teile.append(eintrag.get("produktname", ""))
    teile.append(eintrag.get("code", ""))
    teile.append(eintrag.get("bemerkung", ""))

    marken = eintrag.get("marken", {})

    for modellbezeichnung in marken.values():
        if modellbezeichnung:
            teile.append(modellbezeichnung)

    for alias in eintrag.get("aliases", []):
        teile.append(alias)

    return " ".join(teile).lower()


def suche_modelle(modelle, suchbegriff):
    suchbegriff = suchbegriff.lower().strip()

    if suchbegriff == "":
        return modelle

    treffer = []

    for eintrag in modelle:
        suchtext = baue_suchtext(eintrag)

        if suchbegriff in suchtext:
            treffer.append(eintrag)

    return treffer


st.set_page_config(
    page_title="Kyocera / UTAX Modellfinder",
    page_icon="🔎",
    layout="centered"
)

st.title("Kyocera / UTAX Modellfinder")

st.write(
    "Suche nach Kyocera-, UTAX-, Triumph-Adler- oder baugleichen Modellbezeichnungen."
)

modelle = lade_modelle()

suchbegriff = st.text_input(
    "Modell suchen",
    placeholder="z. B. 5054ci, 5008ci, PA6000x, P-6034DN ..."
)

treffer = suche_modelle(modelle, suchbegriff)

st.write(f"Gefundene Treffer: {len(treffer)}")

for eintrag in treffer:
    marken = eintrag.get("marken", {})

    kyocera_modell = marken.get("kyocera") or "Unbekanntes Modell"

    with st.container(border=True):
        st.subheader(kyocera_modell)

        st.write(f"**Kategorie:** {eintrag.get('kategorie', '-')}")
        st.write(f"**Gerätetyp:** {eintrag.get('geraetetyp', '-')}")
        st.write(f"**Farbe:** {'Ja' if eintrag.get('farbe') else 'Nein'}")
        st.write(f"**Produktname:** {eintrag.get('produktname', '-')}")
        st.write(f"**Code:** {eintrag.get('code', '-')}")
        st.write(f"**Beginn:** {eintrag.get('beginn', '-')}")

        if eintrag.get("vertrieb_eingestellt"):
            st.write("**Vertrieb:** eingestellt")
        else:
            st.write("**Vertrieb:** aktiv / nicht als eingestellt markiert")

        st.write("**Modellbezeichnungen:**")
        st.write(f"- Kyocera: {marken.get('kyocera') or '-'}")
        st.write(f"- UTAX: {marken.get('utax') or '-'}")
        st.write(f"- Triumph-Adler: {marken.get('triumph_adler') or '-'}")
        st.write(f"- Olivetti: {marken.get('olivetti') or '-'}")

        bemerkung = eintrag.get("bemerkung")

        if bemerkung:
            st.write(f"**Bemerkung:** {bemerkung}")