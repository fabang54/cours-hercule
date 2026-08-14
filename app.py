import streamlit as st
import pandas as pd
import os
from datetime import date, datetime


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
        "📖 Cahier de texte",
        "📊 Bilan mensuel"
    ]
)


# ============================================================
# COMPTEUR POUR RÉINITIALISER LE FORMULAIRE
# ============================================================

if "formulaire_id" not in st.session_state:
    st.session_state.formulaire_id = 0


# ============================================================
# PAGE 1 : GESTION DES SÉANCES
# ============================================================

if page == "📚 Gestion des séances":

    st.title("📚 Gestion des séances")

    st.subheader("Nouvelle séance")

    f = st.session_state.formulaire_id


    # --------------------------------------------------------
    # ÉLÈVE
    # --------------------------------------------------------

    eleve = st.selectbox(
        "Élève",
        ELEVES,
        key=f"eleve_{f}"
    )


    # --------------------------------------------------------
    # DATE ET HEURES
    # --------------------------------------------------------

    date_seance = st.date_input(
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


    # --------------------------------------------------------
    # MODE
    # --------------------------------------------------------

    mode = st.selectbox(
        "Mode",
        ["Présentiel", "Distanciel"],
        key=f"mode_{f}"
    )


    # --------------------------------------------------------
    # DISCIPLINES
    # --------------------------------------------------------

    discipline = st.multiselect(
        "Discipline(s)",
        DISCIPLINES,
        key=f"discipline_{f}"
    )


    # --------------------------------------------------------
    # CONTENU
    # --------------------------------------------------------

    contenu = st.multiselect(
        "Contenu de la séance",
        CONTENUS,
        key=f"contenu_{f}"
    )

    contenu_manuel = st.text_input(
        "Ajouter un contenu personnalisé (facultatif)",
        key=f"contenu_manuel_{f}"
    )


    # --------------------------------------------------------
    # TRAVAIL
    # --------------------------------------------------------

    travail = st.multiselect(
        "Travail à faire",
        TRAVAUX,
        key=f"travail_{f}"
    )


    # --------------------------------------------------------
    # OBSERVATIONS
    # --------------------------------------------------------

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

        contenu_final = contenu.copy()

        if contenu_manuel:
            contenu_final.append(contenu_manuel)


        observation_finale = observation.copy()

        if observation_manuel:
            observation_finale.append(observation_manuel)


        # ----------------------------------------------------
        # CALCUL DE LA DURÉE
        # ----------------------------------------------------

        debut_minutes = (
            heure_debut.hour * 60
            + heure_debut.minute
        )

        fin_minutes = (
            heure_fin.hour * 60
            + heure_fin.minute
        )

        duree_minutes = fin_minutes - debut_minutes

        if duree_minutes <= 0:

            st.error(
                "❌ L'heure de fin doit être supérieure "
                "à l'heure de début."
            )

            st.stop()


        # ----------------------------------------------------
        # CRÉATION DE LA SÉANCE
        # ----------------------------------------------------

        nouvelle_seance = pd.DataFrame([{

            "eleve": eleve,

            "date": date_seance,

            "heure_debut": heure_debut,

            "heure_fin": heure_fin,

            "duree_minutes": duree_minutes,

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


        st.success("✅ Séance enregistrée !")


        # ----------------------------------------------------
        # NOUVEAU FORMULAIRE
        # ----------------------------------------------------

        st.session_state.formulaire_id += 1

        st.rerun()


# ============================================================
# PAGE 2 : CAHIER DE TEXTE
# ============================================================

elif page == "📖 Cahier de texte":

    st.title("📖 Cahier de texte")

    st.subheader("Suivi des séances")


    eleve_cahier = st.selectbox(
        "Élève",
        ELEVES,
        key="cahier_eleve"
    )


    fichier = "seances.csv"


    if os.path.exists(fichier):

        df = pd.read_csv(fichier)


        df_eleve = df[
            df["eleve"] == eleve_cahier
        ]


        if len(df_eleve) > 0:

            st.write(
                f"📖 **Cahier de texte de {eleve_cahier}**"
            )


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
                f"Aucune séance enregistrée pour "
                f"{eleve_cahier}."
            )


    else:

        st.info(
            "Aucune séance enregistrée pour le moment."
        )


# ============================================================
# PAGE 3 : BILAN MENSUEL
# ============================================================

elif page == "📊 Bilan mensuel":

    st.title("📊 Bilan mensuel")

    st.subheader("Bilan individuel de l'élève")


    # ========================================================
    # SÉLECTION ÉLÈVE
    # ========================================================

    eleve_bilan = st.selectbox(
        "Élève",
        ELEVES,
        key="bilan_eleve"
    )


    # ========================================================
    # SÉLECTION DU MOIS
    # ========================================================

    mois = st.selectbox(
        "Mois",
        list(range(1, 13)),
        format_func=lambda x: datetime(
            2026,
            x,
            1
        ).strftime("%B"),
        key="bilan_mois"
    )


    annee = st.number_input(
        "Année",
        min_value=2020,
        max_value=2100,
        value=2026,
        step=1
    )


    # ========================================================
    # LECTURE DES SÉANCES
    # ========================================================

    fichier = "seances.csv"


    if not os.path.exists(fichier):

        st.info(
            "Aucune séance enregistrée."
        )

        st.stop()


    df = pd.read_csv(fichier)


    # ========================================================
    # CONVERSION DES DATES
    # ========================================================

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )


    # ========================================================
    # FILTRE
    # ========================================================

    df_bilan = df[
        (df["eleve"] == eleve_bilan)
        &
        (df["date"].dt.month == mois)
        &
        (df["date"].dt.year == annee)
    ]


    # ========================================================
    # AFFICHAGE
    # ========================================================

    mois_nom = datetime(
        annee,
        mois,
        1
    ).strftime("%B %Y")


    st.markdown(
        f"## 📊 Bilan de {eleve_bilan} — {mois_nom}"
    )


    if len(df_bilan) == 0:

        st.warning(
            "Aucune séance pour cet élève durant cette période."
        )

        st.stop()


    # ========================================================
    # NOMBRE DE SÉANCES
    # ========================================================

    nombre_seances = len(df_bilan)


    # ========================================================
    # NOMBRE D'HEURES
    # ========================================================

    total_minutes = df_bilan[
        "duree_minutes"
    ].sum()


    heures = int(
        total_minutes // 60
    )

    minutes = int(
        total_minutes % 60
    )


    # ========================================================
    # PRÉSENTIEL / DISTANCIEL
    # ========================================================

    minutes_presentiel = df_bilan[
        df_bilan["mode"] == "Présentiel"
    ]["duree_minutes"].sum()


    minutes_distanciel = df_bilan[
        df_bilan["mode"] == "Distanciel"
    ]["duree_minutes"].sum()


    # ========================================================
    # AFFICHAGE STATISTIQUES
    # ========================================================

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Nombre de séances",
            nombre_seances
        )


    with col2:

        st.metric(
            "Heures travaillées",
            f"{heures} h {minutes:02d}"
        )


    with col3:

        st.metric(
            "Durée moyenne",
            f"{total_minutes / nombre_seances:.0f} min"
        )


    # ========================================================
    # MODES
    # ========================================================

    st.subheader("🖥️ Mode des séances")


    heures_presentiel = int(
        minutes_presentiel // 60
    )

    min_presentiel = int(
        minutes_presentiel % 60
    )


    heures_distanciel = int(
        minutes_distanciel // 60
    )

    min_distanciel = int(
        minutes_distanciel % 60
    )


    st.write(
        f"🏫 Présentiel : "
        f"{heures_presentiel} h "
        f"{min_presentiel:02d}"
    )


    st.write(
        f"💻 Distanciel : "
        f"{heures_distanciel} h "
        f"{min_distanciel:02d}"
    )


    # ========================================================
    # DISCIPLINES
    # ========================================================

    st.subheader("📚 Disciplines travaillées")


    toutes_disciplines = []


    for valeur in df_bilan["disciplines"].dropna():

        for discipline in valeur.split(","):

            discipline = discipline.strip()

            if discipline:
                toutes_disciplines.append(
                    discipline
                )


    if toutes_disciplines:

        compteur_disciplines = pd.Series(
            toutes_disciplines
        ).value_counts()


        for discipline, nombre in compteur_disciplines.items():

            st.write(
                f"• {discipline} : "
                f"{nombre} séance(s)"
            )


    # ========================================================
    # OBSERVATIONS
    # ========================================================

    st.subheader("💬 Bilan comportement")


    toutes_observations = []


    for valeur in df_bilan["observations"].dropna():

        for observation in valeur.split(","):

            observation = observation.strip()

            if observation:
                toutes_observations.append(
                    observation
                )


    if toutes_observations:

        compteur_observations = pd.Series(
            toutes_observations
        ).value_counts()


        for observation, nombre in compteur_observations.items():

            st.write(
                f"• {observation} : "
                f"{nombre}"
            )


    else:

        st.write(
            "Aucune observation enregistrée."
        )


    # ========================================================
    # BILAN PERSONNALISÉ
    # ========================================================

    st.subheader("📝 Bilan personnalisé")


    bilan_personnalise = st.text_area(
        "Rédiger le bilan du mois",
        height=150,
        placeholder=(
            "Exemple : Nino a réalisé de bons progrès "
            "ce mois-ci. Il doit poursuivre ses efforts "
            "en calcul littéral..."
        )
    )


    if st.button(
        "💾 Enregistrer le bilan",
        key="enregistrer_bilan"
    ):

        st.success(
            "✅ Bilan enregistré."
        )
