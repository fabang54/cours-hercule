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
    "Difficultés de compréhension",
    "Bonne participation",
    "Très bonne séance",
    "Progrès constatés",
    "Travail régulier recommandé",
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

    contenu_csv = dataframe_csv_bytes(df)

    media = MediaIoBaseUpload(
        BytesIO(contenu_csv),
        mimetype="text/csv",
        resumable=False
    )

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
# BILAN DES OBSERVATIONS
# ============================================================

def analyser_observations(df_eleve):

    """
    Analyse les observations des séances.

    Exemple :
    Élève fatigué : 5/8 séances
    Élève attentif : 6/8 séances
    Bonne participation : 4/8 séances
    """

    nombre_seances = len(df_eleve)

    bilan = {}

    if nombre_seances == 0:
        return bilan

    if "observations" not in df_eleve.columns:
        return bilan

    texte_observations = (
        df_eleve["observations"]
        .fillna("")
        .astype(str)
    )

    for observation in OBSERVATIONS:

        if observation == "Autre":
            continue

        nombre = texte_observations.apply(
            lambda texte:
                observation.lower()
                in texte.lower()
        ).sum()

        if nombre > 0:

            bilan[observation] = int(nombre)

    return bilan


# ============================================================
# GÉNÉRATION AUTOMATIQUE DE L'OBSERVATION
# ============================================================

def generer_observation_automatique(
    df_eleve
):

    nombre_seances = len(df_eleve)

    if nombre_seances == 0:

        return (
            "Aucune séance n'est disponible "
            "pour cette période."
        )

    bilan = analyser_observations(
        df_eleve
    )

    phrases = []

    # --------------------------------------------------------
    # ATTENTION
    # --------------------------------------------------------

    attentif = bilan.get(
        "Élève attentif",
        0
    )

    if attentif > 0:

        if attentif >= nombre_seances * 0.75:

            phrases.append(
                "L'élève s'est montré attentif "
                "sur la majorité des séances."
            )

        elif attentif >= nombre_seances * 0.5:

            phrases.append(
                "L'attention de l'élève a été "
                "globalement satisfaisante."
            )

    # --------------------------------------------------------
    # FATIGUE
    # --------------------------------------------------------

    fatigue = bilan.get(
        "Élève fatigué",
        0
    )

    if fatigue > 0:

        if fatigue >= nombre_seances * 0.5:

            phrases.append(
                "Une certaine fatigue a été observée "
                "lors de plusieurs séances."
            )

        else:

            phrases.append(
                "Quelques signes de fatigue "
                "ont été observés."
            )

    # --------------------------------------------------------
    # DISTRACTION
    # --------------------------------------------------------

    distrait = bilan.get(
        "Élève distrait",
        0
    )

    if distrait > 0:

        if distrait >= nombre_seances * 0.5:

            phrases.append(
                "Des difficultés de concentration "
                "ont été observées régulièrement."
            )

        else:

            phrases.append(
                "Quelques moments de distraction "
                "ont été observés."
            )

    # --------------------------------------------------------
    # PARTICIPATION
    # --------------------------------------------------------

    participation = bilan.get(
        "Bonne participation",
        0
    )

    if participation > 0:

        if participation >= nombre_seances * 0.5:

            phrases.append(
                "La participation est globalement "
                "satisfaisante."
            )

    # --------------------------------------------------------
    # DIFFICULTÉS
    # --------------------------------------------------------

    difficultes = bilan.get(
        "Difficultés importantes",
        0
    )

    comprehension = bilan.get(
        "Difficultés de compréhension",
        0
    )

    if difficultes > 0:

        phrases.append(
            "Certaines difficultés importantes "
            "nécessitent encore un accompagnement."
        )

    elif comprehension > 0:

        phrases.append(
            "Certaines notions nécessitent encore "
            "des explications et des consolidations."
        )

    # --------------------------------------------------------
    # PROGRÈS
    # --------------------------------------------------------

    progres = bilan.get(
        "Progrès constatés",
        0
    )

    if progres > 0:

        if progres >= nombre_seances * 0.5:

            phrases.append(
                "Des progrès sont constatés "
                "au cours de la période."
            )

        else:

            phrases.append(
                "Des progrès commencent à apparaître."
            )

    # --------------------------------------------------------
    # PARTICIPATION TRÈS BONNE
    # --------------------------------------------------------

    tres_bonne = bilan.get(
        "Très bonne séance",
        0
    )

    if tres_bonne >= nombre_seances * 0.5:

        phrases.append(
            "L'implication de l'élève est "
            "très encourageante."
        )

    # --------------------------------------------------------
    # PHRASE PAR DÉFAUT
    # --------------------------------------------------------

    if not phrases:

        return (
            "La période de travail s'est déroulée "
            "dans de bonnes conditions. "
            "La poursuite d'un travail régulier "
            "est recommandée."
        )

    # --------------------------------------------------------
    # ASSEMBLAGE
    # --------------------------------------------------------

    texte = " ".join(phrases)

    texte += (
        " Un travail régulier est recommandé "
        "afin de consolider les notions étudiées."
    )

    return texte


