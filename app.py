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
    "Préparer le prochain cours",
    "Aucun",
    "Autre"
]

OBSERVATIONS = [
    "Élève attentif",
    "Élève fatigué",
    "Élève distrait",
    "Difficulté de compréhension",
    "Difficultés importantes",
    "Bonne participation",
    "Très bonne séance",
    "Progrès constatés",
    "Travail sérieux",
    "Manque de travail",
    "Autre"
]


# ============================================================
# RÉCUPÉRER LES ÉLÈVES
# ============================================================

def recuperer_eleves():

    resultat = (
        supabase
        .table("eleves")
        .select("*")
        .order("prenom")
        .execute()
    )

    donnees = resultat.data

    if not donnees:
        return pd.DataFrame()

    return pd.DataFrame(donnees)


# ============================================================
# NOM COMPLET D'UN ÉLÈVE
# ============================================================

def nom_complet_eleve(ligne):

    prenom = str(
        ligne.get("prenom", "")
    ).strip()

    nom = str(
        ligne.get("nom", "")
    ).strip()

    if nom:
        return f"{prenom} {nom}"

    return prenom


# ============================================================
# LISTE DES ÉLÈVES POUR LES MENUS
# ============================================================

def liste_eleves():

    df = recuperer_eleves()

    if df.empty:
        return []

    resultats = []

    for _, ligne in df.iterrows():

        nom = nom_complet_eleve(ligne)

        classe = str(
            ligne.get("classe_actuelle", "")
        ).strip()

        if classe:
            nom += f" — {classe}"

        resultats.append(nom)

    return resultats


# ============================================================
# RÉCUPÉRER UN ÉLÈVE À PARTIR DE SON AFFICHAGE
# ============================================================

def recuperer_id_eleve(nom_affiche):

    df = recuperer_eleves()

    if df.empty:
        return None

    for _, ligne in df.iterrows():

        nom = nom_complet_eleve(ligne)

        classe = str(
            ligne.get("classe_actuelle", "")
        ).strip()

        affichage = nom

        if classe:
            affichage += f" — {classe}"

        if affichage == nom_affiche:
            return ligne["id"]

    return None


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
# OBSERVATION AUTOMATIQUE
# ============================================================

