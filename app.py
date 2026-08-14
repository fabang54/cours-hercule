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
# CONNEXION GOOGLE
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
# MOT DE PASSE ENSEIGNANT
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
# RÉCUPÉRER LES SÉANCES
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

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    try:

        access_token = st.user.tokens["access"]

    except Exception:

        raise Exception(
            "Jeton Google Drive introuvable. "
            "Reconnectez-vous avec Google."
        )

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


# ============================================================
# DATAFRAME → CSV
# ============================================================

def dataframe_csv_bytes(df):

    buffer = io.StringIO()

    df.to_csv(
        buffer,
        index=False,
        encoding="utf-8-sig"
    )

    return buffer.getvalue().encode(
        "utf-8-sig"
    )


# ============================================================
# SAUVEGARDE DANS GOOGLE DRIVE
# ============================================================

def sauvegarder_dans_drive(df):

    from googleapiclient.http import (
        MediaIoBaseUpload
    )

    service = obtenir_service_drive()


    # ========================================================
    # 1. CHERCHER LE DOSSIER COURS HERCULE
    # ========================================================

    resultat_dossier = (
        service.files()
        .list(
            q=(
                "name = 'Cours Hercule' "
                "and mimeType = "
                "'application/vnd.google-apps.folder' "
                "and trashed = false"
            ),
            spaces="drive",
            fields="files(id,name)",
            pageSize=10
        )
        .execute()
    )

    dossiers = resultat_dossier.get(
        "files",
        []
    )


    # ========================================================
    # 2. CRÉER LE DOSSIER S'IL N'EXISTE PAS
    # ========================================================

    if dossiers:

        dossier_id = dossiers[0]["id"]

    else:

        metadata_dossier = {
            "name": "Cours Hercule",
            "mimeType":
                "application/vnd.google-apps.folder"
        }

        dossier = (
            service.files()
            .create(
                body=metadata_dossier,
                fields="id,name"
            )
            .execute()
        )

        dossier_id = dossier["id"]


    # ========================================================
    # 3. CONVERTIR EN CSV
    # ========================================================

    contenu_csv = dataframe_csv_bytes(df)

    media = MediaIoBaseUpload(
        BytesIO(contenu_csv),
        mimetype="text/csv",
        resumable=False
    )


    # ========================================================
    # 4. CHERCHER SEANCES.CSV DANS LE DOSSIER
    # ========================================================

    resultat_fichier = (
        service.files()
        .list(
            q=(
                f"'{dossier_id}' in parents "
                "and name = 'seances.csv' "
                "and trashed = false"
            ),
            spaces="drive",
            fields="files(id,name)",
            pageSize=10
        )
        .execute()
    )

    fichiers = resultat_fichier.get(
        "files",
        []
    )


    # ========================================================
    # 5. METTRE À JOUR LE CSV
    # ========================================================

    if fichiers:

        fichier_id = fichiers[0]["id"]

        (
            service.files()
            .update(
                fileId=fichier_id,
                media_body=media
            )
            .execute()
        )

        return "mis à jour"


    # ========================================================
    # 6. CRÉER LE CSV
    # ========================================================

    metadata_fichier = {
        "name": "seances.csv",
        "parents": [dossier_id],
        "mimeType": "text/csv"
    }

    (
        service.files()
        .create(
            body=metadata_fichier,
            media_body=media,
            fields="id,name"
        )
        .execute()
    )

    return "créé"


# ============================================================
# SYNCHRONISATION
# ============================================================

