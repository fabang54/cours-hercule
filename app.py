import streamlit as st
import pandas as pd

from supabase import create_client
from datetime import date, time, datetime

from io import BytesIO
import io


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cours Hercule",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# CONNEXION SUPABASE
# ============================================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


# ============================================================
# AUTHENTIFICATION GOOGLE
# ============================================================

def connexion_google():

    if not st.user.is_logged_in:

        st.title("📚 Cours Hercule")

        st.info(
            "Une connexion Google est nécessaire "
            "pour sauvegarder automatiquement les séances "
            "dans Google Drive."
        )

        if st.button(
            "🔐 Se connecter avec Google",
            type="primary"
        ):
            st.login("google")

        st.stop()


connexion_google()


# ============================================================
# PROTECTION ENSEIGNANT
# ============================================================

mot_de_passe = st.text_input(
    "Mot de passe enseignant",
    type="password"
)

if mot_de_passe != st.secrets["mot_de_passe"]:

    st.info(
        "🔒 Espace réservé à l'enseignant."
    )

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
    "Cultures générales"
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

MOIS = [
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


# ============================================================
# TITRE
# ============================================================

st.title("📚 Cours Hercule")


# ============================================================
# FONCTION : RÉCUPÉRER LES SÉANCES
# ============================================================

def recuperer_seances():

    resultat = (
        supabase
        .table("seances")
        .select("*")
        .order("date", desc=True)
        .execute()
    )

    donnees = resultat.data

    if not donnees:
        return pd.DataFrame()

    return pd.DataFrame(donnees)


# ============================================================
# GOOGLE DRIVE
# ============================================================

def obtenir_service_drive():

    """
    Construit le service Google Drive à partir
    du jeton d'accès fourni par Streamlit.
    """

    try:

        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        access_token = st.user.tokens["access"]

        credentials = Credentials(
            token=access_token
        )

        service = build(
            "drive",
            "v3",
            credentials=credentials,
            cache_discovery=False
        )

        return service

    except Exception as e:

        raise Exception(
            f"Connexion Google Drive impossible : {e}"
        )


# ============================================================
# EXPORT CSV
# ============================================================

def dataframe_csv_bytes(df):

    """
    Transforme le DataFrame en CSV UTF-8.
    """

    buffer = io.StringIO()

    df.to_csv(
        buffer,
        index=False,
        encoding="utf-8-sig"
    )

    return buffer.getvalue().encode("utf-8-sig")


# ============================================================
# SAUVEGARDE GOOGLE DRIVE
# ============================================================

def sauvegarder_dans_drive(df):

    """
    Crée seances.csv s'il n'existe pas.

    Sinon, met à jour le fichier existant.

    Il n'y aura donc qu'un seul fichier :
    seances.csv
    """

    from googleapiclient.http import MediaIoBaseUpload

    service = obtenir_service_drive()

    contenu_csv = dataframe_csv_bytes(df)

    media = MediaIoBaseUpload(
        BytesIO(contenu_csv),
        mimetype="text/csv",
        resumable=False
    )

    # --------------------------------------------------------
    # RECHERCHE DU FICHIER EXISTANT
    # --------------------------------------------------------

    resultat = (
        service.files()
        .list(
            q="name = 'seances.csv' "
              "and trashed = false",
            spaces="drive",
            fields="files(id, name)",
            pageSize=10
        )
        .execute()
    )

    fichiers = resultat.get(
        "files",
        []
    )

    # --------------------------------------------------------
    # MISE À JOUR
    # --------------------------------------------------------

    if fichiers:

        file_id = fichiers[0]["id"]

        (
            service.files()
            .update(
                fileId=file_id,
                media_body=media
            )
            .execute()
        )

        return "mis à jour"

    # --------------------------------------------------------
    # CRÉATION
    # --------------------------------------------------------

    else:

        metadata = {
            "name": "seances.csv",
            "mimeType": "text/csv"
        }

        (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id"
            )
            .execute()
        )

        return "créé"


# ============================================================
# SYNCHRONISATION GOOGLE DRIVE
# ============================================================

