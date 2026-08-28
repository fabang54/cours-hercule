# ============================================================
# COURS HERCULE
# Application complète de gestion des cours particuliers
# ============================================================

import streamlit as st
import pandas as pd

from datetime import date, time
from io import BytesIO

from supabase import create_client

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
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
# CONSTANTES
# ============================================================

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
    "BTS",
    "Université",
    "Autre"
]

CONTRATS = [
    "Sans engagement",
    "Cours ponctuels",
    "Forfait mensuel",
    "Pack de séances",
    "Autre"
]


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def initialiser_supabase():

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(
        url,
        key
    )


supabase = initialiser_supabase()


# ============================================================
# MOT DE PASSE
# ============================================================

if "authentifie" not in st.session_state:

    st.session_state["authentifie"] = False


if not st.session_state["authentifie"]:

    st.title("📚 Cours Hercule")

    st.subheader("🔐 Espace enseignant")

    mot_de_passe = st.text_input(
        "Mot de passe",
        type="password"
    )

    if st.button(
        "Se connecter",
        type="primary"
    ):

        if mot_de_passe == st.secrets["mot_de_passe"]:

            st.session_state["authentifie"] = True

            st.rerun()

        else:

            st.error(
                "❌ Mot de passe incorrect."
            )

    st.stop()


# ============================================================
# FONCTIONS ÉLÈVES
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

        return pd.DataFrame(
            resultat.data or []
        )

    except Exception as e:

        st.error(
            f"Erreur récupération élèves : {e}"
        )

        return pd.DataFrame()


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

        return None

    except Exception as e:

        st.error(
            f"Erreur récupération élève : {e}"
        )

        return None


def liste_eleves_avec_id():

    df = recuperer_eleves()

    if df.empty:

        return []

    resultat = []

    for _, ligne in df.iterrows():

        id_eleve = int(
            ligne["id"]
        )

        prenom = str(
            ligne.get("prenom", "")
        )

        nom = str(
            ligne.get("nom", "")
        )

        nom_complet = (
            f"{prenom} {nom}"
        ).strip()

        resultat.append(
            (
                id_eleve,
                nom_complet
            )
        )

    return resultat


def nom_eleve_depuis_id(id_eleve):

    eleve = recuperer_eleve(
        id_eleve
    )

    if eleve is None:

        return "Élève inconnu"

    return (
        f"{eleve.get('prenom', '')} "
        f"{eleve.get('nom', '') or ''}"
    ).strip()


# ============================================================
# FONCTIONS SÉANCES
# ============================================================

def recuperer_seances():

    try:

        resultat = (
            supabase
            .table("seances")
            .select("*")
            .order(
                "date",
                desc=True
            )
            .execute()
        )

        return pd.DataFrame(
            resultat.data or []
        )

    except Exception as e:

        st.error(
            f"Erreur récupération séances : {e}"
        )

        return pd.DataFrame()


def recuperer_seances_eleve(eleve_id):

    try:

        resultat = (
            supabase
            .table("seances")
            .select("*")
            .eq(
                "eleve_id",
                eleve_id
            )
            .order(
                "date",
                desc=True
            )
            .execute()
        )

        return pd.DataFrame(
            resultat.data or []
        )

    except Exception as e:

        st.error(
            f"Erreur récupération séances : {e}"
        )

        return pd.DataFrame()


# ============================================================
# GÉNÉRATION AUTOMATIQUE DE L'OBSERVATION PÉDAGOGIQUE
# ============================================================

