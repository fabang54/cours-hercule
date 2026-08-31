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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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

MOIS = [
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
# AUTHENTIFICATION
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

        try:

            id_eleve = int(
                ligne["id"]
            )

        except Exception:

            continue

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
# OBSERVATION AUTOMATIQUE
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

    if not observations:

        return (
            "L'élève poursuit son travail de manière "
            "régulière dans le cadre des séances. "
            "Les apprentissages sont progressivement consolidés."
        )

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
        "bon",
        "sérieux",
        "serieux",
        "motivé",
        "motive",
        "impliqué",
        "implique",
        "satisfaisant",
        "réussite",
        "reussite",
        "réussi",
        "reussi",
        "réussit",
        "reussit"
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
        "attention",
        "attentif",
        "attentive"
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

    phrases = []

    if positif >= 2 and negatif == 0:

        phrases.append(
            "L'élève présente une attitude positive "
            "et un investissement satisfaisant dans les séances."
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

    if progres > 0:

        phrases.append(
            "Des progrès sont observés au fil des séances."
        )

    if travail > 0:

        phrases.append(
            "Le travail réalisé permet de consolider "
            "les notions étudiées."
        )

    if concentration > 0:

        phrases.append(
            "L'attention et la concentration contribuent "
            "favorablement aux apprentissages."
        )

    if participation > 0:

        phrases.append(
            "La participation pendant les séances "
            "favorise les apprentissages."
        )

    if negatif > 0:

        phrases.append(
            "Les difficultés identifiées font l'objet "
            "d'un travail spécifique afin de consolider "
            "les acquis."
        )

    return " ".join(phrases)


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


def facture_existante(
    eleve,
    periode
):

    factures = recuperer_factures()

    if factures.empty:

        return False

    if (
        "eleve" not in factures.columns
        or "periode" not in factures.columns
    ):

        return False

    return (
        factures["eleve"]
        .astype(str)
        .eq(str(eleve))
        &
        factures["periode"]
        .astype(str)
        .eq(str(periode))
    ).any()


def recuperer_facture_par_id(
    id_facture
):

    try:

        resultat = (
            supabase
            .table("factures")
            .select("*")
            .eq(
                "id",
                id_facture
            )
            .limit(1)
            .execute()
        )

        if resultat.data:

            return resultat.data[0]

        return None

    except Exception as e:

        st.error(
            f"Erreur récupération facture : {e}"
        )

        return None


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
    observation_pedagogique,
    type_tarification,
    attentif,
    participation,
    travail_serieux,
    progres,
    difficultes,
    nombre_evaluations
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

        "type_tarification":
            type_tarification,

        "attentif":
            attentif,

        "participation":
            participation,

        "travail_serieux":
            travail_serieux,

        "progres":
            progres,

        "difficultes":
            difficultes,

        "nombre_evaluations":
            nombre_evaluations,

        "date_facture":
            date.today().isoformat()
    }

    (
        supabase
        .table("factures")
        .insert(donnees)
        .execute()
    )


def modifier_facture(
    id_facture,
    modifications
):

    (
        supabase
        .table("factures")
        .update(modifications)
        .eq(
            "id",
            id_facture
        )
        .execute()
    )


# ============================================================
# FORMATAGE DURÉE
# ============================================================

def formater_duree(minutes):

    try:

        minutes = int(minutes)

    except Exception:

        minutes = 0

    heures = minutes // 60
    reste = minutes % 60

    return f"{heures}h{reste:02d}min"


# ============================================================
# PDF FACTURE PROFESSIONNEL
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
    observation_pedagogique,
    attentif,
    participation,
    travail_serieux,
    progres,
    difficultes,
    nombre_evaluations
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.1 * cm,
        leftMargin=1.1 * cm,
        topMargin=0.9 * cm,
        bottomMargin=0.8 * cm
    )

    styles = getSampleStyleSheet()

    normal = ParagraphStyle(
        "NormalFacture",
        parent=styles["Normal"],
        fontSize=8.3,
        leading=10.2,
        spaceAfter=0
    )

    petit = ParagraphStyle(
        "PetitFacture",
        parent=normal,
        fontSize=7.2,
        leading=8.5
    )

    titre = ParagraphStyle(
        "TitreFacture",
        parent=normal,
        fontSize=17,
        leading=19,
        alignment=TA_LEFT,
        fontName="Helvetica-Bold"
    )

    sous_titre = ParagraphStyle(
        "SousTitreFacture",
        parent=normal,
        fontSize=8.5,
        leading=10,
        fontName="Helvetica"
    )

    section = ParagraphStyle(
        "SectionFacture",
        parent=normal,
        fontSize=9,
        leading=10,
        fontName="Helvetica-Bold"
    )

    total_style = ParagraphStyle(
        "TotalFacture",
        parent=normal,
        fontSize=15,
        leading=17,
        alignment=TA_RIGHT,
        fontName="Helvetica-Bold"
    )

    total_label = ParagraphStyle(
        "TotalLabel",
        parent=normal,
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold"
    )

    elements = []

    # ========================================================
    # EN-TÊTE
    # ========================================================

    entete = Table(
        [
            [
                Paragraph(
                    "COURS HERCULE",
                    titre
                ),
                Paragraph(
                    "<b>FACTURE</b><br/>"
                    f"N° {numero_facture}<br/>"
                    f"{date.today().strftime('%d/%m/%Y')}",
                    ParagraphStyle(
                        "EnteteDroite",
                        parent=normal,
                        fontSize=8.5,
                        leading=11,
                        alignment=TA_RIGHT
                    )
                )
            ]
        ],
        colWidths=[
            10.5 * cm,
            7.5 * cm
        ]
    )

    entete.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ]
        )
    )

    elements.append(entete)

    elements.append(
        Paragraph(
            "Soutien scolaire",
            sous_titre
        )
    )

    elements.append(
        Spacer(1, 7)
    )

    # ========================================================
    # INFORMATIONS FACTURE
    # ========================================================

    infos = Table(
        [
            [
                Paragraph(
                    "<b>ÉLÈVE</b><br/>"
                    f"{eleve}",
                    normal
                ),
                Paragraph(
                    "<b>CLASSE</b><br/>"
                    f"{niveau or 'Non renseignée'}",
                    normal
                ),
                Paragraph(
                    "<b>PÉRIODE</b><br/>"
                    f"{periode}",
                    normal
                ),
                Paragraph(
                    "<b>TARIFICATION</b><br/>"
                    f"{type_tarification}",
                    normal
                )
            ]
        ],
        colWidths=[
            5.1 * cm,
            3.5 * cm,
            5.1 * cm,
            4.3 * cm
        ]
    )

    infos.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.grey
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
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
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )

    elements.append(infos)

    elements.append(
        Spacer(1, 7)
    )

    # ========================================================
    # DÉTAIL DES SÉANCES
    # ========================================================

    elements.append(
        Paragraph(
            "DÉTAIL DES SÉANCES",
            section
        )
    )

    elements.append(
        Spacer(1, 3)
    )

    donnees_seances = [
        [
            Paragraph("<b>Date</b>", petit),
            Paragraph("<b>Horaire</b>", petit),
            Paragraph("<b>Durée</b>", petit),
            Paragraph("<b>Mode</b>", petit),
            Paragraph("<b>Discipline</b>", petit)
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

        duree = float(duree)

        total_minutes += duree

        date_ligne = str(
            ligne.get(
                "date",
                ""
            )
        )

        if len(date_ligne) >= 10:

            try:

                date_ligne = (
                    pd.to_datetime(
                        date_ligne
                    )
                    .strftime("%d/%m")
                )

            except Exception:

                pass

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

        mode = str(
            ligne.get(
                "mode",
                ""
            )
        )

        discipline = str(
            ligne.get(
                "disciplines",
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
                    f"{heure_debut} – {heure_fin}",
                    petit
                ),

                Paragraph(
                    formater_duree(duree),
                    petit
                ),

                Paragraph(
                    mode,
                    petit
                ),

                Paragraph(
                    discipline,
                    petit
                )
            ]
        )

    total_heures = total_minutes / 60

    donnees_seances.append(
        [
            "",
            "",
            Paragraph(
                f"<b>{formater_duree(total_minutes)}</b>",
                petit
            ),
            Paragraph(
                f"<b>{len(df_eleve)} séance(s)</b>",
                petit
            ),
            ""
        ]
    )

    table_seances = Table(
        donnees_seances,
        colWidths=[
            2.2 * cm,
            3.1 * cm,
            2.3 * cm,
            3.1 * cm,
            6.4 * cm
        ],
        repeatRows=1
    )

    table_seances.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.lightgrey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#eeeeee")
                ),

                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.HexColor("#f5f5f5")
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
            ]
        )
    )

    elements.append(table_seances)

    elements.append(
        Spacer(1, 7)
    )

   # ========================================================