def synchroniser_drive():

    """
    Récupère toutes les séances depuis Supabase
    et les sauvegarde dans seances.csv.
    """

    df = recuperer_seances()

    if df.empty:

        return False, "Aucune séance à sauvegarder."

    try:

        resultat = sauvegarder_dans_drive(
            df
        )

        return (
            True,
            f"Google Drive : fichier seances.csv {resultat}."
        )

    except Exception as e:

        return (
            False,
            f"Google Drive indisponible : {e}"
        )


# ============================================================
# MENU
# ============================================================

menu = st.sidebar.radio(
    "Menu",
    [
        "📚 Gestion des séances",
        "📖 Cahier de texte",
        "📊 Bilan",
        "🧾 Facturation"
    ]
)


# ============================================================
# GESTION DES SÉANCES
# ============================================================

if menu == "📚 Gestion des séances":

    st.header("📚 Gestion des séances")

    action_seance = st.radio(
        "Que souhaitez-vous faire ?",
        [
            "➕ Nouvelle séance",
            "✏️ Modifier une séance"
        ],
        horizontal=True,
        key="action_seance"
    )


    # ========================================================
    # NOUVELLE SÉANCE
    # ========================================================

    if action_seance == "➕ Nouvelle séance":

        st.subheader("➕ Nouvelle séance")

        eleve = st.selectbox(
            "Élève",
            ELEVES,
            key="nouvelle_eleve"
        )

        date_seance = st.date_input(
            "Date de la séance",
            value=date.today(),
            key="nouvelle_date"
        )

        heure_debut = st.time_input(
            "Heure de début",
            value=time(14, 0),
            key="nouvelle_heure_debut"
        )

        heure_fin = st.time_input(
            "Heure de fin",
            value=time(15, 0),
            key="nouvelle_heure_fin"
        )

        mode = st.selectbox(
            "Mode",
            [
                "Présentiel",
                "Distanciel"
            ],
            key="nouvelle_mode"
        )

        disciplines = st.multiselect(
            "Discipline(s)",
            DISCIPLINES,
            key="nouvelles_disciplines"
        )

        contenu_selection = st.multiselect(
            "Contenu de la séance",
            CONTENUS,
            key="nouveaux_contenus"
        )

        contenu_manuel = st.text_area(
            "Saisie manuelle du contenu",
            key="contenu_manuel"
        )

        contenu_final = ", ".join(
            contenu_selection
        )

        if contenu_manuel.strip():

            if contenu_final:
                contenu_final += " — "

            contenu_final += contenu_manuel.strip()

        travail_selection = st.selectbox(
            "Travail à faire",
            TRAVAUX,
            key="nouveau_travail_selection"
        )

        if travail_selection == "Autre":

            travail = st.text_input(
                "Préciser le travail à faire",
                key="nouveau_travail_autre"
            )

        else:

            travail = travail_selection

        observations_selection = st.multiselect(
            "Observations",
            OBSERVATIONS,
            key="nouvelles_observations"
        )

        observation_manuel = st.text_area(
            "Saisie manuelle de l'observation",
            key="observation_manuel"
        )

        observation_finale = ", ".join(
            observations_selection
        )

        if observation_manuel.strip():

            if observation_finale:
                observation_finale += " — "

            observation_finale += observation_manuel.strip()


        # ====================================================
        # ENREGISTREMENT
        # ====================================================

        if st.button(
            "💾 Enregistrer la séance",
            type="primary"
        ):

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
                    "après l'heure de début."
                )

            elif not disciplines:

                st.error(
                    "❌ Sélectionnez au moins "
                    "une discipline."
                )

            elif not contenu_final.strip():

                st.error(
                    "❌ Indiquez le contenu "
                    "de la séance."
                )

            else:

                nouvelle_seance = {

                    "eleve": eleve,

                    "date":
                        date_seance.isoformat(),

                    "heure_debut":
                        heure_debut.strftime(
                            "%H:%M:%S"
                        ),

                    "heure_fin":
                        heure_fin.strftime(
                            "%H:%M:%S"
                        ),

                    "duree_minutes":
                        duree_minutes,

                    "mode":
                        mode,

                    "disciplines":
                        ", ".join(
                            disciplines
                        ),

                    "contenu":
                        contenu_final,

                    "travail":
                        travail,

                    "observations":
                        observation_finale
                }

                try:

                    # ----------------------------------------
                    # SUPABASE
                    # ----------------------------------------

                    (
                        supabase
                        .table("seances")
                        .insert(
                            nouvelle_seance
                        )
                        .execute()
                    )

                    st.success(
                        "✅ Séance enregistrée dans Supabase !"
                    )

                    # ----------------------------------------
                    # GOOGLE DRIVE
                    # ----------------------------------------

                    succes_drive, message_drive = (
                        synchroniser_drive()
                    )

                    if succes_drive:

                        st.success(
                            f"☁️ {message_drive}"
                        )

                    else:

                        st.warning(
                            f"⚠️ {message_drive}"
                        )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "❌ Erreur lors de l'enregistrement."
                    )

                    st.write(e)


    # ========================================================
    # MODIFICATION
    # ========================================================

    else:

        st.subheader(
            "✏️ Modifier une séance"
        )

        df = recuperer_seances()

        if df.empty:

            st.info(
                "Aucune séance enregistrée."
            )

        else:

            eleve_modification = st.selectbox(
                "Élève",
                sorted(
                    df["eleve"]
                    .dropna()
                    .unique()
                ),
                key="modif_eleve"
            )

            df_eleve = df[
                df["eleve"]
                == eleve_modification
            ].copy()

            df_eleve = df_eleve.sort_values(
                "date",
                ascending=False
            )

            choix = []

            for _, ligne in df_eleve.iterrows():

                choix.append(
                    f"{ligne['date']} - "
                    f"{ligne['heure_debut']} - "
                    f"{ligne['contenu']}"
                )

            index_choisi = st.selectbox(
                "Séance à modifier",
                range(len(choix)),
                format_func=lambda x: choix[x],
                key="choix_seance"
            )

            ligne = df_eleve.iloc[
                index_choisi
            ]

            identifiant = ligne["id"]

            st.markdown("---")

            nouvelle_date = st.date_input(
                "Date",
                value=datetime.strptime(
                    str(ligne["date"]),
                    "%Y-%m-%d"
                ).date(),
                key="modif_date"
            )

            try:

                heure_debut_initiale = (
                    datetime.strptime(
                        str(ligne["heure_debut"]),
                        "%H:%M:%S"
                    ).time()
                )

            except ValueError:

                heure_debut_initiale = (
                    datetime.strptime(
                        str(ligne["heure_debut"]),
                        "%H:%M"
                    ).time()
                )

            try:

                heure_fin_initiale = (
                    datetime.strptime(
                        str(ligne["heure_fin"]),
                        "%H:%M:%S"
                    ).time()
                )

            except ValueError:

                heure_fin_initiale = (
                    datetime.strptime(
                        str(ligne["heure_fin"]),
                        "%H:%M"
                    ).time()
                )

            nouvelle_heure_debut = st.time_input(
                "Heure de début",
                value=heure_debut_initiale,
                key="modif_heure_debut"
            )

            nouvelle_heure_fin = st.time_input(
                "Heure de fin",
                value=heure_fin_initiale,
                key="modif_heure_fin"
            )

            nouveau_mode = st.selectbox(
                "Mode",
                [
                    "Présentiel",
                    "Distanciel"
                ],
                index=(
                    0
                    if ligne["mode"] == "Présentiel"
                    else 1
                ),
                key="modif_mode"
            )

            nouvelle_disciplines = st.text_input(
                "Discipline(s)",
                value=str(
                    ligne["disciplines"]
                ),
                key="modif_disciplines"
            )

            nouveau_contenu = st.text_area(
                "Contenu",
                value=str(
                    ligne["contenu"]
                ),
                key="modif_contenu"
            )

            nouveau_travail = st.text_area(
                "Travail à faire",
                value=str(
                    ligne["travail"]
                ),
                key="modif_travail"
            )

            nouvelles_observations = st.text_area(
                "Observations",
                value=str(
                    ligne["observations"]
                ),
                key="modif_observations"
            )


            # =================================================
            # SAUVEGARDE MODIFICATION
            # =================================================

            if st.button(
                "💾 Enregistrer les modifications",
                type="primary"
            ):

                debut_minutes = (
                    nouvelle_heure_debut.hour * 60
                    + nouvelle_heure_debut.minute
                )

                fin_minutes = (
                    nouvelle_heure_fin.hour * 60
                    + nouvelle_heure_fin.minute
                )

                duree_minutes = (
                    fin_minutes - debut_minutes
                )

                if duree_minutes <= 0:

                    st.error(
                        "❌ L'heure de fin doit être "
                        "après l'heure de début."
                    )

                else:

                    modifications = {

                        "date":
                            nouvelle_date.isoformat(),

                        "heure_debut":
                            nouvelle_heure_debut.strftime(
                                "%H:%M:%S"
                            ),

                        "heure_fin":
                            nouvelle_heure_fin.strftime(
                                "%H:%M:%S"
                            ),

                        "duree_minutes":
                            duree_minutes,

                        "mode":
                            nouveau_mode,

                        "disciplines":
                            nouvelle_disciplines,

                        "contenu":
                            nouveau_contenu,

                        "travail":
                            nouveau_travail,

                        "observations":
                            nouvelles_observations
                    }

                    try:

                        (
                            supabase
                            .table("seances")
                            .update(
                                modifications
                            )
                            .eq(
                                "id",
                                identifiant
                            )
                            .execute()
                        )

                        st.success(
                            "✅ Séance modifiée avec succès !"
                        )

                        # ------------------------------------
                        # GOOGLE DRIVE
                        # ------------------------------------

                        succes_drive, message_drive = (
                            synchroniser_drive()
                        )

                        if succes_drive:

                            st.success(
                                f"☁️ {message_drive}"
                            )

                        else:

                            st.warning(
                                f"⚠️ {message_drive}"
                            )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur lors de la modification."
                        )

                        st.write(e)


