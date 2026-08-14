import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


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
        "📊 Bilan mensuel",
        "🧾 Facturation"
    ]
)


# ============================================================
# COMPTEUR POUR RÉINITIALISER LE FORMULAIRE
# ============================================================

if "formulaire_id" not in st.session_state:
    st.session_state.formulaire_id = 0


# ============================================================
# PAGE : GESTION DES SÉANCES
# ============================================================

if page == "📚 Gestion des séances":

    st.title("📚 Gestion des séances")

    operation = st.radio(
        "Action",
        [
            "➕ Nouvelle séance",
            "✏️ Modifier une séance"
        ],
        horizontal=True
    )


    # ========================================================
    # NOUVELLE SÉANCE
    # ========================================================

    if operation == "➕ Nouvelle séance":

        st.subheader("Nouvelle séance")

        f = st.session_state.formulaire_id

        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        eleve = st.selectbox(
            "Élève",
            ELEVES,
            key=f"eleve_{f}"
        )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        date_seance = st.date_input(
            "Date de la séance",
            key=f"date_{f}"
        )

        # ----------------------------------------------------
        # HEURES
        # ----------------------------------------------------

        heure_debut = st.time_input(
            "Heure de début",
            key=f"heure_debut_{f}"
        )

        heure_fin = st.time_input(
            "Heure de fin",
            key=f"heure_fin_{f}"
        )

        # ----------------------------------------------------
        # MODE
        # ----------------------------------------------------

        mode = st.selectbox(
            "Mode",
            [
                "Présentiel",
                "Distanciel"
            ],
            key=f"mode_{f}"
        )

        # ----------------------------------------------------
        # DISCIPLINES
        # ----------------------------------------------------

        discipline = st.multiselect(
            "Discipline(s)",
            DISCIPLINES,
            key=f"discipline_{f}"
        )

        # ----------------------------------------------------
        # CONTENU
        # ----------------------------------------------------

        contenu = st.multiselect(
            "Contenu de la séance",
            CONTENUS,
            key=f"contenu_{f}"
        )

        contenu_manuel = st.text_input(
            "Ajouter un contenu personnalisé (facultatif)",
            key=f"contenu_manuel_{f}"
        )

        # ----------------------------------------------------
        # TRAVAIL
        # ----------------------------------------------------

        travail = st.multiselect(
            "Travail à faire",
            TRAVAUX,
            key=f"travail_{f}"
        )

        # ----------------------------------------------------
        # OBSERVATIONS
        # ----------------------------------------------------

        observation = st.multiselect(
            "Observations",
            OBSERVATIONS,
            key=f"observation_{f}"
        )

        observation_manuel = st.text_input(
            "Ajouter une observation personnalisée (facultatif)",
            key=f"observation_manuel_{f}"
        )


        # ====================================================
        # ENREGISTREMENT
        # ====================================================

        if st.button(
            "💾 Enregistrer la séance",
            key=f"enregistrer_{f}"
        ):

            # ------------------------------------------------
            # CALCUL DURÉE
            # ------------------------------------------------

            debut_minutes = (
                heure_debut.hour * 60
                + heure_debut.minute
            )

            fin_minutes = (
                heure_fin.hour * 60
                + heure_fin.minute
            )

            duree_minutes = (
                fin_minutes - debut_minutes
            )

            if duree_minutes <= 0:

                st.error(
                    "❌ L'heure de fin doit être "
                    "supérieure à l'heure de début."
                )

                st.stop()


            # ------------------------------------------------
            # CONTENU FINAL
            # ------------------------------------------------

            contenu_final = contenu.copy()

            if contenu_manuel.strip():

                contenu_final.append(
                    contenu_manuel.strip()
                )


            # ------------------------------------------------
            # OBSERVATION FINALE
            # ------------------------------------------------

            observation_finale = observation.copy()

            if observation_manuel.strip():

                observation_finale.append(
                    observation_manuel.strip()
                )


            # ------------------------------------------------
            # CRÉATION DE LA SÉANCE
            # ------------------------------------------------

            nouvelle_seance = pd.DataFrame([{

                "eleve": eleve,

                "date": date_seance,

                "heure_debut": heure_debut,

                "heure_fin": heure_fin,

                "duree_minutes": duree_minutes,

                "mode": mode,

                "disciplines": ", ".join(
                    discipline
                ),

                "contenu": ", ".join(
                    contenu_final
                ),

                "travail": ", ".join(
                    travail
                ),

                "observations": ", ".join(
                    observation_finale
                )
            }])


            # ------------------------------------------------
            # SAUVEGARDE
            # ------------------------------------------------

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


            st.success(
                "✅ Séance enregistrée !"
            )


            # ------------------------------------------------
            # NOUVEAU FORMULAIRE
            # ------------------------------------------------

            st.session_state.formulaire_id += 1

            st.rerun()


    # ========================================================
    # MODIFIER UNE SÉANCE
    # ========================================================

    elif operation == "✏️ Modifier une séance":

        st.subheader("✏️ Modifier une séance")

        fichier = "seances.csv"

        if not os.path.exists(fichier):

            st.info(
                "Aucune séance enregistrée."
            )

            st.stop()


        df = pd.read_csv(fichier)

        if len(df) == 0:

            st.info(
                "Aucune séance enregistrée."
            )

            st.stop()


        # ----------------------------------------------------
        # LISTE DES SÉANCES
        # ----------------------------------------------------

        liste_seances = []

        for index, ligne in df.iterrows():

            texte = (
                f"{index + 1} — "
                f"{ligne.get('date', '')} — "
                f"{ligne.get('eleve', '')} — "
                f"{ligne.get('heure_debut', '')} → "
                f"{ligne.get('heure_fin', '')} — "
                f"{ligne.get('disciplines', '')}"
            )

            liste_seances.append(texte)


        choix = st.selectbox(
            "Séance à modifier",
            liste_seances
        )

        index = liste_seances.index(choix)

        ancienne_seance = df.iloc[index]


        st.markdown("---")


        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        eleve_modif = st.selectbox(
            "Élève",
            ELEVES,
            index=(
                ELEVES.index(
                    ancienne_seance["eleve"]
                )
                if ancienne_seance["eleve"] in ELEVES
                else 0
            )
        )


        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        try:

            date_modif = pd.to_datetime(
                ancienne_seance["date"]
            ).date()

        except:

            date_modif = datetime.now().date()


        date_modif = st.date_input(
            "Date de la séance",
            value=date_modif
        )


        # ----------------------------------------------------
        # HEURE DÉBUT
        # ----------------------------------------------------

        try:

            heure_debut_modif = datetime.strptime(
                str(ancienne_seance["heure_debut"]),
                "%H:%M:%S"
            ).time()

        except:

            try:

                heure_debut_modif = datetime.strptime(
                    str(ancienne_seance["heure_debut"]),
                    "%H:%M"
                ).time()

            except:

                heure_debut_modif = datetime.now().time()


        heure_debut_modif = st.time_input(
            "Heure de début",
            value=heure_debut_modif
        )


        # ----------------------------------------------------
        # HEURE FIN
        # ----------------------------------------------------

        try:

            heure_fin_modif = datetime.strptime(
                str(ancienne_seance["heure_fin"]),
                "%H:%M:%S"
            ).time()

        except:

            try:

                heure_fin_modif = datetime.strptime(
                    str(ancienne_seance["heure_fin"]),
                    "%H:%M"
                ).time()

            except:

                heure_fin_modif = datetime.now().time()


        heure_fin_modif = st.time_input(
            "Heure de fin",
            value=heure_fin_modif
        )


        # ----------------------------------------------------
        # MODE
        # ----------------------------------------------------

        modes = [
            "Présentiel",
            "Distanciel"
        ]

        ancien_mode = ancienne_seance.get(
            "mode",
            "Présentiel"
        )

        mode_modif = st.selectbox(
            "Mode",
            modes,
            index=(
                modes.index(ancien_mode)
                if ancien_mode in modes
                else 0
            )
        )


        # ----------------------------------------------------
        # DISCIPLINES
        # ----------------------------------------------------

        anciennes_disciplines = str(
            ancienne_seance.get(
                "disciplines",
                ""
            )
        )

        disciplines_selectionnees = [
            x.strip()
            for x in anciennes_disciplines.split(",")
            if x.strip() in DISCIPLINES
        ]

        discipline_modif = st.multiselect(
            "Discipline(s)",
            DISCIPLINES,
            default=disciplines_selectionnees
        )


        # ----------------------------------------------------
        # CONTENU
        # ----------------------------------------------------

        ancien_contenu = str(
            ancienne_seance.get(
                "contenu",
                ""
            )
        )

        contenus_selectionnes = [
            x.strip()
            for x in ancien_contenu.split(",")
            if x.strip() in CONTENUS
        ]

        contenu_modif = st.multiselect(
            "Contenu de la séance",
            CONTENUS,
            default=contenus_selectionnes
        )


        # ----------------------------------------------------
        # CONTENU PERSONNALISÉ
        # ----------------------------------------------------

        contenu_personnalise = [
            x.strip()
            for x in ancien_contenu.split(",")
            if x.strip()
            and x.strip() not in CONTENUS
        ]

        contenu_manuel_modif = st.text_input(
            "Contenu personnalisé",
            value=", ".join(
                contenu_personnalise
            )
        )


        # ----------------------------------------------------
        # TRAVAIL
        # ----------------------------------------------------

        ancien_travail = str(
            ancienne_seance.get(
                "travail",
                ""
            )
        )

        travail_selectionne = [
            x.strip()
            for x in ancien_travail.split(",")
            if x.strip() in TRAVAUX
        ]

        travail_modif = st.multiselect(
            "Travail à faire",
            TRAVAUX,
            default=travail_selectionne
        )


        # ----------------------------------------------------
        # OBSERVATIONS
        # ----------------------------------------------------

        anciennes_observations = str(
            ancienne_seance.get(
                "observations",
                ""
            )
        )

        observations_selectionnees = [
            x.strip()
            for x in anciennes_observations.split(",")
            if x.strip() in OBSERVATIONS
        ]

        observation_modif = st.multiselect(
            "Observations",
            OBSERVATIONS,
            default=observations_selectionnees
        )


        # ----------------------------------------------------
        # OBSERVATION PERSONNALISÉE
        # ----------------------------------------------------

        observations_personnalisees = [
            x.strip()
            for x in anciennes_observations.split(",")
            if x.strip()
            and x.strip() not in OBSERVATIONS
        ]

        observation_manuel_modif = st.text_input(
            "Observation personnalisée",
            value=", ".join(
                observations_personnalisees
            )
        )


        # ====================================================
        # ENREGISTRER MODIFICATIONS
        # ====================================================

        if st.button(
            "💾 Enregistrer les modifications"
        ):

            debut_minutes = (
                heure_debut_modif.hour * 60
                + heure_debut_modif.minute
            )

            fin_minutes = (
                heure_fin_modif.hour * 60
                + heure_fin_modif.minute
            )

            duree_minutes = (
                fin_minutes - debut_minutes
            )

            if duree_minutes <= 0:

                st.error(
                    "❌ L'heure de fin doit être "
                    "supérieure à l'heure de début."
                )

                st.stop()


            contenu_final_modif = (
                contenu_modif.copy()
            )

            if contenu_manuel_modif.strip():

                contenu_final_modif.append(
                    contenu_manuel_modif.strip()
                )


            observation_finale_modif = (
                observation_modif.copy()
            )

            if observation_manuel_modif.strip():

                observation_finale_modif.append(
                    observation_manuel_modif.strip()
                )


            # ------------------------------------------------
            # MODIFICATION
            # ------------------------------------------------

            df.at[
                index,
                "eleve"
            ] = eleve_modif

            df.at[
                index,
                "date"
            ] = date_modif

            df.at[
                index,
                "heure_debut"
            ] = heure_debut_modif

            df.at[
                index,
                "heure_fin"
            ] = heure_fin_modif

            df.at[
                index,
                "duree_minutes"
            ] = duree_minutes

            df.at[
                index,
                "mode"
            ] = mode_modif

            df.at[
                index,
                "disciplines"
            ] = ", ".join(
                discipline_modif
            )

            df.at[
                index,
                "contenu"
            ] = ", ".join(
                contenu_final_modif
            )

            df.at[
                index,
                "travail"
            ] = ", ".join(
                travail_modif
            )

            df.at[
                index,
                "observations"
            ] = ", ".join(
                observation_finale_modif
            )


            # ------------------------------------------------
            # SAUVEGARDE
            # ------------------------------------------------

            df.to_csv(
                fichier,
                index=False
            )

            st.success(
                "✅ Séance modifiée avec succès !"
            )

            st.rerun()


