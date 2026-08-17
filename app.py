import streamlit as st
import pandas as pd

from supabase import create_client
from datetime import date, time
from io import BytesIO
import io
import calendar

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
    "Élève fatigué",
    "Élève distrait",
    "Difficultés importantes",
    "Difficulté de compréhension",
    "Bonne participation",
    "Très bonne séance",
    "Progrès constatés",
    "Manque de concentration",
    "Travail sérieux",
    "Autonomie satisfaisante",
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
# NOM AFFICHÉ DE L'ÉLÈVE
# ============================================================

def nom_eleve(ligne):

    prenom = str(
        ligne.get("prenom", "")
    ).strip()

    nom = str(
        ligne.get("nom", "")
    ).strip()

    classe = str(
        ligne.get("classe_actuelle", "")
    ).strip()

    resultat = prenom

    if nom:
        resultat += f" {nom}"

    if classe:
        resultat += f" ({classe})"

    return resultat


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
# OBSERVATION AUTOMATIQUE
# ============================================================

def generer_observation_automatique(
    df_eleve
):

    if df_eleve.empty:

        return (
            "Aucune observation disponible "
            "pour cette période."
        )

    observations = []

    for valeur in df_eleve["observations"].fillna(""):

        texte = str(valeur)

        if texte.strip():

            morceaux = texte.split(",")

            for morceau in morceaux:

                observation = morceau.strip()

                if observation:
                    observations.append(
                        observation
                    )

    total = len(df_eleve)

    if total == 0:

        return (
            "Aucune observation disponible "
            "pour cette période."
        )

    compte = pd.Series(
        observations
    ).value_counts()

    phrases = []

    # --------------------------------------------------------
    # ATTENTION
    # --------------------------------------------------------

    if "Élève attentif" in compte:

        n = int(
            compte["Élève attentif"]
        )

        phrases.append(
            f"Élève attentif : {n}/{total} séances."
        )

    # --------------------------------------------------------
    # FATIGUE
    # --------------------------------------------------------

    if "Élève fatigué" in compte:

        n = int(
            compte["Élève fatigué"]
        )

        phrases.append(
            f"Fatigue observée : {n}/{total} séances."
        )

    # --------------------------------------------------------
    # PARTICIPATION
    # --------------------------------------------------------

    if "Bonne participation" in compte:

        n = int(
            compte["Bonne participation"]
        )

        phrases.append(
            f"Bonne participation : {n}/{total} séances."
        )

    # --------------------------------------------------------
    # PROGRÈS
    # --------------------------------------------------------

    if "Progrès constatés" in compte:

        n = int(
            compte["Progrès constatés"]
        )

        phrases.append(
            f"Progrès constatés : {n}/{total} séances."
        )

    # --------------------------------------------------------
    # DIFFICULTÉS
    # --------------------------------------------------------

    if "Difficultés importantes" in compte:

        n = int(
            compte["Difficultés importantes"]
        )

        phrases.append(
            f"Difficultés importantes : "
            f"{n}/{total} séances."
        )

    if "Difficulté de compréhension" in compte:

        n = int(
            compte["Difficulté de compréhension"]
        )

        phrases.append(
            f"Difficultés de compréhension : "
            f"{n}/{total} séances."
        )

    # --------------------------------------------------------
    # DISTRACTION
    # --------------------------------------------------------

    if "Élève distrait" in compte:

        n = int(
            compte["Élève distrait"]
        )

        phrases.append(
            f"Manque de concentration : "
            f"{n}/{total} séances."
        )

    # --------------------------------------------------------
    # CONSTRUCTION DU TEXTE
    # --------------------------------------------------------

    if not phrases:

        return (
            "Bonne progression sur la période. "
            "Les notions étudiées sont "
            "progressivement maîtrisées. "
            "Un travail régulier est recommandé."
        )

    texte = " ".join(
        phrases
    )

    texte += (
        " Les notions étudiées sont "
        "progressivement maîtrisées. "
        "Un travail régulier est recommandé."
    )

    return texte


# ============================================================
# FACTURE PDF
# ============================================================