# ============================================================
# CAHIER DE TEXTE
# ============================================================

elif menu == "📖 Cahier de texte":

    st.header(
        "📖 Cahier de texte"
    )

    df = recuperer_seances()

    if df.empty:

        st.info(
            "Aucune séance enregistrée."
        )

    else:

        eleve_cahier = st.selectbox(
            "Choisir l'élève",
            ELEVES,
            key="cahier_eleve"
        )

        df_eleve = df[
            df["eleve"]
            == eleve_cahier
        ].copy()

        if df_eleve.empty:

            st.info(
                "Aucune séance enregistrée "
                "pour cet élève."
            )

        else:

            df_eleve = df_eleve.sort_values(
                "date",
                ascending=False
            )

            for _, ligne in df_eleve.iterrows():

                st.markdown("---")

                st.subheader(
                    f"📅 {ligne['date']}"
                )

                st.write(
                    f"**Horaire :** "
                    f"{ligne['heure_debut']} → "
                    f"{ligne['heure_fin']}"
                )

                st.write(
                    f"**Discipline(s) :** "
                    f"{ligne['disciplines']}"
                )

                st.write(
                    f"**Contenu :** "
                    f"{ligne['contenu']}"
                )

                st.write(
                    f"**Travail à faire :** "
                    f"{ligne['travail']}"
                )

                st.write(
                    f"**Observations :** "
                    f"{ligne['observations']}"
                )


