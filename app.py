import streamlit as st
import pandas as pd
import os

# ============================================================
# PROTECTION ENSEIGNANT
# ============================================================

mot_de_passe = st.text_input(
    "Mot de passe enseignant",
    type="password"
)

if mot_de_passe != st.secrets["mot_de_passe"]:
    st.info("🔒 Espace réservé à l'enseignant.")
    st.stop()


# ============================================================
# LISTES
# ============================================================

ELEVES = [
    "Nino",
    "Emma",
    "Lucas",
    "Sarah"
]

DISCIPLINES = [
    "Mathématiques",
    "Physique",
    "Informatique"
]

CONTENUS = [
    "Équations simples",
    "Fractions",
    "Calcul littéral",
    "Pythagore",
    "Fonctions",
    "Proportionnalité",
    "Géométrie",
    "Statistiques",
    "Probabilités",
    "Autre"
]

TRAVAUX = [
    "Exercices du manuel",
    "Exercices supplémentaires",
    "Revoir le cours",
    "Apprendre le cours",
    "Préparer le prochain cours",
    "Aucun",
    "Autre"
]

OBSERVATIONS = [
    "Élève attentif",
    "Élève fatigué",
    "Élève distrait",
    "Difficultés importantes",
    "Bonne participation",
    "Très bonne séance",
    "Progrès constatés",
    "Autre"
]


# ============================================================
# TITRE
# ============================================================

st.title("📚 Gestion des séances")

st.subheader("Nouvelle séance")


# ============================================================
# ÉLÈVE
# ============================================================

eleve = st.selectbox(
    "Élève",
    ELEVES
)


# ============================================================
# DATE ET HEURES
# ============================================================

date = st.date_input(
    "Date de la séance"
)

heure_debut = st.time_input(
    "Heure de début"
)

heure_fin = st.time_input(
    "Heure de fin"
)


# ============================================================
# MODE
# ============================================================

mode = st.selectbox(
    "Mode",
    ["Présentiel", "Distanciel"]
)


# ============================================================
# DISCIPLINE
# ============================================================

discipline = st.selectbox(
    "Discipline",
    DISCIPLINES
)


# ============================================================
# CONTENU
# ============================================================

contenu = st.selectbox(
    "Contenu de la séance",
    CONTENUS
)

if contenu == "Autre":
    contenu = st.text_input(
        "Préciser le contenu"
    )


# ============================================================
# TRAVAIL À FAIRE
# ============================================================

travail = st.selectbox(
    "Travail à faire",
    TRAVAUX
)

if travail == "Autre":
    travail = st.text_input(
        "Préciser le travail à faire"
    )


# ============================================================
# OBSERVATIONS
# ============================================================

observation = st.selectbox(
    "Observations",
    OBSERVATIONS
)

if observation == "Autre":
    observation = st.text_input(
        "Préciser l'observation"
    )


# ============================================================
# ENREGISTREMENT
# ============================================================

if st.button("💾 Enregistrer la séance"):

    nouvelle_seance = pd.DataFrame([{
        "eleve": eleve,
        "date": date,
        "heure_debut": heure_debut,
        "heure_fin": heure_fin,
        "mode": mode,
        "disciplines": discipline,
        "contenu": contenu,
        "travail": travail,
        "observations": observation
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
