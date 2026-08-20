import streamlit as st
import pandas as pd
import io

from supabase import create_client
from datetime import date, time
from io import BytesIO

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
        "pour accéder à l'application."
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
# MOT DE PASSE ENSEIGNANT
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

DISCIPLINES = [
    "Mathématiques",
    "Physique",
    "Chimie",
    "Informatique",
    "Français",
    "Anglais",
    "Histoire",
    "Géographie",
    "SVT",
    "Technologie",
    "Culture générale",
    "Méthodologie",
    "Préparation examen",
    "Autre"
]


CONTENUS = [
    "Nombres relatifs",
    "Calcul numérique",
    "Fractions",
    "Puissances",
    "Calcul littéral",
    "Développement",
    "Factorisation",
    "Équations",
    "Inéquations",
    "Proportionnalité",
    "Pourcentages",
    "Fonctions",
    "Repérage",
    "Statistiques",
    "Probabilités",
    "Pythagore",
    "Thalès",
    "Trigonométrie",
    "Géométrie",
    "Volumes et aires",
    "Conversions",
    "Algorithmique",
    "Programmation",
    "Préparation contrôle",
    "Préparation examen",
    "Révisions",
    "Autre"
]


TRAVAUX = [
    "Aucun",
    "Exercices du manuel",
    "Exercices supplémentaires",
    "Exercices à terminer",
    "Corriger les exercices",
    "Revoir le cours",
    "Apprendre le cours",
    "Relire la leçon",
    "Faire une fiche de révision",
    "Mémoriser les formules",
    "S'entraîner sur des exercices",
    "Préparer le prochain cours",
    "Préparer un contrôle",
    "Préparer un devoir",
    "Réviser pour un examen",
    "Travail sur ordinateur",
    "Travail de recherche",
    "Lecture",
    "Autre"
]


OBSERVATIONS = [
    "Élève attentif",
    "Très bonne attention",
    "Élève sérieux",
    "Élève motivé",
    "Élève volontaire",
    "Bonne participation",
    "Très bonne séance",
    "Bonne compréhension",
    "Bonne maîtrise des notions",
    "Progrès constatés",
    "Progrès importants",
    "Travail régulier",
    "Travail satisfaisant",
    "Élève autonome",
    "Autonomie à développer",
    "Difficultés de compréhension",
    "Difficultés importantes",
    "Notions à consolider",
    "Manque de méthode",
    "Manque de confiance",
    "Élève distrait",
    "Difficultés de concentration",
    "Élève fatigué",
    "Travail insuffisant",
    "Participation à renforcer",
    "Travail régulier recommandé",
    "Autre"
]


# ============================================================
# RÉCUPÉRER LES ÉLÈVES
# ============================================================

def recuperer_eleves():

    try:

        resultat = (
            supabase
            .table("eleves")
            .select("*")
            .order("prenom")
            .execute()
        )

        donnees = resultat.data

        if not donnees:

            return pd.DataFrame(
                columns=[
                    "id",
                    "prenom",
                    "nom",
                    "classe_actuelle",
                    "type_tarification",
                    "tarif_horaire",
                    "forfait_mensuel",
                    "created_at"
                ]
            )

        return pd.DataFrame(donnees)

    except Exception as e:

        st.error(
            f"Erreur lors de la récupération des élèves : {e}"
        )

        return pd.DataFrame()


# ============================================================
# LISTE DES ÉLÈVES
# ============================================================

def liste_eleves():

    df = recuperer_eleves()

    if df.empty:
        return []

    noms = []

    for _, ligne in df.iterrows():

        prenom = str(
            ligne.get("prenom", "")
        ).strip()

        nom = str(
            ligne.get("nom", "")
        ).strip()

        if prenom:

            if nom:
                affichage = f"{prenom} {nom}"
            else:
                affichage = prenom

            noms.append(affichage)

    return sorted(noms)


# ============================================================
# RÉCUPÉRER LES SÉANCES
# ============================================================

def recuperer_seances():

    try:

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

    except Exception as e:

        st.error(
            f"Erreur lors de la récupération des séances : {e}"
        )

        return pd.DataFrame()


# ============================================================
# GOOGLE DRIVE
# ============================================================

def obtenir_service_drive():

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    if "access" not in st.user.tokens:

        raise Exception(
            "Le jeton Google Drive n'est pas disponible."
        )

    access_token = st.user.tokens["access"]

    credentials = Credentials(
        token=access_token
    )

    return build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )


