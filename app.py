import streamlit as st
import pandas as pd

from supabase import create_client
from datetime import date, time, timedelta
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
    "Élève très attentif",
    "Élève fatigué",
    "Élève distrait",
    "Élève peu concentré",
    "Difficultés de compréhension",
    "Difficultés importantes",
    "Bonne compréhension",
    "Bonne participation",
    "Participation satisfaisante",
    "Très bonne séance",
    "Progrès constatés",
    "Travail sérieux",
    "Manque de travail",
    "Bonne autonomie",
    "Doit encore gagner en autonomie",
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
            .order("nom")
            .execute()
        )

        donnees = resultat.data

        if not donnees:
            return pd.DataFrame()

        return pd.DataFrame(donnees)

    except Exception:

        return pd.DataFrame()


# ============================================================
# LISTE DES NOMS D'ÉLÈVES
# ============================================================

def liste_eleves():

    df_eleves = recuperer_eleves()

    if df_eleves.empty:
        return []

    if "nom" not in df_eleves.columns:
        return []

    return sorted(
        df_eleves["nom"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


# ============================================================
# RÉCUPÉRER LA CLASSE D'UN ÉLÈVE
# ============================================================

def recuperer_classe_eleve(nom):

    df_eleves = recuperer_eleves()

    if df_eleves.empty:
        return ""

    lignes = df_eleves[
        df_eleves["nom"].astype(str) == str(nom)
    ]

    if lignes.empty:
        return ""

    if "classe_actuelle" not in lignes.columns:
        return ""

    valeur = lignes.iloc[0]["classe_actuelle"]

    if pd.isna(valeur):
        return ""

    return str(valeur)


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
# GÉNÉRER BILAN AUTOMATIQUE
# ============================================================

def generer_bilan(
    df_eleve
):

    if df_eleve.empty:

        return (
            {},
            "Aucune séance sur la période."
        )

    total_seances = len(df_eleve)

    compteurs = {}

    for valeur in df_eleve[
        "observations"
    ].fillna(""):

        texte = str(valeur)

        if not texte.strip():
            continue

        morceaux = [
            x.strip()
            for x in texte.split(",")
            if x.strip()
        ]

        for observation in morceaux:

            compteurs[observation] = (
                compteurs.get(
                    observation,
                    0
                ) + 1
            )

    phrases = []

    # --------------------------------------------------------
    # ATTENTION
    # --------------------------------------------------------

    attention = (
        compteurs.get(
            "Élève attentif",
            0
        )
        +
        compteurs.get(
            "Élève très attentif",
            0
        )
    )

    if attention >= total_seances * 0.875:

        phrases.append(
            "L'élève fait preuve d'une très bonne "
            "attention tout au long des séances."
        )

    elif attention >= total_seances * 0.5:

        phrases.append(
            "L'élève fait preuve d'une bonne attention "
            "lors des séances."
        )

    elif attention > 0:

        phrases.append(
            "L'attention est globalement satisfaisante, "
            "mais peut encore être renforcée."
        )

    # --------------------------------------------------------
    # PARTICIPATION
    # --------------------------------------------------------

    participation = (
        compteurs.get(
            "Bonne participation",
            0
        )
        +
        compteurs.get(
            "Participation satisfaisante",
            0
        )
    )

    if participation >= total_seances * 0.875:

        phrases.append(
            "La participation est très active "
            "et régulière."
        )

    elif participation >= total_seances * 0.5:

        phrases.append(
            "L'élève participe de manière satisfaisante "
            "aux séances."
        )

    # --------------------------------------------------------
    # COMPRÉHENSION
    # --------------------------------------------------------

    comprehension = compteurs.get(
        "Bonne compréhension",
        0
    )

    difficultes = (
        compteurs.get(
            "Difficultés de compréhension",
            0
        )
        +
        compteurs.get(
            "Difficultés importantes",
            0
        )
    )

    if comprehension >= total_seances * 0.5:

        phrases.append(
            "Les notions étudiées sont globalement "
            "bien comprises."
        )

    elif difficultes >= total_seances * 0.5:

        phrases.append(
            "Certaines notions nécessitent encore "
            "un travail de consolidation."
        )

    elif difficultes > 0:

        phrases.append(
            "Quelques difficultés de compréhension "
            "persistent sur certaines notions."
        )

    # --------------------------------------------------------
    # PROGRÈS
    # --------------------------------------------------------

    progres = compteurs.get(
        "Progrès constatés",
        0
    )

    if progres >= total_seances * 0.75:

        phrases.append(
            "Une progression très régulière est "
            "constatée sur la période."
        )

    elif progres >= total_seances * 0.5:

        phrases.append(
            "Des progrès réguliers sont constatés "
            "sur la période."
        )

    elif progres > 0:

        phrases.append(
            "Des progrès commencent à être constatés "
            "sur la période."
        )

    # --------------------------------------------------------
    # TRAVAIL
    # --------------------------------------------------------

    travail = compteurs.get(
        "Travail sérieux",
        0
    )

    manque_travail = compteurs.get(
        "Manque de travail",
        0
    )

    if travail >= total_seances * 0.5:

        phrases.append(
            "L'élève fait preuve de sérieux et "
            "d'implication dans son travail."
        )

    if manque_travail >= total_seances * 0.5:

        phrases.append(
            "Un travail personnel plus régulier "
            "permettrait de consolider les acquis."
        )

    # --------------------------------------------------------
    # AUTONOMIE
    # --------------------------------------------------------

    autonomie = compteurs.get(
        "Bonne autonomie",
        0
    )

    manque_autonomie = compteurs.get(
        "Doit encore gagner en autonomie",
        0
    )

    if autonomie >= total_seances * 0.5:

        phrases.append(
            "L'élève gagne progressivement "
            "en autonomie."
        )

    if manque_autonomie >= total_seances * 0.5:

        phrases.append(
            "L'autonomie doit encore être développée."
        )

    # --------------------------------------------------------
    # FATIGUE
    # --------------------------------------------------------

    fatigue = compteurs.get(
        "Élève fatigué",
        0
    )

    if fatigue >= total_seances * 0.5:

        phrases.append(
            "Une fatigue assez fréquente a été observée "
            "au cours de la période."
        )

    elif fatigue > 0:

        phrases.append(
            "Quelques signes de fatigue ont été observés "
            "lors de certaines séances."
        )

    # --------------------------------------------------------
    # DISTRACTION
    # --------------------------------------------------------

    distrait = (
        compteurs.get(
            "Élève distrait",
            0
        )
        +
        compteurs.get(
            "Élève peu concentré",
            0
        )
    )

    if distrait >= total_seances * 0.5:

        phrases.append(
            "La concentration reste à renforcer "
            "afin de favoriser les apprentissages."
        )

    # --------------------------------------------------------
    # AUCUNE OBSERVATION
    # --------------------------------------------------------

    if not phrases:

        phrases.append(
            "La période s'est déroulée normalement. "
            "Le travail se poursuit régulièrement."
        )

    bilan = " ".join(
        phrases
    )

    return (
        compteurs,
        bilan
    )


# ============================================================
# GÉNÉRATION FACTURE PDF
# ============================================================

def generer_facture_pdf(
    df_eleve,
    eleve,
    classe,
    tarif_presentiel,
    tarif_distanciel,
    numero_facture,
    periode,
    statut,
    date_paiement,
    bilan
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    titre = ParagraphStyle(
        "TitreFacture",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=17,
        leading=19,
        spaceAfter=8
    )

    normal = ParagraphStyle(
        "NormalFacture",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9
    )

    petit = ParagraphStyle(
        "Petit",
        parent=normal,
        fontSize=6.5,
        leading=7.5
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
        Spacer(1, 6)
    )

    # ========================================================
    # INFORMATIONS
    # ========================================================

    date_facture = date.today().strftime(
        "%d/%m/%Y"
    )

    infos = [
        [
            Paragraph("<b>Élève</b>", normal),
            Paragraph(str(eleve), normal),
            Paragraph("<b>Classe</b>", normal),
            Paragraph(str(classe), normal)
        ],
        [
            Paragraph("<b>Date facture</b>", normal),
            Paragraph(date_facture, normal),
            Paragraph("<b>Période</b>", normal),
            Paragraph(periode, normal)
        ]
    ]

    table_infos = Table(
        infos,
        colWidths=[
            70,
            175,
            60,
            220
        ]
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
                "BACKGROUND",
                (2, 0),
                (2, -1),
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
                3
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3
            )
        ])
    )

    elements.append(
        table_infos
    )

    elements.append(
        Spacer(1, 7)
    )

    # ========================================================
    # TABLE DES SÉANCES
    # ========================================================

    donnees_table = [
        [
            Paragraph("<b>Date</b>", petit),
            Paragraph("<b>Horaire</b>", petit),
            Paragraph("<b>Mode</b>", petit),
            Paragraph("<b>Discipline</b>", petit),
            Paragraph("<b>Durée</b>", petit),
            Paragraph("<b>Tarif</b>", petit),
            Paragraph("<b>Montant</b>", petit)
        ]
    ]

    total_minutes = 0
    total_presentiel = 0
    total_distanciel = 0
    montant_total = 0

    for _, ligne in df_eleve.iterrows():

        duree = pd.to_numeric(
            ligne.get(
                "duree_minutes"
            ),
            errors="coerce"
        )

        if pd.isna(duree):
            duree = 0

        duree = float(duree)

        total_minutes += duree

        mode = str(
            ligne.get(
                "mode",
                "Présentiel"
            )
        )

        if mode == "Distanciel":

            tarif_ligne = tarif_distanciel

            total_distanciel += duree

        else:

            tarif_ligne = tarif_presentiel

            total_presentiel += duree

        heures = duree / 60

        montant_ligne = (
            heures * tarif_ligne
        )

        montant_total += montant_ligne

        try:

            date_ligne = pd.to_datetime(
                ligne.get("date")
            ).strftime("%d/%m/%Y")

        except Exception:

            date_ligne = str(
                ligne.get("date", "")
            )

        heure_debut = str(
            ligne.get(
                "heure_debut",
                ""
            )
        )[:5]

        heure_fin = str(
            ligne.get(
                "heure_fin",
                ""
            )
        )[:5]

        discipline = str(
            ligne.get(
                "disciplines",
                ""
            )
        )

        donnees_table.append(
            [
                Paragraph(
                    date_ligne,
                    petit
                ),
                Paragraph(
                    f"{heure_debut} - {heure_fin}",
                    petit
                ),
                Paragraph(
                    mode,
                    petit
                ),
                Paragraph(
                    discipline,
                    petit
                ),
                Paragraph(
                    f"{heures:.2f} h",
                    petit
                ),
                Paragraph(
                    f"{tarif_ligne:.2f} €",
                    petit
                ),
                Paragraph(
                    f"{montant_ligne:.2f} €",
                    petit
                )
            ]
        )

    table_seances = Table(
        donnees_table,
        colWidths=[
            55,
            75,
            70,
            150,
            50,
            55,
            65
        ],
        repeatRows=1
    )

    table_seances.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "ALIGN",
                (4, 1),
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
        Spacer(1, 6)
    )

    # ========================================================
    # RÉCAPITULATIF
    # ========================================================

    heures_presentiel = (
        total_presentiel / 60
    )

    heures_distanciel = (
        total_distanciel / 60
    )

    recap = [
        [
            Paragraph(
                "<b>Présentiel</b>",
                normal
            ),
            Paragraph(
                f"{heures_presentiel:.2f} h × "
                f"{tarif_presentiel:.2f} € = "
                f"{heures_presentiel * tarif_presentiel:.2f} €",
                droite
            )
        ],
        [
            Paragraph(
                "<b>Distanciel</b>",
                normal
            ),
            Paragraph(
                f"{heures_distanciel:.2f} h × "
                f"{tarif_distanciel:.2f} € = "
                f"{heures_distanciel * tarif_distanciel:.2f} €",
                droite
            )
        ],
        [
            Paragraph(
                "<b>TOTAL</b>",
                normal
            ),
            Paragraph(
                f"<b>{montant_total:.2f} €</b>",
                droite
            )
        ]
    ]

    table_recap = Table(
        recap,
        colWidths=[
            160,
            360
        ]
    )

    table_recap.setStyle(
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
                3
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3
            )
        ])
    )

    elements.append(
        table_recap
    )

    elements.append(
        Spacer(1, 6)
    )

    # ========================================================
    # OBSERVATION / BILAN
    # ========================================================

    elements.append(
        Paragraph(
            "<b>Observation concernant l'élève</b>",
            normal
        )
    )

    elements.append(
        Spacer(1, 3)
    )

    elements.append(
        Paragraph(
            bilan.replace(
                "\n",
                "<br/>"
            ),
            petit
        )
    )

    elements.append(
        Spacer(1, 6)
    )

    # ========================================================
    # PAIEMENT
    # ========================================================

    if statut == "Payée":

        date_paiement_pdf = (
            date_paiement.strftime(
                "%d/%m/%Y"
            )
            if date_paiement
            else ""
        )

        paiement_texte = (
            f"<b>Statut :</b> PAYÉE — "
            f"<b>Date de paiement :</b> "
            f"{date_paiement_pdf}"
        )

    else:

        paiement_texte = (
            "<b>Statut :</b> EN ATTENTE DE PAIEMENT"
        )

    elements.append(
        Paragraph(
            paiement_texte,
            normal
        )
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
        "👨‍🎓 Élèves",
        "📚 Gestion des séances",
        "📖 Cahier de texte",
        "📊 Bilan",
        "🧾 Facturation"
    ]
)


