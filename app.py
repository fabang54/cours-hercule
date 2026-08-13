import streamlit as st
import pandas as pd
import os

# =========================
# PROTECTION ENSEIGNANT
# =========================

mot_de_passe = st.text_input(
    "Mot de passe enseignant",
    type="password"
)

if mot_de_passe != st.secrets["mot_de_passe"]:
    st.info("🔒 Espace réservé à l'enseignant.")
    st.stop()

# =========================
# GESTION DES SÉANCES
# =========================

st.title("Gestion des séances")

st.subheader("Nouvelle séance")

eleve = st.text_input("Nom de l'élève")

date = st.date_input("Date de la séance")

heure_debut = st.time_input("Heure de début")
heure_fin = st.time_input("Heure de fin")

mode = st.selectbox(
    "Mode",
    ["Présentiel", "Distanciel"]
)

disciplines = st.multiselect(
    "Discipline(s)",
    ["Mathématiques", "Physique", "Informatique"]
)

contenu = st.text_area("Contenu de la séance")

travail = st.text_area("Travail à faire")

observations = st.text_area("Observations")

# =========================
# ENREGISTREMENT
# =========================

if st.button("Enregistrer"):

    nouvelle_seance = pd.DataFrame([{
        "eleve": eleve,
        "date": date,
        "heure_debut": heure_debut,
        "heure_fin": heure_fin,
        "mode": mode,
        "disciplines": ", ".join(disciplines),
        "contenu": contenu,
        "travail": travail,
        "observations": observations
    }])

    fichier = "seances.csv"

    if os.path.exists(fichier):

        nouvelle_seance.to_csv(
            fichier,
            mode="a",
            header=False,
            index=False
        )

    else:

        nouvelle_seance.to_csv(
            fichier,
            index=False
        )

    st.success("✅ Séance enregistrée !")