def dataframe_csv_bytes(df):

    buffer = io.StringIO()

    df.to_csv(
        buffer,
        index=False,
        encoding="utf-8-sig"
    )

    return buffer.getvalue().encode("utf-8-sig")


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

    dossiers = resultat.get("files", [])

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

    fichiers = resultat.get("files", [])

    if fichiers:

        (
            service.files()
            .update(
                fileId=fichiers[0]["id"],
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
# OBSERVATIONS
# ============================================================

def analyser_observations(df_eleve):

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
                observation.lower() in texte.lower()
        ).sum()

        if nombre > 0:

            bilan[observation] = int(nombre)

    return bilan


def generer_observation_automatique(df_eleve):

    nombre_seances = len(df_eleve)

    if nombre_seances == 0:

        return (
            "Aucune séance n'est disponible "
            "pour cette période."
        )

    bilan = analyser_observations(df_eleve)

    phrases = []

    attentif = bilan.get("Élève attentif", 0)
    tres_attention = bilan.get("Très bonne attention", 0)

    if (
        attentif + tres_attention
        >= nombre_seances * 0.75
    ):

        phrases.append(
            "L'élève s'est montré attentif "
            "sur la majorité des séances."
        )

    elif (
        attentif + tres_attention
        >= nombre_seances * 0.5
    ):

        phrases.append(
            "L'attention de l'élève a été "
            "globalement satisfaisante."
        )

    fatigue = bilan.get("Élève fatigué", 0)

    if fatigue >= nombre_seances * 0.75:

        phrases.append(
            "Une fatigue importante a été observée "
            "sur la majorité des séances."
        )

    elif fatigue >= nombre_seances * 0.5:

        phrases.append(
            "Une certaine fatigue a été observée "
            "lors de plusieurs séances."
        )

    elif fatigue > 0:

        phrases.append(
            "Quelques signes de fatigue "
            "ont été observés."
        )

    distrait = bilan.get(
        "Élève distrait",
        0
    )

    concentration = bilan.get(
        "Difficultés de concentration",
        0
    )

    if distrait + concentration >= nombre_seances * 0.5:

        phrases.append(
            "Des difficultés de concentration "
            "ont été observées régulièrement."
        )

    participation = bilan.get(
        "Bonne participation",
        0
    )

    if participation >= nombre_seances * 0.5:

        phrases.append(
            "La participation est globalement "
            "satisfaisante."
        )

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

    progres = bilan.get(
        "Progrès constatés",
        0
    )

    progres_importants = bilan.get(
        "Progrès importants",
        0
    )

    if (
        progres + progres_importants
        >= nombre_seances * 0.5
    ):

        phrases.append(
            "Des progrès sont constatés "
            "au cours de la période."
        )

    elif progres + progres_importants > 0:

        phrases.append(
            "Des progrès commencent à apparaître."
        )

    tres_bonne = bilan.get(
        "Très bonne séance",
        0
    )

    if tres_bonne >= nombre_seances * 0.5:

        phrases.append(
            "L'implication de l'élève est "
            "très encourageante."
        )

    if not phrases:

        return (
            "La période de travail s'est déroulée "
            "dans de bonnes conditions. "
            "La poursuite d'un travail régulier "
            "est recommandée."
        )

    texte = " ".join(phrases)

    texte += (
        " Un travail régulier est recommandé "
        "afin de consolider les notions étudiées."
    )

    return texte


# ============================================================
# FACTURE PDF
# ============================================================

def generer_facture_pdf(
    df_eleve,
    eleve,
    niveau,
    type_tarification,
    tarif,
    remise_type,
    remise_valeur,
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

    elements.append(Spacer(1, 7))

    # --------------------------------------------------------
    # CALCULS
    # --------------------------------------------------------

    df_eleve = df_eleve.copy()

    df_eleve["duree_minutes"] = pd.to_numeric(
        df_eleve["duree_minutes"],
        errors="coerce"
    ).fillna(0)

    total_minutes = df_eleve[
        "duree_minutes"
    ].sum()

    total_heures = total_minutes / 60

    if type_tarification == "Forfait mensuel":

        sous_total = float(tarif)

    else:

        sous_total = (
            total_heures * float(tarif)
        )

    montant_remise = 0.0

    if remise_type == "Pourcentage":

        montant_remise = (
            sous_total
            * float(remise_valeur)
            / 100
        )

    elif remise_type == "Montant (€)":

        montant_remise = min(
            float(remise_valeur),
            sous_total
        )

    total_a_payer = (
        sous_total - montant_remise
    )

    nombre_seances = len(df_eleve)

    # --------------------------------------------------------
    # INFORMATIONS
    # --------------------------------------------------------

    date_facture = date.today().strftime(
        "%d/%m/%Y"
    )

    infos = [
        [
            Paragraph("<b>Élève</b>", normal),
            Paragraph(str(eleve), normal)
        ],
        [
            Paragraph("<b>Niveau / classe</b>", normal),
            Paragraph(str(niveau), normal)
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
            Paragraph(
                "<b>Tarification</b>",
                normal
            ),
            Paragraph(
                (
                    f"{type_tarification} — "
                    f"{tarif:.2f} €"
                ),
                normal
            )
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

    elements.append(table_infos)

    elements.append(Spacer(1, 8))

    # --------------------------------------------------------
    # TABLE DES SÉANCES
    # --------------------------------------------------------

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

    elements.append(table_seances)

    elements.append(Spacer(1, 7))

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    lignes_total = [
        [
            Paragraph(
                "<b>Sous-total</b>",
                normal
            ),
            Paragraph(
                f"<b>{sous_total:.2f} €</b>",
                droite
            )
        ]
    ]

    if montant_remise > 0:

        if remise_type == "Pourcentage":

            texte_remise = (
                f"Remise exceptionnelle "
                f"({remise_valeur:.2f} %)"
            )

        else:

            texte_remise = (
                f"Remise exceptionnelle"
            )

        lignes_total.append(
            [
                Paragraph(
                    texte_remise,
                    normal
                ),
                Paragraph(
                    f"- {montant_remise:.2f} €",
                    droite
                )
            ]
        )

    lignes_total.append(
        [
            Paragraph(
                "<b>TOTAL À PAYER</b>",
                normal
            ),
            Paragraph(
                f"<b>{total_a_payer:.2f} €</b>",
                droite
            )
        ]
    )

    total_table = Table(
        lignes_total,
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
                (0, -1),
                (-1, -1),
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

    elements.append(total_table)

    elements.append(Spacer(1, 8))

    # --------------------------------------------------------
    # BILAN
    # --------------------------------------------------------

    bilan = analyser_observations(df_eleve)

    if bilan:

        elements.append(
            Paragraph(
                "<b>Bilan de la période</b>",
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

        elements.append(table_bilan)

        elements.append(Spacer(1, 6))

    # --------------------------------------------------------
    # OBSERVATION AUTOMATIQUE
    # --------------------------------------------------------

    observation_automatique = (
        generer_observation_automatique(
            df_eleve
        )
    )

    elements.append(
        Paragraph(
            "<b>Observation pédagogique</b>",
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

    elements.append(observation_table)

    elements.append(Spacer(1, 8))

    # --------------------------------------------------------
    # PAIEMENT
    # --------------------------------------------------------

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

    elements.append(table_paiement)

    elements.append(Spacer(1, 8))

    elements.append(
        Paragraph(
            "Merci pour votre confiance.",
            normal
        )
    )

    document.build(elements)

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
        "🧾 Facturation",
        "👨‍🎓 Élèves"
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

    eleves = liste_eleves()

    if not eleves:

        st.warning(
            "Aucun élève enregistré. "
            "Ajoute d'abord un élève dans "
            "l'onglet 👨‍🎓 Élèves."
        )

    elif action == "➕ Nouvelle séance":

        st.subheader("➕ Nouvelle séance")

        eleve = st.selectbox(
            "Élève",
            eleves,
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

        # ----------------------------------------------------
        # DISCIPLINE
        # ----------------------------------------------------

        disciplines_selection = st.multiselect(
            "Discipline(s)",
            DISCIPLINES,
            default=["Mathématiques"],
            key="nouvelle_disciplines"
        )

        discipline_manuel = st.text_input(
            "➕ Ajouter une discipline",
            key="nouvelle_discipline_manuel",
            placeholder="Ex. Français juridique"
        )

        disciplines_finales = [
            d for d in disciplines_selection
            if d != "Autre"
        ]

        if discipline_manuel.strip():

            disciplines_finales.append(
                discipline_manuel.strip()
            )

        disciplines = ", ".join(
            disciplines_finales
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

        travail_selection = st.multiselect(
            "Travail à faire",
            TRAVAUX,
            key="nouvelle_travail_selection"
        )

        travail_manuel = st.text_area(
            "Précisions sur le travail à faire",
            key="nouvelle_travail_manuel"
        )

        travail = ", ".join(
            [
                x for x in travail_selection
                if x != "Autre"
            ]
        )

        if travail_manuel.strip():

            if travail:
                travail += " — "

            travail += travail_manuel.strip()

        # ----------------------------------------------------
        # OBSERVATIONS
        # ----------------------------------------------------

        observations_selection = st.multiselect(
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
            [
                x for x in observations_selection
                if x != "Autre"
            ]
        )

        if observation_manuel.strip():

            if observations_finales:
                observations_finales += " — "

            observations_finales += (
                observation_manuel.strip()
            )

        # ----------------------------------------------------
        # ENREGISTRER
        # ----------------------------------------------------

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

                st.error(
                    "❌ L'heure de fin doit être "
                    "postérieure à l'heure de début."
                )

                st.stop()

            nouvelle_seance = {

                "eleve":
                    eleve,

                "date":
                    date_seance.isoformat(),

                "heure_debut":
                    heure_debut.strftime("%H:%M:%S"),

                "heure_fin":
                    heure_fin.strftime("%H:%M:%S"),

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

                try:

                    ok, message = synchroniser_drive()

                    if ok:
                        st.success(message)
                    else:
                        st.warning(message)

                except Exception as e:

                    st.warning(
                        f"Google Drive non synchronisé : {e}"
                    )

                st.rerun()

            except Exception as e:

                st.error(
                    "❌ Erreur lors de l'enregistrement."
                )

                st.code(str(e))

    # ========================================================
    # MODIFIER UNE SÉANCE
    # ========================================================

    else:

        st.subheader("✏️ Modifier une séance")

        df = recuperer_seances()

        if df.empty:

            st.info("Aucune séance enregistrée.")

        else:

            eleves_seances = sorted(
                df["eleve"]
                .dropna()
                .unique()
                .tolist()
            )

            eleve = st.selectbox(
                "Élève",
                eleves_seances
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
                    f"{str(ligne.get('heure_debut', ''))[:5]} - "
                    f"{ligne.get('contenu', '')}"
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
                    if ligne.get("mode") == "Présentiel"
                    else 1
                )
            )

            disciplines = st.text_input(
                "Discipline(s)",
                value=str(
                    ligne.get(
                        "disciplines",
                        ""
                    )
                )
            )

            contenu = st.text_area(
                "Contenu",
                value=str(
                    ligne.get(
                        "contenu",
                        ""
                    )
                )
            )

            travail = st.text_area(
                "Travail à faire",
                value=str(
                    ligne.get(
                        "travail",
                        ""
                    )
                )
            )

            observations = st.text_area(
                "Observations",
                value=str(
                    ligne.get(
                        "observations",
                        ""
                    )
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

                    st.error(
                        "❌ L'heure de fin doit être "
                        "postérieure à l'heure de début."
                    )

                    st.stop()

                modifications = {

                    "date":
                        nouvelle_date.isoformat(),

                    "heure_debut":
                        heure_debut.strftime("%H:%M:%S"),

                    "heure_fin":
                        heure_fin.strftime("%H:%M:%S"),

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

                    try:

                        ok, message = synchroniser_drive()

                        if ok:
                            st.success(message)
                        else:
                            st.warning(message)

                    except Exception as e:

                        st.warning(
                            f"Google Drive non synchronisé : {e}"
                        )

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

    st.header("📖 Cahier de texte")

    df = recuperer_seances()

    if df.empty:

        st.info("Aucune séance.")

    else:

        eleves = sorted(
            df["eleve"]
            .dropna()
            .unique()
            .tolist()
        )

        eleve = st.selectbox(
            "Élève",
            eleves
        )

        df_eleve = df[
            df["eleve"] == eleve
        ]

        if df_eleve.empty:

            st.info(
                "Aucune séance pour cet élève."
            )

        else:

            for _, ligne in df_eleve.sort_values(
                "date",
                ascending=False
            ).iterrows():

                st.markdown("---")

                st.write(
                    f"### 📅 {ligne['date']}"
                )

                st.write(
                    f"**Horaire :** "
                    f"{str(ligne['heure_debut'])[:5]} → "
                    f"{str(ligne['heure_fin'])[:5]}"
                )

                st.write(
                    f"**Mode :** "
                    f"{ligne.get('mode', '')}"
                )

                st.write(
                    f"**Discipline :** "
                    f"{ligne.get('disciplines', '')}"
                )

                st.write(
                    f"**Contenu :** "
                    f"{ligne.get('contenu', '')}"
                )

                st.write(
                    f"**Travail :** "
                    f"{ligne.get('travail', '')}"
                )

                st.write(
                    f"**Observations :** "
                    f"{ligne.get('observations', '')}"
                )


# ============================================================
# BILAN
# ============================================================

elif menu == "📊 Bilan":

    st.header("📊 Bilan")

    df = recuperer_seances()

    if df.empty:

        st.info("Aucune séance.")

    else:

        eleves = sorted(
            df["eleve"]
            .dropna()
            .unique()
            .tolist()
        )

        eleve = st.selectbox(
            "Élève",
            eleves
        )

        df_eleve = df[
            df["eleve"] == eleve
        ].copy()

        if df_eleve.empty:

            st.info("Aucune séance.")

        else:

            total_minutes = pd.to_numeric(
                df_eleve["duree_minutes"],
                errors="coerce"
            ).fillna(0).sum()

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Nombre de séances",
                    len(df_eleve)
                )

            with col2:

                st.metric(
                    "Nombre d'heures",
                    f"{total_minutes / 60:.2f} h"
                )

            st.subheader("📊 Observations")

            bilan = analyser_observations(
                df_eleve
            )

            if bilan:

                for observation, nombre in bilan.items():

                    st.write(
                        f"**{observation} :** "
                        f"{nombre}/{len(df_eleve)} séances"
                    )

            else:

                st.info(
                    "Aucune observation enregistrée."
                )

            st.subheader(
                "📝 Observation automatique"
            )

            st.info(
                generer_observation_automatique(
                    df_eleve
                )
            )

            st.dataframe(
                df_eleve,
                use_container_width=True
            )


# ============================================================
# FACTURATION
# ============================================================

elif menu == "🧾 Facturation":

    st.header("🧾 Facturation")

    df = recuperer_seances()

    if df.empty:

        st.info("Aucune séance.")

    else:

        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        eleves = sorted(
            df["eleve"]
            .dropna()
            .unique()
            .tolist()
        )

        eleve = st.selectbox(
            "Élève",
            eleves,
            key="facture_eleve"
        )

        # ----------------------------------------------------
        # RÉCUPÉRATION DES INFORMATIONS DE L'ÉLÈVE
        # ----------------------------------------------------

        df_eleves = recuperer_eleves()

        infos_eleve = df_eleves[
            df_eleves.apply(
                lambda ligne:
                    (
                        f"{ligne.get('prenom', '')} "
                        f"{ligne.get('nom', '')}"
                    ).strip()
                    == eleve,
                axis=1
            )
        ]

        if not infos_eleve.empty:

            ligne_eleve = infos_eleve.iloc[0]

            niveau = ligne_eleve.get(
                "classe_actuelle",
                ""
            )

            if pd.isna(niveau):
                niveau = ""

            type_tarification = ligne_eleve.get(
                "type_tarification",
                "Tarif horaire"
            )

            if pd.isna(type_tarification):
                type_tarification = "Tarif horaire"

            tarif_horaire = ligne_eleve.get(
                "tarif_horaire",
                0
            )

            if pd.isna(tarif_horaire):
                tarif_horaire = 0.0

            forfait_mensuel = ligne_eleve.get(
                "forfait_mensuel",
                0
            )

            if pd.isna(forfait_mensuel):
                forfait_mensuel = 0.0

        else:

            niveau = ""

            type_tarification = "Tarif horaire"

            tarif_horaire = 0.0

            forfait_mensuel = 0.0

        # ----------------------------------------------------
        # INFORMATIONS
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.info(
                f"🎓 **Niveau / classe :** {niveau}"
            )

        with col2:

            st.info(
                f"💶 **Tarification :** "
                f"{type_tarification}"
            )

        # ----------------------------------------------------
        # TARIF RÉCUPÉRÉ
        # ----------------------------------------------------

        if type_tarification == "Forfait mensuel":

            tarif_defaut = float(
                forfait_mensuel
            )

        else:

            tarif_defaut = float(
                tarif_horaire
            )

        tarif = st.number_input(
            (
                "Forfait mensuel (€)"
                if type_tarification == "Forfait mensuel"
                else "Tarif horaire (€)"
            ),
            min_value=0.0,
            value=tarif_defaut,
            step=1.0,
            key="facture_tarif"
        )

        st.caption(
            "Le tarif est récupéré automatiquement "
            "depuis la fiche de l'élève. "
            "Tu peux exceptionnellement le modifier "
            "pour cette facture."
        )

        # ----------------------------------------------------
        # PÉRIODE
        # ----------------------------------------------------

        type_periode = st.selectbox(
            "Période de facturation",
            [
                "Mensuelle",
                "Personnalisée"
            ],
            key="facture_type_periode"
        )

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

        periode = (
            f"{date_debut.strftime('%d/%m/%Y')} "
            f"– "
            f"{date_fin_inclusive.strftime('%d/%m/%Y')}"
        )

        st.info(
            f"📅 Période facturée : {periode}"
        )

        # ----------------------------------------------------
        # REMISE EXCEPTIONNELLE
        # ----------------------------------------------------

        st.subheader(
            "🏷️ Remise exceptionnelle"
        )

        remise_type = st.selectbox(
            "Type de remise",
            [
                "Aucune",
                "Pourcentage",
                "Montant (€)"
            ],
            key="facture_remise_type"
        )

        remise_valeur = 0.0

        if remise_type == "Pourcentage":

            remise_valeur = st.number_input(
                "Remise (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=1.0,
                key="facture_remise_pourcentage"
            )

        elif remise_type == "Montant (€)":

            remise_valeur = st.number_input(
                "Montant de la remise (€)",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key="facture_remise_montant"
            )

        # ----------------------------------------------------
        # STATUT
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # FILTRAGE DES SÉANCES
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # AUCUNE SÉANCE
        # ----------------------------------------------------

        if df_eleve.empty:

            st.warning(
                "Aucune séance pour cet élève "
                "durant cette période."
            )

        else:

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

            # ------------------------------------------------
            # CALCUL DU SOUS-TOTAL
            # ------------------------------------------------

            if type_tarification == "Forfait mensuel":

                sous_total = float(tarif)

            else:

                sous_total = (
                    total_heures
                    * float(tarif)
                )

            # ------------------------------------------------
            # CALCUL REMISE
            # ------------------------------------------------

            montant_remise = 0.0

            if remise_type == "Pourcentage":

                montant_remise = (
                    sous_total
                    * remise_valeur
                    / 100
                )

            elif remise_type == "Montant (€)":

                montant_remise = min(
                    remise_valeur,
                    sous_total
                )

            total_a_payer = (
                sous_total
                - montant_remise
            )

            nombre_seances = len(
                df_eleve
            )

            # ------------------------------------------------
            # INDICATEURS
            # ------------------------------------------------

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
                    "Total à payer",
                    f"{total_a_payer:.2f} €"
                )

            # ------------------------------------------------
            # RÉSUMÉ
            # ------------------------------------------------

            st.subheader(
                "💶 Résumé financier"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    f"**Sous-total :** "
                    f"{sous_total:.2f} €"
                )

            with col2:

                st.write(
                    f"**Remise :** "
                    f"- {montant_remise:.2f} €"
                )

            with col3:

                st.write(
                    f"**TOTAL :** "
                    f"{total_a_payer:.2f} €"
                )

            # ------------------------------------------------
            # TABLEAU DES SÉANCES
            # ------------------------------------------------

            st.subheader(
                "📋 Bilan des séances"
            )

            tableau = df_eleve.copy()

            tableau["Date"] = pd.to_datetime(
                tableau["date"],
                errors="coerce"
            ).dt.strftime(
                "%d/%m/%Y"
            )

            tableau["Horaire"] = (
                tableau["heure_debut"]
                .astype(str)
                .str[:5]
                + "-"
                + tableau["heure_fin"]
                .astype(str)
                .str[:5]
            )

            tableau["Durée"] = (
                tableau["duree_minutes"]
                / 60
            ).round(2).astype(str) + " h"

            tableau_facture = tableau[
                [
                    "Date",
                    "Horaire",
                    "mode",
                    "disciplines",
                    "Durée"
                ]
            ].rename(
                columns={
                    "mode": "Mode",
                    "disciplines": "Discipline"
                }
            )

            st.dataframe(
                tableau_facture,
                use_container_width=True,
                hide_index=True
            )

            # ------------------------------------------------
            # BILAN OBSERVATIONS
            # ------------------------------------------------

            st.subheader(
                "📊 Bilan des observations"
            )

            bilan = analyser_observations(
                df_eleve
            )

            if bilan:

                for observation, nombre in bilan.items():

                    pourcentage = (
                        nombre
                        / nombre_seances
                        * 100
                    )

                    st.write(
                        f"**{observation} :** "
                        f"{nombre}/{nombre_seances} "
                        f"séances "
                        f"({pourcentage:.0f} %)"
                    )

            else:

                st.info(
                    "Aucune observation enregistrée "
                    "pour cette période."
                )

            # ------------------------------------------------
            # OBSERVATION AUTOMATIQUE
            # ------------------------------------------------

            st.subheader(
                "📝 Observation automatique"
            )

            st.info(
                generer_observation_automatique(
                    df_eleve
                )
            )

            # ------------------------------------------------
            # NUMÉRO FACTURE
            # ------------------------------------------------

            numero_facture = st.text_input(
                "Numéro de facture",
                value=(
                    f"CH-"
                    f"{date_debut.strftime('%Y%m%d')}-"
                    f"{date_fin_inclusive.strftime('%Y%m%d')}-"
                    f"{eleve.upper().replace(' ', '-')}"
                ),
                key="numero_facture"
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
                        niveau,
                        type_tarification,
                        tarif,
                        remise_type,
                        remise_valeur,
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
                        f"{eleve.replace(' ', '_')}_"
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

                    st.code(str(e))

            # ------------------------------------------------
            # TÉLÉCHARGEMENT
            # ------------------------------------------------

            if "facture_pdf" in st.session_state:

                st.subheader(
                    "👁️ Facture générée"
                )

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


# ============================================================
# GESTION DES ÉLÈVES
# ============================================================

elif menu == "👨‍🎓 Élèves":

    st.header("👨‍🎓 Gestion des élèves")

    action_eleve = st.radio(
        "Action",
        [
            "➕ Ajouter un élève",
            "✏️ Modifier un élève",
            "🗑️ Supprimer un élève"
        ],
        horizontal=True
    )

    # ========================================================
    # AJOUT
    # ========================================================

    if action_eleve == "➕ Ajouter un élève":

        st.subheader("➕ Ajouter un élève")

        prenom = st.text_input(
            "Prénom *",
            key="eleve_nouveau_prenom"
        )

        nom = st.text_input(
            "Nom",
            key="eleve_nouveau_nom"
        )

        classe = st.text_input(
            "Niveau / classe",
            key="eleve_nouvelle_classe",
            placeholder="Ex. 4e, 2nde, Terminale..."
        )

        st.subheader("💶 Tarification")

        type_tarification = st.selectbox(
            "Type de tarification",
            [
                "Tarif horaire",
                "Forfait mensuel"
            ],
            key="eleve_nouveau_type_tarification"
        )

        if type_tarification == "Tarif horaire":

            tarif_horaire = st.number_input(
                "Tarif horaire (€)",
                min_value=0.0,
                value=30.0,
                step=1.0,
                key="eleve_nouveau_tarif_horaire"
            )

            forfait_mensuel = 0.0

        else:

            tarif_horaire = 0.0

            forfait_mensuel = st.number_input(
                "Forfait mensuel (€)",
                min_value=0.0,
                value=120.0,
                step=5.0,
                key="eleve_nouveau_forfait_mensuel"
            )

        if st.button(
            "💾 Ajouter l'élève",
            type="primary"
        ):

            prenom = prenom.strip()
            nom = nom.strip()
            classe = classe.strip()

            if not prenom:

                st.error(
                    "❌ Le prénom est obligatoire."
                )

            else:

                nouvel_eleve = {

                    "prenom":
                        prenom,

                    "nom":
                        nom if nom else None,

                    "classe_actuelle":
                        classe if classe else None,

                    "type_tarification":
                        type_tarification,

                    "tarif_horaire":
                        tarif_horaire,

                    "forfait_mensuel":
                        forfait_mensuel
                }

                try:

                    (
                        supabase
                        .table("eleves")
                        .insert(
                            nouvel_eleve
                        )
                        .execute()
                    )

                    st.success(
                        f"✅ Élève {prenom} ajouté."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "❌ Erreur lors de l'ajout."
                    )

                    st.code(str(e))

    # ========================================================
    # MODIFICATION
    # ========================================================

    elif action_eleve == "✏️ Modifier un élève":

        st.subheader(
            "✏️ Modifier un élève"
        )

        df_eleves = recuperer_eleves()

        if df_eleves.empty:

            st.info(
                "Aucun élève enregistré."
            )

        else:

            choix_eleves = []

            for _, ligne in df_eleves.iterrows():

                prenom = str(
                    ligne.get(
                        "prenom",
                        ""
                    )
                ).strip()

                nom = str(
                    ligne.get(
                        "nom",
                        ""
                    )
                ).strip()

                affichage = (
                    f"{prenom} {nom}"
                    if nom
                    else prenom
                )

                choix_eleves.append(
                    (
                        ligne["id"],
                        affichage
                    )
                )

            choix = st.selectbox(
                "Élève à modifier",
                choix_eleves,
                format_func=lambda x: x[1],
                key="eleve_a_modifier"
            )

            id_eleve = choix[0]

            ligne = df_eleves[
                df_eleves["id"] == id_eleve
            ].iloc[0]

            prenom_modifie = st.text_input(
                "Prénom *",
                value=str(
                    ligne.get(
                        "prenom",
                        ""
                    )
                ),
                key="eleve_mod_prenom"
            )

            nom_valeur = ligne.get(
                "nom",
                ""
            )

            if pd.isna(nom_valeur):
                nom_valeur = ""

            nom_modifie = st.text_input(
                "Nom",
                value=str(nom_valeur),
                key="eleve_mod_nom"
            )

            classe_valeur = ligne.get(
                "classe_actuelle",
                ""
            )

            if pd.isna(classe_valeur):
                classe_valeur = ""

            classe_modifiee = st.text_input(
                "Niveau / classe",
                value=str(classe_valeur),
                key="eleve_mod_classe"
            )

            st.subheader("💶 Tarification")

            type_actuel = ligne.get(
                "type_tarification",
                "Tarif horaire"
            )

            if pd.isna(type_actuel):
                type_actuel = "Tarif horaire"

            type_actuel = str(type_actuel)

            if type_actuel not in [
                "Tarif horaire",
                "Forfait mensuel"
            ]:

                type_actuel = "Tarif horaire"

            type_tarification_modifie = st.selectbox(
                "Type de tarification",
                [
                    "Tarif horaire",
                    "Forfait mensuel"
                ],
                index=[
                    "Tarif horaire",
                    "Forfait mensuel"
                ].index(type_actuel),
                key="eleve_mod_type_tarification"
            )

            if (
                type_tarification_modifie
                == "Tarif horaire"
            ):

                tarif_horaire_actuel = ligne.get(
                    "tarif_horaire",
                    0
                )

                if pd.isna(
                    tarif_horaire_actuel
                ):
                    tarif_horaire_actuel = 0.0

                tarif_horaire_modifie = st.number_input(
                    "Tarif horaire (€)",
                    min_value=0.0,
                    value=float(
                        tarif_horaire_actuel
                    ),
                    step=1.0,
                    key="eleve_mod_tarif_horaire"
                )

                forfait_mensuel_modifie = 0.0

            else:

                tarif_horaire_modifie = 0.0

                forfait_mensuel_actuel = ligne.get(
                    "forfait_mensuel",
                    0
                )

                if pd.isna(
                    forfait_mensuel_actuel
                ):
                    forfait_mensuel_actuel = 0.0

                forfait_mensuel_modifie = st.number_input(
                    "Forfait mensuel (€)",
                    min_value=0.0,
                    value=float(
                        forfait_mensuel_actuel
                    ),
                    step=5.0,
                    key="eleve_mod_forfait_mensuel"
                )

            if st.button(
                "💾 Enregistrer les modifications",
                type="primary"
            ):

                prenom_modifie = (
                    prenom_modifie.strip()
                )

                if not prenom_modifie:

                    st.error(
                        "❌ Le prénom est obligatoire."
                    )

                else:

                    modifications = {

                        "prenom":
                            prenom_modifie,

                        "nom":
                            nom_modifie.strip()
                            if nom_modifie.strip()
                            else None,

                        "classe_actuelle":
                            classe_modifiee.strip()
                            if classe_modifiee.strip()
                            else None,

                        "type_tarification":
                            type_tarification_modifie,

                        "tarif_horaire":
                            tarif_horaire_modifie,

                        "forfait_mensuel":
                            forfait_mensuel_modifie
                    }

                    try:

                        (
                            supabase
                            .table("eleves")
                            .update(
                                modifications
                            )
                            .eq(
                                "id",
                                id_eleve
                            )
                            .execute()
                        )

                        st.success(
                            "✅ Élève et tarification modifiés."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur lors de la modification."
                        )

                        st.code(str(e))

    # ========================================================
    # SUPPRESSION
    # ========================================================

    else:

        st.subheader(
            "🗑️ Supprimer un élève"
        )

        df_eleves = recuperer_eleves()

        if df_eleves.empty:

            st.info(
                "Aucun élève enregistré."
            )

        else:

            choix_eleves = []

            for _, ligne in df_eleves.iterrows():

                prenom = str(
                    ligne.get(
                        "prenom",
                        ""
                    )
                ).strip()

                nom = str(
                    ligne.get(
                        "nom",
                        ""
                    )
                ).strip()

                affichage = (
                    f"{prenom} {nom}"
                    if nom
                    else prenom
                )

                choix_eleves.append(
                    (
                        ligne["id"],
                        affichage
                    )
                )

            choix = st.selectbox(
                "Élève à supprimer",
                choix_eleves,
                format_func=lambda x: x[1],
                key="eleve_a_supprimer"
            )

            id_eleve = choix[0]

            nom_eleve = choix[1]

            st.warning(
                f"⚠️ Tu es sur le point de supprimer : "
                f"**{nom_eleve}**"
            )

            st.write(
                "La suppression de l'élève ne supprime "
                "pas automatiquement ses séances."
            )

            confirmation = st.checkbox(
                "Je confirme vouloir supprimer cet élève.",
                key="confirmation_suppression_eleve"
            )

            if st.button(
                "🗑️ Supprimer définitivement",
                type="primary"
            ):

                if not confirmation:

                    st.error(
                        "❌ Coche d'abord la case de confirmation."
                    )

                else:

                    try:

                        (
                            supabase
                            .table("eleves")
                            .delete()
                            .eq(
                                "id",
                                id_eleve
                            )
                            .execute()
                        )

                        st.success(
                            f"✅ {nom_eleve} a été supprimé."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur lors de la suppression."
                        )

                        st.code(str(e))