# ============================================================
# ÉLÈVES
# ============================================================

if menu == "👨‍🎓 Élèves":

    st.header("👨‍🎓 Gestion des élèves")

    st.subheader(
        "➕ Ajouter un élève"
    )

    nouveau_nom = st.text_input(
        "Nom et prénom",
        placeholder="Ex. Paul Dupont"
    )

    nouvelle_classe = st.text_input(
        "Classe actuelle",
        placeholder="Ex. 4ème"
    )

    if st.button(
        "➕ Ajouter l'élève",
        type="primary"
    ):

        if not nouveau_nom.strip():

            st.error(
                "Veuillez indiquer le nom de l'élève."
            )

        else:

            try:

                (
                    supabase
                    .table("eleves")
                    .insert(
                        {
                            "nom":
                                nouveau_nom.strip(),
                            "classe_actuelle":
                                nouvelle_classe.strip()
                        }
                    )
                    .execute()
                )

                st.success(
                    f"✅ {nouveau_nom} a été ajouté."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "❌ Impossible d'ajouter l'élève."
                )

                st.code(str(e))

    st.divider()

    st.subheader(
        "👨‍🎓 Élèves enregistrés"
    )

    df_eleves = recuperer_eleves()

    if df_eleves.empty:

        st.info(
            "Aucun élève enregistré."
        )

    else:

        colonnes = [
            c
            for c in [
                "nom",
                "classe_actuelle"
            ]
            if c in df_eleves.columns
        ]

        st.dataframe(
            df_eleves[colonnes],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader(
            "✏️ Modifier la classe actuelle"
        )

        noms = sorted(
            df_eleves["nom"]
            .dropna()
            .astype(str)
            .tolist()
        )

        eleve_modification = st.selectbox(
            "Élève",
            noms
        )

        classe_actuelle = recuperer_classe_eleve(
            eleve_modification
        )

        nouvelle_classe_modifiee = st.text_input(
            "Nouvelle classe actuelle",
            value=classe_actuelle
        )

        if st.button(
            "💾 Enregistrer la nouvelle classe"
        ):

            try:

                (
                    supabase
                    .table("eleves")
                    .update(
                        {
                            "classe_actuelle":
                                nouvelle_classe_modifiee.strip()
                        }
                    )
                    .eq(
                        "nom",
                        eleve_modification
                    )
                    .execute()
                )

                st.success(
                    "✅ Classe actuelle mise à jour."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "❌ Erreur lors de la modification."
                )

                st.code(str(e))


# ============================================================
# GESTION DES SÉANCES
# ============================================================

elif menu == "📚 Gestion des séances":

    st.header(
        "📚 Gestion des séances"
    )

    eleves = liste_eleves()

    if not eleves:

        st.warning(
            "Aucun élève n'est enregistré. "
            "Ajoutez d'abord un élève dans 👨‍🎓 Élèves."
        )

    else:

        action = st.radio(
            "Action",
            [
                "➕ Nouvelle séance",
                "✏️ Modifier une séance"
            ],
            horizontal=True
        )

        # ====================================================
        # NOUVELLE SÉANCE
        # ====================================================

        if action == "➕ Nouvelle séance":

            st.subheader(
                "➕ Nouvelle séance"
            )

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

                contenu += (
                    contenu_manuel.strip()
                )

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

            st.markdown(
                "**Observations de la séance**"
            )

            st.caption(
                "Vous pouvez sélectionner plusieurs observations "
                "pour une même séance."
            )

            observations = st.multiselect(
                "Observations",
                OBSERVATIONS,
                key="nouvelle_observations"
            )

            observation_manuel = st.text_area(
                "Observation supplémentaire",
                key="nouvelle_observation_manuel"
            )

            observations_finales = ", ".join(
                observations
            )

            if observation_manuel.strip():

                if observations_finales:
                    observations_finales += ", "

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

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur lors de l'enregistrement."
                        )

                        st.code(str(e))

        # ====================================================
        # MODIFICATION
        # ====================================================

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

                        st.error(
                            "L'heure de fin doit être "
                            "postérieure à l'heure de début."
                        )

                    else:

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

    eleves = liste_eleves()

    if df.empty or not eleves:

        st.info(
            "Aucune séance."
        )

    else:

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
        "📊 Bilan de l'élève"
    )

    df = recuperer_seances()

    eleves = liste_eleves()

    if df.empty or not eleves:

        st.info(
            "Aucune séance."
        )

    else:

        eleve = st.selectbox(
            "Élève",
            eleves,
            key="bilan_eleve"
        )

        df_eleve = df[
            df["eleve"] == eleve
        ].copy()

        if df_eleve.empty:

            st.info(
                "Aucune séance pour cet élève."
            )

        else:

            compteurs, bilan = generer_bilan(
                df_eleve
            )

            total_seances = len(
                df_eleve
            )

            st.metric(
                "Nombre de séances",
                total_seances
            )

            st.subheader(
                "📊 Observations"
            )

            if compteurs:

                for observation, nombre in (
                    compteurs.items()
                ):

                    st.write(
                        f"**{observation} :** "
                        f"{nombre} / "
                        f"{total_seances} séances"
                    )

            st.divider()

            st.subheader(
                "📝 Observation générale automatique"
            )

            bilan_modifie = st.text_area(
                "Bilan",
                value=bilan,
                height=180
            )

            st.success(
                "Ce texte pourra être utilisé sur la facture."
            )


