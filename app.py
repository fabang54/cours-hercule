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

NIVEAUX = [
    "CP",
    "CE1",
    "CE2",
    "CM1",
    "CM2",
    "6ème",
    "5ème",
    "4ème",
    "3ème",
    "Seconde",
    "Première",
    "Terminale",
    "Supérieur"
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
    "Difficultés de compréhension",
    "Difficultés importantes",
    "Bonne participation",
    "Très bonne séance",
    "Progrès constatés",
    "Travail sérieux",
    "Manque de travail",
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
    niveau,
    tarif_presentiel,
    tarif_distanciel,
    numero_facture,
    periode,
    statut,
    date_paiement,
    observation_bilan
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
        fontSize=19,
        spaceAfter=12
    )

    normal = ParagraphStyle(
        "NormalFacture",
        parent=styles["Normal"],
        fontSize=9,
        leading=11
    )

    petit = ParagraphStyle(
        "Petit",
        parent=normal,
        fontSize=8,
        leading=9
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
            Paragraph("<b>Niveau</b>", normal),
            Paragraph(str(niveau), normal)
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
        colWidths=[130, 440]
    )

    table_infos.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)
        ])
    )

    elements.append(table_infos)

    elements.append(
        Spacer(1, 10)
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

    total_presentiel = 0
    total_distanciel = 0

    for _, ligne in df_eleve.iterrows():

        duree = pd.to_numeric(
            ligne.get("duree_minutes"),
            errors="coerce"
        )

        if pd.isna(duree):
            duree = 0

        mode = str(
            ligne.get("mode", "")
        )

        if mode == "Présentiel":
            total_presentiel += float(duree)
        else:
            total_distanciel += float(duree)

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
                f"{float(duree) / 60:.2f} h"
            ]
        )

    table_seances = Table(
        donnees_table,
        colWidths=[
            70,
            95,
            75,
            235,
            70
        ],
        repeatRows=1
    )

    table_seances.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ALIGN", (4, 1), (4, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
        ])
    )

    elements.append(
        table_seances
    )

    elements.append(
        Spacer(1, 8)
    )

    # ========================================================
    # CALCULS
    # ========================================================

    heures_presentiel = total_presentiel / 60
    heures_distanciel = total_distanciel / 60

    montant_presentiel = (
        heures_presentiel * tarif_presentiel
    )

    montant_distanciel = (
        heures_distanciel * tarif_distanciel
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
    # RÉCAPITULATIF FACTURATION
    # ========================================================

    recap = [
        [
            Paragraph("<b>Mode</b>", normal),
            Paragraph("<b>Heures</b>", normal),
            Paragraph("<b>Tarif horaire</b>", normal),
            Paragraph("<b>Montant</b>", normal)
        ]
    ]

    if heures_presentiel > 0:

        recap.append(
            [
                Paragraph("Présentiel", normal),
                Paragraph(
                    f"{heures_presentiel:.2f} h",
                    normal
                ),
                Paragraph(
                    f"{tarif_presentiel:.2f} €",
                    normal
                ),
                Paragraph(
                    f"{montant_presentiel:.2f} €",
                    droite
                )
            ]
        )

    if heures_distanciel > 0:

        recap.append(
            [
                Paragraph("Distanciel", normal),
                Paragraph(
                    f"{heures_distanciel:.2f} h",
                    normal
                ),
                Paragraph(
                    f"{tarif_distanciel:.2f} €",
                    normal
                ),
                Paragraph(
                    f"{montant_distanciel:.2f} €",
                    droite
                )
            ]
        )

    recap.append(
        [
            Paragraph("<b>TOTAL</b>", normal),
            Paragraph(
                f"<b>{total_heures:.2f} h</b>",
                normal
            ),
            Paragraph("", normal),
            Paragraph(
                f"<b>{montant_total:.2f} €</b>",
                droite
            )
        ]
    )

    table_recap = Table(
        recap,
        colWidths=[
            150,
            110,
            130,
            150
        ]
    )

    table_recap.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
        ])
    )

    elements.append(
        table_recap
    )

    elements.append(
        Spacer(1, 8)
    )

    # ========================================================
    # OBSERVATION
    # ========================================================

    if observation_bilan.strip():

        elements.append(
            Paragraph(
                "<b>Observation sur la période</b>",
                normal
            )
        )

        elements.append(
            Spacer(1, 3)
        )

        elements.append(
            Paragraph(
                observation_bilan,
                petit
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
                Paragraph(date_paiement_pdf, normal)
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
        colWidths=[130, 440]
    )

    table_paiement.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)
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
            petit
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

        niveau = st.selectbox(
            "Niveau de l'élève",
            NIVEAUX,
            key="nouveau_niveau"
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

                "niveau": niveau,

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

                ok, message = synchroniser_drive()

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


# ============================================================
# CAHIER DE TEXTE
# ============================================================

elif menu == "📖 Cahier de texte":

    st.header("📖 Cahier de texte")

    df = recuperer_seances()

    if df.empty:

        st.info("Aucune séance.")

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

    st.header("📊 Bilan")

    df = recuperer_seances()

    if df.empty:

        st.info("Aucune séance.")

    else:

        eleve = st.selectbox(
            "Élève",
            ELEVES
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

    st.header("🧾 Facturation")

    df = recuperer_seances()

    if df.empty:

        st.info("Aucune séance.")

    else:

        # ----------------------------------------------------
        # ÉLÈVE
        # ----------------------------------------------------

        eleve = st.selectbox(
            "Élève",
            ELEVES,
            key="facture_eleve"
        )

        # ----------------------------------------------------
        # NIVEAU
        # ----------------------------------------------------

        niveau = st.selectbox(
            "Niveau de l'élève",
            NIVEAUX,
            key="facture_niveau"
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
            index=0,
            key="type_periode"
        )

        # ----------------------------------------------------
        # DATES
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
                date_fin - pd.Timedelta(days=1)
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

        st.subheader("💶 Tarifs")

        col1, col2 = st.columns(2)

        with col1:

            tarif_presentiel = st.number_input(
                "Tarif présentiel (€ / h)",
                min_value=0.0,
                value=30.0,
                step=1.0
            )

        with col2:

            tarif_distanciel = st.number_input(
                "Tarif distanciel (€ / h)",
                min_value=0.0,
                value=25.0,
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
                df_eleve["date_temp"] >= date_debut
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
            # CALCUL DES HEURES
            # ------------------------------------------------

            df_eleve["duree_minutes"] = pd.to_numeric(
                df_eleve["duree_minutes"],
                errors="coerce"
            ).fillna(0)

            df_presentiel = df_eleve[
                df_eleve["mode"] == "Présentiel"
            ]

            df_distanciel = df_eleve[
                df_eleve["mode"] == "Distanciel"
            ]

            minutes_presentiel = (
                df_presentiel["duree_minutes"].sum()
            )

            minutes_distanciel = (
                df_distanciel["duree_minutes"].sum()
            )

            heures_presentiel = (
                minutes_presentiel / 60
            )

            heures_distanciel = (
                minutes_distanciel / 60
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
            # INDICATEURS
            # ------------------------------------------------

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
                "duree_minutes"
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
            # OBSERVATION
            # ------------------------------------------------

            st.subheader(
                "📝 Observation du bilan"
            )

            suggestions = [
                "Bonne progression sur la période. "
                "Les notions étudiées sont progressivement maîtrisées.",

                "Élève sérieux et attentif. "
                "Les progrès sont encourageants.",

                "Bonne participation durant les séances. "
                "Les notions sont progressivement maîtrisées.",

                "Quelques difficultés de compréhension persistent. "
                "Un travail régulier est recommandé.",

                "Les efforts sont réguliers et les progrès sont visibles.",

                "Une attention particulière doit être portée "
                "aux notions encore fragiles.",

                "Très bonne implication sur l'ensemble de la période.",

                "Les acquis sont satisfaisants. "
                "Il convient de poursuivre les efforts."
            ]

            observation_choisie = st.selectbox(
                "Suggestion",
                [
                    "Aucune suggestion"
                ] + suggestions
            )

            observation_manuel = st.text_area(
                "Observation complémentaire",
                placeholder=(
                    "Vous pouvez compléter ou modifier "
                    "l'observation."
                )
            )

            if observation_manuel.strip():

                observation_bilan = (
                    observation_manuel.strip()
                )

            elif observation_choisie != "Aucune suggestion":

                observation_bilan = observation_choisie

            else:

                observation_bilan = ""

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
            # GÉNÉRATION PDF
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
                        observation_bilan
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
                        f"{date_fin_inclusive.strftime('%Y%m%d')}"
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

                    st.code(str(e))

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
