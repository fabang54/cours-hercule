import streamlit as st
import pandas as pd
import io

from supabase import create_client
from datetime import date, time
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
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

    st.info(
        "🔒 Espace réservé à l'enseignant."
    )

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
    "Faire une fiche de révision",
    "Revoir les notions difficiles",
    "Préparer le prochain cours",
    "Aucun"
]


# ============================================================
# OBSERVATIONS
# ============================================================

OBSERVATIONS = [

    # --------------------------------------------------------
    # ATTITUDE ET PARTICIPATION
    # --------------------------------------------------------

    "Élève attentif",
    "Élève très attentif",
    "Bonne participation",
    "Très bonne participation",
    "Participation active",
    "Participation satisfaisante",
    "Élève motivé",
    "Élève très motivé",
    "Élève volontaire",
    "Bonne attitude",
    "Très bonne attitude",
    "Élève sérieux",
    "Élève très sérieux",
    "Bonne implication",
    "Très bonne implication",
    "Travail régulier",

    # --------------------------------------------------------
    # CONCENTRATION
    # --------------------------------------------------------

    "Élève distrait",
    "Manque de concentration",
    "Concentration satisfaisante",
    "Bonne concentration",
    "Difficultés à rester concentré",
    "Quelques moments de distraction",

    # --------------------------------------------------------
    # FATIGUE
    # --------------------------------------------------------

    "Élève fatigué",
    "Élève très fatigué",
    "Manque d'énergie",
    "Baisse d'attention liée à la fatigue",

    # --------------------------------------------------------
    # COMPRÉHENSION
    # --------------------------------------------------------

    "Bonne compréhension",
    "Très bonne compréhension",
    "Compréhension satisfaisante",
    "Difficultés de compréhension",
    "Difficultés importantes",
    "Notion à revoir",
    "Notions à consolider",
    "Besoin d'explications supplémentaires",
    "Besoin d'un accompagnement renforcé",

    # --------------------------------------------------------
    # MÉTHODE ET ORGANISATION
    # --------------------------------------------------------

    "Bonne méthode de travail",
    "Méthode de travail à améliorer",
    "Manque de méthode",
    "Difficultés d'organisation",
    "Travail à structurer",
    "Doit gagner en autonomie",
    "Autonomie satisfaisante",
    "Bonne autonomie",
    "Très bonne autonomie",

    # --------------------------------------------------------
    # CALCUL ET RAISONNEMENT
    # --------------------------------------------------------

    "Calculs maîtrisés",
    "Erreurs de calcul",
    "Erreurs d'inattention",
    "Difficultés en calcul",
    "Raisonnement satisfaisant",
    "Bon raisonnement",
    "Très bon raisonnement",
    "Difficultés de raisonnement",
    "Démarche à améliorer",
    "Bonne démarche de résolution",

    # --------------------------------------------------------
    # MÉMORISATION
    # --------------------------------------------------------

    "Cours bien mémorisé",
    "Mémorisation satisfaisante",
    "Difficultés de mémorisation",
    "Notions insuffisamment mémorisées",
    "Révisions nécessaires",

    # --------------------------------------------------------
    # TRAVAIL PERSONNEL
    # --------------------------------------------------------

    "Travail personnel satisfaisant",
    "Travail personnel insuffisant",
    "Travail personnel régulier",
    "Travail personnel à renforcer",
    "Exercices correctement réalisés",
    "Exercices partiellement réalisés",
    "Travail demandé non réalisé",

    # --------------------------------------------------------
    # PROGRESSION
    # --------------------------------------------------------

    "Progrès constatés",
    "Progrès importants",
    "Progrès réguliers",
    "Bonne progression",
    "Très bonne progression",
    "Notions en cours d'acquisition",
    "Acquisitions satisfaisantes",
    "Maîtrise en cours",
    "Des efforts restent nécessaires",

    # --------------------------------------------------------
    # QUALITÉ DE LA SÉANCE
    # --------------------------------------------------------

    "Très bonne séance",
    "Bonne séance",
    "Séance satisfaisante",
    "Séance productive",
    "Séance très productive",
    "Séance difficile",
    "Séance à consolider",

    # --------------------------------------------------------
    # RECOMMANDATIONS
    # --------------------------------------------------------

    "Difficultés persistantes",
    "Difficultés ponctuelles",
    "Attention à maintenir les efforts",
    "Travail régulier recommandé",
    "Davantage d'entraînement recommandé",
    "Révisions recommandées",
    "Consolidation nécessaire",

    # --------------------------------------------------------
    # PERSONNALISATION
    # --------------------------------------------------------

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
# ANALYSE DES OBSERVATIONS
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
                observation.lower()
                in texte.lower()
        ).sum()

        if nombre > 0:

            bilan[observation] = int(nombre)

    return bilan


