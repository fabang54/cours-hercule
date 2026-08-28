import streamlit as st
import pandas as pd
import io
import base64

from datetime import date, time
from io import BytesIO

from supabase import create_client

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
# UTILISATEUR
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
    "Informatique",
    "Français",
    "Anglais",
    "Technologie",
    "Culture générale",
    "Autre"
]

NIVEAUX = [
    "CP",
    "CE1",
    "CE2",
    "CM1",
    "CM2",
    "6e",
    "5e",
    "4e",
    "3e",
    "2nde",
    "1re",
    "Terminale",
    "BTS",
    "Supérieur",
    "Autre"
]

CONTENUS = [
    "Nombres relatifs",
    "Fractions",
    "Calcul littéral",
    "Développement",
    "Factorisation",
    "Équations",
    "Inéquations",
    "Proportionnalité",
    "Pourcentages",
    "Pythagore",
    "Thalès",
    "Trigonométrie",
    "Géométrie",
    "Fonctions",
    "Fonctions linéaires",
    "Fonctions affines",
    "Statistiques",
    "Probabilités",
    "Algorithmique",
    "Python",
    "SQL",
    "Révisions",
    "Préparation contrôle",
    "Préparation examen",
    "Autre"
]

TRAVAUX = [
    "Aucun",
    "Exercices du manuel",
    "Exercices supplémentaires",
    "Exercices d'application",
    "Exercices de consolidation",
    "Exercices d'approfondissement",
    "Revoir le cours",
    "Apprendre le cours",
    "Relire la leçon",
    "Faire une fiche de révision",
    "Terminer les exercices",
    "Corriger les exercices",
    "Préparer le prochain cours",
    "Préparer un contrôle",
    "Préparer un devoir",
    "Réviser les notions vues",
    "S'entraîner régulièrement",
    "Travail à poursuivre",
    "Autre"
]

OBSERVATIONS = [
    "Élève attentif",
    "Très attentif",
    "Bonne concentration",
    "Concentration satisfaisante",
    "Élève distrait",
    "Difficultés de concentration",
    "Élève fatigué",
    "Manque d'énergie",
    "Bonne participation",
    "Très bonne participation",
    "Participation satisfaisante",
    "Élève volontaire",
    "Élève motivé",
    "Bonne implication",
    "Très bonne implication",
    "Travail sérieux",
    "Travail régulier",
    "Bonne autonomie",
    "Autonomie à renforcer",
    "Difficultés de compréhension",
    "Difficultés importantes",
    "Notions à consolider",
    "Bases à reprendre",
    "Besoin d'accompagnement",
    "Progrès constatés",
    "Progrès importants",
    "Notions bien maîtrisées",
    "Bonne maîtrise",
    "Très bonne séance",
    "Séance satisfaisante",
    "Travail à poursuivre",
    "Travail régulier recommandé",
    "Autre"
]

CONTRATS = [
    "Aucun contrat spécifique",
    "Cours à l'heure",
    "Forfait mensuel",
    "Forfait mensuel avec engagement",
    "Cours ponctuels",
    "Cours réguliers",
    "Cours intensifs",
    "Préparation examen",
    "Autre"
]


# ============================================================
# ÉLÈVES
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

        if not resultat.data:
            return pd.DataFrame()

        return pd.DataFrame(resultat.data)

    except Exception as e:

        st.error(f"Erreur récupération élèves : {e}")

        return pd.DataFrame()


def nom_affichage_eleve(ligne):

    prenom = str(
        ligne.get("prenom", "")
    ).strip()

    nom = str(
        ligne.get("nom", "")
    ).strip()

    if nom:
        return f"{prenom} {nom}"

    return prenom


def liste_eleves_avec_id():

    df = recuperer_eleves()

    if df.empty:
        return []

    resultat = []

    for _, ligne in df.iterrows():

        if pd.isna(ligne.get("id")):
            continue

        nom = nom_affichage_eleve(ligne)

        if nom:
            resultat.append(
                (
                    int(ligne["id"]),
                    nom
                )
            )

    return sorted(
        resultat,
        key=lambda x: x[1].lower()
    )


def recuperer_eleve(id_eleve):

    try:

        resultat = (
            supabase
            .table("eleves")
            .select("*")
            .eq("id", id_eleve)
            .limit(1)
            .execute()
        )

        if resultat.data:
            return resultat.data[0]

    except Exception as e:

        st.error(
            f"Erreur récupération élève : {e}"
        )

    return None


# ============================================================
# SÉANCES
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

        if not resultat.data:
            return pd.DataFrame()

        return pd.DataFrame(resultat.data)

    except Exception as e:

        st.error(
            f"Erreur récupération séances : {e}"
        )

        return pd.DataFrame()


def recuperer_seances_eleve(id_eleve):

    df = recuperer_seances()

    if df.empty:
        return pd.DataFrame()

    if "eleve_id" not in df.columns:
        return pd.DataFrame()

    df = df[
        pd.to_numeric(
            df["eleve_id"],
            errors="coerce"
        ) == int(id_eleve)
    ].copy()

    return df


def nom_eleve_depuis_id(id_eleve):

    eleve = recuperer_eleve(id_eleve)

    if eleve is None:
        return "Élève inconnu"

    return nom_affichage_eleve(eleve)


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

    credentials = Credentials(
        token=st.user.tokens["access"]
    )

    return build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )


def obtenir_dossier_cours_hercule(service):

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
        return dossiers[0]["id"]

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

    return dossier["id"]


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