# ============================================================
# GÉNÉRATION FACTURE PDF
# ============================================================

def generer_facture_pdf(
    df_eleve,
    eleve,
    tarif,
    numero_facture,
    periode,
    statut,
    date_paiement
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    titre = ParagraphStyle(
        "TitreFacture",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=20,
        spaceAfter=10
    )

    normal = ParagraphStyle(
        "NormalFacture",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=10.5
    )

    petit = ParagraphStyle(
        "Petit",
        parent=normal,
        fontSize=7.5,
        leading=9
    )

    observation_style = ParagraphStyle(
        "Observation",
        parent=normal,
        fontSize=8,
        leading=10
    )

    droite = ParagraphStyle(
        "Droite",
        parent=normal,
        alignment=TA_RIGHT
    )

    elements = []

    # ========================================================
    # TITRE
    # ========================================================

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
        Spacer(1, 7)
    )

    # ========================================================
    # CALCULS
    # ========================================================

    df_eleve = df_eleve.copy()

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

    nombre_seances = len(df_eleve)

    # ========================================================
    # INFORMATIONS FACTURE
    # ========================================================

    date_facture = date.today().strftime(
        "%d/%m/%Y"
    )

    infos = [
        [
            Paragraph("<b>Élève</b>", normal),
            Paragraph(str(eleve), normal)
        ],
        [
            Paragraph("<b>Date de facture</b>", normal),
            Paragraph(date_facture, normal)
        ],
        [
            Paragraph("<b>Période facturée</b>", normal),
            Paragraph(periode, normal)
        ],
        [
            Paragraph("<b>Nombre de séances</b>", normal),
            Paragraph(str(nombre_seances), normal)
        ],
        [
            Paragraph("<b>Tarif horaire</b>", normal),
            Paragraph(f"{tarif:.2f} € / h", normal)
        ]
    ]

    table_infos = Table(
        infos,
        colWidths=[145, 385]
    )

    table_infos.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.whitesmoke
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    elements.append(
        table_infos
    )

    elements.append(
        Spacer(1, 8)
    )

    # ========================================================
    # TABLE DES SÉANCES
    # ========================================================

    donnees_table = [
        [
            "Date",
            "Horaire",
            "Mode",
            "Discipline",
            "Durée"
        ]
    ]

    for _, ligne in df_eleve.iterrows():

        duree = pd.to_numeric(
            ligne.get("duree_minutes"),
            errors="coerce"
        )

        if pd.isna(duree):
            duree = 0

        heures = float(duree) / 60

        try:

            date_ligne = pd.to_datetime(
                ligne.get("date")
            ).strftime("%d/%m/%Y")

        except Exception:

            date_ligne = str(
                ligne.get("date", "")
            )

        heure_debut = str(
            ligne.get("heure_debut", "")
        )[:5]

        heure_fin = str(
            ligne.get("heure_fin", "")
        )[:5]

        mode = str(
            ligne.get("mode", "")
        )

        discipline = str(
            ligne.get("disciplines", "")
        )

        donnees_table.append(
            [
                date_ligne,
                f"{heure_debut}-{heure_fin}",
                mode,
                discipline,
                f"{heures:.2f} h"
            ]
        )

    table_seances = Table(
        donnees_table,
        colWidths=[
            65,
            85,
            70,
            240,
            70
        ],
        repeatRows=1
    )

    table_seances.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
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
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "ALIGN",
                (4, 1),
                (4, -1),
                "RIGHT"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                3
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                3
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                2
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2
            )
        ])
    )

    elements.append(
        table_seances
    )

    elements.append(
        Spacer(1, 7)
    )

    # ========================================================
    # TOTAL
    # ========================================================

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
                    "<b>Tarif horaire</b>",
                    normal
                ),
                Paragraph(
                    f"<b>{tarif:.2f} € / h</b>",
                    droite
                )
            ],
            [
                Paragraph(
                    "<b>TOTAL À PAYER</b>",
                    normal
                ),
                Paragraph(
                    f"<b>{montant:.2f} €</b>",
                    droite
                )
            ]
        ],
        colWidths=[380, 150]
    )

    total_table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 2),
                (-1, 2),
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
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    elements.append(
        total_table
    )

    elements.append(
        Spacer(1, 7)
    )

    # ========================================================
    # BILAN DES OBSERVATIONS
    # ========================================================

    bilan = analyser_observations(
        df_eleve
    )

    if bilan:

        elements.append(
            Paragraph(
                "<b>📊 Bilan de la période</b>",
                normal
            )
        )

        lignes_bilan = []

        for observation, nombre in bilan.items():

            lignes_bilan.append(
                [
                    Paragraph(
                        observation,
                        petit
                    ),
                    Paragraph(
                        f"{nombre}/{nombre_seances} séances",
                        petit
                    )
                ]
            )

        table_bilan = Table(
            lignes_bilan,
            colWidths=[380, 150]
        )

        table_bilan.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                )
            ])
        )

        elements.append(
            table_bilan
        )

        elements.append(
            Spacer(1, 5)
        )

    # ========================================================
    # OBSERVATION AUTOMATIQUE
    # ========================================================

    observation_automatique = (
        generer_observation_automatique(
            df_eleve
        )
    )

    elements.append(
        Paragraph(
            "<b>📝 Observation pédagogique</b>",
            normal
        )
    )

    observation_table = Table(
        [
            [
                Paragraph(
                    observation_automatique,
                    observation_style
                )
            ]
        ],
        colWidths=[530]
    )

    observation_table.setStyle(
        TableStyle([
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.whitesmoke
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
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
        observation_table
    )

    elements.append(
        Spacer(1, 7)
    )

    # ========================================================
    # PAIEMENT
    # ========================================================

    if statut == "Payée":

        date_paiement_pdf = (
            date_paiement.strftime("%d/%m/%Y")
            if date_paiement
            else ""
        )

        paiement = [
            [
                Paragraph(
                    "<b>Statut</b>",
                    normal
                ),
                Paragraph(
                    "<b>PAYÉE</b>",
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Date de paiement</b>",
                    normal
                ),
                Paragraph(
                    date_paiement_pdf,
                    normal
                )
            ]
        ]

    else:

        paiement = [
            [
                Paragraph(
                    "<b>Statut</b>",
                    normal
                ),
                Paragraph(
                    "<b>EN ATTENTE DE PAIEMENT</b>",
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Date de paiement</b>",
                    normal
                ),
                Paragraph(
                    "—",
                    normal
                )
            ]
        ]

    table_paiement = Table(
        paiement,
        colWidths=[145, 385]
    )

    table_paiement.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.whitesmoke
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    elements.append(
        table_paiement
    )

    elements.append(
        Spacer(1, 8)
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

    st.header("📚 Gestion des séances")

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

        st.subheader("➕ Nouvelle séance")

        eleve = st.selectbox(
            "Élève",
            ELEVES,
            key="nouvelle_eleve"
        )

        date_seance = st.date_input(
            "Date *",
            value=date.today(),
            key="nouvelle_date"
        )

        st.caption(
            "* La date est le seul champ obligatoire."
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
            default=["Mathématiques"],
            key="nouvelle_disciplines"
        )

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

        if st.button(
            "💾 Enregistrer la séance",
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

                ok, message = (
                    synchroniser_drive()
                )

                if ok:
                    st.success(message)
                else:
                    st.warning(message)

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

                st.code(str(e))


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
                    if ligne["mode"] == "Présentiel"
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

                    st.code(str(e))


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
                    f"**Mode :** "
                    f"{ligne.get('mode', '')}"
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

            st.subheader(
                "📊 Observations"
            )

            bilan = analyser_observations(
                df_eleve
            )

            for observation, nombre in bilan.items():

                st.write(
                    f"**{observation} :** "
                    f"{nombre}/{len(df_eleve)} séances"
                )

            st.subheader(
                "📝 Observation automatique"
            )

            observation_auto = (
                generer_observation_automatique(
                    df_eleve
                )
            )

            st.info(
                observation_auto
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

        # ====================================================
        # ÉLÈVE
        # ====================================================

        eleve = st.selectbox(
            "Élève",
            ELEVES,
            key="facture_eleve"
        )

        # ====================================================
        # PÉRIODE
        # ====================================================

        type_periode = st.selectbox(
            "Période de facturation",
            [
                "Mensuelle",
                "Personnalisée"
            ],
            index=0,
            key="facture_type_periode"
        )

        # ====================================================
        # PÉRIODE MENSUELLE
        # ====================================================

        if type_periode == "Mensuelle":

            col1, col2 = st.columns(2)

            with col1:

                mois = st.selectbox(
                    "Mois",
                    list(range(1, 13)),
                    index=date.today().month - 1,
                    format_func=lambda x: [
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
                    ][x - 1]
                )

            with col2:

                annee = st.number_input(
                    "Année",
                    min_value=2024,
                    max_value=2100,
                    value=date.today().year,
                    step=1
                )

            date_debut = date(
                int(annee),
                int(mois),
                1
            )

            if mois == 12:

                date_fin = date(
                    int(annee) + 1,
                    1,
                    1
                )

            else:

                date_fin = date(
                    int(annee),
                    int(mois) + 1,
                    1
                )

            date_fin_inclusive = (
                date_fin -
                pd.Timedelta(days=1)
            )

        # ====================================================
        # PÉRIODE PERSONNALISÉE
        # ====================================================

        else:

            col1, col2 = st.columns(2)

            with col1:

                date_debut = st.date_input(
                    "Date de début",
                    value=date(
                        date.today().year,
                        date.today().month,
                        1
                    ),
                    key="facture_date_debut"
                )

            with col2:

                date_fin_inclusive = st.date_input(
                    "Date de fin",
                    value=date.today(),
                    key="facture_date_fin"
                )

            if date_fin_inclusive < date_debut:

                st.error(
                    "❌ La date de fin doit être "
                    "postérieure ou égale à la date de début."
                )

                st.stop()

        # ====================================================
        # PÉRIODE AFFICHÉE
        # ====================================================

        periode = (
            f"{date_debut.strftime('%d/%m/%Y')} "
            f"– "
            f"{date_fin_inclusive.strftime('%d/%m/%Y')}"
        )

        st.info(
            f"📅 Période facturée : {periode}"
        )

        # ====================================================
        # TARIF
        # ====================================================

        tarif = st.number_input(
            "Tarif horaire (€)",
            min_value=0.0,
            value=30.0,
            step=1.0,
            key="facture_tarif"
        )

        # ====================================================
        # STATUT
        # ====================================================

        statut = st.selectbox(
            "Statut du paiement",
            [
                "En attente de paiement",
                "Payée"
            ],
            key="facture_statut"
        )

        date_paiement = None

        if statut == "Payée":

            date_paiement = st.date_input(
                "Date de paiement",
                value=date.today(),
                key="facture_date_paiement"
            )

        # ====================================================
        # FILTRAGE DES SÉANCES
        # ====================================================

        df_eleve = df[
            df["eleve"] == eleve
        ].copy()

        df_eleve["date_temp"] = pd.to_datetime(
            df_eleve["date"],
            errors="coerce"
        ).dt.date

        df_eleve = df_eleve[
            (
                df_eleve["date_temp"]
                >= date_debut
            )
            &
            (
                df_eleve["date_temp"]
                <= date_fin_inclusive
            )
        ].copy()

        # ====================================================
        # AUCUNE SÉANCE
        # ====================================================

        if df_eleve.empty:

            st.warning(
                "Aucune séance pour cet élève "
                "durant cette période."
            )

        else:

            # =================================================
            # CALCUL
            # =================================================

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

            nombre_seances = len(
                df_eleve
            )

            # =================================================
            # INDICATEURS
            # =================================================

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Nombre de séances",
                    nombre_seances
                )

            with col2:

                st.metric(
                    "Heures",
                    f"{total_heures:.2f} h"
                )

            with col3:

                st.metric(
                    "Total",
                    f"{montant:.2f} €"
                )

            # =================================================
            # TABLEAU DES SÉANCES
            # =================================================

            st.subheader(
                "📋 Bilan des séances"
            )

            colonnes_affichage = [
                "date",
                "heure_debut",
                "heure_fin",
                "mode",
                "disciplines",
                "duree_minutes"
            ]

            colonnes_existantes = [
                c
                for c in colonnes_affichage
                if c in df_eleve.columns
            ]

            tableau_affichage = (
                df_eleve[
                    colonnes_existantes
                ].copy()
            )

            st.dataframe(
                tableau_affichage,
                use_container_width=True
            )

            # =================================================
            # BILAN DES OBSERVATIONS
            # =================================================

            st.subheader(
                "📊 Bilan des observations"
            )

            bilan = analyser_observations(
                df_eleve
            )

            if bilan:

                for observation, nombre in bilan.items():

                    st.write(
                        f"**{observation} :** "
                        f"{nombre}/{nombre_seances} séances"
                    )

            else:

                st.info(
                    "Aucune observation enregistrée "
                    "pour cette période."
                )

            # =================================================
            # OBSERVATION AUTOMATIQUE
            # =================================================

            st.subheader(
                "📝 Observation automatique"
            )

            observation_auto = (
                generer_observation_automatique(
                    df_eleve
                )
            )

            st.info(
                observation_auto
            )

            # =================================================
            # NUMÉRO FACTURE
            # =================================================

            numero_facture = st.text_input(
                "Numéro de facture",
                value=(
                    f"CH-"
                    f"{date_debut.strftime('%Y%m%d')}-"
                    f"{date_fin_inclusive.strftime('%Y%m%d')}-"
                    f"{eleve.upper()}"
                ),
                key="numero_facture"
            )

            # =================================================
            # GÉNÉRATION PDF
            # =================================================

            if st.button(
                "🧾 Générer la facture PDF",
                type="primary"
            ):

                try:

                    pdf = generer_facture_pdf(
                        df_eleve,
                        eleve,
                        tarif,
                        numero_facture,
                        periode,
                        statut,
                        date_paiement
                    )

                    st.session_state[
                        "facture_pdf"
                    ] = pdf

                    st.session_state[
                        "facture_nom"
                    ] = (
                        f"Facture_"
                        f"{eleve}_"
                        f"{date_debut.strftime('%Y%m%d')}_"
                        f"{date_fin_inclusive.strftime('%Y%m%d')}.pdf"
                    )

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

            # =================================================
            # TÉLÉCHARGEMENT
            # =================================================

            if "facture_pdf" in st.session_state:

                st.download_button(
                    label="📥 Télécharger la facture PDF",
                    data=st.session_state[
                        "facture_pdf"
                    ],
                    file_name=st.session_state[
                        "facture_nom"
                    ],
                    mime="application/pdf"
                )