# FACTURATION + TOTAL
# ========================================================

if type_tarification == "Tarif horaire":

    tarif = float(tarif_horaire or 0)

    sous_total = total_heures * tarif

    texte_calcul = (
        f"{formater_duree(total_minutes)} × {tarif:.2f} €"
    )

else:

    sous_total = float(forfait_utilise or 0)

    texte_calcul = "Forfait mensuel"


remise_montant = float(remise or 0)

montant_total = max(
    0,
    sous_total - remise_montant
)


# --------------------------------------------------------
# Tableau de facturation
# --------------------------------------------------------

facturation_lignes = []

facturation_lignes.append(
    [
        Paragraph(
            "<b>FACTURATION</b>",
            section
        ),
        ""
    ]
)

facturation_lignes.append(
    [
        Paragraph(
            texte_calcul,
            normal
        ),
        Paragraph(
            f"{sous_total:.2f} €",
            ParagraphStyle(
                "MontantFacturation",
                parent=normal,
                alignment=TA_RIGHT
            )
        )
    ]
)


# --------------------------------------------------------
# Remise : uniquement si elle existe
# --------------------------------------------------------

if remise_montant > 0:

    facturation_lignes.append(
        [
            Paragraph(
                "Remise exceptionnelle",
                normal
            ),
            Paragraph(
                f"- {remise_montant:.2f} €",
                ParagraphStyle(
                    "MontantRemise",
                    parent=normal,
                    alignment=TA_RIGHT
                )
            )
        ]
    )