def sauvegarder_dans_drive(df):

    from googleapiclient.http import MediaIoBaseUpload

    service = obtenir_service_drive()

    dossier_id = obtenir_dossier_cours_hercule(
        service
    )

    contenu = dataframe_csv_bytes(df)

    media = MediaIoBaseUpload(
        BytesIO(contenu),
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

        return False, "Aucune séance à sauvegarder."

    try:

        resultat = sauvegarder_dans_drive(df)

        return (
            True,
            f"☁️ seances.csv {resultat} dans Google Drive."
        )

    except Exception as e:

        return False, f"⚠️ Google Drive : {e}"


def sauvegarder_facture_pdf_dans_drive(
    pdf_bytes,
    nom_fichier
):

    from googleapiclient.http import MediaIoBaseUpload

    service = obtenir_service_drive()

    dossier_id = obtenir_dossier_cours_hercule(
        service
    )

    media = MediaIoBaseUpload(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        resumable=False
    )

    resultat = (
        service.files()
        .list(
            q=(
                f"'{dossier_id}' in parents "
                f"and name = '{nom_fichier}' "
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

        return "mise à jour"

    (
        service.files()
        .create(
            body={
                "name": nom_fichier,
                "parents": [dossier_id],
                "mimeType": "application/pdf"
            },
            media_body=media,
            fields="id,name"
        )
        .execute()
    )

    return "créée"


# ============================================================
# OBSERVATIONS
# ============================================================

def analyser_observations(df_eleve):

    bilan = {}

    if df_eleve.empty:
        return bilan

    if "observations" not in df_eleve.columns:
        return bilan

    textes = (
        df_eleve["observations"]
        .fillna("")
        .astype(str)
    )

    for observation in OBSERVATIONS:

        if observation == "Autre":
            continue

        nombre = textes.apply(
            lambda texte:
            observation.lower() in texte.lower()
        ).sum()

        if nombre > 0:
            bilan[observation] = int(nombre)

    return bilan


def generer_observation_automatique(df_eleve):

    nombre_seances = len(df_eleve)

    if nombre_seances == 0:
        return "Aucune séance disponible."

    bilan = analyser_observations(df_eleve)

    phrases = []

    for observation in [
        "Élève attentif",
        "Très attentif",
        "Bonne concentration",
        "Concentration satisfaisante",
        "Élève distrait",
        "Difficultés de concentration",
        "Bonne participation",
        "Très bonne participation",
        "Élève motivé",
        "Bonne implication",
        "Travail sérieux",
        "Bonne autonomie",
        "Difficultés de compréhension",
        "Difficultés importantes",
        "Notions à consolider",
        "Progrès constatés",
        "Progrès importants",
        "Notions bien maîtrisées"
    ]:

        nombre = bilan.get(
            observation,
            0
        )

        if nombre > 0:

            phrases.append(
                f"{observation} : "
                f"{nombre} séance(s) sur "
                f"{nombre_seances}."
            )

    if not phrases:

        phrases.append(
            "Aucune observation particulière "
            "n'a été relevée."
        )

    return " ".join(phrases)


# ============================================================
# FACTURE PDF
# ============================================================

def generer_facture_pdf(
    df_eleve,
    eleve,
    niveau,
    tarif_horaire,
    forfait_mensuel,
    remise,
    numero_facture,
    periode,
    statut,
    date_paiement,
    type_tarification,
    observation_pedagogique
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

    droite = ParagraphStyle(
        "Droite",
        parent=normal,
        alignment=TA_RIGHT
    )

    elements = []

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

    df_eleve = df_eleve.copy()

    df_eleve["duree_minutes"] = pd.to_numeric(
        df_eleve["duree_minutes"],
        errors="coerce"
    ).fillna(0)

    total_minutes = (
        df_eleve["duree_minutes"].sum()
    )

    total_heures = total_minutes / 60

    nombre_seances = len(df_eleve)

    if type_tarification == "Forfait mensuel":

        sous_total = float(
            forfait_mensuel or 0
        )

        libelle_tarif = (
            f"Forfait mensuel : "
            f"{sous_total:.2f} €"
        )

    else:

        sous_total = (
            total_heures *
            float(tarif_horaire or 0)
        )

        libelle_tarif = (
            f"Tarif horaire : "
            f"{float(tarif_horaire or 0):.2f} € / h"
        )

    montant_final = max(
        0,
        sous_total - float(remise or 0)
    )

    infos = [
        [
            Paragraph("<b>Élève</b>", normal),
            Paragraph(str(eleve), normal)
        ],
        [
            Paragraph("<b>Niveau / classe</b>", normal),
            Paragraph(str(niveau or ""), normal)
        ],
        [
            Paragraph("<b>Date de facture</b>", normal),
            Paragraph(
                date.today().strftime("%d/%m/%Y"),
                normal
            )
        ],
        [
            Paragraph("<b>Période</b>", normal),
            Paragraph(periode, normal)
        ],
        [
            Paragraph("<b>Nombre de séances</b>", normal),
            Paragraph(str(nombre_seances), normal)
        ],
        [
            Paragraph("<b>Total heures</b>", normal),
            Paragraph(
                f"{total_heures:.2f} h",
                normal
            )
        ],
        [
            Paragraph("<b>Tarification</b>", normal),
            Paragraph(
                type_tarification,
                normal
            )
        ],
        [
            Paragraph("<b>Tarif appliqué</b>", normal),
            Paragraph(
                libelle_tarif,
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
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
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

    donnees = [
        [
            "Date",
            "Horaire",
            "Mode",
            "Discipline",
            "Durée"
        ]
    ]

    for _, ligne in df_eleve.iterrows():

        duree = float(
            pd.to_numeric(
                ligne.get("duree_minutes"),
                errors="coerce"
            ) or 0
        )

        try:

            date_ligne = pd.to_datetime(
                ligne.get("date")
            ).strftime("%d/%m/%Y")

        except Exception:

            date_ligne = str(
                ligne.get("date", "")
            )

        debut = str(
            ligne.get("heure_debut", "")
        )[:5]

        fin = str(
            ligne.get("heure_fin", "")
        )[:5]

        donnees.append([
            date_ligne,
            f"{debut}-{fin}",
            str(ligne.get("mode", "")),
            str(ligne.get("disciplines", "")),
            f"{duree / 60:.2f} h"
        ])

    table_seances = Table(
        donnees,
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
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
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
    elements.append(Spacer(1, 8))

    total_table = Table(
        [
            [
                Paragraph(
                    "<b>Sous-total</b>",
                    normal
                ),
                Paragraph(
                    f"<b>{sous_total:.2f} €</b>",
                    droite
                )
            ],
            [
                Paragraph(
                    "<b>Remise</b>",
                    normal
                ),
                Paragraph(
                    f"<b>- {float(remise or 0):.2f} €</b>",
                    droite
                )
            ],
            [
                Paragraph(
                    "<b>TOTAL À PAYER</b>",
                    normal
                ),
                Paragraph(
                    f"<b>{montant_final:.2f} €</b>",
                    droite
                )
            ]
        ],
        colWidths=[380, 150]
    )

    total_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
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

    elements.append(total_table)
    elements.append(Spacer(1, 8))

    # --------------------------------------------------------
    # BILAN COMPORTEMENTAL
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "<b>Bilan comportemental</b>",
            normal
        )
    )

    bilan = analyser_observations(df_eleve)

    lignes_bilan = []

    for observation, nombre in bilan.items():

        lignes_bilan.append([
            Paragraph(
                str(observation),
                normal
            ),
            Paragraph(
                f"{nombre} séance(s) sur "
                f"{nombre_seances}",
                droite
            )
        ])

    if not lignes_bilan:

        lignes_bilan.append([
            Paragraph(
                "Aucune observation enregistrée.",
                normal
            ),
            Paragraph(
                "",
                normal
            )
        ])

    bilan_table = Table(
        lignes_bilan,
        colWidths=[380, 150]
    )

    bilan_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
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

    elements.append(bilan_table)
    elements.append(Spacer(1, 8))

    # --------------------------------------------------------
    # OBSERVATION PÉDAGOGIQUE PERSONNALISÉE
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "<b>Observation pédagogique</b>",
            normal
        )
    )

    obs_table = Table(
        [[
            Paragraph(
                observation_pedagogique
                .replace("\n", "<br/>"),
                normal
            )
        ]],
        colWidths=[530]
    )

    obs_table.setStyle(
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

    elements.append(obs_table)
    elements.append(Spacer(1, 8))

    # --------------------------------------------------------
    # PAIEMENT
    # --------------------------------------------------------

    statut_pdf = (
        "PAYÉE"
        if statut == "Payée"
        else "EN ATTENTE DE PAIEMENT"
    )

    date_pdf = (
        date_paiement.strftime("%d/%m/%Y")
        if date_paiement
        else "—"
    )

    paiement = [
        [
            Paragraph(
                "<b>Statut</b>",
                normal
            ),
            Paragraph(
                f"<b>{statut_pdf}</b>",
                normal
            )
        ],
        [
            Paragraph(
                "<b>Date de paiement</b>",
                normal
            ),
            Paragraph(
                date_pdf,
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
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
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

    return buffer.getvalue(), montant_final


# ============================================================
# AFFICHER PDF DANS STREAMLIT
# ============================================================

def afficher_pdf(pdf_bytes):

    base64_pdf = base64.b64encode(
        pdf_bytes
    ).decode("utf-8")

    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="100%"
        height="850"
        type="application/pdf">
    </iframe>
    """

    st.components.v1.html(
        pdf_display,
        height=870
    )


# ============================================================
# FACTURES
# ============================================================

def recuperer_factures():

    try:

        resultat = (
            supabase
            .table("factures")
            .select("*")
            .order(
                "date_facture",
                desc=True
            )
            .execute()
        )

        if not resultat.data:
            return pd.DataFrame()

        return pd.DataFrame(
            resultat.data
        )

    except Exception as e:

        st.error(
            f"Erreur récupération factures : {e}"
        )

        return pd.DataFrame()


def enregistrer_facture(
    numero_facture,
    eleve,
    periode,
    nombre_seances,
    total_heures,
    tarif_horaire,
    forfait_mensuel,
    remise,
    montant_total,
    statut,
    date_paiement
):

    donnees = {
        "numero_facture": numero_facture,
        "eleve": eleve,
        "periode": periode,
        "date_facture": date.today().isoformat(),
        "nombre_seances": int(
            nombre_seances
        ),
        "total_heures": float(
            total_heures
        ),
        "tarif_horaire": float(
            tarif_horaire or 0
        ),
        "forfait_mensuel": float(
            forfait_mensuel or 0
        ),
        "remise": float(
            remise or 0
        ),
        "montant_total": float(
            montant_total
        ),
        "statut": statut,
        "date_paiement": (
            date_paiement.isoformat()
            if date_paiement
            else None
        )
    }

    return (
        supabase
        .table("factures")
        .insert(donnees)
        .execute()
    )


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
            "✏️ Modifier une séance",
            "🗑️ Supprimer une séance"
        ],
        horizontal=True
    )

    eleves = liste_eleves_avec_id()

    if not eleves:

        st.warning(
            "Aucun élève enregistré."
        )

    # ========================================================
    # NOUVELLE SÉANCE
    # ========================================================

    elif action == "➕ Nouvelle séance":

        st.subheader("➕ Nouvelle séance")

        eleve_selection = st.selectbox(
            "Élève",
            eleves,
            format_func=lambda x: x[1]
        )

        eleve_id = eleve_selection[0]
        eleve_nom = eleve_selection[1]

        date_seance = st.date_input(
            "Date *",
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
            DISCIPLINES,
            default=["Mathématiques"]
        )

        discipline_autre = st.text_input(
            "✏️ Autre discipline"
        )

        disciplines_finales = list(
            disciplines
        )

        if discipline_autre.strip():

            disciplines_finales.append(
                discipline_autre.strip()
            )

        contenu_selection = st.multiselect(
            "Contenu",
            CONTENUS
        )

        contenu_manuel = st.text_area(
            "Précisions / contenu supplémentaire"
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
            TRAVAUX
        )

        travail_manuel = st.text_input(
            "✏️ Précision sur le travail à faire"
        )

        if travail == "Autre":

            travail_final = travail_manuel.strip()

        elif travail_manuel.strip():

            travail_final = (
                travail
                + " — "
                + travail_manuel.strip()
            )

        else:

            travail_final = travail

        observations = st.multiselect(
            "Observations",
            OBSERVATIONS,
            default=["Élève attentif"]
        )

        observation_manuel = st.text_area(
            "Observations supplémentaires"
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

                st.error(
                    "L'heure de fin doit être "
                    "postérieure à l'heure de début."
                )

                st.stop()

            nouvelle_seance = {
                "eleve_id": eleve_id,
                "eleve": eleve_nom,
                "date": date_seance.isoformat(),
                "heure_debut":
                    heure_debut.strftime("%H:%M:%S"),
                "heure_fin":
                    heure_fin.strftime("%H:%M:%S"),
                "duree_minutes": duree,
                "mode": mode,
                "disciplines":
                    ", ".join(
                        disciplines_finales
                    ),
                "contenu": contenu,
                "travail": travail_final,
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
                    "✅ Séance enregistrée."
                )

                ok, message = synchroniser_drive()

                if ok:
                    st.success(message)

                st.rerun()

            except Exception as e:

                st.error(
                    "❌ Erreur lors de l'enregistrement."
                )

                st.code(str(e))

    # ========================================================
    # MODIFIER
    # ========================================================

    elif action == "✏️ Modifier une séance":

        st.subheader(
            "✏️ Modifier une séance"
        )

        df = recuperer_seances()

        if df.empty:

            st.info(
                "Aucune séance."
            )

        else:

            if "eleve_id" not in df.columns:

                st.error(
                    "La colonne eleve_id est absente "
                    "de la table seances."
                )

                st.stop()

            df = df[
                df["eleve_id"].notna()
            ].copy()

            choix_eleves = []

            for id_eleve in sorted(
                df["eleve_id"].unique()
            ):

                choix_eleves.append(
                    (
                        int(id_eleve),
                        nom_eleve_depuis_id(
                            int(id_eleve)
                        )
                    )
                )

            eleve_selection = st.selectbox(
                "Élève",
                choix_eleves,
                format_func=lambda x: x[1]
            )

            eleve_id = eleve_selection[0]

            df_eleve = df[
                pd.to_numeric(
                    df["eleve_id"],
                    errors="coerce"
                ) == eleve_id
            ].copy()

            choix = []

            for _, ligne in df_eleve.iterrows():

                choix.append(
                    (
                        int(ligne["id"]),
                        f"{ligne.get('date','')} | "
                        f"{str(ligne.get('heure_debut',''))[:5]} → "
                        f"{str(ligne.get('heure_fin',''))[:5]} | "
                        f"{ligne.get('contenu','')}"
                    )
                )

            seance = st.selectbox(
                "Séance",
                choix,
                format_func=lambda x: x[1]
            )

            identifiant = seance[0]

            ligne = df_eleve[
                df_eleve["id"] == identifiant
            ].iloc[0]

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
                    if ligne.get("mode")
                    == "Présentiel"
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
                        "Horaire incorrect."
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
                    "mode": mode,
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

                    ok, message = synchroniser_drive()

                    if ok:
                        st.success(message)

                    st.rerun()

                except Exception as e:

                    st.error(
                        "❌ Erreur modification."
                    )

                    st.code(str(e))

    # ========================================================
    # SUPPRIMER
    # ========================================================

    else:

        st.subheader(
            "🗑️ Supprimer une séance"
        )

        df = recuperer_seances()

        if df.empty:

            st.info(
                "Aucune séance."
            )

        else:

            df = df[
                df["eleve_id"].notna()
            ].copy()

            choix_eleves = []

            for id_eleve in sorted(
                df["eleve_id"].unique()
            ):

                choix_eleves.append(
                    (
                        int(id_eleve),
                        nom_eleve_depuis_id(
                            int(id_eleve)
                        )
                    )
                )

            eleve_selection = st.selectbox(
                "Élève",
                choix_eleves,
                format_func=lambda x: x[1]
            )

            eleve_id = eleve_selection[0]

            df_eleve = df[
                pd.to_numeric(
                    df["eleve_id"],
                    errors="coerce"
                ) == eleve_id
            ].copy()

            choix_seances = []

            for _, ligne in df_eleve.iterrows():

                choix_seances.append(
                    (
                        int(ligne["id"]),
                        f"{ligne.get('date','')} | "
                        f"{str(ligne.get('heure_debut',''))[:5]} → "
                        f"{str(ligne.get('heure_fin',''))[:5]} | "
                        f"{ligne.get('contenu','')}"
                    )
                )

            seance_choisie = st.selectbox(
                "Séance à supprimer",
                choix_seances,
                format_func=lambda x: x[1]
            )

            id_seance = seance_choisie[0]

            ligne = df_eleve[
                df_eleve["id"] == id_seance
            ].iloc[0]

            st.info(
                f"""
**Élève :** {nom_eleve_depuis_id(eleve_id)}

**Date :** {ligne.get('date', '')}

**Horaire :** {str(ligne.get('heure_debut', ''))[:5]}
→ {str(ligne.get('heure_fin', ''))[:5]}

**Durée :** {ligne.get('duree_minutes', 0)} minutes

**Discipline :** {ligne.get('disciplines', '')}

**Contenu :** {ligne.get('contenu', '')}

**Travail :** {ligne.get('travail', '')}

**Observations :** {ligne.get('observations', '')}
"""
            )

            confirmation = st.checkbox(
                "Je confirme vouloir supprimer définitivement cette séance."
            )

            if st.button(
                "🗑️ Supprimer définitivement",
                type="primary"
            ):

                if not confirmation:

                    st.error(
                        "Veuillez confirmer."
                    )

                else:

                    try:

                        (
                            supabase
                            .table("seances")
                            .delete()
                            .eq(
                                "id",
                                id_seance
                            )
                            .execute()
                        )

                        st.success(
                            "✅ Séance supprimée."
                        )

                        ok, message = synchroniser_drive()

                        if ok:
                            st.success(message)

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur suppression."
                        )

                        st.code(str(e))


# ============================================================
# CAHIER DE TEXTE
# ============================================================

elif menu == "📖 Cahier de texte":

    st.header("📖 Cahier de texte")

    eleves = liste_eleves_avec_id()

    if not eleves:

        st.info("Aucun élève.")

    else:

        eleve_selection = st.selectbox(
            "Élève",
            eleves,
            format_func=lambda x: x[1]
        )

        eleve_id = eleve_selection[0]

        df_eleve = recuperer_seances_eleve(
            eleve_id
        )

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
                    f"### 📅 {ligne.get('date','')}"
                )

                st.write(
                    f"**Horaire :** "
                    f"{str(ligne.get('heure_debut',''))[:5]} "
                    f"→ "
                    f"{str(ligne.get('heure_fin',''))[:5]}"
                )

                st.write(
                    f"**Mode :** "
                    f"{ligne.get('mode','')}"
                )

                st.write(
                    f"**Discipline :** "
                    f"{ligne.get('disciplines','')}"
                )

                st.write(
                    f"**Contenu :** "
                    f"{ligne.get('contenu','')}"
                )

                st.write(
                    f"**Travail :** "
                    f"{ligne.get('travail','')}"
                )

                st.write(
                    f"**Observations :** "
                    f"{ligne.get('observations','')}"
                )


# ============================================================
# BILAN
# ============================================================

elif menu == "📊 Bilan":

    st.header("📊 Bilan")

    eleves = liste_eleves_avec_id()

    if not eleves:

        st.info("Aucun élève.")

    else:

        eleve_selection = st.selectbox(
            "Élève",
            eleves,
            format_func=lambda x: x[1]
        )

        eleve_id = eleve_selection[0]

        df_eleve = recuperer_seances_eleve(
            eleve_id
        )

        if df_eleve.empty:

            st.info(
                "Aucune séance."
            )

        else:

            df_eleve["duree_minutes"] = pd.to_numeric(
                df_eleve["duree_minutes"],
                errors="coerce"
            ).fillna(0)

            total_minutes = (
                df_eleve["duree_minutes"].sum()
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Nombre de séances",
                    len(df_eleve)
                )

            with col2:

                st.metric(
                    "Heures",
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
                    f"{nombre} séance(s) sur "
                    f"{len(df_eleve)}"
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
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# FACTURATION
# ============================================================

elif menu == "🧾 Facturation":

    st.header("🧾 Facturation")

    sous_menu = st.radio(
        "Facturation",
        [
            "🧾 Nouvelle facture",
            "📋 Factures",
            "🔴 Factures impayées"
        ],
        horizontal=True
    )

    # ========================================================
    # NOUVELLE FACTURE
    # ========================================================

    if sous_menu == "🧾 Nouvelle facture":

        eleves = liste_eleves_avec_id()

        if not eleves:

            st.info(
                "Aucun élève."
            )

        else:

            eleve_selection = st.selectbox(
                "Élève",
                eleves,
                format_func=lambda x: x[1]
            )

            eleve_id = eleve_selection[0]
            eleve = eleve_selection[1]

            informations_eleve = recuperer_eleve(
                eleve_id
            )

            niveau_existant = ""

            type_tarification_eleve = (
                "Tarif horaire"
            )

            tarif_horaire_eleve = 0.0
            forfait_mensuel_eleve = 0.0

            if informations_eleve:

                niveau_existant = (
                    informations_eleve.get(
                        "classe_actuelle",
                        ""
                    ) or ""
                )

                type_tarification_eleve = (
                    informations_eleve.get(
                        "type_tarification",
                        "Tarif horaire"
                    )
                    or "Tarif horaire"
                )

                tarif_horaire_eleve = float(
                    informations_eleve.get(
                        "tarif_horaire",
                        0
                    ) or 0
                )

                forfait_mensuel_eleve = float(
                    informations_eleve.get(
                        "forfait_mensuel",
                        0
                    ) or 0
                )

            # ------------------------------------------------
            # NIVEAU
            # ------------------------------------------------

            if niveau_existant in NIVEAUX:

                niveau_index = NIVEAUX.index(
                    niveau_existant
                )

            else:

                niveau_index = 0

            niveau_choix = st.selectbox(
                "Niveau / classe",
                NIVEAUX,
                index=niveau_index
            )

            if niveau_choix == "Autre":

                niveau = st.text_input(
                    "Niveau / classe"
                )

            else:

                niveau = niveau_choix

            # ------------------------------------------------
            # PÉRIODE
            # ------------------------------------------------

            type_periode = st.selectbox(
                "Période de facturation",
                [
                    "Mensuelle",
                    "Personnalisée"
                ]
            )

            if type_periode == "Mensuelle":

                col1, col2 = st.columns(2)

                with col1:

                    mois = st.selectbox(
                        "Mois",
                        range(1, 13),
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
                        2024,
                        2100,
                        date.today().year
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
                    date_fin
                    - pd.Timedelta(days=1)
                )

            else:

                col1, col2 = st.columns(2)

                with col1:

                    date_debut = st.date_input(
                        "Date de début",
                        date(
                            date.today().year,
                            date.today().month,
                            1
                        )
                    )

                with col2:

                    date_fin_inclusive = st.date_input(
                        "Date de fin",
                        date.today()
                    )

                if date_fin_inclusive < date_debut:

                    st.error(
                        "La date de fin est incorrecte."
                    )

                    st.stop()

            periode = (
                f"{date_debut.strftime('%d/%m/%Y')} "
                f"– "
                f"{date_fin_inclusive.strftime('%d/%m/%Y')}"
            )

            st.info(
                f"📅 {periode}"
            )

            # ------------------------------------------------
            # SÉANCES
            # ------------------------------------------------

            df_eleve = recuperer_seances_eleve(
                eleve_id
            )

            if df_eleve.empty:

                st.warning(
                    "Aucune séance pour cet élève."
                )

                st.stop()

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

            if df_eleve.empty:

                st.warning(
                    "Aucune séance pour cette période."
                )

                st.stop()

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

            nombre_seances = len(
                df_eleve
            )

            # ------------------------------------------------
            # TARIFICATION
            # ------------------------------------------------

            st.subheader(
                "💶 Tarification"
            )

            type_tarification = st.selectbox(
                "Type de tarification",
                [
                    "Tarif horaire",
                    "Forfait mensuel"
                ],
                index=(
                    1
                    if type_tarification_eleve
                    == "Forfait mensuel"
                    else 0
                )
            )

            if type_tarification == "Tarif horaire":

                tarif_horaire = st.number_input(
                    "Tarif horaire (€)",
                    min_value=0.0,
                    value=tarif_horaire_eleve,
                    step=1.0
                )

                forfait_utilise = 0.0

                sous_total = (
                    total_heures
                    * tarif_horaire
                )

            else:

                forfait_mensuel = st.number_input(
                    "Forfait mensuel (€)",
                    min_value=0.0,
                    value=forfait_mensuel_eleve,
                    step=1.0
                )

                forfait_utilise = (
                    forfait_mensuel
                )

                tarif_horaire = 0.0

                sous_total = (
                    forfait_mensuel
                )

            remise = st.number_input(
                "Remise exceptionnelle (€)",
                min_value=0.0,
                value=0.0,
                step=1.0
            )

            montant_total = max(
                0,
                sous_total - remise
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Séances",
                    nombre_seances
                )

            with col2:

                st.metric(
                    "Heures",
                    f"{total_heures:.2f} h"
                )

            with col3:

                st.metric(
                    "TOTAL",
                    f"{montant_total:.2f} €"
                )

            # ------------------------------------------------
            # PAIEMENT
            # ------------------------------------------------

            statut = st.selectbox(
                "Statut",
                [
                    "En attente de paiement",
                    "Payée"
                ]
            )

            date_paiement = None

            if statut == "Payée":

                date_paiement = st.date_input(
                    "Date de paiement",
                    date.today()
                )

            # ------------------------------------------------
            # NUMÉRO FACTURE
            # ------------------------------------------------

            numero_defaut = (
                f"CH-"
                f"{date.today().strftime('%Y%m%d')}-"
                f"{eleve_id}"
            )

            numero_facture = st.text_input(
                "Numéro de facture",
                value=numero_defaut,
                help=(
                    "Le numéro de facture ne contient "
                    "pas le nom ou le prénom de l'élève."
                )
            )

            # ------------------------------------------------
            # OBSERVATION PÉDAGOGIQUE
            # ------------------------------------------------

            st.subheader(
                "📝 Observation pédagogique"
            )

            observation_auto = (
                generer_observation_automatique(
                    df_eleve
                )
            )

            observation_pedagogique = st.text_area(
                "Observation figurant sur la facture",
                value=observation_auto,
                height=140,
                key="observation_facture"
            )

            st.caption(
                "Tu peux modifier ou compléter librement "
                "ce texte avant de générer la facture."
            )

            # ------------------------------------------------
            # APERÇU
            # ------------------------------------------------

            st.subheader(
                "👁️ Aperçu de la facture"
            )

            if st.button(
                "👁️ Afficher l'aperçu",
                type="secondary"
            ):

                try:

                    pdf, montant_final = (
                        generer_facture_pdf(
                            df_eleve,
                            eleve,
                            niveau,
                            tarif_horaire,
                            forfait_utilise,
                            remise,
                            numero_facture,
                            periode,
                            statut,
                            date_paiement,
                            type_tarification,
                            observation_pedagogique
                        )
                    )

                    st.session_state[
                        "facture_pdf_apercu"
                    ] = pdf

                    st.session_state[
                        "facture_nom_apercu"
                    ] = (
                        f"Facture_"
                        f"{numero_facture}.pdf"
                    )

                except Exception as e:

                    st.error(
                        "❌ Erreur génération aperçu."
                    )

                    st.code(str(e))

            if (
                "facture_pdf_apercu"
                in st.session_state
            ):

                afficher_pdf(
                    st.session_state[
                        "facture_pdf_apercu"
                    ]
                )

                st.download_button(
                    "📥 Télécharger l'aperçu PDF",
                    data=st.session_state[
                        "facture_pdf_apercu"
                    ],
                    file_name=st.session_state[
                        "facture_nom_apercu"
                    ],
                    mime="application/pdf"
                )

                st.divider()

                # ------------------------------------------------
                # ENREGISTREMENT
                # ------------------------------------------------

                st.subheader(
                    "💾 Enregistrer la facture"
                )

                enregistrer_drive = st.checkbox(
                    "☁️ Enregistrer également le PDF dans Google Drive",
                    value=False
                )

                if st.button(
                    "💾 Enregistrer la facture",
                    type="primary"
                ):

                    try:

                        pdf = st.session_state[
                            "facture_pdf_apercu"
                        ]

                        nom_facture = (
                            st.session_state[
                                "facture_nom_apercu"
                            ]
                        )

                        # Vérification doublon
                        anciennes = recuperer_factures()

                        doublon = False

                        if not anciennes.empty:

                            if (
                                "numero_facture"
                                in anciennes.columns
                            ):

                                doublon = (
                                    anciennes[
                                        "numero_facture"
                                    ]
                                    .astype(str)
                                    .eq(
                                        str(
                                            numero_facture
                                        )
                                    )
                                    .any()
                                )

                        if doublon:

                            st.error(
                                "❌ Ce numéro de facture existe déjà."
                            )

                        else:

                            enregistrer_facture(
                                numero_facture,
                                eleve,
                                periode,
                                nombre_seances,
                                total_heures,
                                tarif_horaire,
                                forfait_utilise,
                                remise,
                                montant_total,
                                statut,
                                date_paiement
                            )

                            st.success(
                                "✅ Facture enregistrée dans Supabase."
                            )

                            # --------------------------------
                            # DRIVE
                            # --------------------------------

                            if enregistrer_drive:

                                try:

                                    resultat_drive = (
                                        sauvegarder_facture_pdf_dans_drive(
                                            pdf,
                                            nom_facture
                                        )
                                    )

                                    st.success(
                                        "☁️ Facture "
                                        f"{resultat_drive} "
                                        "dans Google Drive."
                                    )

                                except Exception as e:

                                    st.error(
                                        "⚠️ La facture est enregistrée "
                                        "dans Supabase mais pas dans "
                                        "Google Drive."
                                    )

                                    st.code(str(e))

                    except Exception as e:

                        st.error(
                            "❌ Erreur lors de "
                            "l'enregistrement."
                        )

                        st.code(str(e))

    # ========================================================
    # FACTURES
    # ========================================================

    elif sous_menu == "📋 Factures":

        st.subheader(
            "📋 Factures enregistrées"
        )

        factures = recuperer_factures()

        if factures.empty:

            st.info(
                "Aucune facture enregistrée."
            )

        else:

            affichage = factures.copy()

            if "date_facture" in affichage.columns:

                affichage["date_facture"] = (
                    pd.to_datetime(
                        affichage["date_facture"],
                        errors="coerce"
                    )
                    .dt.strftime("%d/%m/%Y")
                )

            st.dataframe(
                affichage,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader(
                "🔎 Rechercher une facture"
            )

            numero_recherche = st.text_input(
                "Numéro de facture"
            )

            if numero_recherche.strip():

                resultat = factures[
                    factures[
                        "numero_facture"
                    ]
                    .astype(str)
                    .str.contains(
                        numero_recherche.strip(),
                        case=False,
                        na=False
                    )
                ]

                if resultat.empty:

                    st.warning(
                        "Aucune facture trouvée."
                    )

                else:

                    st.dataframe(
                        resultat,
                        use_container_width=True,
                        hide_index=True
                    )

            st.divider()

            st.subheader(
                "🗑️ Supprimer une facture"
            )

            choix = st.selectbox(
                "Facture",
                factures["id"].tolist(),
                format_func=lambda x:
                str(
                    factures.loc[
                        factures["id"] == x,
                        "numero_facture"
                    ].iloc[0]
                )
            )

            confirmation = st.checkbox(
                "Je confirme la suppression définitive."
            )

            if st.button(
                "🗑️ Supprimer la facture",
                type="primary"
            ):

                if not confirmation:

                    st.error(
                        "Coche la confirmation."
                    )

                else:

                    try:

                        (
                            supabase
                            .table("factures")
                            .delete()
                            .eq(
                                "id",
                                choix
                            )
                            .execute()
                        )

                        st.success(
                            "✅ Facture supprimée."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur suppression."
                        )

                        st.code(str(e))

    # ========================================================
    # IMPAYÉES
    # ========================================================

    else:

        st.subheader(
            "🔴 Factures impayées"
        )

        factures = recuperer_factures()

        if factures.empty:

            st.info(
                "Aucune facture enregistrée."
            )

        else:

            impayees = factures[
                factures["statut"]
                == "En attente de paiement"
            ].copy()

            if impayees.empty:

                st.success(
                    "🎉 Aucune facture impayée."
                )

            else:

                total_impaye = pd.to_numeric(
                    impayees[
                        "montant_total"
                    ],
                    errors="coerce"
                ).fillna(0).sum()

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Factures impayées",
                        len(impayees)
                    )

                with col2:

                    st.metric(
                        "Montant impayé",
                        f"{total_impaye:.2f} €"
                    )

                st.dataframe(
                    impayees,
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# ÉLÈVES
# ============================================================

elif menu == "👨‍🎓 Élèves":

    st.header(
        "👨‍🎓 Gestion des élèves"
    )

    action = st.radio(
        "Action",
        [
            "📋 Liste des élèves",
            "➕ Ajouter un élève",
            "✏️ Modifier un élève",
            "🗑️ Supprimer un élève"
        ],
        horizontal=True
    )

    # ========================================================
    # LISTE
    # ========================================================

    if action == "📋 Liste des élèves":

        df = recuperer_eleves()

        if df.empty:

            st.info(
                "Aucun élève enregistré."
            )

        else:

            colonnes = [
                c for c in [
                    "id",
                    "prenom",
                    "nom",
                    "classe_actuelle",
                    "type_tarification",
                    "tarif_horaire",
                    "forfait_mensuel",
                    "contrat"
                ]
                if c in df.columns
            ]

            affichage = df[
                colonnes
            ].copy()

            affichage = affichage.rename(
                columns={
                    "id": "ID",
                    "prenom": "Prénom",
                    "nom": "Nom",
                    "classe_actuelle":
                        "Niveau / Classe",
                    "type_tarification":
                        "Tarification",
                    "tarif_horaire":
                        "Tarif horaire",
                    "forfait_mensuel":
                        "Forfait mensuel",
                    "contrat":
                        "Contrat"
                }
            )

            st.dataframe(
                affichage,
                use_container_width=True,
                hide_index=True
            )

    # ========================================================
    # AJOUT
    # ========================================================

    elif action == "➕ Ajouter un élève":

        st.subheader(
            "➕ Ajouter un élève"
        )

        prenom = st.text_input(
            "Prénom *"
        )

        nom = st.text_input(
            "Nom"
        )

        niveau_choix = st.selectbox(
            "Niveau / Classe",
            NIVEAUX
        )

        if niveau_choix == "Autre":

            classe = st.text_input(
                "Niveau / classe"
            )

        else:

            classe = niveau_choix

        type_tarification = st.selectbox(
            "Type de tarification",
            [
                "Tarif horaire",
                "Forfait mensuel"
            ]
        )

        tarif_horaire = 0.0
        forfait_mensuel = 0.0

        if type_tarification == "Tarif horaire":

            tarif_horaire = st.number_input(
                "Tarif horaire (€)",
                min_value=0.0,
                step=1.0
            )

        else:

            forfait_mensuel = st.number_input(
                "Forfait mensuel (€)",
                min_value=0.0,
                step=1.0
            )

        contrat = st.selectbox(
            "Contrat / modalités",
            CONTRATS
        )

        contrat_precisions = st.text_area(
            "Précisions sur le contrat"
        )

        if contrat == "Autre":

            contrat_final = (
                contrat_precisions.strip()
            )

        elif contrat_precisions.strip():

            contrat_final = (
                contrat
                + " — "
                + contrat_precisions.strip()
            )

        else:

            contrat_final = contrat

        if st.button(
            "💾 Ajouter l'élève",
            type="primary"
        ):

            if not prenom.strip():

                st.error(
                    "Le prénom est obligatoire."
                )

            elif not classe.strip():

                st.error(
                    "Le niveau / classe est obligatoire."
                )

            else:

                donnees = {
                    "prenom":
                        prenom.strip(),
                    "nom":
                        nom.strip() or None,
                    "classe_actuelle":
                        classe.strip(),
                    "type_tarification":
                        type_tarification,
                    "tarif_horaire":
                        tarif_horaire,
                    "forfait_mensuel":
                        forfait_mensuel,
                    "contrat":
                        contrat_final
                }

                try:

                    (
                        supabase
                        .table("eleves")
                        .insert(donnees)
                        .execute()
                    )

                    st.success(
                        "✅ Élève ajouté."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "❌ Erreur ajout élève."
                    )

                    st.code(str(e))

    # ========================================================
    # MODIFICATION ÉLÈVE
    # ========================================================

    elif action == "✏️ Modifier un élève":

        st.subheader(
            "✏️ Modifier un élève"
        )

        eleves = liste_eleves_avec_id()

        if not eleves:

            st.info(
                "Aucun élève."
            )

        else:

            eleve_selection = st.selectbox(
                "Élève",
                eleves,
                format_func=lambda x: x[1]
            )

            id_eleve = eleve_selection[0]

            ligne = recuperer_eleve(
                id_eleve
            )

            if ligne is None:

                st.error(
                    "Élève introuvable."
                )

                st.stop()

            prenom = st.text_input(
                "Prénom",
                value=str(
                    ligne.get(
                        "prenom",
                        ""
                    )
                )
            )

            nom = st.text_input(
                "Nom",
                value=str(
                    ligne.get(
                        "nom",
                        ""
                    ) or ""
                )
            )

            classe_actuelle = str(
                ligne.get(
                    "classe_actuelle",
                    ""
                ) or ""
            )

            if classe_actuelle in NIVEAUX:

                index_niveau = NIVEAUX.index(
                    classe_actuelle
                )

            else:

                index_niveau = NIVEAUX.index(
                    "Autre"
                )

            niveau_choix = st.selectbox(
                "Niveau / Classe",
                NIVEAUX,
                index=index_niveau
            )

            if niveau_choix == "Autre":

                classe = st.text_input(
                    "Niveau / classe",
                    value=(
                        classe_actuelle
                        if classe_actuelle not in NIVEAUX
                        else ""
                    )
                )

            else:

                classe = niveau_choix

            type_tarification = st.selectbox(
                "Type de tarification",
                [
                    "Tarif horaire",
                    "Forfait mensuel"
                ],
                index=(
                    1
                    if ligne.get(
                        "type_tarification"
                    )
                    == "Forfait mensuel"
                    else 0
                )
            )

            tarif_horaire = st.number_input(
                "Tarif horaire (€)",
                min_value=0.0,
                value=float(
                    ligne.get(
                        "tarif_horaire",
                        0
                    ) or 0
                ),
                step=1.0
            )

            forfait_mensuel = st.number_input(
                "Forfait mensuel (€)",
                min_value=0.0,
                value=float(
                    ligne.get(
                        "forfait_mensuel",
                        0
                    ) or 0
                ),
                step=1.0
            )

            contrat_actuel = str(
                ligne.get(
                    "contrat",
                    ""
                ) or ""
            )

            contrat = st.selectbox(
                "Contrat / modalités",
                CONTRATS,
                index=(
                    CONTRATS.index(
                        contrat_actuel
                    )
                    if contrat_actuel in CONTRATS
                    else 0
                )
            )

            contrat_precisions = st.text_area(
                "Précisions contrat",
                value=(
                    ""
                    if contrat_actuel in CONTRATS
                    else contrat_actuel
                )
            )

            if st.button(
                "💾 Enregistrer les modifications",
                type="primary"
            ):

                if not prenom.strip():

                    st.error(
                        "Le prénom est obligatoire."
                    )

                elif not classe.strip():

                    st.error(
                        "Le niveau / classe est obligatoire."
                    )

                else:

                    if contrat == "Autre":

                        contrat_final = (
                            contrat_precisions.strip()
                        )

                    elif contrat_precisions.strip():

                        contrat_final = (
                            contrat
                            + " — "
                            + contrat_precisions.strip()
                        )

                    else:

                        contrat_final = contrat

                    modifications = {
                        "prenom":
                            prenom.strip(),
                        "nom":
                            nom.strip() or None,
                        "classe_actuelle":
                            classe.strip(),
                        "type_tarification":
                            type_tarification,
                        "tarif_horaire":
                            tarif_horaire,
                        "forfait_mensuel":
                            forfait_mensuel,
                        "contrat":
                            contrat_final
                    }

                    try:

                        # IMPORTANT :
                        # On ne touche PAS à la table seances.
                        # Les séances sont liées par eleve_id.

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
                            "✅ Élève modifié."
                        )

                        st.info(
                            "Les séances existantes sont conservées "
                            "car elles sont liées à l'identifiant "
                            "de l'élève."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur modification."
                        )

                        st.code(str(e))

    # ========================================================
    # SUPPRESSION ÉLÈVE
    # ========================================================

    else:

        st.subheader(
            "🗑️ Supprimer un élève"
        )

        eleves = liste_eleves_avec_id()

        if not eleves:

            st.info(
                "Aucun élève."
            )

        else:

            eleve_selection = st.selectbox(
                "Élève",
                eleves,
                format_func=lambda x: x[1]
            )

            id_eleve = eleve_selection[0]

            st.warning(
                "⚠️ La suppression de l'élève "
                "ne doit être effectuée que si elle est voulue. "
                "Les séances associées ne seront pas supprimées "
                "automatiquement par cette application."
            )

            confirmation = st.checkbox(
                "Je confirme vouloir supprimer cet élève."
            )

            if st.button(
                "🗑️ Supprimer définitivement",
                type="primary"
            ):

                if not confirmation:

                    st.error(
                        "Confirme d'abord la suppression."
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
                            "✅ Élève supprimé."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur suppression."
                        )

                        st.code(str(e))