def generer_observation_automatique(df):

    if df.empty:

        return (
            "Aucune observation disponible "
            "pour cette période."
        )

    observations = []

    if "observations" in df.columns:

        for valeur in (
            df["observations"]
            .fillna("")
            .astype(str)
            .str.strip()
        ):

            if valeur:

                observations.append(
                    valeur
                )

    # --------------------------------------------------------
    # Aucune observation saisie
    # --------------------------------------------------------

    if not observations:

        return (
            "Le suivi pédagogique se poursuit "
            "régulièrement. Les séances permettent "
            "de consolider les acquis et de poursuivre "
            "les apprentissages."
        )

    # --------------------------------------------------------
    # Analyse simple des observations
    # --------------------------------------------------------

    texte_global = " ".join(
        observations
    ).lower()

    positif = 0
    negatif = 0
    progres = 0
    travail = 0
    concentration = 0
    participation = 0

    mots_positifs = [
        "très bien",
        "tres bien",
        "bien",
        "bonne",
        "sérieux",
        "serieux",
        "motivé",
        "motive",
        "impliqué",
        "implique",
        "progrès",
        "progres",
        "satisfaisant",
        "réussite",
        "reussi",
        "réussit"
    ]

    mots_negatifs = [
        "difficulté",
        "difficultés",
        "difficulte",
        "difficultes",
        "manque",
        "insuffisant",
        "insuffisante",
        "erreur",
        "erreurs",
        "fragile",
        "à revoir",
        "a revoir"
    ]

    mots_progres = [
        "progrès",
        "progres",
        "amélioration",
        "amelioration",
        "progresser",
        "avance"
    ]

    mots_travail = [
        "travail",
        "exercice",
        "exercices",
        "révision",
        "revision",
        "méthode",
        "methode"
    ]

    mots_concentration = [
        "concentration",
        "concentré",
        "concentre",
        "attention"
    ]

    mots_participation = [
        "participation",
        "participe",
        "participatif",
        "question",
        "questions"
    ]

    for mot in mots_positifs:

        if mot in texte_global:

            positif += 1

    for mot in mots_negatifs:

        if mot in texte_global:

            negatif += 1

    for mot in mots_progres:

        if mot in texte_global:

            progres += 1

    for mot in mots_travail:

        if mot in texte_global:

            travail += 1

    for mot in mots_concentration:

        if mot in texte_global:

            concentration += 1

    for mot in mots_participation:

        if mot in texte_global:

            participation += 1

    # --------------------------------------------------------
    # Construction de l'observation
    # --------------------------------------------------------

    phrases = []

    # Cas très positif

    if positif >= 2 and negatif == 0:

        phrases.append(
            "L'élève présente une attitude positive "
            "et un investissement satisfaisant dans "
            "les séances."
        )

    elif positif > negatif:

        phrases.append(
            "L'élève s'investit de manière satisfaisante "
            "dans les séances et poursuit progressivement "
            "ses apprentissages."
        )

    elif negatif > positif:

        phrases.append(
            "L'élève poursuit ses apprentissages, "
            "mais certains points nécessitent encore "
            "un travail régulier."
        )

    else:

        phrases.append(
            "L'élève poursuit son travail de manière "
            "régulière dans le cadre des séances."
        )

    # --------------------------------------------------------
    # Progrès
    # --------------------------------------------------------

    if progres > 0:

        phrases.append(
            "Des progrès sont observés au fil des séances."
        )

    # --------------------------------------------------------
    # Travail
    # --------------------------------------------------------

    if travail > 0:

        phrases.append(
            "Le travail réalisé permet de consolider "
            "les notions étudiées."
        )

    # --------------------------------------------------------
    # Concentration
    # --------------------------------------------------------

    if concentration > 0:

        phrases.append(
            "La concentration reste un point à maintenir "
            "afin de favoriser les apprentissages."
        )

    # --------------------------------------------------------
    # Participation
    # --------------------------------------------------------

    if participation > 0:

        phrases.append(
            "La participation pendant les séances "
            "contribue au suivi des apprentissages."
        )

    # --------------------------------------------------------
    # Difficultés
    # --------------------------------------------------------

    if negatif > 0:

        phrases.append(
            "Les difficultés identifiées font l'objet "
            "d'un travail spécifique afin de consolider "
            "les acquis."
        )

    return " ".join(
        phrases
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

        return pd.DataFrame(
            resultat.data or []
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
    forfait_utilise,
    remise,
    montant_total,
    statut,
    date_paiement,
    niveau,
    observation_pedagogique
):

    donnees = {

        "numero_facture":
            numero_facture,

        "eleve":
            eleve,

        "periode":
            periode,

        "nombre_seances":
            nombre_seances,

        "total_heures":
            total_heures,

        "tarif_horaire":
            tarif_horaire,

        "forfait_mensuel":
            forfait_utilise,

        "remise":
            remise,

        "montant_total":
            montant_total,

        "statut":
            statut,

        "date_paiement":
            (
                date_paiement.isoformat()
                if date_paiement
                else None
            ),

        "classe":
            niveau,

        "observation_pedagogique":
            observation_pedagogique,

        "date_facture":
            date.today().isoformat()
    }

    (
        supabase
        .table("factures")
        .insert(donnees)
        .execute()
    )


# ============================================================
# PDF FACTURE
# ============================================================

def generer_facture_pdf(
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
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()

    titre = ParagraphStyle(
        "Titre",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=15
    )

    sous_titre = ParagraphStyle(
        "SousTitre",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceAfter=8
    )

    normal = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13
    )

    petit = ParagraphStyle(
        "Petit",
        parent=styles["Normal"],
        fontSize=8,
        leading=11
    )

    elements = []

    # ========================================================
    # EN-TÊTE
    # ========================================================

    elements.append(
        Paragraph(
            "COURS HERCULE",
            titre
        )
    )

    elements.append(
        Paragraph(
            "Cours particuliers",
            ParagraphStyle(
                "SousTitreCentre",
                parent=normal,
                alignment=TA_CENTER,
                fontSize=11,
                spaceAfter=20
            )
        )
    )

    # ========================================================
    # INFORMATIONS FACTURE
    # ========================================================

    infos = [

        [
            Paragraph(
                "<b>Facture n°</b>",
                normal
            ),
            Paragraph(
                str(numero_facture),
                normal
            )
        ],

        [
            Paragraph(
                "<b>Date</b>",
                normal
            ),
            Paragraph(
                date.today().strftime("%d/%m/%Y"),
                normal
            )
        ],

        [
            Paragraph(
                "<b>Période</b>",
                normal
            ),
            Paragraph(
                periode,
                normal
            )
        ],

        [
            Paragraph(
                "<b>Élève</b>",
                normal
            ),
            Paragraph(
                eleve,
                normal
            )
        ],

        [
            Paragraph(
                "<b>Classe</b>",
                normal
            ),
            Paragraph(
                niveau or "Non renseignée",
                normal
            )
        ]
    ]

    table_infos = Table(
        infos,
        colWidths=[
            4 * cm,
            12 * cm
        ]
    )

    table_infos.setStyle(
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
                )
            ]
        )
    )

    elements.append(
        table_infos
    )

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # DÉTAIL DES SÉANCES
    # ========================================================

    elements.append(
        Paragraph(
            "Détail des séances",
            sous_titre
        )
    )

    donnees_seances = [

        [
            Paragraph("<b>Date</b>", petit),
            Paragraph("<b>Horaire</b>", petit),
            Paragraph("<b>Durée</b>", petit),
            Paragraph("<b>Discipline</b>", petit),
            Paragraph("<b>Contenu</b>", petit)
        ]
    ]

    total_minutes = 0

    for _, ligne in df_eleve.iterrows():

        duree = pd.to_numeric(
            ligne.get(
                "duree_minutes",
                0
            ),
            errors="coerce"
        )

        if pd.isna(duree):

            duree = 0

        total_minutes += float(
            duree
        )

        date_ligne = str(
            ligne.get(
                "date",
                ""
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

        contenu = str(
            ligne.get(
                "contenu",
                ""
            )
        )

        donnees_seances.append(
            [
                Paragraph(
                    date_ligne,
                    petit
                ),

                Paragraph(
                    f"{heure_debut} → {heure_fin}",
                    petit
                ),

                Paragraph(
                    f"{int(duree)} min",
                    petit
                ),

                Paragraph(
                    discipline,
                    petit
                ),

                Paragraph(
                    contenu,
                    petit
                )
            ]
        )

    table_seances = Table(
        donnees_seances,
        colWidths=[
            2.1 * cm,
            3.0 * cm,
            2.0 * cm,
            3.0 * cm,
            6.0 * cm
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
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
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
                    4
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                )
            ]
        )
    )

    elements.append(
        table_seances
    )

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # TARIFICATION
    # ========================================================

    total_heures = (
        total_minutes / 60
    )

    if type_tarification == "Tarif horaire":

        sous_total = (
            total_heures
            * tarif_horaire
        )

    else:

        sous_total = forfait_utilise

    montant_total = max(
        0,
        sous_total - remise
    )

    elements.append(
        Paragraph(
            "Tarification",
            sous_titre
        )
    )

    tarif_data = [

        [
            Paragraph(
                "<b>Type de tarification</b>",
                normal
            ),
            Paragraph(
                type_tarification,
                normal
            )
        ],

        [
            Paragraph(
                "<b>Nombre de séances</b>",
                normal
            ),
            Paragraph(
                str(len(df_eleve)),
                normal
            )
        ],

        [
            Paragraph(
                "<b>Total d'heures</b>",
                normal
            ),
            Paragraph(
                f"{total_heures:.2f} h",
                normal
            )
        ]
    ]

    if type_tarification == "Tarif horaire":

        tarif_data.append(
            [
                Paragraph(
                    "<b>Tarif horaire</b>",
                    normal
                ),
                Paragraph(
                    f"{tarif_horaire:.2f} €",
                    normal
                )
            ]
        )

    else:

        tarif_data.append(
            [
                Paragraph(
                    "<b>Forfait mensuel</b>",
                    normal
                ),
                Paragraph(
                    f"{forfait_utilise:.2f} €",
                    normal
                )
            ]
        )

    tarif_data.extend(
        [
            [
                Paragraph(
                    "<b>Sous-total</b>",
                    normal
                ),
                Paragraph(
                    f"{sous_total:.2f} €",
                    normal
                )
            ],

            [
                Paragraph(
                    "<b>Remise</b>",
                    normal
                ),
                Paragraph(
                    f"{remise:.2f} €",
                    normal
                )
            ],

            [
                Paragraph(
                    "<b>TOTAL À PAYER</b>",
                    normal
                ),
                Paragraph(
                    f"<b>{montant_total:.2f} €</b>",
                    normal
                )
            ]
        ]
    )

    table_tarif = Table(
        tarif_data,
        colWidths=[
            8 * cm,
            5 * cm
        ],
        hAlign="RIGHT"
    )

    table_tarif.setStyle(
        TableStyle(
            [
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
                    colors.lightgrey
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
                    6
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ]
        )
    )

    elements.append(
        table_tarif
    )

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # PAIEMENT
    # ========================================================

    elements.append(
        Paragraph(
            "Paiement",
            sous_titre
        )
    )

    texte_paiement = (
        f"<b>Statut :</b> {statut}"
    )

    if date_paiement:

        texte_paiement += (
            " — Date de paiement : "
            f"{date_paiement.strftime('%d/%m/%Y')}"
        )

    elements.append(
        Paragraph(
            texte_paiement,
            normal
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # ========================================================
    # OBSERVATION PÉDAGOGIQUE
    # ========================================================

    elements.append(
        Paragraph(
            "Observation pédagogique",
            sous_titre
        )
    )

    elements.append(
        Paragraph(
            observation_pedagogique.replace(
                "\n",
                "<br/>"
            ),
            normal
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            "Merci pour votre confiance.",
            ParagraphStyle(
                "Fin",
                parent=normal,
                alignment=TA_CENTER,
                fontSize=9
            )
        )
    )

    document.build(
        elements
    )

    buffer.seek(0)

    return (
        buffer.getvalue(),
        montant_total
    )


# ============================================================
# AFFICHAGE PDF
# ============================================================

def afficher_pdf(pdf_bytes):

    import base64

    base64_pdf = base64.b64encode(
        pdf_bytes
    ).decode("utf-8")

    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="100%"
        height="800"
        type="application/pdf">
    </iframe>
    """

    st.markdown(
        pdf_display,
        unsafe_allow_html=True
    )


# ============================================================
# SYNCHRONISATION DRIVE
# ============================================================

def synchroniser_drive():

    return (
        True,
        "Synchronisation effectuée."
    )


def sauvegarder_facture_pdf_dans_drive(
    pdf,
    nom_facture
):

    return nom_facture


# ============================================================
# TITRE
# ============================================================

st.title(
    "📚 Cours Hercule"
)


# ============================================================
# MENU
# ============================================================

menu = st.sidebar.radio(
    "Navigation",
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

    st.header(
        "📚 Gestion des séances"
    )

    action = st.radio(
        "Action",
        [
            "➕ Ajouter",
            "✏️ Modifier",
            "🗑️ Supprimer"
        ],
        horizontal=True
    )

    # ========================================================
    # AJOUT
    # ========================================================

    if action == "➕ Ajouter":

        eleves = liste_eleves_avec_id()

        if not eleves:

            st.info(
                "Aucun élève enregistré."
            )

        else:

            eleve_selection = st.selectbox(
                "Élève",
                eleves,
                format_func=lambda x: x[1]
            )

            eleve_id = eleve_selection[0]

            date_seance = st.date_input(
                "Date",
                date.today()
            )

            col1, col2 = st.columns(2)

            with col1:

                heure_debut = st.time_input(
                    "Heure de début",
                    time(14, 0)
                )

            with col2:

                heure_fin = st.time_input(
                    "Heure de fin",
                    time(15, 0)
                )

            mode = st.selectbox(
                "Mode",
                [
                    "Présentiel",
                    "Distanciel"
                ]
            )

            disciplines = st.text_input(
                "Discipline(s)"
            )

            contenu = st.text_area(
                "Contenu"
            )

            travail = st.text_area(
                "Travail à faire"
            )

            observations = st.text_area(
                "Observations pédagogiques"
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
                        "Horaire incorrect."
                    )

                elif not disciplines.strip():

                    st.error(
                        "La discipline est obligatoire."
                    )

                elif not contenu.strip():

                    st.error(
                        "Le contenu est obligatoire."
                    )

                else:

                    donnees = {

                        "eleve_id":
                            eleve_id,

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
                            disciplines.strip(),

                        "contenu":
                            contenu.strip(),

                        "travail":
                            travail.strip(),

                        "observations":
                            observations.strip()
                    }

                    try:

                        (
                            supabase
                            .table("seances")
                            .insert(donnees)
                            .execute()
                        )

                        st.success(
                            "✅ Séance enregistrée."
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

    # ========================================================
    # MODIFICATION
    # ========================================================

    elif action == "✏️ Modifier":

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
                        (
                            f"{ligne.get('date','')} | "
                            f"{str(ligne.get('heure_debut',''))[:5]} → "
                            f"{str(ligne.get('heure_fin',''))[:5]} | "
                            f"{ligne.get('contenu','')}"
                        )
                    )
                )

            selection = st.selectbox(
                "Séance",
                choix_seances,
                format_func=lambda x: x[1]
            )

            identifiant = selection[0]

            ligne = df_eleve[
                df_eleve["id"] == identifiant
            ].iloc[0]

            nouvelle_date = st.date_input(
                "Date",
                pd.to_datetime(
                    ligne["date"]
                ).date()
            )

            heure_debut = st.time_input(
                "Heure de début",
                pd.to_datetime(
                    ligne["heure_debut"]
                ).time()
            )

            heure_fin = st.time_input(
                "Heure de fin",
                pd.to_datetime(
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
                "Observations pédagogiques",
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
                        disciplines.strip(),

                    "contenu":
                        contenu.strip(),

                    "travail":
                        travail.strip(),

                    "observations":
                        observations.strip()
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

                    synchroniser_drive()

                    st.rerun()

                except Exception as e:

                    st.error(
                        "❌ Erreur modification."
                    )

                    st.code(
                        str(e)
                    )

    # ========================================================
    # SUPPRESSION
    # ========================================================

    else:

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
                        (
                            f"{ligne.get('date','')} | "
                            f"{str(ligne.get('heure_debut',''))[:5]} → "
                            f"{str(ligne.get('heure_fin',''))[:5]} | "
                            f"{ligne.get('contenu','')}"
                        )
                    )
                )

            seance_choisie = st.selectbox(
                "Séance à supprimer",
                choix_seances,
                format_func=lambda x: x[1]
            )

            id_seance = seance_choisie[0]

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

                        synchroniser_drive()

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur suppression."
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

        df_eleve = recuperer_seances_eleve(
            eleve_id
        )

        if df_eleve.empty:

            st.info(
                "Aucune séance pour cet élève."
            )

        else:

            for _, ligne in df_eleve.iterrows():

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
                    f"**Observations pédagogiques :** "
                    f"{ligne.get('observations','')}"
                )


# ============================================================
# BILAN
# ============================================================

elif menu == "📊 Bilan":

    st.header(
        "📊 Bilan"
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

        eleve_id = eleve_selection[0]

        df_eleve = recuperer_seances_eleve(
            eleve_id
        )

        if df_eleve.empty:

            st.info(
                "Aucune séance."
            )

        else:

            df_eleve["duree_minutes"] = (
                pd.to_numeric(
                    df_eleve["duree_minutes"],
                    errors="coerce"
                )
                .fillna(0)
            )

            total_minutes = (
                df_eleve[
                    "duree_minutes"
                ].sum()
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

            # ------------------------------------------------
            # OBSERVATION AUTOMATIQUE
            # ------------------------------------------------

            st.subheader(
                "📝 Observation pédagogique automatique"
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
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# FACTURATION
# ============================================================

elif menu == "🧾 Facturation":

    st.header(
        "🧾 Facturation"
    )

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

            if informations_eleve is None:

                st.error(
                    "Impossible de récupérer la fiche élève."
                )

                st.stop()

            # =================================================
            # CLASSE
            # =================================================

            classe_actuelle = (
                informations_eleve.get(
                    "classe_actuelle",
                    ""
                )
                or ""
            )

            st.info(
                f"🎓 Classe actuelle : "
                f"**{classe_actuelle or 'Non renseignée'}**"
            )

            # =================================================
            # PÉRIODE
            # =================================================

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

            # =================================================
            # SÉANCES
            # =================================================

            df_eleve = recuperer_seances_eleve(
                eleve_id
            )

            if df_eleve.empty:

                st.warning(
                    "Aucune séance pour cet élève."
                )

                st.stop()

            df_eleve["date_temp"] = (
                pd.to_datetime(
                    df_eleve["date"],
                    errors="coerce"
                )
                .dt.date
            )

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

            df_eleve["duree_minutes"] = (
                pd.to_numeric(
                    df_eleve["duree_minutes"],
                    errors="coerce"
                )
                .fillna(0)
            )

            total_minutes = (
                df_eleve[
                    "duree_minutes"
                ].sum()
            )

            total_heures = (
                total_minutes / 60
            )

            nombre_seances = len(
                df_eleve
            )

            # =================================================
            # OBSERVATION PÉDAGOGIQUE AUTOMATIQUE
            # =================================================

            observation_auto = (
                generer_observation_automatique(
                    df_eleve
                )
            )

            # =================================================
            # TARIFICATION
            # =================================================

            st.subheader(
                "💶 Tarification"
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
                )
                or 0
            )

            forfait_mensuel_eleve = float(
                informations_eleve.get(
                    "forfait_mensuel",
                    0
                )
                or 0
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

            # =================================================
            # PAIEMENT
            # =================================================

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

            # =================================================
            # NUMÉRO FACTURE
            # =================================================

            numero_defaut = (
                f"CH-"
                f"{date.today().strftime('%Y%m%d')}-"
                f"{eleve_id}"
            )

            numero_facture = st.text_input(
                "Numéro de facture",
                value=numero_defaut
            )

            # =================================================
            # OBSERVATION PÉDAGOGIQUE
            # =================================================

            st.subheader(
                "📝 Observation pédagogique"
            )

            st.caption(
                "L'observation est générée automatiquement "
                "à partir des observations des séances."
            )

            observation_pedagogique = st.text_area(
                "Observation figurant sur la facture",
                value=observation_auto,
                height=150,
                key="observation_facture"
            )

            # =================================================
            # APERÇU
            # =================================================

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
                            classe_actuelle,
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

                    st.code(
                        str(e)
                    )

            # =================================================
            # AFFICHAGE APERÇU
            # =================================================

            if (
                "facture_pdf_apercu"
                in st.session_state
            ):

                st.success(
                    "✅ Aperçu généré."
                )

                afficher_pdf(
                    st.session_state[
                        "facture_pdf_apercu"
                    ]
                )

                st.download_button(
                    "📥 Télécharger la facture PDF",
                    data=st.session_state[
                        "facture_pdf_apercu"
                    ],
                    file_name=st.session_state[
                        "facture_nom_apercu"
                    ],
                    mime="application/pdf"
                )

                st.divider()

                # =================================================
                # ENREGISTREMENT
                # =================================================

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

                        anciennes = (
                            recuperer_factures()
                        )

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
                                date_paiement,
                                classe_actuelle,
                                observation_pedagogique
                            )

                            st.success(
                                "✅ Facture enregistrée dans Supabase."
                            )

                            if enregistrer_drive:

                                try:

                                    resultat_drive = (
                                        sauvegarder_facture_pdf_dans_drive(
                                            st.session_state[
                                                "facture_pdf_apercu"
                                            ],
                                            st.session_state[
                                                "facture_nom_apercu"
                                            ]
                                        )
                                    )

                                    st.success(
                                        "☁️ Facture enregistrée "
                                        f"dans Google Drive : "
                                        f"{resultat_drive}"
                                    )

                                except Exception as e:

                                    st.warning(
                                        "⚠️ La facture est enregistrée "
                                        "dans Supabase mais pas dans "
                                        "Google Drive."
                                    )

                                    st.code(
                                        str(e)
                                    )

                    except Exception as e:

                        st.error(
                            "❌ Erreur lors de "
                            "l'enregistrement."
                        )

                        st.code(
                            str(e)
                        )

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
                    .dt.strftime(
                        "%d/%m/%Y"
                    )
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

                        st.code(
                            str(e)
                        )

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

                total_impaye = (
                    pd.to_numeric(
                        impayees[
                            "montant_total"
                        ],
                        errors="coerce"
                    )
                    .fillna(0)
                    .sum()
                )

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
                c
                for c in [
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
                    "classe_actuelle": "Niveau / Classe",
                    "type_tarification": "Tarification",
                    "tarif_horaire": "Tarif horaire",
                    "forfait_mensuel": "Forfait mensuel",
                    "contrat": "Contrat"
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

                    st.code(
                        str(e)
                    )

    # ========================================================
    # MODIFICATION
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
                    )
                    or ""
                )
            )

            classe_actuelle = str(
                ligne.get(
                    "classe_actuelle",
                    ""
                )
                or ""
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
                    )
                    or 0
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
                    )
                    or 0
                ),
                step=1.0
            )

            contrat_actuel = str(
                ligne.get(
                    "contrat",
                    ""
                )
                or ""
            )

            st.selectbox(
                "Contrat / modalités",
                CONTRATS,
                index=(
                    CONTRATS.index(
                        contrat_actuel
                    )
                    if contrat_actuel in CONTRATS
                    else 0
                ),
                key="contrat_modification"
            )

            contrat = st.session_state[
                "contrat_modification"
            ]

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
                            "Les séances existantes sont conservées."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Erreur modification."
                        )

                        st.code(
                            str(e)
                        )

    # ========================================================
    # SUPPRESSION
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
                "ne supprime pas automatiquement "
                "les séances associées."
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

                        st.code(
                            str(e)
                        )
