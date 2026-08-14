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
# MENU ESPACE ENSEIGNANT
# ============================================================

page = st.sidebar.radio(
    "Espace enseignant",
    [
        "📚 Gestion des séances",
        "📖 Cahier de texte"
    ]
)


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
    "Informatique",
    "Français",
    "Anglais",
    "Technologie",
    "Culture générale"
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
    "Probabilités"
]

TRAVAUX = [
    "Exercices du manuel",
    "Exercices supplémentaires",
    "Revoir le cours",
    "Apprendre le cours",
    "Préparer le prochain cours",
    "Aucun"
]

OBSERVATIONS = [
    "Élève attentif",
    "Élève fatigué",
    "Élève distrait",
    "Difficultés importantes",
    "Bonne participation",
    "Très bonne séance",
    "Progrès constatés"
]


# ============================================================
# PAGE 1 : GESTION DES SÉANCES
# ============================================================

if page == "📚 Gestion des séances":

    st.title("📚 Gestion des séances")

    st.subheader("Nouvelle séance")


    # ========================================================
    # ÉLÈVE
    # ========================================================

    eleve = st.selectbox(
        "Élève",
        ELEVES
    )


    # ========================================================
    # DATE ET HEURES
    # ========================================================

    date = st.date_input(
        "Date de la séance"
    )

    heure_debut = st.time_input(
        "Heure de début"
    )

    heure_fin = st.time_input(
        "Heure de fin"
    )


    # ========================================================
    # MODE
    # ========================================================

    mode = st.selectbox(
        "Mode",
        ["Présentiel", "Distanciel"]
    )


    # ========================================================
    # DISCIPLINE(S)
    # ========================================================

    discipline = st.multiselect(
        "Discipline(s)",
        DISCIPLINES
    )


    # ========================================================
    # CONTENU DE LA SÉANCE
    # ========================================================

    contenu = st.multiselect(
        "Contenu de la séance",
        CONTENUS
    )

    contenu_manuel = st.text_input(
        "Ajouter un contenu personnalisé (facultatif)"
    )

    if contenu_manuel:
        contenu.append(contenu_manuel)


    # ========================================================
    # TRAVAIL À FAIRE
    # ========================================================

    travail = st.multiselect(
        "Travail à faire",
        TRAVAUX
    )


    # ========================================================
    # OBSERVATIONS
    # ========================================================

    observation = st.multiselect(
        "Observations",
        OBSERVATIONS
    )

    observation_manuel = st.text_input(
        "Ajouter une observation personnalisée (facultatif)"
    )

    if observation_manuel:
        observation.append(observation_manuel)


    # ========================================================
    # ENREGISTREMENT
    # ========================================================

    if st.button("💾 Enregistrer la séance"):

        nouvelle_seance = pd.DataFrame([{
            "eleve": eleve,
            "date": date,
            "heure_debut": heure_debut,
            "heure_fin": heure_fin,
            "mode": mode,
            "disciplines": ", ".join(discipline),
            "contenu": ", ".join(contenu),
            "travail": ", ".join(travail),
            "observations": ", ".join(observation)
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


# ============================================================
# PAGE 2 : CAHIER DE TEXTE
# ============================================================

elif page == "📖 Cahier de texte":

    st.title("📖 Cahier de texte")

    st.subheader("Suivi des séances")

    st.info(
        "Le cahier de texte sera automatiquement alimenté "
        "par les séances enregistrées."
    )

    st.write("👨‍🎓 Élève")
    st.selectbox(
        "Sélectionner un élève",
        ELEVES,
        key="cahier_eleve"
    )

    st.write("📅 Historique des séances")

    st.write(
        "Aucune séance affichée pour le moment."
    )
