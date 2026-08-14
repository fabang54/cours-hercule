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
# INITIALISATION DU COMPTEUR
# ============================================================

if "formulaire_id" not in st.session_state:
    st.session_state.formulaire_id = 0


# ============================================================
# PAGE : GESTION DES SÉANCES
# ============================================================

if page == "📚 Gestion des séances":

    st.title("📚 Gestion des séances")

    st.subheader("Nouvelle séance")

    # Identifiant unique du formulaire actuel
    f = st.session_state.formulaire_id


    # ========================================================
    # ÉLÈVE
    # ========================================================

    eleve = st.selectbox(
        "Élève",
        ELEVES,
        key=f"eleve_{f}"
    )


    # ========================================================
    # DATE ET HEURES
    # ========================================================

    date = st.date_input(
        "Date de la séance",
        key=f"date_{f}"
    )

    heure_debut = st.time_input(
        "Heure de début",
        key=f"heure_debut_{f}"
    )

    heure_fin = st.time_input(
        "Heure de fin",
        key=f"heure_fin_{f}"
    )


    # ========================================================
    # MODE
    # ========================================================

    mode = st.selectbox(
        "Mode",
        ["Présentiel", "Distanciel"],
        key=f"mode_{f}"
    )


    # ========================================================
    # DISCIPLINE(S)
    # ========================================================

    discipline = st.multiselect(
        "Discipline(s)",
        DISCIPLINES,
        key=f"discipline_{f}"
    )


    # ========================================================
    # CONTENU DE LA SÉANCE
    # ========================================================

    contenu = st.multiselect(
        "Contenu de la séance",
        CONTENUS,
        key=f"contenu_{f}"
    )

    contenu_manuel = st.text_input(
        "Ajouter un contenu personnalisé (facultatif)",
        key=f"contenu_manuel_{f}"
    )


    # ========================================================
    # TRAVAIL À FAIRE
    # ========================================================

    travail = st.multiselect(
        "Travail à faire",
        TRAVAUX,
        key=f"travail_{f}"
    )


    # ========================================================
    # OBSERVATIONS
    # ========================================================

    observation = st.multiselect(
        "Observations",
        OBSERVATIONS,
        key=f"observation_{f}"
    )

    observation_manuel = st.text_input(
        "Ajouter une observation personnalisée (facultatif)",
        key=f"observation_manuel_{f}"
    )


    # ========================================================
    # ENREGISTREMENT
    # ========================================================

    if st.button(
        "💾 Enregistrer la séance",
        key=f"enregistrer_{f}"
    ):

        # ----------------------------------------------------
        # CONTENU FINAL
        # ----------------------------------------------------

        contenu_final = contenu.copy()

        if contenu_manuel:
            contenu_final.append(contenu_manuel)


        # ----------------------------------------------------
        # OBSERVATION FINALE
        # ----------------------------------------------------

        observation_finale = observation.copy()

        if observation_manuel:
            observation_finale.append(observation_manuel)


        # ----------------------------------------------------
        # CRÉATION DE LA SÉANCE
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
        # MESSAGE DE CONFIRMATION
        # ----------------------------------------------------

        st.success("✅ Séance enregistrée !")


        # ----------------------------------------------------
        # NOUVEAU FORMULAIRE
        # ----------------------------------------------------

        st.session_state.formulaire_id += 1

        st.rerun()


# ============================================================
# PAGE : CAHIER DE TEXTE
# ============================================================

elif page == "📖 Cahier de texte":

    st.title("📖 Cahier de texte")

    st.subheader("Suivi des séances")


    # ========================================================
    # CHOIX DE L'ÉLÈVE
    # ========================================================

    eleve_cahier = st.selectbox(
        "Élève",
        ELEVES
    )


    # ========================================================
    # LECTURE DU FICHIER
    # ========================================================

    fichier = "seances.csv"

    if os.path.exists(fichier):

        df = pd.read_csv(fichier)


        # ====================================================
        # FILTRE SUR L'ÉLÈVE
        # ====================================================

        df_eleve = df[
            df["eleve"] == eleve_cahier
        ]


        if len(df_eleve) > 0:

            st.write(
                f"📖 **Cahier de texte de {eleve_cahier}**"
            )


            # =================================================
            # AFFICHAGE DES SÉANCES
            # =================================================

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
                f"Aucune séance enregistrée pour {eleve_cahier}."
            )


    else:

        st.info(
            "Aucune séance enregistrée pour le moment."
        )