def generer_facture_pdf(
    df_eleve,
    eleve,
    niveau,
    tarif_presentiel,
    tarif_distanciel,
    numero_facture,
    periode,
    statut,
    date_paiement,
    observation_automatique
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    titre = ParagraphStyle(
        "TitreFacture",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=8
    )

    normal = ParagraphStyle(
        "NormalFacture",
        parent=styles["Normal"],
        fontSize=8,
        leading=10
    )

    petit = ParagraphStyle(
        "Petit",
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
        Spacer(1, 7)
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
            Paragraph("<b>Niveau / classe</b>", normal),
            Paragraph(str(niveau), normal)
        ],
        [
            Paragraph("<b>Date de facture</b>", normal),
            Paragraph(date_facture, normal)
        ],
        [
            Paragraph("<b>Période facturée</b>", normal),
            Paragraph(str(periode), normal)
        ],
        [
            Paragraph("<b>Tarif présentiel</b>", normal),
            Paragraph(
                f"{tarif_presentiel:.2f} €/h",
                normal
            )
        ],
        [
            Paragraph("<b>Tarif distanciel</b>", normal),
            Paragraph(
                f"{tarif_distanciel:.2f} €/h",
                normal
            )
        ]
    ]

    table_infos = Table(
        infos,
        colWidths=[145, 365]
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

    total_minutes_presentiel = 0
    total_minutes_distanciel = 0

    for _, ligne in df_eleve.iterrows():

        duree = pd.to_numeric(
            ligne.get("duree_minutes"),
            errors="coerce"
        )

        if pd.isna(duree):
            duree = 0

        duree = float(duree)

        mode = str(
            ligne.get("mode", "")
        )

        if mode == "Présentiel":

            total_minutes_presentiel += duree

        else:

            total_minutes_distanciel += duree

        date_ligne = pd.to_datetime(
            ligne.get("date"),
            errors="coerce"
        )

        if pd.isna(date_ligne):

            date_affichee = ""

        else:

            date_affichee = (
                date_ligne.strftime(
                    "%d/%m/%Y"
                )
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
                date_affichee,
                f"{heure_debut}-{heure_fin}",
                mode,
                discipline,
                f"{duree / 60:.2f} h"
            ]
        )

    table_seances = Table(
        donnees_table,
        colWidths=[
            70,
            90,
            70,
            210,
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
    # CALCULS
    # ========================================================

    heures_presentiel = (
        total_minutes_presentiel / 60
    )

    heures_distanciel = (
        total_minutes_distanciel / 60
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

    # ========================================================
    # RÉCAPITULATIF
    # ========================================================

    recap = [
        [
            Paragraph(
                "<b>Présentiel</b>",
                normal
            ),
            Paragraph(
                f"{heures_presentiel:.2f} h",
                droite
            ),
            Paragraph(
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
                f"{heures_distanciel:.2f} h",
                droite
            ),
            Paragraph(
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
                f"<b>{total_heures:.2f} h</b>",
                droite
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
            270,
            110,
            130
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
                (-1, -1),
                "RIGHT"
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
        table_recap
    )

    elements.append(
        Spacer(1, 7)
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

        texte_statut = (
            f"PAYÉE le {date_paiement_pdf}"
        )

    else:

        texte_statut = (
            "EN ATTENTE DE PAIEMENT"
        )

    paiement = [
        [
            Paragraph(
                "<b>Statut</b>",
                normal
            ),
            Paragraph(
                texte_statut,
                normal
            )
        ]
    ]

    table_paiement = Table(
        paiement,
        colWidths=[145, 365]
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
                (0, 0),
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
        Spacer(1, 7)
    )

    # ========================================================
    # OBSERVATION PARENTS
    # ========================================================

    elements.append(
        Paragraph(
            "<b>Bilan pédagogique</b>",
            normal
        )
    )

    elements.append(
        Spacer(1, 3)
    )

    elements.append(
        Paragraph(
            observation_automatique,
            petit
        )
    )

    elements.append(
        Spacer(1, 8)
    )

    elements.append(
        Paragraph(
            "Merci pour votre confiance.",
            petit
        )
    )

    # ========================================================
    # CONSTRUCTION
    # ========================================================

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

    st.header(
        "👨‍🎓 Gestion des élèves"
    )

    action = st.radio(
        "Action",
        [
            "➕ Ajouter un élève",
            "📋 Liste des élèves"
        ],
        horizontal=True
    )

    # ========================================================
    # AJOUT
    # ========================================================

    if action == "➕ Ajouter un élève":

        st.subheader(
            "➕ Ajouter un élève"
        )

        prenom = st.text_input(
            "Prénom *"
        )

        nom = st.text_input(
            "Nom"
        )

        classe = st.selectbox(
            "Niveau / classe",
            [
                "",
                "CP",
                "CE1",
                "CE2",
                "CM1",
                "CM2",
                "6ème",
                "5ème",
                "4ème",
                "3ème",
                "2nde",
                "1ère",
                "Terminale",
                "Supérieur",
                "Autre"
            ]
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
    # LISTE
    # ========================================================

    else:

        df_eleves = recuperer_eleves()

        if df_eleves.empty:

            st.info(
                "Aucun élève enregistré."
            )

        else:

            affichage = []

            for _, ligne in df_eleves.iterrows():

                affichage.append({
                    "Prénom":
                        ligne.get("prenom", ""),
                    "Nom":
                        ligne.get("nom", ""),
                    "Classe":
                        ligne.get(
                            "classe_actuelle",
                            ""
                        )
                })

            st.dataframe(
                pd.DataFrame(affichage),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# GESTION DES SÉANCES
# ============================================================

elif menu == "📚 Gestion des séances":

    st.header(
        "📚 Gestion des séances"
    )

    df_eleves = recuperer_eleves()

    if df_eleves.empty:

        st.warning(
            "⚠️ Aucun élève enregistré. "
            "Ajoutez d'abord un élève dans "
            "« 👨‍🎓 Élèves »."
        )

        st.stop()

    liste_eleves = [
        nom_eleve(ligne)
        for _, ligne in df_eleves.iterrows()
    ]

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

        choix_eleve = st.selectbox(
            "Élève",
            liste_eleves
        )

        ligne_eleve = df_eleves[
            df_eleves.apply(
                lambda ligne:
                nom_eleve(ligne)
                == choix_eleve,
                axis=1
            )
        ].iloc[0]

        eleve_id = int(
            ligne_eleve["id"]
        )

        eleve = choix_eleve

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

        if travail == "Autre":

            travail = st.text_input(
                "Préciser"
            )

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
                    "✅ Séance enregistrée."
                )

                ok, message = (
                    synchroniser_drive()
                )

                if ok:
                    st.success(message)

                else:
                    st.warning(message)

            except Exception as e:

                st.error(
                    "❌ Erreur lors de l'enregistrement."
                )

                st.code(
                    str(e)
                )

    # ========================================================
    # MODIFICATION
    # ========================================================

    else:

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

            choix = []

            for _, ligne in df_eleve.iterrows():

                choix.append(
                    f"{ligne['date']} - "
                    f"{ligne['heure_debut']} - "
                    f"{ligne['contenu']}"
                )

            index = st.selectbox(
                "Séance",
                range(len(choix)),
                format_func=lambda i: choix[i]
            )

            ligne = df_eleve.iloc[index]

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
                            ligne["id"]
                        )
                        .execute()
                    )

                    st.success(
                        "✅ Séance modifiée."
                    )

                    synchroniser_drive()

                    st.rerun()

                except Exception as e:

                    st.error(
                        "❌ Erreur."
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
            sorted(
                df["eleve"]
                .dropna()
                .unique()
            )
        )

        df_eleve = df[
            df["eleve"] == eleve
        ]

        for _, ligne in df_eleve.iterrows():

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
            "📋 Observations"
        )

        observation = generer_observation_automatique(
            df_eleve
        )

        st.info(
            observation
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
            "Aucune donnée disponible."
        )

    else:

        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        liste_eleves = [
            nom_eleve(ligne)
            for _, ligne in df_eleves.iterrows()
        ]

        eleve = st.selectbox(
            "Élève",
            liste_eleves,
            key="facture_eleve"
        )

        ligne_eleve = df_eleves[
            df_eleves.apply(
                lambda ligne:
                nom_eleve(ligne)
                == eleve,
                axis=1
            )
        ].iloc[0]

        niveau = ligne_eleve.get(
            "classe_actuelle",
            ""
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

            dernier_jour = calendar.monthrange(
                int(annee),
                int(mois)
            )[1]

            date_fin = date(
                int(annee),
                int(mois),
                dernier_jour
            )

        # ----------------------------------------------------
        # PÉRIODE PERSONNALISÉE
        # ----------------------------------------------------

        else:

            col1, col2 = st.columns(2)

            with col1:

                date_debut = st.date_input(
                    "Date de début",
                    value=date.today()
                )

            with col2:

                date_fin = st.date_input(
                    "Date de fin",
                    value=date.today()
                )

        if date_fin < date_debut:

            st.error(
                "❌ La date de fin doit être "
                "postérieure ou égale à la date de début."
            )

            st.stop()

        periode = (
            f"{date_debut.strftime('%d/%m/%Y')}"
            f" – "
            f"{date_fin.strftime('%d/%m/%Y')}"
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
                "Tarif présentiel (€/h)",
                min_value=0.0,
                value=30.0,
                step=1.0
            )

        with col2:

            tarif_distanciel = st.number_input(
                "Tarif distanciel (€/h)",
                min_value=0.0,
                value=30.0,
                step=1.0
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
                <= date_fin
            )
        ].copy()

        if df_eleve.empty:

            st.warning(
                "Aucune séance pour cet élève "
                "durant cette période."
            )

        else:

            # ------------------------------------------------
            # DURÉES
            # ------------------------------------------------

            df_eleve["duree_minutes"] = pd.to_numeric(
                df_eleve[
                    "duree_minutes"
                ],
                errors="coerce"
            ).fillna(0)

            df_eleve["montant"] = 0.0

            for index, ligne in df_eleve.iterrows():

                heures = (
                    ligne["duree_minutes"]
                    / 60
                )

                if ligne["mode"] == "Présentiel":

                    tarif_ligne = (
                        tarif_presentiel
                    )

                else:

                    tarif_ligne = (
                        tarif_distanciel
                    )

                df_eleve.loc[
                    index,
                    "montant"
                ] = (
                    heures
                    * tarif_ligne
                )

            # ------------------------------------------------
            # BILAN
            # ------------------------------------------------

            total_minutes = (
                df_eleve[
                    "duree_minutes"
                ].sum()
            )

            total_heures = (
                total_minutes / 60
            )

            presentiel = df_eleve[
                df_eleve["mode"]
                == "Présentiel"
            ]

            distanciel = df_eleve[
                df_eleve["mode"]
                == "Distanciel"
            ]

            heures_presentiel = (
                presentiel[
                    "duree_minutes"
                ].sum() / 60
            )

            heures_distanciel = (
                distanciel[
                    "duree_minutes"
                ].sum() / 60
            )

            montant_total = (
                df_eleve[
                    "montant"
                ].sum()
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "Séances",
                    len(df_eleve)
                )

            with col2:

                st.metric(
                    "Présentiel",
                    f"{heures_presentiel:.2f} h"
                )

            with col3:

                st.metric(
                    "Distanciel",
                    f"{heures_distanciel:.2f} h"
                )

            with col4:

                st.metric(
                    "Total",
                    f"{montant_total:.2f} €"
                )

            # ------------------------------------------------
            # BILAN OBSERVATIONS
            # ------------------------------------------------

            st.subheader(
                "📊 Bilan des observations"
            )

            observation_automatique = (
                generer_observation_automatique(
                    df_eleve
                )
            )

            st.info(
                observation_automatique
            )

            # ------------------------------------------------
            # DÉTAIL DES OBSERVATIONS
            # ------------------------------------------------

            toutes_observations = []

            for valeur in df_eleve[
                "observations"
            ].fillna(""):

                morceaux = str(
                    valeur
                ).split(",")

                for morceau in morceaux:

                    obs = morceau.strip()

                    if obs:
                        toutes_observations.append(
                            obs
                        )

            if toutes_observations:

                compte_obs = pd.Series(
                    toutes_observations
                ).value_counts()

                bilan_obs = []

                total_seances = len(
                    df_eleve
                )

                for obs, nombre in compte_obs.items():

                    bilan_obs.append({
                        "Observation":
                            obs,
                        "Nombre de séances":
                            int(nombre),
                        "Sur":
                            total_seances,
                        "Pourcentage":
                            f"{nombre / total_seances * 100:.0f} %"
                    })

                st.dataframe(
                    pd.DataFrame(
                        bilan_obs
                    ),
                    use_container_width=True,
                    hide_index=True
                )

            # ------------------------------------------------
            # TABLEAU SÉANCES
            # ------------------------------------------------

            st.subheader(
                "📋 Séances de la période"
            )

            tableau = df_eleve[
                [
                    "date",
                    "heure_debut",
                    "heure_fin",
                    "mode",
                    "disciplines",
                    "duree_minutes"
                ]
            ].copy()

            tableau = tableau.rename(
                columns={
                    "date":
                        "Date",
                    "heure_debut":
                        "Début",
                    "heure_fin":
                        "Fin",
                    "mode":
                        "Mode",
                    "disciplines":
                        "Discipline",
                    "duree_minutes":
                        "Durée (min)"
                }
            )

            st.dataframe(
                tableau,
                use_container_width=True,
                hide_index=True
            )

            # ------------------------------------------------
            # STATUT
            # ------------------------------------------------

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

            # ------------------------------------------------
            # NUMÉRO
            # ------------------------------------------------

            numero_facture = st.text_input(
                "Numéro de facture",
                value=(
                    f"CH-"
                    f"{date_debut.strftime('%Y%m%d')}-"
                    f"{date_fin.strftime('%Y%m%d')}"
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
                        niveau,
                        tarif_presentiel,
                        tarif_distanciel,
                        numero_facture,
                        periode,
                        statut,
                        date_paiement,
                        observation_automatique
                    )

                    st.session_state[
                        "facture_pdf"
                    ] = pdf

                    st.session_state[
                        "facture_nom"
                    ] = (
                        "Facture_"
                        f"{eleve.replace(' ', '_')}_"
                        f"{date_debut.strftime('%Y%m%d')}_"
                        f"{date_fin.strftime('%Y%m%d')}.pdf"
                    )

                    st.success(
                        "✅ Facture PDF générée."
                    )

                except Exception as e:

                    st.error(
                        "❌ Erreur lors de la génération "
                        "de la facture."
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