def generer_observation_automatique(
    df_eleve
):

    if df_eleve.empty:
        return ""

    compteur = {}

    for _, ligne in df_eleve.iterrows():

        observation = str(
            ligne.get(
                "observations",
                ""
            )
        )

        if not observation:
            continue

        for obs in observation.split(","):

            obs = obs.strip()

            if "—" in obs:
                obs = obs.split("—")[0].strip()

            if obs:
                compteur[obs] = (
                    compteur.get(obs, 0) + 1
                )

    if not compteur:
        return (
            "Bonne progression sur la période. "
            "Un travail régulier est recommandé."
        )

    total = len(df_eleve)

    phrases = []

    if compteur.get("Élève attentif", 0):

        n = compteur["Élève attentif"]

        phrases.append(
            f"L'élève a été attentif "
            f"lors de {n} séance(s) sur {total}."
        )

    if compteur.get("Bonne participation", 0):

        n = compteur["Bonne participation"]

        phrases.append(
            f"La participation a été bonne "
            f"lors de {n} séance(s)."
        )

    if compteur.get("Progrès constatés", 0):

        phrases.append(
            "Des progrès ont été constatés "
            "au cours de la période."
        )

    if compteur.get("Difficulté de compréhension", 0):

        phrases.append(
            "Certaines difficultés de compréhension "
            "restent à travailler."
        )

    if compteur.get("Difficultés importantes", 0):

        phrases.append(
            "Des difficultés importantes "
            "ont été relevées."
        )

    if compteur.get("Élève fatigué", 0):

        n = compteur["Élève fatigué"]

        phrases.append(
            f"Une certaine fatigue a été observée "
            f"lors de {n} séance(s)."
        )

    if compteur.get("Élève distrait", 0):

        n = compteur["Élève distrait"]

        phrases.append(
            f"Des moments de distraction ont été "
            f"observés lors de {n} séance(s)."
        )

    if compteur.get("Travail sérieux", 0):

        phrases.append(
            "Le travail fourni est sérieux."
        )

    if compteur.get("Manque de travail", 0):

        phrases.append(
            "Un travail personnel plus régulier "
            "est recommandé."
        )

    if not phrases:

        phrases.append(
            "Bonne progression sur la période."
        )

        phrases.append(
            "Les notions étudiées sont "
            "progressivement maîtrisées."
        )

        phrases.append(
            "Un travail régulier est recommandé."
        )

    return " ".join(phrases)


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
    observation
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    titre = ParagraphStyle(
        "TitreFacture",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=12
    )

    normal = ParagraphStyle(
        "NormalFacture",
        parent=styles["Normal"],
        fontSize=8,
        leading=10
    )

    petite = ParagraphStyle(
        "Petite",
        parent=normal,
        fontSize=7,
        leading=8
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
        Spacer(1, 8)
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
            Paragraph(str(eleve), normal)
        ],
        [
            Paragraph("<b>Classe actuelle</b>", normal),
            Paragraph(str(classe), normal)
        ],
        [
            Paragraph("<b>Date de facture</b>", normal),
            Paragraph(date_facture, normal)
        ],
        [
            Paragraph("<b>Période facturée</b>", normal),
            Paragraph(periode, normal)
        ]
    ]

    table_infos = Table(
        infos,
        colWidths=[130, 410]
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
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
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
            "Durée",
            "Tarif"
        ]
    ]

    total_presentiel = 0
    total_distanciel = 0

    for _, ligne in df_eleve.iterrows():

        duree = pd.to_numeric(
            ligne.get("duree_minutes"),
            errors="coerce"
        )

        if pd.isna(duree):
            duree = 0

        heures = float(duree) / 60

        mode = str(
            ligne.get("mode", "Présentiel")
        )

        if mode == "Distanciel":

            tarif_utilise = tarif_distanciel
            total_distanciel += heures

        else:

            tarif_utilise = tarif_presentiel
            total_presentiel += heures

        date_ligne = pd.to_datetime(
            ligne.get("date")
        ).strftime("%d/%m/%Y")

        heure_debut = str(
            ligne.get("heure_debut", "")
        )[:5]

        heure_fin = str(
            ligne.get("heure_fin", "")
        )[:5]

        discipline = str(
            ligne.get("disciplines", "")
        )

        donnees_table.append(
            [
                date_ligne,
                f"{heure_debut}-{heure_fin}",
                mode,
                discipline,
                f"{heures:.2f} h",
                f"{tarif_utilise:.2f} €"
            ]
        )

    table_seances = Table(
        donnees_table,
        colWidths=[
            65,
            90,
            75,
            165,
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
                6.5
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
                3
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3
            ),
            (
                "ALIGN",
                (4, 1),
                (-1, -1),
                "RIGHT"
            )
        ])
    )

    elements.append(
        table_seances
    )

    elements.append(
        Spacer(1, 8)
    )

    # ========================================================
    # TOTAL
    # ========================================================

    montant_presentiel = (
        total_presentiel * tarif_presentiel
    )

    montant_distanciel = (
        total_distanciel * tarif_distanciel
    )

    total_heures = (
        total_presentiel
        + total_distanciel
    )

    montant_total = (
        montant_presentiel
        + montant_distanciel
    )

    total_table = Table(
        [
            [
                Paragraph(
                    "<b>Présentiel</b>",
                    normal
                ),
                Paragraph(
                    f"{total_presentiel:.2f} h × "
                    f"{tarif_presentiel:.2f} € = "
                    f"{montant_presentiel:.2f} €",
                    droite
                )
            ],
            [
                Paragraph(
                    "<b>Distanciel</b>",
                    normal
                ),
                Paragraph(
                    f"{total_distanciel:.2f} h × "
                    f"{tarif_distanciel:.2f} € = "
                    f"{montant_distanciel:.2f} €",
                    droite
                )
            ],
            [
                Paragraph(
                    "<b>TOTAL</b>",
                    normal
                ),
                Paragraph(
                    f"<b>{total_heures:.2f} h — "
                    f"{montant_total:.2f} €</b>",
                    droite
                )
            ]
        ],
        colWidths=[150, 390]
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
        Spacer(1, 8)
    )

    # ========================================================
    # OBSERVATION
    # ========================================================

    if observation:

        elements.append(
            Paragraph(
                "<b>Observation pédagogique</b>",
                normal
            )
        )

        elements.append(
            Spacer(1, 3)
        )

        elements.append(
            Paragraph(
                observation,
                petite
            )
        )

        elements.append(
            Spacer(1, 8)
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
                Paragraph("<b>Statut</b>", normal),
                Paragraph("<b>PAYÉE</b>", normal)
            ],
            [
                Paragraph("<b>Date de paiement</b>", normal),
                Paragraph(
                    date_paiement_pdf,
                    normal
                )
            ]
        ]

    else:

        paiement = [
            [
                Paragraph("<b>Statut</b>", normal),
                Paragraph(
                    "<b>EN ATTENTE DE PAIEMENT</b>",
                    normal
                )
            ],
            [
                Paragraph("<b>Date de paiement</b>", normal),
                Paragraph("—", normal)
            ]
        ]

    table_paiement = Table(
        paiement,
        colWidths=[130, 410]
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
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
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
        Spacer(1, 10)
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
        "👨‍🎓 Élèves",
        "📖 Cahier de texte",
        "📊 Bilan",
        "🧾 Facturation"
    ]
)