def synchroniser_drive():

    df = recuperer_seances()

    if df.empty:

        return (
            False,
            "Aucune séance à sauvegarder."
        )

    try:

        resultat = sauvegarder_dans_drive(
            df
        )

        return (
            True,
            f"Google Drive : seances.csv {resultat}."
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

    st.header(
        "📚 Gestion des séances"
    )

    action_seance = st.radio(
        "Que souhaitez-vous faire ?",
        [
            "➕ Nouvelle séance",
            "✏️ Modifier une séance"
        ],
        horizontal=True
    )


    # ========================================================
    # NOUVELLE SÉANCE
    # ========================================================

    if action_seance == "➕ Nouvelle séance":

        st.subheader(
            "➕ Nouvelle séance"
        )

        eleve = st.selectbox(
            "Élève",
            ELEVES
        )

        date_seance = st.date_input(
            "Date de la séance",
            value=date.today()
        )

        heure_debut = st.time_input(
            "Heure de début",
            value=time(14, 0)
        )

        heure_fin = st.time_input(
            "Heure de fin",
            value=time(15, 0)
        )

        mode = st.selectbox(
            "Mode",
            [
                "Présentiel",
                "Distanciel"
            ]
        )

        disciplines = st.multiselect(
            "Discipline(s)",
            DISCIPLINES
        )

        contenu_selection = st.multiselect(
            "Contenu de la séance",
            CONTENUS
        )

        contenu_manuel = st.text_area(
            "Saisie manuelle du contenu"
        )

        contenu_final = ", ".join(
            contenu_selection
        )

        if contenu_manuel.strip():

            if contenu_final:
                contenu_final += " — "

            contenu_final += (
                contenu_manuel.strip()
            )

        travail_selection = st.selectbox(
            "Travail à faire",
            TRAVAUX
        )

        if travail_selection == "Autre":

            travail = st.text_input(
                "Préciser le travail à faire"
            )

        else:

            travail = travail_selection

        observations_selection = st.multiselect(
            "Observations",
            OBSERVATIONS
        )

        observation_manuel = st.text_area(
            "Saisie manuelle de l'observation"
        )

        observation_finale = ", ".join(
            observations_selection
        )

        if observation_manuel.strip():

            if observation_finale:
                observation_finale += " — "

            observation_finale += (
                observation_manuel.strip()
            )


        # ====================================================
        # ENREGISTRER
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
                fin_minutes
                - debut_minutes
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

                    "eleve":
                        eleve,

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
                        "❌ Erreur lors de "
                        "l'enregistrement."
                    )

                    st.write(e)


    # ========================================================
    # MODIFIER UNE SÉANCE
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
                )
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
                format_func=lambda x: choix[x]
            )

            ligne = df_eleve.iloc[
                index_choisi
            ]

            identifiant = ligne["id"]

            st.markdown("---")


            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            nouvelle_date = st.date_input(
                "Date",
                value=datetime.strptime(
                    str(ligne["date"]),
                    "%Y-%m-%d"
                ).date()
            )


            # ------------------------------------------------
            # HEURES
            # ------------------------------------------------

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
                value=heure_debut_initiale
            )

            nouvelle_heure_fin = st.time_input(
                "Heure de fin",
                value=heure_fin_initiale
            )


            # ------------------------------------------------
            # MODE
            # ------------------------------------------------

            nouveau_mode = st.selectbox(
                "Mode",
                [
                    "Présentiel",
                    "Distanciel"
                ],
                index=(
                    0
                    if ligne["mode"]
                    == "Présentiel"
                    else 1
                )
            )


            # ------------------------------------------------
            # DISCIPLINES
            # ------------------------------------------------

            nouvelle_disciplines = st.text_input(
                "Discipline(s)",
                value=str(
                    ligne["disciplines"]
                )
            )


            # ------------------------------------------------
            # CONTENU
            # ------------------------------------------------

            nouveau_contenu = st.text_area(
                "Contenu",
                value=str(
                    ligne["contenu"]
                )
            )


            # ------------------------------------------------
            # TRAVAIL
            # ------------------------------------------------

            nouveau_travail = st.text_area(
                "Travail à faire",
                value=str(
                    ligne["travail"]
                )
            )


            # ------------------------------------------------
            # OBSERVATIONS
            # ------------------------------------------------

            nouvelles_observations = st.text_area(
                "Observations",
                value=str(
                    ligne["observations"]
                )
            )


            # =================================================
            # ENREGISTRER MODIFICATION
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
                    fin_minutes
                    - debut_minutes
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
                            "✅ Séance modifiée "
                            "avec succès !"
                        )


                        # ------------------------------------
                        # DRIVE
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
                            "❌ Erreur lors de "
                            "la modification."
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
            ELEVES
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
            ELEVES
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
                df_eleve[
                    "duree_minutes"
                ],
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
            ELEVES
        )

        type_periode = st.selectbox(
            "Période de facturation",
            [
                "Mensuelle",
                "Hebdomadaire",
                "Personnalisée",
                "Toutes les séances"
            ]
        )


        # ====================================================
        # MENSUELLE
        # ====================================================

        if type_periode == "Mensuelle":

            mois_nom = st.selectbox(
                "Mois",
                MOIS,
                index=date.today().month - 1
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
                step=1
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
                value=date.today()
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
                value=date.today()
            )

            date_fin = st.date_input(
                "Date de fin",
                value=date.today()
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
        # RÉSULTAT FACTURATION
        # ====================================================

        if df_filtre.empty:

            st.warning(
                "Aucune séance pour cette période."
            )

        else:

            total_minutes = pd.to_numeric(
                df_filtre[
                    "duree_minutes"
                ],
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
                step=1.0
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
            # FACTURE
            # =================================================

            st.markdown("---")

            st.subheader(
                "📄 Facture pour la famille"
            )

            nom_facture = st.text_input(
                "Nom de la famille",
                value=(
                    f"Famille de "
                    f"{eleve_facturation}"
                )
            )

            adresse_facture = st.text_area(
                "Adresse de facturation "
                "(facultatif)"
            )

            numero_facture = st.text_input(
                "Numéro de facture",
                value=(
                    f"FAC-"
                    f"{date.today().strftime('%Y%m%d')}"
                )
            )


            # =================================================
            # PDF
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


                    # ------------------------------------------------
                    # TITRE
                    # ------------------------------------------------

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


                    # ------------------------------------------------
                    # INFORMATIONS
                    # ------------------------------------------------

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


                    # ------------------------------------------------
                    # TABLEAU DES SÉANCES
                    # ------------------------------------------------

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


                    # ------------------------------------------------
                    # TOTAL
                    # ------------------------------------------------

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


                    # ------------------------------------------------
                    # CONSTRUCTION PDF
                    # ------------------------------------------------

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


                except Exception as e:

                    st.error(
                        "❌ Erreur lors de "
                        "la génération de la facture."
                    )

                    st.write(e)
