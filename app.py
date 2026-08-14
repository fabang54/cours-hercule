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
# PAGE : GESTION DES SÉANCES
# ============================================================

if page == "📚 Gestion des séances":

    st.title("📚 Gestion des séances")
    st.subheader("Nouvelle séance")

    # --------------------------------------------------------
    # VALEURS PAR DÉFAUT
    # --------------------------------------------------------

    if "seance_enregistree" not in st.session_state:
        st.session_state.seance_enregistree = False

    # --------------------------------------------------------
    # ÉLÈVE
    # --------------------------------------------------------

    eleve = st.selectbox(
        "Élève",
        ELEVES,
        key="eleve"
    )

    # --------------------------------------------------------
    # DATE ET HEURES
    # --------------------------------------------------------

    date = st.date_input(
        "Date de la séance",
        key="date"
    )

    heure_debut = st.time_input(
        "Heure de début",
        key="heure_debut"
    )

    heure_fin = st.time_input(
        "Heure de fin",
        key="heure_fin"
    )

    # --------------------------------------------------------
    # MODE
    # --------------------------------------------------------

    mode = st.selectbox(
        "Mode",
        ["Présentiel", "Distanciel"],
        key="mode"
    )

    # --------------------------------------------------------
    # DISCIPLINE(S)
    # --------------------------------------------------------

    discipline = st.multiselect(
        "Discipline(s)",
        DISCIPLINES,
        key="discipline"
    )

    # --------------------------------------------------------
    # CONTENU
    # --------------------------------------------------------

    contenu = st.multiselect(
        "Contenu de la séance",
        CONTENUS,
        key="contenu"
    )

    contenu_manuel = st.text_input(
        "Ajouter un contenu personnalisé (facultatif)",
        key="contenu_manuel"
    )

    # --------------------------------------------------------
    # TRAVAIL À FAIRE
    # --------------------------------------------------------

    travail = st.multiselect(
        "Travail à faire",
        TRAVAUX,
        key="travail"
    )

    # --------------------------------------------------------
    # OBSERVATIONS
    # --------------------------------------------------------

    observation = st.multiselect(
        "Observations",
        OBSERVATIONS,
        key="observation"
    )

    observation_manuel = st.text_input(
        "Ajouter une observation personnalisée (facultatif)",
        key="observation_manuel"
    )

    # ========================================================
    # ENREGISTREMENT
    # ========================================================

    if st.button("💾 Enregistrer la séance"):

        # Ajouter le contenu manuel
        contenu_final = contenu.copy()

        if contenu_manuel:
            contenu_final.append(contenu_manuel)

        # Ajouter l'observation manuelle
        observation_finale = observation.copy()

        if observation_manuel:
            observation_finale.append(observation_manuel)

        # ----------------------------------------------------
        # CRÉATION DE LA LIGNE
        # ----------------------------------------------------

        nouvelle_seance = pd.DataFrame([{
            "eleve": eleve,
            "date": date,
            "heure_debut": heure_debut,
            "heure_fin": heure_fin,
            "mode": mode,
            "disciplines": ", ".join(discipline),
            "contenu": ", ".join(contenu_final),
            "travail": ", ".join(travail),
            "observations": ", ".join(observation_finale)
        }])

        # ----------------------------------------------------
        # ENREGISTREMENT CSV
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # MESSAGE
        # ----------------------------------------------------

        st.success("✅ Séance enregistrée !")

        # ----------------------------------------------------
        # RÉINITIALISATION
        # ----------------------------------------------------

        st.session_state["eleve"] = ELEVES[0]
        st.session_state["discipline"] = []
        st.session_state["contenu"] = []
        st.session_state["contenu_manuel"] = ""
        st.session_state["travail"] = []
        st.session_state["observation"] = []
        st.session_state["observation_manuel"] = ""

        st.rerun()


# ============================================================
# PAGE : CAHIER DE TEXTE
# ============================================================

elif page == "📖 Cahier de texte":

    st.title("📖 Cahier de texte")

    st.subheader("Suivi des séances")

    st.info(
        "Le cahier de texte sera automatiquement alimenté "
        "par les séances enregistrées."
    )

    eleve_cahier = st.selectbox(
        "Élève",
        ELEVES,
        key="cahier_eleve"
    )

    st.write("📅 Historique des séances")

    fichier = "seances.csv"

    if os.path.exists(fichier):

        df = pd.read_csv(fichier)

        # Séances de l'élève sélectionné
        df_eleve = df[
            df["eleve"] == eleve_cahier
        ]

        if len(df_eleve) > 0:

            for _, seance in df_eleve.iterrows():

                st.markdown("---")

                st.subheader(
                    f"📅 {seance['date']}"
                )

                st.write(
                    f"⏰ {seance['heure_debut']} → "
                    f"{seance['heure_fin']}"
                )

                st.write(
                    f"📚 **Discipline(s) :** "
                    f"{seance['disciplines']}"
                )

                st.write(
                    f"📖 **Contenu :** "
                    f"{seance['contenu']}"
                )

                st.write(
                    f"📝 **Travail à faire :** "
                    f"{seance['travail']}"
                )

                st.write(
                    f"💬 **Observations :** "
                    f"{seance['observations']}"
                )

        else:

            st.info(
                "Aucune séance enregistrée pour cet élève."
            )

    else:

        st.info(
            "Aucune séance enregistrée pour le moment."
        )