# ============================================================
# PAGE : CAHIER DE TEXTE
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
                f"📖 **Cahier de texte de "
                f"{eleve_cahier}**"
            )


            # Plus récente en premier
            df_eleve = df_eleve.iloc[::-1]


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
                f"Aucune séance enregistrée "
                f"pour {eleve_cahier}."
            )


    else:

        st.info(
            "Aucune séance enregistrée "
            "pour le moment."
        )


# ============================================================
# PAGE : BILAN MENSUEL
# ============================================================

elif page == "📊 Bilan mensuel":

    st.title("📊 Bilan mensuel")

    st.subheader(
        "Bilan individuel de l'élève"
    )


    # --------------------------------------------------------
    # ÉLÈVE
    # --------------------------------------------------------

    eleve_bilan = st.selectbox(
        "Élève",
        ELEVES,
        key="bilan_eleve"
    )


    # --------------------------------------------------------
    # MOIS
    # --------------------------------------------------------

    mois_noms = [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre"
    ]


    mois = st.selectbox(
        "Mois",
        range(1, 13),
        format_func=lambda x: mois_noms[x - 1],
        key="bilan_mois"
    )


    annee = st.number_input(
        "Année",
        min_value=2020,
        max_value=2100,
        value=2026,
        step=1
    )


    # --------------------------------------------------------
    # LECTURE
    # --------------------------------------------------------

    fichier = "seances.csv"


    if not os.path.exists(fichier):

        st.info(
            "Aucune séance enregistrée."
        )

        st.stop()


    df = pd.read_csv(fichier)


    if len(df) == 0:

        st.info(
            "Aucune séance enregistrée."
        )

        st.stop()


    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # DURÉE
    # --------------------------------------------------------

    if "duree_minutes" not in df.columns:

        def calculer_duree(ligne):

            try:

                debut = datetime.strptime(
                    str(ligne["heure_debut"]),
                    "%H:%M:%S"
                )

            except:

                debut = datetime.strptime(
                    str(ligne["heure_debut"]),
                    "%H:%M"
                )


            try:

                fin = datetime.strptime(
                    str(ligne["heure_fin"]),
                    "%H:%M:%S"
                )

            except:

                fin = datetime.strptime(
                    str(ligne["heure_fin"]),
                    "%H:%M"
                )


            return (
                fin.hour * 60
                + fin.minute
                - debut.hour * 60
                - debut.minute
            )


        df["duree_minutes"] = df.apply(
            calculer_duree,
            axis=1
        )


    else:

        df["duree_minutes"] = pd.to_numeric(
            df["duree_minutes"],
            errors="coerce"
        )


    # --------------------------------------------------------
    # FILTRE
    # --------------------------------------------------------

    df_bilan = df[
        (df["eleve"] == eleve_bilan)
        &
        (df["date"].dt.month == mois)
        &
        (df["date"].dt.year == annee)
    ]


    mois_nom = mois_noms[mois - 1]


    st.markdown(
        f"## 📊 Bilan de {eleve_bilan} "
        f"— {mois_nom} {annee}"
    )


    if len(df_bilan) == 0:

        st.warning(
            "Aucune séance pour cet élève "
            "durant cette période."
        )

        st.stop()


    # --------------------------------------------------------
    # CALCUL
    # --------------------------------------------------------

    nombre_seances = len(df_bilan)

    total_minutes = int(
        df_bilan["duree_minutes"].sum()
    )

    heures = total_minutes // 60

    minutes = total_minutes % 60

    moyenne = round(
        total_minutes / nombre_seances
    )


    # --------------------------------------------------------
    # PRÉSENTIEL
    # --------------------------------------------------------

    minutes_presentiel = int(
        df_bilan[
            df_bilan["mode"] == "Présentiel"
        ]["duree_minutes"].sum()
    )


    # --------------------------------------------------------
    # DISTANCIEL
    # --------------------------------------------------------

    minutes_distanciel = int(
        df_bilan[
            df_bilan["mode"] == "Distanciel"
        ]["duree_minutes"].sum()
    )


    # --------------------------------------------------------
    # STATISTIQUES
    # --------------------------------------------------------

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
            f"{moyenne} min"
        )


    # --------------------------------------------------------
    # MODES
    # --------------------------------------------------------

    st.subheader(
        "🖥️ Mode des séances"
    )


    st.write(
        f"🏫 Présentiel : "
        f"{minutes_presentiel // 60} h "
        f"{minutes_presentiel % 60:02d}"
    )


    st.write(
        f"💻 Distanciel : "
        f"{minutes_distanciel // 60} h "
        f"{minutes_distanciel % 60:02d}"
    )


    # --------------------------------------------------------
    # DISCIPLINES
    # --------------------------------------------------------

    st.subheader(
        "📚 Disciplines travaillées"
    )


    toutes_disciplines = []


    for valeur in df_bilan[
        "disciplines"
    ].dropna():

        for discipline in str(
            valeur
        ).split(","):

            discipline = discipline.strip()

            if discipline:

                toutes_disciplines.append(
                    discipline
                )


    if toutes_disciplines:

        compteur = pd.Series(
            toutes_disciplines
        ).value_counts()


        for discipline, nombre in compteur.items():

            st.write(
                f"• {discipline} : "
                f"{nombre} séance(s)"
            )


    # --------------------------------------------------------
    # OBSERVATIONS
    # --------------------------------------------------------

    st.subheader(
        "💬 Bilan comportement"
    )


    toutes_observations = []


    for valeur in df_bilan[
        "observations"
    ].dropna():

        for observation in str(
            valeur
        ).split(","):

            observation = observation.strip()

            if observation:

                toutes_observations.append(
                    observation
                )


    if toutes_observations:

        compteur_observations = pd.Series(
            toutes_observations
        ).value_counts()


        for observation, nombre in (
            compteur_observations.items()
        ):

            st.write(
                f"• {observation} : "
                f"{nombre}"
            )


    else:

        st.write(
            "Aucune observation enregistrée."
        )


    # --------------------------------------------------------
    # BILAN PERSONNALISÉ
    # --------------------------------------------------------

    st.subheader(
        "📝 Bilan personnalisé"
    )


    bilan_personnalise = st.text_area(
        "Rédiger le bilan du mois",
        height=150,
        placeholder=(
            "Exemple : Nino a réalisé de bons "
            "progrès ce mois-ci..."
        )
    )


    if st.button(
        "💾 Enregistrer le bilan",
        key="enregistrer_bilan"
    ):

        st.success(
            "✅ Bilan enregistré."
        )


