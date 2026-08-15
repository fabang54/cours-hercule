import streamlit as st
import pandas as pd

from supabase import create_client
from datetime import date, time
from io import BytesIO
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cours Hercule",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# SUPABASE
# ============================================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


# ============================================================
# CONNEXION GOOGLE
# ============================================================

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


# ============================================================
# UTILISATEUR CONNECTÉ
# ============================================================

st.sidebar.success(
    f"Connecté : {st.user.get('email', 'Google')}"
)

if st.sidebar.button("🚪 Se déconnecter"):
    st.logout()


# ============================================================
# MOT DE PASSE
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

    if "access" not in st.user.tokens:

        raise Exception(
            "Le jeton Google Drive n'est pas disponible. "
            "Vérifiez expose_tokens = ['access'] "
            "dans les Secrets Streamlit."
        )

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
# SAUVEGARDE DRIVE
# ============================================================

def sauvegarder_dans_drive(df):

    from googleapiclient.http import MediaIoBaseUpload

    service = obtenir_service_drive()

    # --------------------------------------------------------
    # RECHERCHE DU DOSSIER
    # --------------------------------------------------------

    resultat = (
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

    dossiers = resultat.get(
        "files",
        []
    )

    # --------------------------------------------------------
    # CRÉATION DU DOSSIER
    # --------------------------------------------------------

    if dossiers:

        dossier_id = dossiers[0]["id"]

    else:

        dossier = (
            service.files()
            .create(
                body={
                    "name": "Cours Hercule",
                    "mimeType":
                        "application/vnd.google-apps.folder"
                },
                fields="id,name"
            )
            .execute()
        )

        dossier_id = dossier["id"]

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    contenu_csv = dataframe_csv_bytes(df)

    media = MediaIoBaseUpload(
        BytesIO(contenu_csv),
        mimetype="text/csv",
        resumable=False
    )

    # --------------------------------------------------------
    # RECHERCHE SEANCES.CSV
    # --------------------------------------------------------

    resultat = (
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

    fichiers = resultat.get(
        "files",
        []
    )

    # --------------------------------------------------------
    # MISE À JOUR
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CRÉATION
    # --------------------------------------------------------

    (
        service.files()
        .create(
            body={
                "name": "seances.csv",
                "parents": [dossier_id],
                "mimeType": "text/csv"
            },
            media_body=media,
            fields="id,name"
        )
        .execute()
    )

    return "créé"


# ============================================================
# SYNCHRONISATION DRIVE
# ============================================================

def synchroniser_drive():

    df = recuperer_seances()

    if df.empty:

        return (
            False,
            "Aucune séance à sauvegarder."
        )

    try:

        resultat = sauvegarder_dans_drive(df)

        return (
            True,
            f"☁️ seances.csv {resultat} dans Google Drive."
        )

    except Exception as e:

        return (
            False,
            f"⚠️ Erreur Google Drive : {e}"
        )


# ============================================================
# GÉNÉRATION FACTURE PDF
# ============================================================

def generer_facture_pdf(
    df_eleve,
    eleve,
    tarif,
    numero_facture
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    titre = ParagraphStyle(
        "TitreFacture",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=20
    )

    normal = ParagraphStyle(
        "NormalFacture",
        parent=styles["Normal"],
        fontSize=10,
        leading=14
    )

    droite = ParagraphStyle(
        "Droite",
        parent=normal,
        alignment=TA_RIGHT
    )

    elements = []

    # --------------------------------------------------------
    # TITRE
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "COURS HERCULE",
            titre
        )
    )

    elements.append(
        Paragraph(
            f"<b>FACTURE N° {numero_facture}</b>",
            normal
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    # --------------------------------------------------------
    # INFORMATIONS
    # --------------------------------------------------------

    date_facture = date.today().strftime(
        "%d/%m/%Y"
    )

    informations = [
        [
            Paragraph(
                "<b>Élève</b>",
                normal
            ),
            Paragraph(
                str(eleve),
                normal
            )
        ],
        [
            Paragraph(
                "<b>Date de facture</b>",
                normal
            ),
            Paragraph(
                date_facture,
                normal
            )
        ],
        [
            Paragraph(
                "<b>Tarif horaire</b>",
                normal
            ),
            Paragraph(
                f"{tarif:.2f} €",
                normal
            )
        ]
    ]

    table_info = Table(
        informations,
        colWidths=[130, 350]
    )

    table_info.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.whitesmoke
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    elements.append(
        table_info
    )

    elements.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # TABLE DES SÉANCES
    # --------------------------------------------------------

    donnees_table = [
        [
            "Date",
            "Horaire",
            "Discipline",
            "Durée",
            "Montant"
        ]
    ]

    total_minutes = 0

    for _, ligne in df_eleve.iterrows():

        duree = pd.to_numeric(
            ligne.get("duree_minutes"),
            errors="coerce"
        )

        if pd.isna(duree):
            duree = 0

        total_minutes += float(duree)

        heures = float(duree) / 60

        montant = heures * tarif

        date_ligne = str(
            ligne.get("date", "")
        )

        heure_debut = str(
            ligne.get("heure_debut", "")
        )

        heure_fin = str(
            ligne.get("heure_fin", "")
        )

        discipline = str(
            ligne.get("disciplines", "")
        )

        donnees_table.append(
            [
                date_ligne,
                f"{heure_debut} - {heure_fin}",
                discipline,
                f"{heures:.2f} h",
                f"{montant:.2f} €"
            ]
        )

    table_seances = Table(
        donnees_table,
        colWidths=[
            70,
            100,
            130,
            65,
            75
        ],
        repeatRows=1
    )

    table_seances.setStyle(
        TableStyle([
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
                (3, 1),
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
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    elements.append(
        table_seances
    )

    elements.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total_heures = total_minutes / 60

    total = total_heures * tarif

    total_table = Table(
        [
            [
                Paragraph(
                    "<b>Total des heures</b>",
                    normal
                ),
                Paragraph(
                    f"<b>{total_heures:.2f} h</b>",
                    droite
                )
            ],
            [
                Paragraph(
                    "<b>TOTAL À PAYER</b>",
                    normal
                ),
                Paragraph(
                    f"<b>{total:.2f} €</b>",
                    droite
                )
            ]
        ],
        colWidths=[350, 130]
    )

    total_table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.whitesmoke
            ),
            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "RIGHT"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    elements.append(
        total_table
    )

    elements.append(
        Spacer(1, 30)
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

    return buffer.getvalue()


# ============================================================
# TITRE
# ============================================================

st.title("📚 Cours Hercule")


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

    action = st.radio(
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

    if action == "➕ Nouvelle séance":

        st.subheader(
            "➕ Nouvelle séance"
        )

        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        eleve = st.selectbox(
            "Élève",
            ELEVES,
            key="nouvelle_eleve"
        )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        date_seance = st.date_input(
            "Date *",
            value=date.today(),
            key="nouvelle_date"
        )

        st.caption(
            "* La date est le seul champ obligatoire."
        )

        # ----------------------------------------------------
        # HEURES
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # MODE
        # ----------------------------------------------------

        mode = st.selectbox(
            "Mode",
            [
                "Présentiel",
                "Distanciel"
            ],
            key="nouvelle_mode"
        )

        # ----------------------------------------------------
        # DISCIPLINE
        # ----------------------------------------------------

        disciplines = st.multiselect(
            "Discipline(s)",
            DISCIPLINES,
            default=["Mathématiques"],
            key="nouvelle_disciplines"
        )

        # ----------------------------------------------------
        # CONTENU
        # ----------------------------------------------------

        contenu_selection = st.multiselect(
            "Contenu",
            CONTENUS,
            key="nouvelle_contenu_selection"
        )

        contenu_manuel = st.text_area(
            "Précisions / contenu supplémentaire",
            key="nouvelle_contenu_manuel"
        )

        contenu = ", ".join(
            contenu_selection
        )

        if contenu_manuel.strip():

            if contenu:
                contenu += " — "

            contenu += contenu_manuel.strip()

        # ----------------------------------------------------
        # TRAVAIL
        # ----------------------------------------------------

        travail = st.selectbox(
            "Travail à faire",
            TRAVAUX,
            key="nouvelle_travail"
        )

        if travail == "Autre":

            travail = st.text_input(
                "Préciser",
                key="nouvelle_travail_autre"
            )

        # ----------------------------------------------------
        # OBSERVATIONS
        # ----------------------------------------------------

        observations = st.multiselect(
            "Observations",
            OBSERVATIONS,
            default=["Élève attentif"],
            key="nouvelle_observations"
        )

        observation_manuel = st.text_area(
            "Observations supplémentaires",
            key="nouvelle_observation_manuel"
        )

        observations_finales = ", ".join(
            observations
        )

        if observation_manuel.strip():

            if observations_finales:
                observations_finales += " — "

            observations_finales += (
                observation_manuel.strip()
            )

        # ====================================================
        # ENREGISTREMENT
        # ====================================================

        if st.button(
            "💾 Enregistrer la séance",
            type="primary"
        ):

            # ------------------------------------------------
            # CALCUL DURÉE
            # ------------------------------------------------

            debut = (
                heure_debut.hour * 60
                + heure_debut.minute
            )

            fin = (
                heure_fin.hour * 60
                + heure_fin.minute
            )

            duree = fin - debut

            if duree <= 0:

                duree = None

            # ------------------------------------------------
            # DONNÉES
            # ------------------------------------------------

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
                    duree,

                "mode":
                    mode,

                "disciplines":
                    ", ".join(
                        disciplines
                    ),

                "contenu":
                    contenu,

                "travail":
                    travail,

                "observations":
                    observations_finales
            }

            # ------------------------------------------------
            # ENREGISTREMENT SUPABASE
            # ------------------------------------------------

            try:

                (
                    supabase
                    .table("seances")
                    .insert(
                        nouvelle_seance
                    )
                    .execute()
                )

                st.success(
                    "✅ Séance enregistrée dans Supabase."
                )

                # --------------------------------------------
                # GOOGLE DRIVE
                # --------------------------------------------

                ok, message = (
                    synchroniser_drive()
                )

                if ok:

                    st.success(message)

                else:

                    st.warning(message)

                # --------------------------------------------
                # RÉINITIALISATION
                # --------------------------------------------

                cles_formulaire = [
                    "nouvelle_eleve",
                    "nouvelle_date",
                    "nouvelle_heure_debut",
                    "nouvelle_heure_fin",
                    "nouvelle_mode",
                    "nouvelle_disciplines",
                    "nouvelle_contenu_selection",
                    "nouvelle_contenu_manuel",
                    "nouvelle_travail",
                    "nouvelle_travail_autre",
                    "nouvelle_observations",
                    "nouvelle_observation_manuel"
                ]

                for cle in cles_formulaire:

                    st.session_state.pop(
                        cle,
                        None
                    )

                st.rerun()

            except Exception as e:

                st.error(
                    "❌ Erreur lors de l'enregistrement."
                )

                st.code(
                    str(e)
                )


    # ========================================================
    # MODIFICATION D'UNE SÉANCE
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

            eleve = st.selectbox(
                "Élève",
                sorted(
                    df["eleve"]
                    .dropna()
                    .unique()
                )
            )

            df_eleve = df[
                df["eleve"] == eleve
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

            choix_index = st.selectbox(
                "Séance",
                range(len(choix)),
                format_func=lambda i: choix[i]
            )

            ligne = df_eleve.iloc[
                choix_index
            ]

            identifiant = ligne["id"]

            nouvelle_date = st.date_input(
                "Date",
                value=pd.to_datetime(
                    ligne["date"]
                ).date()
            )

            heure_debut = st.time_input(
                "Heure de début",
                value=pd.to_datetime(
                    ligne["heure_debut"]
                ).time()
            )

            heure_fin = st.time_input(
                "Heure de fin",
                value=pd.to_datetime(
                    ligne["heure_fin"]
                ).time()
            )

            mode = st.selectbox(
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

            disciplines = st.text_input(
                "Discipline(s)",
                value=str(
                    ligne["disciplines"]
                )
            )

            contenu = st.text_area(
                "Contenu",
                value=str(
                    ligne["contenu"]
                )
            )

            travail = st.text_area(
                "Travail à faire",
                value=str(
                    ligne["travail"]
                )
            )

            observations = st.text_area(
                "Observations",
                value=str(
                    ligne["observations"]
                )
            )

            if st.button(
                "💾 Enregistrer les modifications",
                type="primary"
            ):

                debut = (
                    heure_debut.hour * 60
                    + heure_debut.minute
                )

                fin = (
                    heure_fin.hour * 60
                    + heure_fin.minute
                )

                duree = fin - debut

                if duree <= 0:

                    duree = None

                modifications = {

                    "date":
                        nouvelle_date.isoformat(),

                    "heure_debut":
                        heure_debut.strftime(
                            "%H:%M:%S"
                        ),

                    "heure_fin":
                        heure_fin.strftime(
                            "%H:%M:%S"
                        ),

                    "duree_minutes":
                        duree,

                    "mode":
                        mode,

                    "disciplines":
                        disciplines,

                    "contenu":
                        contenu,

                    "travail":
                        travail,

                    "observations":
                        observations
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
                        "✅ Séance modifiée."
                    )

                    ok, message = (
                        synchroniser_drive()
                    )

                    if ok:

                        st.success(message)

                    else:

                        st.warning(message)

                    st.rerun()

                except Exception as e:

                    st.error(
                        "❌ Erreur lors de la modification."
                    )

                    st.code(
                        str(e)
                    )


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
            "Aucune séance."
        )

    else:

        eleve = st.selectbox(
            "Élève",
            ELEVES
        )

        df = df[
            df["eleve"] == eleve
        ]

        if df.empty:

            st.info(
                "Aucune séance pour cet élève."
            )

        else:

            for _, ligne in df.sort_values(
                "date",
                ascending=False
            ).iterrows():

                st.markdown("---")

                st.write(
                    f"### 📅 {ligne['date']}"
                )

                st.write(
                    f"**Horaire :** "
                    f"{ligne['heure_debut']} → "
                    f"{ligne['heure_fin']}"
                )

                st.write(
                    f"**Discipline :** "
                    f"{ligne['disciplines']}"
                )

                st.write(
                    f"**Contenu :** "
                    f"{ligne['contenu']}"
                )

                st.write(
                    f"**Travail :** "
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
        "📊 Bilan"
    )

    df = recuperer_seances()

    if df.empty:

        st.info(
            "Aucune séance."
        )

    else:

        eleve = st.selectbox(
            "Élève",
            ELEVES
        )

        df_eleve = df[
            df["eleve"] == eleve
        ].copy()

        if df_eleve.empty:

            st.info(
                "Aucune séance."
            )

        else:

            total_minutes = pd.to_numeric(
                df_eleve[
                    "duree_minutes"
                ],
                errors="coerce"
            ).fillna(0).sum()

            st.metric(
                "Nombre de séances",
                len(df_eleve)
            )

            st.metric(
                "Nombre d'heures",
                f"{total_minutes / 60:.2f} h"
            )

            st.dataframe(
                df_eleve,
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
            "Aucune séance."
        )

    else:

        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        eleve = st.selectbox(
            "Élève",
            ELEVES
        )

        # ----------------------------------------------------
        # TARIF
        # ----------------------------------------------------

        tarif = st.number_input(
            "Tarif horaire (€)",
            min_value=0.0,
            value=30.0,
            step=1.0
        )

        # ----------------------------------------------------
        # FILTRE ÉLÈVE
        # ----------------------------------------------------

        df_eleve = df[
            df["eleve"] == eleve
        ].copy()

        if df_eleve.empty:

            st.info(
                "Aucune séance pour cet élève."
            )

        else:

            # ------------------------------------------------
            # CALCUL
            # ------------------------------------------------

            df_eleve["duree_minutes"] = pd.to_numeric(
                df_eleve["duree_minutes"],
                errors="coerce"
            ).fillna(0)

            total_minutes = (
                df_eleve["duree_minutes"].sum()
            )

            total_heures = (
                total_minutes / 60
            )

            montant = (
                total_heures * tarif
            )

            # ------------------------------------------------
            # AFFICHAGE
            # ------------------------------------------------

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Nombre de séances",
                    len(df_eleve)
                )

            with col2:

                st.metric(
                    "Heures",
                    f"{total_heures:.2f} h"
                )

            with col3:

                st.metric(
                    "Montant",
                    f"{montant:.2f} €"
                )

            st.subheader(
                "📋 Séances facturées"
            )

            st.dataframe(
                df_eleve,
                use_container_width=True
            )

            # ------------------------------------------------
            # NUMÉRO FACTURE
            # ------------------------------------------------

            numero_facture = st.text_input(
                "Numéro de facture",
                value=(
                    f"CH-"
                    f"{date.today().strftime('%Y%m%d')}-"
                    f"{eleve.upper()}"
                )
            )

            # ------------------------------------------------
            # GÉNÉRER PDF
            # ------------------------------------------------

            if st.button(
                "🧾 Générer la facture PDF",
                type="primary"
            ):

                try:

                    pdf = generer_facture_pdf(
                        df_eleve,
                        eleve,
                        tarif,
                        numero_facture
                    )

                    st.session_state[
                        "facture_pdf"
                    ] = pdf

                    st.success(
                        "✅ Facture PDF générée."
                    )

                except Exception as e:

                    st.error(
                        "❌ Erreur lors de la génération "
                        "de la facture PDF."
                    )

                    st.code(
                        str(e)
                    )

            # ------------------------------------------------
            # TÉLÉCHARGEMENT
            # ------------------------------------------------

            if "facture_pdf" in st.session_state:

                st.download_button(
                    label="📥 Télécharger la facture PDF",
                    data=st.session_state[
                        "facture_pdf"
                    ],
                    file_name=(
                        f"Facture_"
                        f"{eleve}_"
                        f"{date.today().strftime('%Y%m%d')}"
                        f".pdf"
                    ),
                    mime="application/pdf"
                )