# ============================================================
# BILAN
# ============================================================

elif menu == "📊 Bilan":

    st.header(
        "📊 Bilan de l'élève"
    )

    df = recuperer_seances()

    if df.empty:

        st.info(
            "Aucune séance enregistrée."
        )

    else:

        eleve_bilan = st.selectbox(
            "Élève",
            ELEVES,
            key="bilan_eleve"
        )

        df_eleve = df[
            df["eleve"]
            == eleve_bilan
        ].copy()

        if df_eleve.empty:

            st.info(
                "Aucune séance pour cet élève."
            )

        else:

            total_minutes = pd.to_numeric(
                df_eleve["duree_minutes"],
                errors="coerce"
            ).fillna(0).sum()

            total_heures = (
                total_minutes / 60
            )

            nombre_seances = len(
                df_eleve
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Nombre de séances",
                    nombre_seances
                )

            with col2:

                st.metric(
                    "Heures travaillées",
                    f"{total_heures:.2f} h"
                )

            st.subheader(
                "📚 Séances"
            )

            st.dataframe(
                df_eleve[
                    [
                        "date",
                        "disciplines",
                        "contenu",
                        "observations"
                    ]
                ],
                use_container_width=True
            )


# ============================================================
# FACTURATION
# ============================================================

elif menu == "🧾 Facturation":

    st.header(
        "🧾 Facturation"
    )

    df = recuperer_seances()

    if df.empty:

        st.info(
            "Aucune séance enregistrée."
        )

    else:

        eleve_facturation = st.selectbox(
            "Élève",
            ELEVES,
            key="facturation_eleve"
        )

        type_periode = st.selectbox(
            "Période de facturation",
            [
                "Mensuelle",
                "Hebdomadaire",
                "Personnalisée",
                "Toutes les séances"
            ],
            key="type_periode"
        )


        # ====================================================
        # MENSUELLE
        # ====================================================

        if type_periode == "Mensuelle":

            mois_nom = st.selectbox(
                "Mois",
                MOIS,
                index=date.today().month - 1,
                key="facturation_mois"
            )

            mois = (
                MOIS.index(mois_nom)
                + 1
            )

            annee = st.number_input(
                "Année",
                min_value=2020,
                max_value=2100,
                value=date.today().year,
                step=1,
                key="facturation_annee"
            )

            df["date"] = pd.to_datetime(
                df["date"]
            )

            df_filtre = df[
                (df["eleve"] == eleve_facturation)
                &
                (df["date"].dt.month == mois)
                &
                (df["date"].dt.year == annee)
            ]

            periode_facture = (
                f"{mois_nom} {annee}"
            )


        # ====================================================
        # HEBDOMADAIRE
        # ====================================================

        elif type_periode == "Hebdomadaire":

            date_debut = st.date_input(
                "Début de la semaine",
                value=date.today(),
                key="semaine_debut"
            )

            date_fin = (
                date_debut
                + pd.Timedelta(days=6)
            )

            df["date"] = pd.to_datetime(
                df["date"]
            )

            df_filtre = df[
                (df["eleve"] == eleve_facturation)
                &
                (df["date"].dt.date >= date_debut)
                &
                (df["date"].dt.date <= date_fin)
            ]

            periode_facture = (
                f"du "
                f"{date_debut.strftime('%d/%m/%Y')} "
                f"au "
                f"{date_fin.strftime('%d/%m/%Y')}"
            )


        # ====================================================
        # PERSONNALISÉE
        # ====================================================

        elif type_periode == "Personnalisée":

            date_debut = st.date_input(
                "Date de début",
                value=date.today(),
                key="periode_debut"
            )

            date_fin = st.date_input(
                "Date de fin",
                value=date.today(),
                key="periode_fin"
            )

            df["date"] = pd.to_datetime(
                df["date"]
            )

            if date_fin < date_debut:

                st.error(
                    "❌ La date de fin doit être "
                    "postérieure à la date de début."
                )

                df_filtre = pd.DataFrame()

                periode_facture = ""

            else:

                df_filtre = df[
                    (df["eleve"] == eleve_facturation)
                    &
                    (df["date"].dt.date >= date_debut)
                    &
                    (df["date"].dt.date <= date_fin)
                ]

                periode_facture = (
                    f"du "
                    f"{date_debut.strftime('%d/%m/%Y')} "
                    f"au "
                    f"{date_fin.strftime('%d/%m/%Y')}"
                )


        # ====================================================
        # TOUTES LES SÉANCES
        # ====================================================

        else:

            df_filtre = df[
                df["eleve"]
                == eleve_facturation
            ].copy()

            periode_facture = (
                "Toutes les séances"
            )


        # ====================================================
        # RÉSULTAT
        # ====================================================

        if df_filtre.empty:

            st.warning(
                "Aucune séance pour cette période."
            )

        else:

            total_minutes = pd.to_numeric(
                df_filtre["duree_minutes"],
                errors="coerce"
            ).fillna(0).sum()

            total_heures = (
                total_minutes / 60
            )

            st.subheader(
                "Résumé de la facture"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Nombre de séances",
                    len(df_filtre)
                )

            with col2:

                st.metric(
                    "Nombre d'heures",
                    f"{total_heures:.2f} h"
                )

            tarif = st.number_input(
                "Tarif horaire (€)",
                min_value=0.0,
                value=30.0,
                step=1.0,
                key="tarif_horaire"
            )

            montant = (
                total_heures
                * tarif
            )

            st.metric(
                "Montant de la facture",
                f"{montant:.2f} €"
            )


            # =================================================
            # DÉTAIL
            # =================================================

            st.subheader(
                "Détail des séances"
            )

            st.dataframe(
                df_filtre[
                    [
                        "date",
                        "heure_debut",
                        "heure_fin",
                        "disciplines",
                        "contenu",
                        "duree_minutes"
                    ]
                ],
                use_container_width=True
            )


            # =================================================
            # FACTURE PDF
            # =================================================

            st.markdown("---")

            st.subheader(
                "📄 Facture pour la famille"
            )

            nom_facture = st.text_input(
                "Nom de la famille",
                value=f"Famille de {eleve_facturation}",
                key="nom_facture"
            )

            adresse_facture = st.text_area(
                "Adresse de facturation (facultatif)",
                key="adresse_facture"
            )

            numero_facture = st.text_input(
                "Numéro de facture",
                value=(
                    f"FAC-"
                    f"{date.today().strftime('%Y%m%d')}"
                ),
                key="numero_facture"
            )


            # =================================================
            # GÉNÉRATION PDF
            # =================================================

            if st.button(
                "📄 Générer la facture PDF",
                type="primary"
            ):

                try:

                    from reportlab.lib.pagesizes import A4

                    from reportlab.platypus import (
                        SimpleDocTemplate,
                        Paragraph,
                        Spacer,
                        Table,
                        TableStyle
                    )

                    from reportlab.lib import colors

                    from reportlab.lib.styles import (
                        getSampleStyleSheet
                    )

                    from reportlab.lib.units import cm


                    buffer = BytesIO()

                    document = SimpleDocTemplate(
                        buffer,
                        pagesize=A4,
                        rightMargin=1.5 * cm,
                        leftMargin=1.5 * cm,
                        topMargin=1.5 * cm,
                        bottomMargin=1.5 * cm
                    )

                    styles = (
                        getSampleStyleSheet()
                    )

                    elements = []


                    # -----------------------------------------
                    # TITRE
                    # -----------------------------------------

                    elements.append(
                        Paragraph(
                            "<b>COURS HERCULE</b>",
                            styles["Title"]
                        )
                    )

                    elements.append(
                        Spacer(
                            1,
                            0.5 * cm
                        )
                    )

                    elements.append(
                        Paragraph(
                            "<b>FACTURE</b>",
                            styles["Heading2"]
                        )
                    )

                    elements.append(
                        Spacer(
                            1,
                            0.3 * cm
                        )
                    )


                    # -----------------------------------------
                    # INFORMATIONS
                    # -----------------------------------------

                    informations = [

                        [
                            "Numéro de facture",
                            numero_facture
                        ],

                        [
                            "Date",
                            date.today().strftime(
                                "%d/%m/%Y"
                            )
                        ],

                        [
                            "Famille",
                            nom_facture
                        ],

                        [
                            "Élève",
                            eleve_facturation
                        ],

                        [
                            "Période",
                            periode_facture
                        ]
                    ]

                    if adresse_facture.strip():

                        informations.append(
                            [
                                "Adresse",
                                adresse_facture
                            ]
                        )


                    table_info = Table(
                        informations,
                        colWidths=[
                            5 * cm,
                            11 * cm
                        ]
                    )

                    table_info.setStyle(
                        TableStyle(
                            [
                                (
                                    "GRID",
                                    (0, 0),
                                    (-1, -1),
                                    0.5,
                                    colors.grey
                                ),

                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (0, -1),
                                    colors.lightgrey
                                ),

                                (
                                    "VALIGN",
                                    (0, 0),
                                    (-1, -1),
                                    "TOP"
                                ),

                                (
                                    "PADDING",
                                    (0, 0),
                                    (-1, -1),
                                    6
                                )
                            ]
                        )
                    )

                    elements.append(
                        table_info
                    )

                    elements.append(
                        Spacer(
                            1,
                            0.7 * cm
                        )
                    )


                    # -----------------------------------------
                    # TABLEAU SÉANCES
                    # -----------------------------------------

                    donnees_facture = [

                        [
                            "Date",
                            "Horaire",
                            "Discipline",
                            "Durée"
                        ]
                    ]

                    for _, ligne in (
                        df_filtre.iterrows()
                    ):

                        duree = float(
                            ligne[
                                "duree_minutes"
                            ]
                        )

                        duree_heures = (
                            duree / 60
                        )

                        donnees_facture.append(
                            [

                                pd.to_datetime(
                                    ligne["date"]
                                ).strftime(
                                    "%d/%m/%Y"
                                ),

                                (
                                    f"{ligne['heure_debut']} "
                                    f"- "
                                    f"{ligne['heure_fin']}"
                                ),

                                str(
                                    ligne[
                                        "disciplines"
                                    ]
                                ),

                                f"{duree_heures:.2f} h"
                            ]
                        )


                    table_seances = Table(
                        donnees_facture,
                        colWidths=[
                            3 * cm,
                            4 * cm,
                            6 * cm,
                            3 * cm
                        ],
                        repeatRows=1
                    )

                    table_seances.setStyle(
                        TableStyle(
                            [
                                (
                                    "GRID",
                                    (0, 0),
                                    (-1, -1),
                                    0.5,
                                    colors.grey
                                ),

                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, 0),
                                    colors.lightgrey
                                ),

                                (
                                    "FONTNAME",
                                    (0, 0),
                                    (-1, 0),
                                    "Helvetica-Bold"
                                ),

                                (
                                    "ALIGN",
                                    (-1, 1),
                                    (-1, -1),
                                    "RIGHT"
                                ),

                                (
                                    "VALIGN",
                                    (0, 0),
                                    (-1, -1),
                                    "MIDDLE"
                                ),

                                (
                                    "PADDING",
                                    (0, 0),
                                    (-1, -1),
                                    6
                                )
                            ]
                        )
                    )

                    elements.append(
                        table_seances
                    )

                    elements.append(
                        Spacer(
                            1,
                            0.7 * cm
                        )
                    )


                    # -----------------------------------------
                    # TOTAL
                    # -----------------------------------------

                    total_table = Table(
                        [

                            [
                                "Total des heures",
                                f"{total_heures:.2f} h"
                            ],

                            [
                                "Tarif horaire",
                                f"{tarif:.2f} €"
                            ],

                            [
                                "TOTAL À PAYER",
                                f"{montant:.2f} €"
                            ]

                        ],
                        colWidths=[
                            11 * cm,
                            5 * cm
                        ]
                    )

                    total_table.setStyle(
                        TableStyle(
                            [

                                (
                                    "GRID",
                                    (0, 0),
                                    (-1, -1),
                                    0.5,
                                    colors.grey
                                ),

                                (
                                    "ALIGN",
                                    (1, 0),
                                    (1, -1),
                                    "RIGHT"
                                ),

                                (
                                    "FONTNAME",
                                    (0, 2),
                                    (-1, 2),
                                    "Helvetica-Bold"
                                ),

                                (
                                    "FONTSIZE",
                                    (0, 2),
                                    (-1, 2),
                                    12
                                ),

                                (
                                    "PADDING",
                                    (0, 0),
                                    (-1, -1),
                                    7
                                )
                            ]
                        )
                    )

                    elements.append(
                        total_table
                    )

                    elements.append(
                        Spacer(
                            1,
                            1 * cm
                        )
                    )


                    elements.append(
                        Paragraph(
                            "Merci pour votre confiance.",
                            styles["Normal"]
                        )
                    )


                    # -----------------------------------------
                    # CRÉATION PDF
                    # -----------------------------------------

                    document.build(
                        elements
                    )

                    buffer.seek(0)

                    st.success(
                        "✅ Facture PDF générée !"
                    )

                    st.download_button(
                        label=(
                            "⬇️ Télécharger "
                            "la facture PDF"
                        ),

                        data=buffer,

                        file_name=(
                            f"facture_"
                            f"{eleve_facturation}_"
                            f"{date.today().strftime('%Y%m%d')}.pdf"
                        ),

                        mime="application/pdf"
                    )


                except ImportError:

                    st.error(
                        "❌ ReportLab n'est pas installé."
                    )

                    st.info(
                        "Ajoutez reportlab dans "
                        "requirements.txt."
                    )


                except Exception as e:

                    st.error(
                        "❌ Erreur lors de la génération "
                        "de la facture PDF."
                    )

                    st.write(e)


# ============================================================
# FIN
# ============================================================