# ============================================================
# PAGE : FACTURATION
# ============================================================

elif page == "🧾 Facturation":

    st.title("🧾 Facturation")

    st.subheader(
        "Facture mensuelle"
    )


    # ========================================================
    # ÉLÈVE
    # ========================================================

    eleve_facture = st.selectbox(
        "Élève",
        ELEVES,
        key="facture_eleve"
    )


    # ========================================================
    # MOIS
    # ========================================================

    mois_noms = [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre"
    ]


    mois_facture = st.selectbox(
        "Mois",
        range(1, 13),
        format_func=lambda x: mois_noms[x - 1],
        key="facture_mois"
    )


    # ========================================================
    # ANNÉE
    # ========================================================

    annee_facture = st.number_input(
        "Année",
        min_value=2020,
        max_value=2100,
        value=2026,
        step=1,
        key="facture_annee"
    )


    # ========================================================
    # TARIF
    # ========================================================

    tarif_horaire = st.number_input(
        "Tarif horaire (€)",
        min_value=0.0,
        value=35.0,
        step=1.0,
        key="tarif_horaire"
    )


    # ========================================================
    # LECTURE DU CSV
    # ========================================================

    fichier = "seances.csv"


    if not os.path.exists(fichier):

        st.info(
            "Aucune séance enregistrée."
        )

        st.stop()


    df_facture = pd.read_csv(
        fichier
    )


    if len(df_facture) == 0:

        st.info(
            "Aucune séance enregistrée."
        )

        st.stop()


    # ========================================================
    # DATES
    # ========================================================

    df_facture["date"] = pd.to_datetime(
        df_facture["date"],
        errors="coerce"
    )


    # ========================================================
    # CALCUL DE LA DURÉE
    # ========================================================

    if "duree_minutes" not in df_facture.columns:

        def calculer_duree_facture(ligne):

            try:

                debut = datetime.strptime(
                    str(ligne["heure_debut"]),
                    "%H:%M:%S"
                )

            except:

                debut = datetime.strptime(
                    str(ligne["heure_debut"]),
                    "%H:%M"
                )


            try:

                fin = datetime.strptime(
                    str(ligne["heure_fin"]),
                    "%H:%M:%S"
                )

            except:

                fin = datetime.strptime(
                    str(ligne["heure_fin"]),
                    "%H:%M"
                )


            return (
                fin.hour * 60
                + fin.minute
                - debut.hour * 60
                - debut.minute
            )


        df_facture["duree_minutes"] = df_facture.apply(
            calculer_duree_facture,
            axis=1
        )

    else:

        df_facture["duree_minutes"] = pd.to_numeric(
            df_facture["duree_minutes"],
            errors="coerce"
        )


    # ========================================================
    # FILTRE ÉLÈVE + MOIS
    # ========================================================

    df_mois = df_facture[
        (df_facture["eleve"] == eleve_facture)
        &
        (df_facture["date"].dt.month == mois_facture)
        &
        (df_facture["date"].dt.year == annee_facture)
    ]


    # ========================================================
    # AUCUNE SÉANCE
    # ========================================================

    if len(df_mois) == 0:

        st.warning(
            "Aucune séance trouvée pour "
            f"{eleve_facture} en "
            f"{mois_noms[mois_facture - 1]} "
            f"{annee_facture}."
        )

        st.stop()


    # ========================================================
    # CALCUL DES HEURES
    # ========================================================

    total_minutes = int(
        df_mois["duree_minutes"].sum()
    )


    total_heures = (
        total_minutes / 60
    )


    heures_entieres = (
        total_minutes // 60
    )

    minutes_restantes = (
        total_minutes % 60
    )


    # ========================================================
    # CALCUL DU TOTAL
    # ========================================================

    montant_total = (
        total_heures * tarif_horaire
    )


    # ========================================================
    # AFFICHAGE
    # ========================================================

    st.markdown("---")

    st.subheader(
        f"🧾 Facture — {eleve_facture}"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Nombre de séances",
            len(df_mois)
        )


    with col2:

        st.metric(
            "Heures",
            f"{heures_entieres} h "
            f"{minutes_restantes:02d}"
        )


    with col3:

        st.metric(
            "Total",
            f"{montant_total:.2f} €"
        )


    # ========================================================
    # DÉTAIL
    # ========================================================

    st.subheader(
        "📋 Détail des séances"
    )


    tableau_facture = df_mois[
        [
            "date",
            "heure_debut",
            "heure_fin",
            "duree_minutes",
            "mode",
            "disciplines"
        ]
    ].copy()


    tableau_facture["date"] = (
        tableau_facture["date"]
        .dt.strftime("%d/%m/%Y")
    )


    tableau_facture["Durée"] = (
        tableau_facture["duree_minutes"]
        .apply(
            lambda x:
            f"{int(x // 60)} h "
            f"{int(x % 60):02d}"
        )
    )


    tableau_facture = tableau_facture[
        [
            "date",
            "heure_debut",
            "heure_fin",
            "Durée",
            "mode",
            "disciplines"
        ]
    ]


    tableau_facture.columns = [
        "Date",
        "Début",
        "Fin",
        "Durée",
        "Mode",
        "Discipline(s)"
    ]


    st.dataframe(
        tableau_facture,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # RÉCAPITULATIF
    # ========================================================

    st.markdown("---")

    st.write(
        f"**Élève :** {eleve_facture}"
    )

    st.write(
        f"**Période :** "
        f"{mois_noms[mois_facture - 1]} "
        f"{annee_facture}"
    )

    st.write(
        f"**Nombre d'heures :** "
        f"{heures_entieres} h "
        f"{minutes_restantes:02d}"
    )

    st.write(
        f"**Tarif horaire :** "
        f"{tarif_horaire:.2f} €"
    )

    st.markdown(
        f"### 💶 Total à payer : "
        f"{montant_total:.2f} €"
    )


    # ========================================================
    # GÉNÉRATION DU PDF
    # ========================================================

    def generer_facture_pdf(
        eleve,
        mois,
        annee,
        df_seances,
        tarif,
        montant
    ):

        buffer = BytesIO()


        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )


        styles = getSampleStyleSheet()


        titre = styles["Title"]

        titre.alignment = TA_CENTER


        normal = styles["Normal"]


        total_style = styles["Heading2"]

        total_style.alignment = TA_RIGHT


        elements = []


        # ----------------------------------------------------
        # EN-TÊTE
        # ----------------------------------------------------

        elements.append(
            Paragraph(
                "COURS HERCULE",
                titre
            )
        )


        elements.append(
            Paragraph(
                "Cours particuliers",
                normal
            )
        )


        elements.append(
            Spacer(1, 25)
        )


        # ----------------------------------------------------
        # NUMÉRO
        # ----------------------------------------------------

        numero_facture = (
            f"{annee}-{mois:02d}-{eleve}"
        )


        elements.append(
            Paragraph(
                f"<b>FACTURE N° :</b> "
                f"{numero_facture}",
                normal
            )
        )


        elements.append(
            Spacer(1, 10)
        )


        elements.append(
            Paragraph(
                f"<b>Élève :</b> {eleve}",
                normal
            )
        )


        elements.append(
            Paragraph(
                f"<b>Période :</b> "
                f"{mois_noms[mois - 1]} "
                f"{annee}",
                normal
            )
        )


        elements.append(
            Spacer(1, 25)
        )


        # ----------------------------------------------------
        # TABLEAU
        # ----------------------------------------------------

        donnees = [
            [
                "Date",
                "Début",
                "Fin",
                "Durée",
                "Mode"
            ]
        ]


        for _, ligne in df_seances.iterrows():

            duree = int(
                ligne["duree_minutes"]
            )

            duree_texte = (
                f"{duree // 60} h "
                f"{duree % 60:02d}"
            )


            date_texte = (
                ligne["date"]
                .strftime("%d/%m/%Y")
                if hasattr(
                    ligne["date"],
                    "strftime"
                )
                else str(
                    ligne["date"]
                )
            )


            donnees.append(
                [
                    date_texte,
                    str(
                        ligne["heure_debut"]
                    ),
                    str(
                        ligne["heure_fin"]
                    ),
                    duree_texte,
                    str(
                        ligne["mode"]
                    )
                ]
            )


        # Ligne total
        donnees.append(
            [
                "",
                "",
                "TOTAL",
                f"{total_heures:.2f} h",
                ""
            ]
        )


        tableau = Table(
            donnees,
            colWidths=[
                75,
                60,
                60,
                70,
                90
            ]
        )


        tableau.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold"
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (-1, -1),
                    "CENTER"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ])
        )


        elements.append(
            tableau
        )


        elements.append(
            Spacer(1, 25)
        )


        # ----------------------------------------------------
        # TARIF
        # ----------------------------------------------------

        elements.append(
            Paragraph(
                f"Tarif horaire : "
                f"{tarif:.2f} €",
                normal
            )
        )


        elements.append(
            Spacer(1, 10)
        )


        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        elements.append(
            Paragraph(
                f"<b>TOTAL À PAYER : "
                f"{montant:.2f} €</b>",
                total_style
            )
        )


        elements.append(
            Spacer(1, 40)
        )


        elements.append(
            Paragraph(
                "Merci pour votre confiance.",
                normal
            )
        )


        document.build(
            elements
        )


        buffer.seek(0)


        return buffer


    # ========================================================
    # BOUTON PDF
    # ========================================================

    pdf = generer_facture_pdf(
        eleve_facture,
        mois_facture,
        annee_facture,
        df_mois,
        tarif_horaire,
        montant_total
    )


    st.download_button(
        label="📄 Télécharger la facture PDF",
        data=pdf,
        file_name=(
            f"facture_"
            f"{eleve_facture}_"
            f"{annee_facture}_"
            f"{mois_facture:02d}.pdf"
        ),
        mime="application/pdf"
    )