# ============================================================
# FACTURATION
# ============================================================

elif menu == "🧾 Facturation":

    st.header(
        "🧾 Facturation"
    )

    df = recuperer_seances()

    eleves = liste_eleves()

    if df.empty or not eleves:

        st.info(
            "Aucune séance disponible."
        )

    else:

        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        eleve = st.selectbox(
            "👨‍🎓 Élève",
            eleves,
            key="facture_eleve"
        )

        classe = recuperer_classe_eleve(
            eleve
        )

        st.info(
            f"🎓 Classe actuelle : "
            f"{classe if classe else 'Non renseignée'}"
        )

        # ----------------------------------------------------
        # TYPE DE PÉRIODE
        # ----------------------------------------------------

        periode_type = st.selectbox(
            "📅 Période de facturation",
            [
                "Mensuelle",
                "Personnalisée"
            ],
            index=0
        )

        if periode_type == "Mensuelle":

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
                date_fin
                - timedelta(days=1)
            )

        else:

            col1, col2 = st.columns(2)

            with col1:

                date_debut = st.date_input(
                    "Date de début",
                    value=date.today().replace(
                        day=1
                    )
                )

            with col2:

                date_fin_inclusive = st.date_input(
                    "Date de fin",
                    value=date.today()
                )

            if date_fin_inclusive < date_debut:

                st.error(
                    "La date de fin doit être "
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
        # TARIFS
        # ----------------------------------------------------

        st.subheader(
            "💶 Tarifs"
        )

        col1, col2 = st.columns(2)

        with col1:

            tarif_presentiel = st.number_input(
                "Tarif horaire présentiel (€)",
                min_value=0.0,
                value=30.0,
                step=1.0
            )

        with col2:

            tarif_distanciel = st.number_input(
                "Tarif horaire distanciel (€)",
                min_value=0.0,
                value=25.0,
                step=1.0
            )

        # ----------------------------------------------------
        # STATUT
        # ----------------------------------------------------

        statut = st.selectbox(
            "Statut du paiement",
            [
                "En attente de paiement",
                "Payée"
            ]
        )

        date_paiement = None

        if statut == "Payée":

            date_paiement = st.date_input(
                "Date de paiement",
                value=date.today()
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

            # ------------------------------------------------
            # DURÉES
            # ------------------------------------------------

            df_eleve[
                "duree_minutes"
            ] = pd.to_numeric(
                df_eleve[
                    "duree_minutes"
                ],
                errors="coerce"
            ).fillna(0)

            total_minutes = (
                df_eleve[
                    "duree_minutes"
                ].sum()
            )

            total_presentiel = 0
            total_distanciel = 0

            montant_presentiel = 0
            montant_distanciel = 0

            for _, ligne in df_eleve.iterrows():

                duree = float(
                    ligne[
                        "duree_minutes"
                    ]
                )

                if str(
                    ligne.get(
                        "mode",
                        "Présentiel"
                    )
                ) == "Distanciel":

                    total_distanciel += duree

                    montant_distanciel += (
                        duree / 60
                    ) * tarif_distanciel

                else:

                    total_presentiel += duree

                    montant_presentiel += (
                        duree / 60
                    ) * tarif_presentiel

            total_heures = (
                total_minutes / 60
            )

            heures_presentiel = (
                total_presentiel / 60
            )

            heures_distanciel = (
                total_distanciel / 60
            )

            montant_total = (
                montant_presentiel
                +
                montant_distanciel
            )

            # ------------------------------------------------
            # BILAN AUTOMATIQUE
            # ------------------------------------------------

            compteurs, bilan_auto = (
                generer_bilan(
                    df_eleve
                )
            )

            # ------------------------------------------------
            # STATISTIQUES
            # ------------------------------------------------

            st.subheader(
                "📊 Récapitulatif"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                st.metric(
                    "Séances",
                    len(df_eleve)
                )

            with c2:

                st.metric(
                    "Présentiel",
                    f"{heures_presentiel:.2f} h"
                )

            with c3:

                st.metric(
                    "Distanciel",
                    f"{heures_distanciel:.2f} h"
                )

            with c4:

                st.metric(
                    "Total",
                    f"{montant_total:.2f} €"
                )

            # ------------------------------------------------
            # OBSERVATIONS
            # ------------------------------------------------

            st.subheader(
                "📊 Observations sur la période"
            )

            if compteurs:

                for observation, nombre in (
                    compteurs.items()
                ):

                    st.write(
                        f"**{observation} :** "
                        f"{nombre} / "
                        f"{len(df_eleve)} séances"
                    )

            # ------------------------------------------------
            # BILAN
            # ------------------------------------------------

            st.subheader(
                "📝 Observation / bilan"
            )

            st.caption(
                "Le texte est généré automatiquement "
                "à partir des observations saisies "
                "pour chaque séance. Vous pouvez le modifier."
            )

            bilan = st.text_area(
                "Texte destiné aux parents",
                value=bilan_auto,
                height=160,
                key="bilan_facture"
            )

            # ------------------------------------------------
            # TABLEAU
            # ------------------------------------------------

            st.subheader(
                "📋 Séances facturées"
            )

            colonnes = [
                "date",
                "heure_debut",
                "heure_fin",
                "mode",
                "disciplines",
                "duree_minutes",
                "observations"
            ]

            colonnes_existantes = [
                c
                for c in colonnes
                if c in df_eleve.columns
            ]

            st.dataframe(
                df_eleve[
                    colonnes_existantes
                ],
                use_container_width=True
            )

            # ------------------------------------------------
            # NUMÉRO FACTURE
            # ------------------------------------------------

            numero_facture = st.text_input(
                "Numéro de facture",
                value=(
                    f"CH-"
                    f"{date_debut.strftime('%Y%m%d')}-"
                    f"{eleve.upper()}"
                )
            )

            # ------------------------------------------------
            # PDF
            # ------------------------------------------------

            if st.button(
                "🧾 Générer la facture PDF",
                type="primary"
            ):

                try:

                    pdf = generer_facture_pdf(
                        df_eleve=df_eleve,
                        eleve=eleve,
                        classe=classe,
                        tarif_presentiel=(
                            tarif_presentiel
                        ),
                        tarif_distanciel=(
                            tarif_distanciel
                        ),
                        numero_facture=(
                            numero_facture
                        ),
                        periode=periode,
                        statut=statut,
                        date_paiement=(
                            date_paiement
                        ),
                        bilan=bilan
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

            # ------------------------------------------------
            # TÉLÉCHARGEMENT
            # ------------------------------------------------

            if "facture_pdf" in st.session_state:

                st.download_button(
                    label=(
                        "📥 Télécharger la facture PDF"
                    ),
                    data=st.session_state[
                        "facture_pdf"
                    ],
                    file_name=st.session_state[
                        "facture_nom"
                    ],
                    mime="application/pdf"
                )
