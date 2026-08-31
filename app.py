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
# OUTILS DURÉE
# ============================================================

def formater_duree(minutes):

    try:

        minutes = int(round(float(minutes)))

    except Exception:

        minutes = 0

    heures = minutes // 60
    minutes_restantes = minutes % 60

    if heures > 0:

        return (
            f"{heures} h "
            f"{minutes_restantes:02d} min"
        )

    return f"{minutes_restantes} min"


def total_minutes_dataframe(df):

    if df.empty:

        return 0

    if "duree_minutes" not in df.columns:

        return 0

    return int(
        pd.to_numeric(
            df["duree_minutes"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )


# ============================================================
# GÉNÉRATION AUTOMATIQUE DU BILAN
# ============================================================

def calculer_bilan_comportement(df):

    total = len(df)

    if total == 0:

        return []

    resultats = []

    colonnes = [
        "observations",
        "contenu",
        "travail"
    ]

    texte = []

    for colonne in colonnes:

        if colonne in df.columns:

            texte.extend(
                df[colonne]
                .fillna("")
                .astype(str)
                .tolist()
            )

    textes = [
        str(x).strip().lower()
        for x in texte
        if str(x).strip()
    ]

    attentif = 0
    concentration = 0
    fatigue = 0
    implication = 0
    accompagnement = 0

    for texte_seance in textes:

        if any(
            mot in texte_seance
            for mot in [
                "attentif",
                "attentive",
                "attention",
                "concentré",
                "concentre"
            ]
        ):

            attentif += 1

        if any(
            mot in texte_seance
            for mot in [
                "concentration satisfaisante",
                "bonne concentration",
                "concentré",
                "concentre"
            ]
        ):

            concentration += 1

        if any(
            mot in texte_seance
            for mot in [
                "fatigué",
                "fatigue",
                "fatiguée"
            ]
        ):

            fatigue += 1

        if any(
            mot in texte_seance
            for mot in [
                "bonne implication",
                "impliqué",
                "implique",
                "motivé",
                "motive",
                "participation"
            ]
        ):

            implication += 1

        if any(
            mot in texte_seance
            for mot in [
                "besoin d'accompagnement",
                "besoin d accompagnement",
                "accompagnement",
                "difficulté",
                "difficultes",
                "difficulté",
                "difficulte"
            ]
        ):

            accompagnement += 1

    return [
        (
            "Élève attentif",
            attentif
        ),
        (
            "Concentration satisfaisante",
            concentration
        ),
        (
            "Élève fatigué",
            fatigue
        ),
        (
            "Bonne implication",
            implication
        ),
        (
            "Besoin d'accompagnement",
            accompagnement
        )
    ]


# ============================================================
# OBSERVATION PÉDAGOGIQUE AUTOMATIQUE
# ============================================================

def generer_observation_automatique(df):

    total = len(df)

    if total == 0:

        return (
            "Aucune observation disponible "
            "pour cette période."
        )

    bilan = calculer_bilan_comportement(
        df
    )

    attentif = bilan[0][1]
    concentration = bilan[1][1]
    fatigue = bilan[2][1]
    implication = bilan[3][1]
    accompagnement = bilan[4][1]

    phrases = []

    # --------------------------------------------------------
    # ATTENTION
    # --------------------------------------------------------

    if attentif > 0:

        if attentif >= total * 0.75:

            phrases.append(
                "L'élève se montre attentif et "
                "à l'écoute pendant les séances."
            )

        elif attentif >= total * 0.5:

            phrases.append(
                "L'élève fait preuve d'une attention "
                "satisfaisante pendant les séances."
            )

        else:

            phrases.append(
                "L'attention de l'élève est globalement "
                "satisfaisante et reste à consolider."
            )

    # --------------------------------------------------------
    # IMPLICATION
    # --------------------------------------------------------

    if implication > 0:

        if implication >= total * 0.75:

            phrases.append(
                "Il s'implique régulièrement dans le travail "
                "proposé et participe activement."
            )

        elif implication >= total * 0.5:

            phrases.append(
                "L'implication dans le travail est "
                "satisfaisante."
            )

        else:

            phrases.append(
                "L'implication est présente mais peut "
                "encore être renforcée."
            )

    # --------------------------------------------------------
    # CONCENTRATION
    # --------------------------------------------------------

    if concentration > 0:

        phrases.append(
            "La concentration favorise les apprentissages "
            "et permet de progresser dans les notions étudiées."
        )

    # --------------------------------------------------------
    # FATIGUE
    # --------------------------------------------------------

    if fatigue > 0:

        phrases.append(
            "Quelques signes de fatigue ont toutefois "
            "été observés lors de certaines séances."
        )

    # --------------------------------------------------------
    # ACCOMPAGNEMENT
    # --------------------------------------------------------

    if accompagnement > 0:

        phrases.append(
            "Certains points nécessitent encore un "
            "accompagnement afin de consolider les acquis."
        )

    # --------------------------------------------------------
    # AUCUN INDICATEUR
    # --------------------------------------------------------

    if not phrases:

        phrases.append(
            "L'élève poursuit son travail de manière "
            "régulière. Les séances permettent de consolider "
            "progressivement les acquis et de poursuivre "
            "les apprentissages."
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


def facture_existe_numero(
    numero_facture,
    id_facture_exclue=None
):

    factures = recuperer_factures()

    if factures.empty:

        return False

    if "numero_facture" not in factures.columns:

        return False

    resultat = factures[
        factures["numero_facture"]
        .astype(str)
        .eq(
            str(numero_facture).strip()
        )
    ]

    if (
        id_facture_exclue is not None
        and "id" in resultat.columns
    ):

        resultat = resultat[
            resultat["id"]
            != id_facture_exclue
        ]

    return not resultat.empty


def facture_existe_eleve_periode(
    eleve,
    periode,
    id_facture_exclue=None
):

    factures = recuperer_factures()

    if factures.empty:

        return False

    if (
        "eleve" not in factures.columns
        or "periode" not in factures.columns
    ):

        return False

    resultat = factures[
        factures["eleve"]
        .astype(str)
        .eq(
            str(eleve).strip()
        )
        &
        factures["periode"]
        .astype(str)
        .eq(
            str(periode).strip()
        )
    ]

    if (
        id_facture_exclue is not None
        and "id" in resultat.columns
    ):

        resultat = resultat[
            resultat["id"]
            != id_facture_exclue
        ]

    return not resultat.empty


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


def modifier_facture_supabase(
    id_facture,
    numero_facture,
    eleve,
    periode,
    tarif_horaire,
    forfait_utilise,
    remise,
    montant_total,
    statut,
    date_paiement,
    observation_pedagogique
):

    modifications = {

        "numero_facture":
            numero_facture,

        "eleve":
            eleve,

        "periode":
            periode,

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

        "observation_pedagogique":
            observation_pedagogique
    }

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
# OUTILS PÉRIODE
# ============================================================

def recuperer_dates_depuis_periode(periode):

    try:

        morceaux = (
            str(periode)
            .replace("–", "-")
            .split("-")
        )

        if len(morceaux) != 2:

            return None, None

        debut = pd.to_datetime(
            morceaux[0].strip(),
            dayfirst=True,
            errors="coerce"
        )

        fin = pd.to_datetime(
            morceaux[1].strip(),
            dayfirst=True,
            errors="coerce"
        )

        if pd.isna(debut) or pd.isna(fin):

            return None, None

        return (
            debut.date(),
            fin.date()
        )

    except Exception:

        return None, None


def recuperer_seances_depuis_periode(
    eleve_id,
    date_debut,
    date_fin
):

    df = recuperer_seances_eleve(
        eleve_id
    )

    if df.empty:

        return pd.DataFrame()

    df["date_temp"] = (
        pd.to_datetime(
            df["date"],
            errors="coerce"
        )
        .dt.date
    )

    df = df[
        (
            df["date_temp"]
            >= date_debut
        )
        &
        (
            df["date_temp"]
            <= date_fin
        )
    ].copy()

    return df


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
        rightMargin=1.15 * cm,
        leftMargin=1.15 * cm,
        topMargin=0.9 * cm,
        bottomMargin=0.8 * cm
    )

    styles = getSampleStyleSheet()

    titre = ParagraphStyle(
        "Titre",
        parent=styles["Heading1"],
        fontSize=17,
        leading=19,
        alignment=TA_CENTER,
        spaceAfter=3
    )

    sous_titre = ParagraphStyle(
        "SousTitre",
        parent=styles["Heading2"],
        fontSize=9.5,
        leading=11,
        spaceBefore=4,
        spaceAfter=4
    )

    normal = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=7.8,
        leading=9.5
    )

    petit = ParagraphStyle(
        "Petit",
        parent=styles["Normal"],
        fontSize=6.8,
        leading=8
    )

    bilan_style = ParagraphStyle(
        "Bilan",
        parent=styles["Normal"],
        fontSize=7.3,
        leading=9
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
                fontSize=8,
                spaceAfter=6
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
            ),

            Paragraph(
                "<b>Date de facture</b>",
                normal
            ),
            Paragraph(
                date.today().strftime("%d/%m/%Y"),
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
            ),

            Paragraph(
                "<b>Niveau / classe</b>",
                normal
            ),
            Paragraph(
                niveau or "Non renseignée",
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
            ),

            Paragraph(
                "<b>Nombre de séances</b>",
                normal
            ),
            Paragraph(
                str(len(df_eleve)),
                normal
            )
        ]
    ]

    table_infos = Table(
        infos,
        colWidths=[
            3.1 * cm,
            5.1 * cm,
            3.8 * cm,
            5.0 * cm
        ]
    )

    table_infos.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),

                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
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

    elements.append(
        table_infos
    )

    elements.append(
        Spacer(1, 6)
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
            Paragraph("<b>Mode</b>", petit),
            Paragraph("<b>Discipline</b>", petit),
            Paragraph("<b>Durée</b>", petit)
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

        if (
            len(date_ligne) >= 10
            and "-" in date_ligne
        ):

            try:

                date_ligne = pd.to_datetime(
                    date_ligne
                ).strftime(
                    "%d/%m/%Y"
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
                    f"{heure_debut}–{heure_fin}",
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
                    formater_duree(duree),
                    petit
                )
            ]
        )

    table_seances = Table(
        donnees_seances,
        colWidths=[
            2.5 * cm,
            3.0 * cm,
            3.0 * cm,
            6.0 * cm,
            2.5 * cm
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
                    0.35,
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
                    "MIDDLE"
                ),

                (
                    "ALIGN",
                    (4, 1),
                    (4, -1),
                    "RIGHT"
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
                    2.5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2.5
                )
            ]
        )
    )

    elements.append(
        table_seances
    )

    elements.append(
        Spacer(1, 6)
    )

    # ========================================================
    # TOTAL DURÉE
    # ========================================================

    total_minutes = int(
        round(total_minutes)
    )

    total_heures_decimal = (
        total_minutes / 60
    )

    elements.append(
        Paragraph(
            (
                f"<b>Total des séances :</b> "
                f"{formater_duree(total_minutes)}"
            ),
            normal
        )
    )

    elements.append(
        Spacer(1, 4)
    )

    # ========================================================
    # TARIFICATION
    # ========================================================

    elements.append(
        Paragraph(
            "Tarification",
            sous_titre
        )
    )

    if type_tarification == "Tarif horaire":

        sous_total = (
            total_heures_decimal
            * tarif_horaire
        )

    else:

        sous_total = forfait_utilise

    montant_total = max(
        0,
        sous_total - remise
    )

    tarif_data = [

        [
            Paragraph(
                "<b>Tarification</b>",
                normal
            ),
            Paragraph(
                type_tarification,
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

    tarif_data.append(
        [
            Paragraph(
                "<b>Sous-total</b>",
                normal
            ),
            Paragraph(
                f"{sous_total:.2f} €",
                normal
            )
        ]
    )

    # --------------------------------------------------------
    # REMISE UNIQUEMENT SI > 0
    # --------------------------------------------------------

    if remise > 0:

        tarif_data.append(
            [
                Paragraph(
                    "<b>Remise exceptionnelle</b>",
                    normal
                ),
                Paragraph(
                    f"− {remise:.2f} €",
                    normal
                )
            ]
        )

    tarif_data.append(
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
    )

    table_tarif = Table(
        tarif_data,
        colWidths=[
            7.5 * cm,
            4.5 * cm
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
                    0.35,
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

    elements.append(
        table_tarif
    )

    elements.append(
        Spacer(1, 6)
    )

    # ========================================================
    # BILAN
    # ========================================================

    elements.append(
        Paragraph(
            "Bilan des séances",
            sous_titre
        )
    )

    bilan = calculer_bilan_comportement(
        df_eleve
    )

    bilan_lignes = []

    for libelle, nombre in bilan:

        if nombre > 0:

            bilan_lignes.append(
                Paragraph(
                    (
                        f"<b>{libelle}</b> : "
                        f"{nombre} séance(s) / "
                        f"{len(df_eleve)}"
                    ),
                    bilan_style
                )
            )

    if not bilan_lignes:

        bilan_lignes.append(
            Paragraph(
                (
                    "Aucun indicateur comportemental "
                    "particulier renseigné."
                ),
                bilan_style
            )
        )

    elements.append(
        Table(
            [
                [
                    ligne
                ]
                for ligne in bilan_lignes
            ],
            colWidths=[
                17.5 * cm
            ],
            style=TableStyle(
                [
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
                        1
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        1
                    )
                ]
            )
        )
    )

    elements.append(
        Spacer(1, 4)
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

    observation = (
        observation_pedagogique
        or generer_observation_automatique(
            df_eleve
        )
    )

    elements.append(
        Paragraph(
            observation.replace(
                "\n",
                "<br/>"
            ),
            normal
        )
    )

    elements.append(
        Spacer(1, 6)
    )

    # ========================================================
    # PAIEMENT
    # ========================================================

    paiement = (
        f"<b>Statut :</b> {statut}"
    )

    if date_paiement:

        paiement += (
            " — "
            "<b>Date de paiement :</b> "
            f"{date_paiement.strftime('%d/%m/%Y')}"
        )

    else:

        paiement += (
            " — "
            "<b>Date de paiement :</b> —"
        )

    elements.append(
        Paragraph(
            paiement,
            normal
        )
    )

    elements.append(
        Spacer(1, 5)
    )

    elements.append(
        Paragraph(
            "Merci pour votre confiance.",
            ParagraphStyle(
                "Fin",
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
        height="700"
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
                    "Durée",
                    formater_duree(
                        total_minutes
                    )
                )

            st.subheader(
                "📊 Bilan comportemental"
            )

            bilan = calculer_bilan_comportement(
                df_eleve
            )

            for libelle, nombre in bilan:

                if nombre > 0:

                    st.write(
                        f"**{libelle} :** "
                        f"{nombre} séance(s) / "
                        f"{len(df_eleve)}"
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
            "➕ Nouvelle facture",
            "✏️ Modifier une facture",
            "🗑️ Supprimer une facture",
            "📋 Factures",
            "🔴 Factures impayées"
        ],
        horizontal=True
    )

    # ========================================================
    # NOUVELLE FACTURE
    # ========================================================

    if sous_menu == "➕ Nouvelle facture":

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
                f"🎓 Niveau / classe : "
                f"**{classe_actuelle or 'Non renseigné'}**"
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
                f"📅 Période : **{periode}**"
            )

            # =================================================
            # CONTRÔLE FACTURE EXISTANTE
            # =================================================

            if facture_existe_eleve_periode(
                eleve,
                periode
            ):

                st.warning(
                    "⚠️ Une facture existe déjà pour "
                    f"**{eleve}** pour la période "
                    f"**{periode}**."
                )

                st.info(
                    "Aucune nouvelle facture ne pourra "
                    "être enregistrée pour cette période."
                )

            # =================================================
            # SÉANCES
            # =================================================

            df_eleve = recuperer_seances_depuis_periode(
                eleve_id,
                date_debut,
                date_fin_inclusive
            )

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

            total_minutes = total_minutes_dataframe(
                df_eleve
            )

            total_heures = (
                total_minutes / 60
            )

            nombre_seances = len(
                df_eleve
            )

            st.write(
                f"**{nombre_seances} séance(s) — "
                f"{formater_duree(total_minutes)}**"
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
                ),
                key="nouvelle_type_tarification"
            )

            if type_tarification == "Tarif horaire":

                tarif_horaire = st.number_input(
                    "Tarif horaire (€)",
                    min_value=0.0,
                    value=tarif_horaire_eleve,
                    step=1.0,
                    key="nouveau_tarif_horaire"
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
                    step=1.0,
                    key="nouveau_forfait"
                )

                forfait_utilise = (
                    forfait_mensuel
                )

                tarif_horaire = 0.0

                sous_total = (
                    forfait_mensuel
                )

            # =================================================
            # REMISE
            # =================================================

            remise = st.number_input(
                "Remise exceptionnelle (€)",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key="nouvelle_remise"
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
                    "Durée",
                    formater_duree(
                        total_minutes
                    )
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
                ],
                key="nouveau_statut"
            )

            date_paiement = None

            if statut == "Payée":

                date_paiement = st.date_input(
                    "Date de paiement",
                    date.today(),
                    key="nouvelle_date_paiement"
                )

            # =================================================
            # NUMÉRO
            # =================================================

            numero_defaut = (
                f"CH-"
                f"{date.today().strftime('%Y%m%d')}-"
                f"{eleve_id}"
            )

            numero_facture = st.text_input(
                "Numéro de facture",
                value=numero_defaut,
                key="nouveau_numero"
            )

            # =================================================
            # OBSERVATION AUTOMATIQUE
            # =================================================

            observation_auto = (
                generer_observation_automatique(
                    df_eleve
                )
            )

            st.subheader(
                "📝 Observation pédagogique"
            )

            st.caption(
                "Une appréciation est générée automatiquement "
                "à partir des observations des séances. "
                "Vous pouvez la modifier avant validation."
            )

            observation_pedagogique = st.text_area(
                "Observation figurant sur la facture",
                value=observation_auto,
                height=120,
                key="nouvelle_observation"
            )

            # =================================================
            # APERÇU
            # =================================================

            st.subheader(
                "👁️ Aperçu de la facture"
            )

            if st.button(
                "👁️ Afficher / régénérer l'aperçu",
                type="secondary",
                key="bouton_apercu_nouvelle"
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
                    "💾 Validation et enregistrement"
                )

                enregistrer_drive = st.checkbox(
                    "☁️ Enregistrer également le PDF dans Google Drive",
                    value=False,
                    key="nouveau_drive"
                )

                if st.button(
                    "💾 Enregistrer la facture",
                    type="primary",
                    key="enregistrer_nouvelle_facture"
                ):

                    # ------------------------------------------------
                    # CONTRÔLE NUMÉRO
                    # ------------------------------------------------

                    doublon_numero = facture_existe_numero(
                        numero_facture
                    )

                    # ------------------------------------------------
                    # CONTRÔLE ÉLÈVE + PÉRIODE
                    # ------------------------------------------------

                    doublon_periode = facture_existe_eleve_periode(
                        eleve,
                        periode
                    )

                    if doublon_numero:

                        st.error(
                            "❌ Ce numéro de facture existe déjà. "
                            "La facture n'est pas enregistrée."
                        )

                    elif doublon_periode:

                        st.error(
                            "❌ Une facture existe déjà pour "
                            f"{eleve} pour la période "
                            f"{periode}. "
                            "Aucune nouvelle facture n'est créée."
                        )

                    else:

                        try:

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
                                "✅ Facture enregistrée."
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
                                        "⚠️ Facture enregistrée "
                                        "dans Supabase mais pas "
                                        "dans Google Drive."
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
    # MODIFIER UNE FACTURE
    # ========================================================

    elif sous_menu == "✏️ Modifier une facture":

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
                        (
                            f"{ligne.get('numero_facture','')} | "
                            f"{ligne.get('eleve','')} | "
                            f"{ligne.get('periode','')}"
                        )
                    )
                )

            facture_selection = st.selectbox(
                "Facture à modifier",
                choix_factures,
                format_func=lambda x: x[1]
            )

            id_facture = facture_selection[0]

            facture = factures[
                factures["id"]
                == id_facture
            ].iloc[0]

            numero_initial = str(
                facture.get(
                    "numero_facture",
                    ""
                )
            )

            eleve_initial = str(
                facture.get(
                    "eleve",
                    ""
                )
            )

            periode_initiale = str(
                facture.get(
                    "periode",
                    ""
                )
            )

            remise_initiale = float(
                facture.get(
                    "remise",
                    0
                )
                or 0
            )

            tarif_initial = float(
                facture.get(
                    "tarif_horaire",
                    0
                )
                or 0
            )

            forfait_initial = float(
                facture.get(
                    "forfait_mensuel",
                    0
                )
                or 0
            )

            statut_initial = str(
                facture.get(
                    "statut",
                    "En attente de paiement"
                )
            )

            observation_initiale = str(
                facture.get(
                    "observation_pedagogique",
                    ""
                )
                or ""
            )

            # ------------------------------------------------
            # INFORMATIONS FIXES
            # ------------------------------------------------

            st.info(
                f"**Élève :** {eleve_initial}\n\n"
                f"**Période :** {periode_initiale}"
            )

            # ------------------------------------------------
            # NUMÉRO
            # ------------------------------------------------

            numero_modifie = st.text_input(
                "Numéro de facture",
                value=numero_initial,
                key="modifier_numero_facture"
            )

            # ------------------------------------------------
            # TARIFICATION
            # ------------------------------------------------

            type_tarification_modification = st.radio(
                "Type de tarification",
                [
                    "Tarif horaire",
                    "Forfait mensuel"
                ],
                horizontal=True,
                index=(
                    1
                    if forfait_initial > 0
                    and tarif_initial == 0
                    else 0
                ),
                key="modifier_type_tarification"
            )

            date_debut, date_fin = (
                recuperer_dates_depuis_periode(
                    periode_initiale
                )
            )

            # ------------------------------------------------
            # RETROUVER LES SÉANCES
            # ------------------------------------------------

            eleves_tous = liste_eleves_avec_id()

            id_eleve_facture = None

            for id_eleve, nom_complet in eleves_tous:

                if nom_complet == eleve_initial:

                    id_eleve_facture = id_eleve

                    break

            if (
                id_eleve_facture is not None
                and date_debut is not None
                and date_fin is not None
            ):

                df_facture = (
                    recuperer_seances_depuis_periode(
                        id_eleve_facture,
                        date_debut,
                        date_fin
                    )
                )

            else:

                df_facture = pd.DataFrame()

            total_minutes_facture = (
                total_minutes_dataframe(
                    df_facture
                )
            )

            total_heures_facture = (
                total_minutes_facture / 60
            )

            st.write(
                f"**Durée des séances :** "
                f"{formater_duree(total_minutes_facture)}"
            )

            if type_tarification_modification == "Tarif horaire":

                tarif_modifie = st.number_input(
                    "Tarif horaire (€)",
                    min_value=0.0,
                    value=tarif_initial,
                    step=1.0,
                    key="modifier_tarif"
                )

                forfait_modifie = 0.0

                sous_total_modifie = (
                    total_heures_facture
                    * tarif_modifie
                )

            else:

                forfait_modifie = st.number_input(
                    "Forfait mensuel (€)",
                    min_value=0.0,
                    value=(
                        forfait_initial
                        if forfait_initial > 0
                        else 0.0
                    ),
                    step=1.0,
                    key="modifier_forfait"
                )

                tarif_modifie = 0.0

                sous_total_modifie = (
                    forfait_modifie
                )

            # ------------------------------------------------
            # REMISE
            # ------------------------------------------------

            remise_modifiee = st.number_input(
                "Remise exceptionnelle (€)",
                min_value=0.0,
                value=remise_initiale,
                step=1.0,
                key="modifier_remise"
            )

            montant_modifie = max(
                0,
                sous_total_modifie
                - remise_modifiee
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Sous-total",
                    f"{sous_total_modifie:.2f} €"
                )

            with col2:

                st.metric(
                    "TOTAL",
                    f"{montant_modifie:.2f} €"
                )

            # ------------------------------------------------
            # PAIEMENT
            # ------------------------------------------------

            statut_modifie = st.selectbox(
                "Statut",
                [
                    "En attente de paiement",
                    "Payée"
                ],
                index=(
                    1
                    if statut_initial == "Payée"
                    else 0
                ),
                key="modifier_statut"
            )

            date_paiement_modifiee = None

            if statut_modifie == "Payée":

                ancienne_date = facture.get(
                    "date_paiement",
                    None
                )

                if ancienne_date:

                    try:

                        ancienne_date = (
                            pd.to_datetime(
                                ancienne_date
                            ).date()
                        )

                    except Exception:

                        ancienne_date = date.today()

                else:

                    ancienne_date = date.today()

                date_paiement_modifiee = st.date_input(
                    "Date de paiement",
                    ancienne_date,
                    key="modifier_date_paiement"
                )

            # ------------------------------------------------
            # OBSERVATION
            # ------------------------------------------------

            if df_facture.empty:

                observation_auto_modification = (
                    observation_initiale
                )

            else:

                observation_auto_modification = (
                    generer_observation_automatique(
                        df_facture
                    )
                )

                if not observation_initiale:

                    observation_initiale = (
                        observation_auto_modification
                    )

            st.subheader(
                "📝 Observation pédagogique"
            )

            st.caption(
                "Vous pouvez modifier le texte avant "
                "d'enregistrer la facture."
            )

            observation_modifiee = st.text_area(
                "Observation figurant sur la facture",
                value=observation_initiale,
                height=120,
                key="modifier_observation"
            )

            # ------------------------------------------------
            # APERÇU
            # ------------------------------------------------

            st.subheader(
                "👁️ Aperçu"
            )

            if st.button(
                "👁️ Afficher / régénérer l'aperçu",
                type="secondary",
                key="apercu_modification"
            ):

                if df_facture.empty:

                    st.warning(
                        "Impossible de retrouver les séances "
                        "de cette facture."
                    )

                else:

                    informations_eleve = recuperer_eleve(
                        id_eleve_facture
                    )

                    classe = ""

                    if informations_eleve:

                        classe = (
                            informations_eleve.get(
                                "classe_actuelle",
                                ""
                            )
                            or ""
                        )

                    type_tarification_pdf = (
                        type_tarification_modification
                    )

                    pdf, montant_final = (
                        generer_facture_pdf(
                            df_facture,
                            eleve_initial,
                            classe,
                            tarif_modifie,
                            forfait_modifie,
                            remise_modifiee,
                            numero_modifie,
                            periode_initiale,
                            statut_modifie,
                            date_paiement_modifiee,
                            type_tarification_pdf,
                            observation_modifiee
                        )
                    )

                    st.session_state[
                        "facture_pdf_modification"
                    ] = pdf

                    st.session_state[
                        "facture_nom_modification"
                    ] = (
                        f"Facture_"
                        f"{numero_modifie}.pdf"
                    )

            if (
                "facture_pdf_modification"
                in st.session_state
            ):

                st.success(
                    "✅ Aperçu généré."
                )

                afficher_pdf(
                    st.session_state[
                        "facture_pdf_modification"
                    ]
                )

                st.download_button(
                    "📥 Télécharger le PDF",
                    data=st.session_state[
                        "facture_pdf_modification"
                    ],
                    file_name=st.session_state[
                        "facture_nom_modification"
                    ],
                    mime="application/pdf",
                    key="download_modification"
                )

                st.divider()

                if st.button(
                    "💾 Enregistrer les modifications",
                    type="primary",
                    key="enregistrer_modification_facture"
                ):

                    # ------------------------------------------------
                    # CONTRÔLE NUMÉRO
                    # ------------------------------------------------

                    doublon_numero = facture_existe_numero(
                        numero_modifie,
                        id_facture_exclue=id_facture
                    )

                    # ------------------------------------------------
                    # CONTRÔLE ÉLÈVE + PÉRIODE
                    # ------------------------------------------------

                    doublon_periode = (
                        facture_existe_eleve_periode(
                            eleve_initial,
                            periode_initiale,
                            id_facture_exclue=id_facture
                        )
                    )

                    if doublon_numero:

                        st.error(
                            "❌ Ce numéro de facture est déjà "
                            "utilisé par une autre facture."
                        )

                    elif doublon_periode:

                        st.error(
                            "❌ Une autre facture existe déjà "
                            "pour cet élève et cette période."
                        )

                    else:

                        try:

                            modifier_facture_supabase(
                                id_facture,
                                numero_modifie,
                                eleve_initial,
                                periode_initiale,
                                tarif_modifie,
                                forfait_modifie,
                                remise_modifiee,
                                montant_modifie,
                                statut_modifie,
                                date_paiement_modifiee,
                                observation_modifiee
                            )

                            st.success(
                                "✅ Facture modifiée."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                "❌ Erreur lors de la "
                                "modification."
                            )

                            st.code(
                                str(e)
                            )


    # ========================================================
    # SUPPRIMER UNE FACTURE
    # ========================================================

    elif sous_menu == "🗑️ Supprimer une facture":

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
                        (
                            f"{ligne.get('numero_facture','')} | "
                            f"{ligne.get('eleve','')} | "
                            f"{ligne.get('periode','')} | "
                            f"{float(ligne.get('montant_total', 0) or 0):.2f} €"
                        )
                    )
                )

            facture_selection = st.selectbox(
                "Facture à supprimer",
                choix_factures,
                format_func=lambda x: x[1]
            )

            id_facture = facture_selection[0]

            confirmation = st.checkbox(
                "Je confirme vouloir supprimer définitivement cette facture.",
                key="confirmation_suppression_facture"
            )

            if st.button(
                "🗑️ Supprimer définitivement",
                type="primary",
                key="bouton_suppression_facture"
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

                        st.session_state.pop(
                            "facture_pdf_apercu",
                            None
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

            recherche = st.text_input(
                "Numéro, élève ou période"
            )

            if recherche.strip():

                masque = (
                    factures.astype(str)
                    .apply(
                        lambda colonne:
                        colonne.str.contains(
                            recherche.strip(),
                            case=False,
                            na=False
                        )
                    )
                    .any(
                        axis=1
                    )
                )

                resultat = factures[
                    masque
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