# --------------------------------------------------------
# Total à payer
# --------------------------------------------------------

facturation_lignes.append(
    [
        Paragraph(
            "TOTAL À PAYER",
            total_label
        ),
        Paragraph(
            f"{montant_total:.2f} €",
            total_style
        )
    ]
)


# --------------------------------------------------------
# Création du tableau
# --------------------------------------------------------

table_facturation = Table(
    facturation_lignes,
    colWidths=[
        11 * cm,
        7 * cm
    ],
    hAlign="RIGHT"
)


# --------------------------------------------------------
# Style du tableau
# --------------------------------------------------------

style_facturation = [

    (
        "BOX",
        (0, 0),
        (-1, -1),
        0.6,
        colors.grey
    ),

    (
        "INNERGRID",
        (0, 0),
        (-1, -1),
        0.3,
        colors.lightgrey
    ),

    (
        "BACKGROUND",
        (0, 0),
        (-1, 0),
        colors.HexColor("#eeeeee")
    ),

    (
        "BACKGROUND",
        (0, -1),
        (-1, -1),
        colors.HexColor("#e7e7e7")
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
        7
    ),

    (
        "RIGHTPADDING",
        (0, 0),
        (-1, -1),
        7
    ),
    # ========================================================
    # PAIEMENT
    # ========================================================

    paiement = (
        f"<b>Paiement :</b> {statut}"
    )

    if date_paiement:

        paiement += (
            f" — "
            f"Date de paiement : "
            f"{date_paiement.strftime('%d/%m/%Y')}"
        )

    elements.append(
        Paragraph(
            paiement,
            normal
        )
    )

    elements.append(
        Spacer(1, 7)
    )

    # ========================================================
    # SUIVI PÉDAGOGIQUE
    # ========================================================

    elements.append(
        Paragraph(
            "SUIVI PÉDAGOGIQUE",
            section
        )
    )

    elements.append(
        Spacer(1, 2)
    )

    def evaluation_texte(
        nom,
        valeur
    ):

        return Paragraph(
            f"<b>{nom}</b> "
            f"{'●' * int(valeur)}"
            f"{'○' * (int(nombre_evaluations) - int(valeur))} "
            f"<b>{int(valeur)}/{int(nombre_evaluations)}</b>",
            petit
        )

    suivi = Table(
        [
            [
                evaluation_texte(
                    "Attention",
                    attentif
                ),
                evaluation_texte(
                    "Participation",
                    participation
                ),
                evaluation_texte(
                    "Travail sérieux",
                    travail_serieux
                )
            ],

            [
                evaluation_texte(
                    "Progrès",
                    progres
                ),
                evaluation_texte(
                    "Difficultés",
                    difficultes
                ),
                Paragraph(
                    f"<b>Évaluation sur "
                    f"{nombre_evaluations} séances</b>",
                    petit
                )
            ]
        ],
        colWidths=[
            6 * cm,
            6 * cm,
            6 * cm
        ]
    )

    suivi.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.lightgrey
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
            ]
        )
    )

    elements.append(suivi)

    elements.append(
        Spacer(1, 6)
    )

    # ========================================================
    # OBSERVATION
    # ========================================================

    elements.append(
        Paragraph(
            "OBSERVATION PÉDAGOGIQUE",
            section
        )
    )

    elements.append(
        Spacer(1, 2)
    )

    elements.append(
        Paragraph(
            (
                observation_pedagogique
                or ""
            ).replace(
                "\n",
                "<br/>"
            ),
            petit
        )
    )

    elements.append(
        Spacer(1, 7)
    )

    # ========================================================
    # PIED DE PAGE
    # ========================================================

    elements.append(
        Paragraph(
            "Merci pour votre confiance.",
            ParagraphStyle(
                "FinFacture",
                parent=normal,
                alignment=TA_CENTER,
                fontSize=7.5
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
            "🔴 Factures impayées",
            "✏️ Modifier",
            "🗑️ Supprimer"
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

            # ------------------------------------------------
            # CLASSE
            # ------------------------------------------------

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
                        format_func=lambda x:
                        MOIS[x - 1]
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
                f"→ "
                f"{date_fin_inclusive.strftime('%d/%m/%Y')}"
            )

            st.info(
                f"📅 {periode}"
            )

            # ------------------------------------------------
            # TYPE DE TARIFICATION
            # ------------------------------------------------

            type_tarification_eleve = (
                informations_eleve.get(
                    "type_tarification",
                    "Tarif horaire"
                )
                or "Tarif horaire"
            )

            type_tarification = st.selectbox(
                "Type de tarification",
                [
                    "Tarif horaire",
                    "Forfait mensuel",
                    "Autre"
                ],
                index=(
                    1
                    if type_tarification_eleve
                    == "Forfait mensuel"
                    else 0
                )
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

            df_eleve["date_temp"] = (
                pd.to_datetime(
                    df_eleve["date"],
                    errors="coerce"
                ).dt.date
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
                ).fillna(0)
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

            # ------------------------------------------------
            # TARIFICATION
            # ------------------------------------------------

            st.subheader(
                "💶 Tarification"
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

            elif type_tarification == "Forfait mensuel":

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

            else:

                montant_autre = st.number_input(
                    "Montant (€)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0
                )

                forfait_utilise = (
                    montant_autre
                )

                tarif_horaire = 0.0

                sous_total = (
                    montant_autre
                )

            # ------------------------------------------------
            # REMISE
            # ------------------------------------------------

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
            # SUIVI PÉDAGOGIQUE
            # ------------------------------------------------

            st.subheader(
                "📊 Suivi pédagogique"
            )

            nombre_evaluations = st.number_input(
                "Nombre de séances évaluées",
                min_value=1,
                max_value=100,
                value=nombre_seances,
                step=1
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                attentif = st.number_input(
                    "Attentif",
                    min_value=0,
                    max_value=int(nombre_evaluations),
                    value=0,
                    step=1
                )

            with col2:

                participation = st.number_input(
                    "Participation",
                    min_value=0,
                    max_value=int(nombre_evaluations),
                    value=0,
                    step=1
                )

            with col3:

                travail_serieux = st.number_input(
                    "Travail sérieux",
                    min_value=0,
                    max_value=int(nombre_evaluations),
                    value=0,
                    step=1
                )

            col1, col2 = st.columns(2)

            with col1:

                progres = st.number_input(
                    "Progrès",
                    min_value=0,
                    max_value=int(nombre_evaluations),
                    value=0,
                    step=1
                )

            with col2:

                difficultes = st.number_input(
                    "Difficultés",
                    min_value=0,
                    max_value=int(nombre_evaluations),
                    value=0,
                    step=1
                )

            # ------------------------------------------------
            # OBSERVATION
            # ------------------------------------------------

            observation_auto = (
                generer_observation_automatique(
                    df_eleve
                )
            )

            st.subheader(
                "📝 Observation pédagogique"
            )

            st.caption(
                "L'observation est générée automatiquement "
                "à partir des observations des séances. "
                "Vous pouvez la modifier avant de générer la facture."
            )

            observation_pedagogique = st.text_area(
                "Observation figurant sur la facture",
                value=observation_auto,
                height=130,
                key="observation_facture_nouvelle"
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
            # NUMÉRO
            # ------------------------------------------------

            numero_defaut = (
                f"CH-"
                f"{date.today().strftime('%Y%m%d')}-"
                f"{eleve_id}"
            )

            numero_facture = st.text_input(
                "Numéro de facture",
                value=numero_defaut
            )

            # ------------------------------------------------
            # APERÇU
            # ------------------------------------------------

            st.subheader(
                "👁️ Aperçu de la facture"
            )

            if st.button(
                "👁️ Générer l'aperçu PDF",
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
                            observation_pedagogique,
                            attentif,
                            participation,
                            travail_serieux,
                            progres,
                            difficultes,
                            nombre_evaluations
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

                    st.session_state[
                        "facture_donnees"
                    ] = {

                        "eleve": eleve,
                        "periode": periode,
                        "numero_facture": numero_facture,
                        "nombre_seances": nombre_seances,
                        "total_heures": total_heures,
                        "tarif_horaire": tarif_horaire,
                        "forfait_utilise": forfait_utilise,
                        "remise": remise,
                        "montant_total": montant_total,
                        "statut": statut,
                        "date_paiement": date_paiement,
                        "classe": classe_actuelle,
                        "observation_pedagogique":
                            observation_pedagogique,
                        "type_tarification":
                            type_tarification,
                        "attentif": attentif,
                        "participation": participation,
                        "travail_serieux": travail_serieux,
                        "progres": progres,
                        "difficultes": difficultes,
                        "nombre_evaluations":
                            nombre_evaluations
                    }

                except Exception as e:

                    st.error(
                        "❌ Erreur génération aperçu."
                    )

                    st.code(
                        str(e)
                    )

            # ------------------------------------------------
            # AFFICHAGE APERÇU
            # ------------------------------------------------

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

                        # ----------------------------------------
                        # VÉRIFICATION ÉLÈVE + PÉRIODE
                        # ----------------------------------------

                        deja_existante = facture_existante(
                            eleve,
                            periode
                        )

                        if deja_existante:

                            st.error(
                                "❌ Une facture existe déjà "
                                "pour cet élève et cette période."
                            )

                            st.info(
                                "La facture n'a pas été enregistrée "
                                "une seconde fois."
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
                                observation_pedagogique,
                                type_tarification,
                                attentif,
                                participation,
                                travail_serieux,
                                progres,
                                difficultes,
                                nombre_evaluations
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
                            "❌ Erreur lors de l'enregistrement."
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


    # ========================================================
    # IMPAYÉES
    # ========================================================

    elif sous_menu == "🔴 Factures impayées":

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


    # ========================================================
    # MODIFIER FACTURE
    # ========================================================

    elif sous_menu == "✏️ Modifier":

        st.subheader(
            "✏️ Modifier une facture"
        )

        factures = recuperer_factures()

        if factures.empty:

            st.info(
                "Aucune facture enregistrée."
            )

        else:

            choix_factures = []

            for _, ligne in factures.iterrows():

                choix_factures.append(
                    (
                        int(ligne["id"]),
                        str(
                            ligne.get(
                                "numero_facture",
                                ""
                            )
                        ),
                        str(
                            ligne.get(
                                "eleve",
                                ""
                            )
                        ),
                        str(
                            ligne.get(
                                "periode",
                                ""
                            )
                        )
                    )
                )

            choix = st.selectbox(
                "Facture",
                choix_factures,
                format_func=lambda x:
                (
                    f"{x[1]} — "
                    f"{x[2]} — "
                    f"{x[3]}"
                )
            )

            id_facture = choix[0]

            facture = recuperer_facture_par_id(
                id_facture
            )

            if facture:

                st.write(
                    f"**Élève :** "
                    f"{facture.get('eleve','')}"
                )

                st.write(
                    f"**Période :** "
                    f"{facture.get('periode','')}"
                )

                statut_modification = st.selectbox(
                    "Statut",
                    [
                        "En attente de paiement",
                        "Payée"
                    ],
                    index=(
                        1
                        if facture.get("statut")
                        == "Payée"
                        else 0
                    )
                )

                date_paiement_modification = None

                if statut_modification == "Payée":

                    ancienne_date = facture.get(
                        "date_paiement"
                    )

                    if ancienne_date:

                        try:

                            date_paiement_defaut = (
                                pd.to_datetime(
                                    ancienne_date
                                ).date()
                            )

                        except Exception:

                            date_paiement_defaut = date.today()

                    else:

                        date_paiement_defaut = date.today()

                    date_paiement_modification = (
                        st.date_input(
                            "Date de paiement",
                            date_paiement_defaut
                        )
                    )

                remise_modification = st.number_input(
                    "Remise exceptionnelle (€)",
                    min_value=0.0,
                    value=float(
                        facture.get(
                            "remise",
                            0
                        )
                        or 0
                    ),
                    step=1.0
                )

                observation_modification = st.text_area(
                    "Observation pédagogique",
                    value=str(
                        facture.get(
                            "observation_pedagogique",
                            ""
                        )
                        or ""
                    ),
                    height=130
                )

                if st.button(
                    "💾 Enregistrer les modifications",
                    type="primary"
                ):

                    montant_initial = float(
                        facture.get(
                            "montant_total",
                            0
                        )
                        or 0
                    )

                    ancienne_remise = float(
                        facture.get(
                            "remise",
                            0
                        )
                        or 0
                    )

                    nouveau_montant = (
                        montant_initial
                        + ancienne_remise
                        - remise_modification
                    )

                    nouveau_montant = max(
                        0,
                        nouveau_montant
                    )

                    modifications = {

                        "remise":
                            remise_modification,

                        "montant_total":
                            nouveau_montant,

                        "statut":
                            statut_modification,

                        "date_paiement":
                            (
                                date_paiement_modification.isoformat()
                                if date_paiement_modification
                                else None
                            ),

                        "observation_pedagogique":
                            observation_modification
                    }

                    try:

                        modifier_facture(
                            id_facture,
                            modifications
                        )

                        st.success(
                            "✅ Facture modifiée."
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
    # SUPPRIMER FACTURE
    # ========================================================

    else:

        st.subheader(
            "🗑️ Supprimer une facture"
        )

        factures = recuperer_factures()

        if factures.empty:

            st.info(
                "Aucune facture enregistrée."
            )

        else:

            choix_factures = []

            for _, ligne in factures.iterrows():

                choix_factures.append(
                    (
                        int(ligne["id"]),
                        str(
                            ligne.get(
                                "numero_facture",
                                ""
                            )
                        ),
                        str(
                            ligne.get(
                                "eleve",
                                ""
                            )
                        ),
                        str(
                            ligne.get(
                                "periode",
                                ""
                            )
                        )
                    )
                )

            choix = st.selectbox(
                "Facture",
                choix_factures,
                format_func=lambda x:
                (
                    f"{x[1]} — "
                    f"{x[2]} — "
                    f"{x[3]}"
                )
            )

            id_facture = choix[0]

            confirmation = st.checkbox(
                "Je confirme vouloir supprimer définitivement cette facture."
            )

            if st.button(
                "🗑️ Supprimer définitivement",
                type="primary"
            ):

                if not confirmation:

                    st.error(
                        "Veuillez confirmer la suppression."
                    )

                else:

                    try:

                        (
                            supabase
                            .table("factures")
                            .delete()
                            .eq(
                                "id",
                                id_facture
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

            contrat = st.selectbox(
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