# ============================================================
# 👨‍🎓 ÉLÈVES
# ============================================================

if menu == "👨‍🎓 Élèves":

    st.header("👨‍🎓 Gestion des élèves")

    action = st.radio(
        "Action",
        [
            "➕ Ajouter un élève",
            "✏️ Modifier un élève",
            "🗑️ Supprimer un élève",
            "📋 Liste des élèves"
        ],
        horizontal=True
    )

    # ========================================================
    # AJOUTER
    # ========================================================

    if action == "➕ Ajouter un élève":

        st.subheader("➕ Ajouter un élève")

        prenom = st.text_input(
            "Prénom *"
        )

        nom = st.text_input(
            "Nom"
        )

        classe = st.selectbox(
            "Classe actuelle",
            [
                "CP",
                "CE1",
                "CE2",
                "CM1",
                "CM2",
                "6e",
                "5e",
                "4e",
                "3e",
                "Seconde",
                "Première",
                "Terminale",
                "Études supérieures",
                "Autre"
            ]
        )

        if classe == "Autre":

            classe = st.text_input(
                "Préciser la classe"
            )

        if st.button(
            "💾 Ajouter l'élève",
            type="primary"
        ):

            if not prenom.strip():

                st.error(
                    "❌ Le prénom est obligatoire."
                )

            else:

                nouvel_eleve = {
                    "prenom": prenom.strip(),
                    "nom": nom.strip(),
                    "classe_actuelle": classe
                }

                try:

                    (
                        supabase
                        .table("eleves")
                        .insert(nouvel_eleve)
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
    # MODIFIER
    # ========================================================

    elif action == "✏️ Modifier un élève":

        st.subheader(
            "✏️ Modifier un élève"
        )

        df_eleves = recuperer_eleves()

        if df_eleves.empty:

            st.info(
                "Aucun élève enregistré."
            )

        else:

            choix = st.selectbox(
                "Élève",
                [
                    nom_complet_eleve(ligne)
                    for _, ligne
                    in df_eleves.iterrows()
                ]
            )

            ligne = None

            for _, element in df_eleves.iterrows():

                if nom_complet_eleve(element) == choix:

                    ligne = element
                    break

            if ligne is not None:

                prenom = st.text_input(
                    "Prénom",
                    value=str(
                        ligne["prenom"]
                    )
                )

                nom = st.text_input(
                    "Nom",
                    value=str(
                        ligne["nom"]
                        if pd.notna(ligne["nom"])
                        else ""
                    )
                )

                classe = st.text_input(
                    "Classe actuelle",
                    value=str(
                        ligne["classe_actuelle"]
                        if pd.notna(
                            ligne["classe_actuelle"]
                        )
                        else ""
                    )
                )

                if st.button(
                    "💾 Enregistrer les modifications",
                    type="primary"
                ):

                    if not prenom.strip():

                        st.error(
                            "❌ Le prénom est obligatoire."
                        )

                    else:

                        modifications = {
                            "prenom": prenom.strip(),
                            "nom": nom.strip(),
                            "classe_actuelle":
                                classe.strip()
                        }

                        try:

                            (
                                supabase
                                .table("eleves")
                                .update(modifications)
                                .eq(
                                    "id",
                                    int(ligne["id"])
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

                            st.code(str(e))

    # ========================================================
    # SUPPRIMER
    # ========================================================

    elif action == "🗑️ Supprimer un élève":

        st.subheader(
            "🗑️ Supprimer un élève"
        )

        st.warning(
            "Cette fonction est surtout destinée "
            "aux élèves fictifs utilisés pour les tests."
        )

        df_eleves = recuperer_eleves()

        if df_eleves.empty:

            st.info(
                "Aucun élève."
            )

        else:

            choix = st.selectbox(
                "Élève à supprimer",
                [
                    nom_complet_eleve(ligne)
                    for _, ligne
                    in df_eleves.iterrows()
                ]
            )

            ligne = None

            for _, element in df_eleves.iterrows():

                if nom_complet_eleve(element) == choix:

                    ligne = element
                    break

            confirmation = st.checkbox(
                "Je confirme vouloir supprimer cet élève."
            )

            if st.button(
                "🗑️ Supprimer",
                type="secondary"
            ):

                if not confirmation:

                    st.error(
                        "Veuillez confirmer la suppression."
                    )

                else:

                    try:

                        (
                            supabase
                            .table("eleves")
                            .delete()
                            .eq(
                                "id",
                                int(ligne["id"])
                            )
                            .execute()
                        )

                        st.success(
                            "✅ Élève supprimé."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur lors de la suppression."
                        )

                        st.code(str(e))

    # ========================================================
    # LISTE
    # ========================================================

    else:

        st.subheader(
            "📋 Liste des élèves"
        )

        df_eleves = recuperer_eleves()

        if df_eleves.empty:

            st.info(
                "Aucun élève enregistré."
            )

        else:

            affichage = df_eleves[
                [
                    "prenom",
                    "nom",
                    "classe_actuelle"
                ]
            ].copy()

            affichage.columns = [
                "Prénom",
                "Nom",
                "Classe actuelle"
            ]

            st.dataframe(
                affichage,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# GESTION DES SÉANCES
# ============================================================

elif menu == "📚 Gestion des séances":

    st.header("📚 Gestion des séances")

    eleves_disponibles = liste_eleves()

    if not eleves_disponibles:

        st.warning(
            "⚠️ Aucun élève n'est enregistré. "
            "Commencez par ajouter un élève dans "
            "👨‍🎓 Élèves."
        )

        st.stop()

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

        eleve_affiche = st.selectbox(
            "Élève",
            eleves_disponibles,
            key="nouvelle_eleve"
        )

        eleve_id = recuperer_id_eleve(
            eleve_affiche
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

                "eleve": eleve_affiche.split(" — ")[0],

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
                    ", ".join(disciplines),

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
                    .insert(nouvelle_seance)
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

                except Exception:
                    pass

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

            eleves_seances = sorted(
                df["eleve"]
                .dropna()
                .unique()
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
                        .update(modifications)
                        .eq(
                            "id",
                            identifiant
                        )
                        .execute()
                    )

                    st.success(
                        "✅ Séance modifiée."
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
        )

        eleve = st.selectbox(
            "Élève",
            eleves
        )

        df_eleve = df[
            df["eleve"] == eleve
        ]

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
                f"{ligne['mode']}"
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

        eleves = sorted(
            df["eleve"]
            .dropna()
            .unique()
        )

        eleve = st.selectbox(
            "Élève",
            eleves
        )

        df_eleve = df[
            df["eleve"] == eleve
        ].copy()

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

        st.subheader(
            "📝 Observation automatique"
        )

        observation = (
            generer_observation_automatique(
                df_eleve
            )
        )

        st.info(
            observation
        )

        st.subheader(
            "📋 Détail des séances"
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

    df_eleves = recuperer_eleves()

    if df.empty or df_eleves.empty:

        st.info(
            "Il faut au moins un élève et une séance."
        )

    else:

        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        eleves_affichage = [
            nom_complet_eleve(ligne)
            for _, ligne
            in df_eleves.iterrows()
        ]

        eleve_affiche = st.selectbox(
            "Élève",
            eleves_affichage,
            key="facture_eleve"
        )

        eleve = eleve_affiche.split(
            " — "
        )[0]

        ligne_eleve = None

        for _, ligne in df_eleves.iterrows():

            if nom_complet_eleve(ligne) == eleve_affiche:

                ligne_eleve = ligne
                break

        classe = ""

        if ligne_eleve is not None:

            classe = str(
                ligne_eleve.get(
                    "classe_actuelle",
                    ""
                )
            )

        st.info(
            f"🎓 Classe actuelle : "
            f"{classe or 'Non renseignée'}"
        )

        # ----------------------------------------------------
        # TYPE DE PÉRIODE
        # ----------------------------------------------------

        type_periode = st.selectbox(
            "Période de facturation",
            [
                "Mensuelle",
                "Personnalisée"
            ],
            index=0
        )

        # ----------------------------------------------------
        # PÉRIODE MENSUELLE
        # ----------------------------------------------------

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
                date_fin
                - pd.Timedelta(days=1)
            )

        # ----------------------------------------------------
        # PÉRIODE PERSONNALISÉE
        # ----------------------------------------------------

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
                    "❌ La date de fin doit être "
                    "postérieure à la date de début."
                )

                st.stop()

        # ----------------------------------------------------
        # PÉRIODE AFFICHÉE
        # ----------------------------------------------------

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
        # FILTRAGE
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

        if df_eleve.empty:

            st.warning(
                "Aucune séance pour cet élève "
                "durant cette période."
            )

        else:

            # ------------------------------------------------
            # CALCUL DES HEURES
            # ------------------------------------------------

            df_eleve["duree_minutes"] = pd.to_numeric(
                df_eleve["duree_minutes"],
                errors="coerce"
            ).fillna(0)

            df_eleve["heures"] = (
                df_eleve["duree_minutes"]
                / 60
            )

            heures_presentiel = (
                df_eleve[
                    df_eleve["mode"]
                    == "Présentiel"
                ]["heures"].sum()
            )

            heures_distanciel = (
                df_eleve[
                    df_eleve["mode"]
                    == "Distanciel"
                ]["heures"].sum()
            )

            montant_presentiel = (
                heures_presentiel
                * tarif_presentiel
            )

            montant_distanciel = (
                heures_distanciel
                * tarif_distanciel
            )

            total_heures = (
                heures_presentiel
                + heures_distanciel
            )

            montant_total = (
                montant_presentiel
                + montant_distanciel
            )

            # ------------------------------------------------
            # OBSERVATION
            # ------------------------------------------------

            st.subheader(
                "📝 Observation pédagogique"
            )

            observation_auto = (
                generer_observation_automatique(
                    df_eleve
                )
            )

            observation = st.text_area(
                "Observation apparaissant sur la facture",
                value=observation_auto,
                height=100
            )

            # ------------------------------------------------
            # INDICATEURS
            # ------------------------------------------------

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Nombre de séances",
                    len(df_eleve)
                )

            with col2:

                st.metric(
                    "Nombre d'heures",
                    f"{total_heures:.2f} h"
                )

            with col3:

                st.metric(
                    "Total",
                    f"{montant_total:.2f} €"
                )

            st.write(
                f"**Présentiel :** "
                f"{heures_presentiel:.2f} h — "
                f"{montant_presentiel:.2f} €"
            )

            st.write(
                f"**Distanciel :** "
                f"{heures_distanciel:.2f} h — "
                f"{montant_distanciel:.2f} €"
            )

            # ------------------------------------------------
            # TABLEAU
            # ------------------------------------------------

            st.subheader(
                "📋 Séances de la période"
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
            # GÉNÉRATION
            # ------------------------------------------------

            if st.button(
                "🧾 Générer la facture PDF",
                type="primary"
            ):

                try:

                    pdf = generer_facture_pdf(
                        df_eleve,
                        eleve,
                        classe,
                        tarif_presentiel,
                        tarif_distanciel,
                        numero_facture,
                        periode,
                        statut,
                        date_paiement,
                        observation
                    )

                    st.session_state[
                        "facture_pdf"
                    ] = pdf

                    st.session_state[
                        "facture_nom"
                    ] = (
                        f"Facture_"
                        f"{eleve}_"
                        f"{date_debut.strftime('%Y%m%d')}"
                        f"_{date_fin_inclusive.strftime('%Y%m%d')}"
                        f".pdf"
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
                    label="📥 Télécharger la facture PDF",
                    data=st.session_state[
                        "facture_pdf"
                    ],
                    file_name=st.session_state[
                        "facture_nom"
                    ],
                    mime="application/pdf"
                )