# ============================================================
# OBSERVATION AUTOMATIQUE
# ============================================================

def generer_observation_automatique(df_eleve):

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

    def nb(texte):

        return bilan.get(
            texte,
            0
        )

    # ========================================================
    # ATTENTION
    # ========================================================

    attention = (
        nb("Élève attentif")
        + nb("Élève très attentif")
        + nb("Bonne concentration")
        + nb("Concentration satisfaisante")
    )

    distraction = (
        nb("Élève distrait")
        + nb("Manque de concentration")
        + nb("Difficultés à rester concentré")
        + nb("Quelques moments de distraction")
    )

    if attention >= nombre_seances * 0.75:

        phrases.append(
            "L'élève s'est montré attentif "
            "et concentré sur la majorité des séances."
        )

    elif attention >= nombre_seances * 0.5:

        phrases.append(
            "L'attention et la concentration "
            "sont globalement satisfaisantes."
        )

    if distraction >= nombre_seances * 0.5:

        phrases.append(
            "Des difficultés de concentration "
            "ont été observées régulièrement."
        )

    elif distraction > 0:

        phrases.append(
            "Quelques moments de distraction "
            "ont été observés."
        )

    # ========================================================
    # PARTICIPATION / MOTIVATION
    # ========================================================

    participation = (
        nb("Bonne participation")
        + nb("Très bonne participation")
        + nb("Participation active")
        + nb("Participation satisfaisante")
    )

    motivation = (
        nb("Élève motivé")
        + nb("Élève très motivé")
        + nb("Élève volontaire")
    )

    implication = (
        nb("Bonne implication")
        + nb("Très bonne implication")
    )

    if participation >= nombre_seances * 0.5:

        phrases.append(
            "La participation de l'élève "
            "est globalement satisfaisante."
        )

    if motivation >= nombre_seances * 0.5:

        phrases.append(
            "L'élève fait preuve d'une bonne motivation."
        )

    if implication >= nombre_seances * 0.5:

        phrases.append(
            "L'implication dans le travail "
            "est très encourageante."
        )

    # ========================================================
    # FATIGUE
    # ========================================================

    fatigue = (
        nb("Élève fatigué")
        + nb("Élève très fatigué")
        + nb("Manque d'énergie")
        + nb("Baisse d'attention liée à la fatigue")
    )

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

    # ========================================================
    # COMPRÉHENSION
    # ========================================================

    bonne_comprehension = (
        nb("Bonne compréhension")
        + nb("Très bonne compréhension")
        + nb("Compréhension satisfaisante")
    )

    difficultes_comprehension = (
        nb("Difficultés de compréhension")
        + nb("Difficultés importantes")
        + nb("Notion à revoir")
        + nb("Notions à consolider")
        + nb("Besoin d'explications supplémentaires")
        + nb("Besoin d'un accompagnement renforcé")
    )

    if bonne_comprehension >= nombre_seances * 0.5:

        phrases.append(
            "La compréhension des notions étudiées "
            "est globalement satisfaisante."
        )

    if difficultes_comprehension >= nombre_seances * 0.5:

        phrases.append(
            "Certaines notions nécessitent encore "
            "des explications et des consolidations."
        )

    elif difficultes_comprehension > 0:

        phrases.append(
            "Quelques notions restent à consolider."
        )

    # ========================================================
    # CALCUL
    # ========================================================

    erreurs_calcul = (
        nb("Erreurs de calcul")
        + nb("Difficultés en calcul")
        + nb("Erreurs d'inattention")
    )

    if erreurs_calcul >= nombre_seances * 0.5:

        phrases.append(
            "Une attention particulière doit être "
            "portée à la précision des calculs."
        )

    elif erreurs_calcul > 0:

        phrases.append(
            "Quelques erreurs de calcul ou "
            "d'inattention ont été relevées."
        )

    # ========================================================
    # RAISONNEMENT
    # ========================================================

    bon_raisonnement = (
        nb("Bon raisonnement")
        + nb("Très bon raisonnement")
        + nb("Bonne démarche de résolution")
        + nb("Raisonnement satisfaisant")
    )

    difficultes_raisonnement = (
        nb("Difficultés de raisonnement")
        + nb("Démarche à améliorer")
    )

    if bon_raisonnement >= nombre_seances * 0.5:

        phrases.append(
            "Le raisonnement et la démarche "
            "de résolution sont satisfaisants."
        )

    if difficultes_raisonnement > 0:

        phrases.append(
            "La démarche de résolution "
            "doit encore être consolidée."
        )

    # ========================================================
    # MÉTHODE / AUTONOMIE
    # ========================================================

    bonne_methode = (
        nb("Bonne méthode de travail")
        + nb("Bonne autonomie")
        + nb("Très bonne autonomie")
        + nb("Autonomie satisfaisante")
    )

    methode_difficile = (
        nb("Méthode de travail à améliorer")
        + nb("Manque de méthode")
        + nb("Difficultés d'organisation")
        + nb("Travail à structurer")
        + nb("Doit gagner en autonomie")
    )

    if bonne_methode >= nombre_seances * 0.5:

        phrases.append(
            "La méthode de travail et l'autonomie "
            "sont satisfaisantes."
        )

    if methode_difficile > 0:

        phrases.append(
            "La méthode de travail et l'organisation "
            "peuvent encore être améliorées."
        )

    # ========================================================
    # MÉMORISATION
    # ========================================================

    memorisation_positive = (
        nb("Cours bien mémorisé")
        + nb("Mémorisation satisfaisante")
    )

    memorisation_difficile = (
        nb("Difficultés de mémorisation")
        + nb("Notions insuffisamment mémorisées")
        + nb("Révisions nécessaires")
    )

    if memorisation_positive >= nombre_seances * 0.5:

        phrases.append(
            "Les notions étudiées sont correctement mémorisées."
        )

    if memorisation_difficile > 0:

        phrases.append(
            "Des révisions régulières sont nécessaires "
            "pour consolider les acquis."
        )

    # ========================================================
    # TRAVAIL PERSONNEL
    # ========================================================

    travail_positif = (
        nb("Travail personnel satisfaisant")
        + nb("Travail personnel régulier")
        + nb("Exercices correctement réalisés")
    )

    travail_insuffisant = (
        nb("Travail personnel insuffisant")
        + nb("Travail personnel à renforcer")
        + nb("Exercices partiellement réalisés")
        + nb("Travail demandé non réalisé")
    )

    if travail_positif >= nombre_seances * 0.5:

        phrases.append(
            "Le travail personnel est régulier "
            "et satisfaisant."
        )

    if travail_insuffisant > 0:

        phrases.append(
            "Le travail personnel doit être "
            "davantage régulier et approfondi."
        )

    # ========================================================
    # PROGRÈS
    # ========================================================

    progres = (
        nb("Progrès constatés")
        + nb("Progrès importants")
        + nb("Progrès réguliers")
        + nb("Bonne progression")
        + nb("Très bonne progression")
        + nb("Acquisitions satisfaisantes")
    )

    if progres >= nombre_seances * 0.5:

        phrases.append(
            "Des progrès réguliers sont constatés "
            "au cours de la période."
        )

    elif progres > 0:

        phrases.append(
            "Des progrès commencent à apparaître."
        )

    # ========================================================
    # TRÈS BONNE SÉANCE
    # ========================================================

    tres_bonne = (
        nb("Très bonne séance")
        + nb("Séance très productive")
    )

    if tres_bonne >= nombre_seances * 0.5:

        phrases.append(
            "Les séances sont très productives "
            "et l'implication de l'élève est encourageante."
        )

    # ========================================================
    # DIFFICULTÉS PERSISTANTES
    # ========================================================

    persistantes = (
        nb("Difficultés persistantes")
        + nb("Difficultés importantes")
    )

    if persistantes > 0:

        phrases.append(
            "Certaines difficultés nécessitent "
            "encore un accompagnement régulier."
        )

    # ========================================================
    # PAR DÉFAUT
    # ========================================================

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

    df_eleve = df_eleve.copy()

    df_eleve["duree_minutes"] = pd.to_numeric(
        df_eleve["duree_minutes"],
        errors="coerce"
    ).fillna(0)

    total_minutes = (
        df_eleve["duree_minutes"].sum()
    )

    total_heures = total_minutes / 60

    montant = total_heures * tarif

    nombre_seances = len(df_eleve)

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

    elements.append(table_infos)

    elements.append(
        Spacer(1, 8)
    )

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

    elements.append(
        Spacer(1, 7)
    )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

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

    elements.append(total_table)

    elements.append(
        Spacer(1, 8)
    )

    # --------------------------------------------------------
    # BILAN
    # --------------------------------------------------------

    bilan = analyser_observations(
        df_eleve
    )

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

        elements.append(
            Spacer(1, 6)
        )

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

    elements.append(
        Spacer(1, 8)
    )

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

    elements.append(
        Spacer(1, 8)
    )

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
            "Ajoute d'abord un élève dans l'onglet 👨‍🎓 Élèves."
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

        # ====================================================
        # TRAVAIL À FAIRE
        # ====================================================

        st.markdown("### 📚 Travail à faire")

        travail_selection = st.multiselect(
            "Sélectionner une ou plusieurs propositions",
            TRAVAUX,
            key="nouvelle_travail_selection"
        )

        travail_manuel = st.text_area(
            "✏️ Travail supplémentaire",
            placeholder=(
                "Exemple : exercices 12, 13 et 15 page 48"
            ),
            key="nouvelle_travail_manuel"
        )

        travail = ", ".join(
            travail_selection
        )

        if travail_manuel.strip():

            if travail:
                travail += " — "

            travail += travail_manuel.strip()

        # ====================================================
        # OBSERVATIONS
        # ====================================================

        st.markdown("### 📝 Observations")

        observations = st.multiselect(
            "Sélectionner une ou plusieurs observations",
            OBSERVATIONS,
            default=["Élève attentif"],
            key="nouvelle_observations"
        )

        observation_manuel = st.text_area(
            "✏️ Observation supplémentaire",
            placeholder=(
                "Vous pouvez saisir ici une observation "
                "personnalisée..."
            ),
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
    # MODIFICATION D'UNE SÉANCE
    # ========================================================

    elif action == "✏️ Modifier une séance":

        st.subheader(
            "✏️ Modifier une séance"
        )

        df = recuperer_seances()

        if df.empty:

            st.info(
                "Aucune séance enregistrée."
            )

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
                    if ligne["mode"] == "Présentiel"
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

    st.header(
        "📖 Cahier de texte"
    )

    df = recuperer_seances()

    if df.empty:

        st.info(
            "Aucune séance."
        )

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

    st.header(
        "📊 Bilan"
    )

    df = recuperer_seances()

    if df.empty:

        st.info(
            "Aucune séance."
        )

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

            st.subheader(
                "📊 Observations"
            )

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

        type_periode = st.selectbox(
            "Période de facturation",
            [
                "Mensuelle",
                "Personnalisée"
            ],
            index=0,
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

        tarif = st.number_input(
            "Tarif horaire (€)",
            min_value=0.0,
            value=30.0,
            step=1.0,
            key="facture_tarif"
        )

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

            montant = (
                total_heures * tarif
            )

            nombre_seances = len(
                df_eleve
            )

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
                tableau["duree_minutes"] / 60
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

            st.subheader(
                "💶 Résumé financier"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    f"**Nombre de séances :** "
                    f"{nombre_seances}"
                )

            with col2:

                st.write(
                    f"**Total d'heures :** "
                    f"{total_heures:.2f} h"
                )

            with col3:

                st.write(
                    f"**Montant :** "
                    f"{montant:.2f} €"
                )

            st.caption(
                f"Tarif appliqué : {tarif:.2f} € / h"
            )

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

                    st.code(
                        str(e)
                    )

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

                st.info(
                    "Le PDF contient le détail des séances, "
                    "le total des heures, le tarif horaire, "
                    "le montant total, le bilan pédagogique "
                    "et l'observation automatique."
                )


# ============================================================
# GESTION DES ÉLÈVES
# ============================================================

elif menu == "👨‍🎓 Élèves":

    st.header(
        "👨‍🎓 Gestion des élèves"
    )

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
    # AJOUTER
    # ========================================================

    if action_eleve == "➕ Ajouter un élève":

        st.subheader(
            "➕ Ajouter un élève"
        )

        prenom = st.text_input(
            "Prénom *",
            key="eleve_nouveau_prenom"
        )

        nom = st.text_input(
            "Nom",
            key="eleve_nouveau_nom"
        )

        classe = st.text_input(
            "Classe actuelle",
            key="eleve_nouvelle_classe"
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

                    "prenom": prenom,

                    "nom":
                        nom if nom else None,

                    "classe_actuelle":
                        classe if classe else None
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

                    st.code(
                        str(e)
                    )

    # ========================================================
    # MODIFIER
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

                if nom:
                    affichage = f"{prenom} {nom}"
                else:
                    affichage = prenom

                choix_eleves.append(
                    (
                        ligne["id"],
                        affichage
                    )
                )

            choix = st.selectbox(
                "Élève à modifier",
                choix_eleves,
                format_func=lambda x: x[1]
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

            nom_modifie = st.text_input(
                "Nom",
                value=str(
                    ligne.get(
                        "nom",
                        ""
                    )
                )
                if pd.notna(
                    ligne.get("nom")
                )
                else "",
                key="eleve_mod_nom"
            )

            classe_modifiee = st.text_input(
                "Classe actuelle",
                value=str(
                    ligne.get(
                        "classe_actuelle",
                        ""
                    )
                )
                if pd.notna(
                    ligne.get(
                        "classe_actuelle"
                    )
                )
                else "",
                key="eleve_mod_classe"
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
                            else None
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
                            "✅ Élève modifié."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur lors de la modification."
                        )

                        st.code(
                            str(e)
                        )

    # ========================================================
    # SUPPRIMER
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

                if nom:
                    affichage = f"{prenom} {nom}"
                else:
                    affichage = prenom

                choix_eleves.append(
                    (
                        ligne["id"],
                        affichage
                    )
                )

            choix = st.selectbox(
                "Élève à supprimer",
                choix_eleves,
                format_func=lambda x: x[1]
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
                "Je confirme vouloir supprimer cet élève."
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

                        st.code(
                            str(e)
                        )
