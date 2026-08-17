import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import calendar


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cours Hercule",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# CONNEXION SUPABASE
# ============================================================

@st.cache_resource
def connexion_supabase():

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


supabase = connexion_supabase()


# ============================================================
# PARAMETRES
# ============================================================

TARIF_HORAIRE = float(
    st.secrets.get("TARIF_HORAIRE", 25)
)


# ============================================================
# CONNEXION
# ============================================================

if "connecte" not in st.session_state:
    st.session_state.connecte = False


if not st.session_state.connecte:

    st.title("📚 Cours Hercule")

    st.subheader("Espace professeur")

    mot_de_passe = st.text_input(
        "Mot de passe",
        type="password"
    )

    if st.button("Se connecter"):

        if mot_de_passe == st.secrets["mot_de_passe"]:

            st.session_state.connecte = True
            st.rerun()

        else:

            st.error("Mot de passe incorrect.")

    st.stop()


# ============================================================
# FONCTIONS ELEVES
# ============================================================

def recuperer_eleves():

    resultat = (
        supabase
        .table("eleves")
        .select("*")
        .order("nom")
        .execute()
    )

    return resultat.data or []


def ajouter_eleve(
    nom,
    prenom,
    telephone,
    email,
    responsable,
    notes
):

    supabase.table("eleves").insert({

        "nom": nom,
        "prenom": prenom,
        "telephone": telephone,
        "email": email,
        "responsable": responsable,
        "notes": notes

    }).execute()


def modifier_eleve(
    id_eleve,
    nom,
    prenom,
    telephone,
    email,
    responsable,
    notes
):

    supabase.table("eleves").update({

        "nom": nom,
        "prenom": prenom,
        "telephone": telephone,
        "email": email,
        "responsable": responsable,
        "notes": notes

    }).eq(
        "id",
        id_eleve
    ).execute()


# ============================================================
# FONCTIONS SEANCES
# ============================================================

def recuperer_seances():

    resultat = (
        supabase
        .table("seances")
        .select("*")
        .order("date", desc=True)
        .execute()
    )

    return resultat.data or []


def ajouter_seance(
    date_seance,
    heure_debut,
    heure_fin,
    eleve,
    disciplines,
    contenu,
    observations
):

    debut = datetime.strptime(
        heure_debut,
        "%H:%M"
    )

    fin = datetime.strptime(
        heure_fin,
        "%H:%M"
    )

    duree = int(
        (fin - debut).total_seconds() / 60
    )

    if duree <= 0:

        raise ValueError(
            "L'heure de fin doit être après l'heure de début."
        )

    supabase.table("seances").insert({

        "date": str(date_seance),
        "heure_debut": heure_debut,
        "heure_fin": heure_fin,
        "duree": duree,
        "eleve": eleve,
        "disciplines": ", ".join(disciplines),
        "contenu": contenu,
        "observations": observations

    }).execute()


def modifier_seance(
    id_seance,
    date_seance,
    heure_debut,
    heure_fin,
    eleve,
    disciplines,
    contenu,
    observations
):

    debut = datetime.strptime(
        heure_debut,
        "%H:%M"
    )

    fin = datetime.strptime(
        heure_fin,
        "%H:%M"
    )

    duree = int(
        (fin - debut).total_seconds() / 60
    )

    if duree <= 0:

        raise ValueError(
            "L'heure de fin doit être après l'heure de début."
        )

    supabase.table("seances").update({

        "date": str(date_seance),
        "heure_debut": heure_debut,
        "heure_fin": heure_fin,
        "duree": duree,
        "eleve": eleve,
        "disciplines": ", ".join(disciplines),
        "contenu": contenu,
        "observations": observations

    }).eq(
        "id",
        id_seance
    ).execute()


def supprimer_seance(id_seance):

    supabase.table("seances").delete().eq(
        "id",
        id_seance
    ).execute()


# ============================================================
# OBSERVATION AUTOMATIQUE
# ============================================================

def generer_observation(seances):

    if not seances:

        return (
            "Aucune séance enregistrée sur la période."
        )

    nombre = len(seances)

    duree_totale = sum(
        int(
            s.get(
                "duree",
                0
            ) or 0
        )
        for s in seances
    )

    observations = []

    for s in seances:

        texte = s.get(
            "observations",
            ""
        )

        if texte:

            observations.append(
                texte.strip()
            )

    texte_obs = " ".join(
        observations
    ).lower()

    phrases = []


    # Participation

    if "bonne participation" in texte_obs:

        phrases.append(
            "L'élève participe activement aux séances."
        )

    elif "participation" in texte_obs:

        phrases.append(
            "La participation est à encourager."
        )


    # Compréhension

    if (
        "difficulté de compréhension"
        in texte_obs
        or
        "difficultés de compréhension"
        in texte_obs
    ):

        phrases.append(
            "Des difficultés de compréhension ont été observées."
        )

    elif (
        "bonne compréhension"
        in texte_obs
        or
        "compréhension satisfaisante"
        in texte_obs
    ):

        phrases.append(
            "La compréhension est satisfaisante."
        )


    # Travail

    if "travail sérieux" in texte_obs:

        phrases.append(
            "Le travail fourni est sérieux."
        )

    if "manque de travail" in texte_obs:

        phrases.append(
            "Le travail personnel doit être renforcé."
        )


    # Progrès

    if "progrès" in texte_obs:

        phrases.append(
            "Des progrès sont constatés."
        )

    if "progression" in texte_obs:

        phrases.append(
            "Une progression est observée."
        )


    # Autonomie

    if "autonomie" in texte_obs:

        phrases.append(
            "L'autonomie est en cours de développement."
        )


    # Observation générale

    debut = (
        f"{nombre} séance(s) ont été réalisées, "
        f"pour une durée totale de "
        f"{duree_totale} minutes."
    )

    if not phrases:

        phrases.append(
            "Le travail se poursuit régulièrement."
        )

    return (
        debut + " "
        + " ".join(phrases)
    )


# ============================================================
# FILTRAGE DES SEANCES
# ============================================================

def filtrer_seances(
    seances,
    eleve,
    date_debut,
    date_fin
):

    resultat = []

    for s in seances:

        if s.get("eleve") != eleve:

            continue

        try:

            d = datetime.strptime(
                str(s.get("date")),
                "%Y-%m-%d"
            ).date()

        except:

            continue

        if date_debut <= d <= date_fin:

            resultat.append(s)

    return resultat


# ============================================================
# CREATION FACTURE PDF
# ============================================================

def creer_facture_pdf(
    eleve,
    seances,
    date_debut,
    date_fin,
    tarif
):

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    largeur, hauteur = A4

    y = hauteur - 60


    # Titre

    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawString(
        50,
        y,
        "COURS HERCULE"
    )

    y -= 40


    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    pdf.drawString(
        50,
        y,
        "FACTURE"
    )

    y -= 40


    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        50,
        y,
        f"Élève : {eleve}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        "Période : "
        f"{date_debut.strftime('%d/%m/%Y')} "
        f"au "
        f"{date_fin.strftime('%d/%m/%Y')}"
    )

    y -= 35


    # Entêtes

    pdf.setFont(
        "Helvetica-Bold",
        10
    )

    pdf.drawString(
        50,
        y,
        "Date"
    )

    pdf.drawString(
        130,
        y,
        "Durée"
    )

    pdf.drawString(
        200,
        y,
        "Discipline"
    )

    pdf.drawString(
        400,
        y,
        "Montant"
    )

    y -= 20


    pdf.setFont(
        "Helvetica",
        10
    )

    total_minutes = 0


    # Séances

    for s in seances:

        minutes = int(
            s.get(
                "duree",
                0
            ) or 0
        )

        total_minutes += minutes

        montant = (
            minutes / 60
        ) * tarif


        pdf.drawString(
            50,
            y,
            str(
                s.get(
                    "date",
                    ""
                )
            )
        )

        pdf.drawString(
            130,
            y,
            f"{minutes} min"
        )

        pdf.drawString(
            200,
            y,
            str(
                s.get(
                    "disciplines",
                    ""
                )
            )[:30]
        )

        pdf.drawString(
            400,
            y,
            f"{montant:.2f} €"
        )

        y -= 18


        if y < 80:

            pdf.showPage()

            y = hauteur - 60


    # Total

    total = (
        total_minutes / 60
    ) * tarif

    y -= 20


    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        50,
        y,
        f"Total : {total:.2f} €"
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        f"Durée totale : {total_minutes} minutes"
    )

    pdf.save()

    buffer.seek(0)

    return buffer


# ============================================================
# MENU
# ============================================================

st.sidebar.title(
    "📚 Cours Hercule"
)

menu = st.sidebar.radio(

    "Menu",

    [
        "📚 Gestion des séances",
        "👨‍🎓 Ajouter un élève",
        "✏️ Modifier un élève",
        "📖 Cahier de texte",
        "✏️ Modifier une séance",
        "📊 Bilan",
        "🧾 Facturation"
    ]
)


# ============================================================
# RECUPERATION DES DONNEES
# ============================================================

eleves = recuperer_eleves()

seances = recuperer_seances()

noms_eleves = [

    (
        e.get("prenom", "")
        + " "
        + e.get("nom", "")
    ).strip()

    for e in eleves

]


# ============================================================
# AJOUTER ELEVE
# ============================================================

if menu == "👨‍🎓 Ajouter un élève":

    st.title(
        "👨‍🎓 Ajouter un élève"
    )

    with st.form(
        "ajouter_eleve"
    ):

        prenom = st.text_input(
            "Prénom *"
        )

        nom = st.text_input(
            "Nom *"
        )

        telephone = st.text_input(
            "Téléphone"
        )

        email = st.text_input(
            "E-mail"
        )

        responsable = st.text_input(
            "Responsable légal"
        )

        notes = st.text_area(
            "Notes"
        )

        envoyer = st.form_submit_button(
            "➕ Ajouter l'élève"
        )

        if envoyer:

            if not prenom or not nom:

                st.error(
                    "Le prénom et le nom sont obligatoires."
                )

            else:

                try:

                    ajouter_eleve(
                        nom,
                        prenom,
                        telephone,
                        email,
                        responsable,
                        notes
                    )

                    st.success(
                        "Élève ajouté avec succès."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Erreur : {e}"
                    )


# ============================================================
# MODIFIER ELEVE
# ============================================================

elif menu == "✏️ Modifier un élève":

    st.title(
        "✏️ Modifier un élève"
    )

    if not eleves:

        st.info(
            "Aucun élève enregistré."
        )

    else:

        choix = st.selectbox(

            "Élève",

            range(
                len(eleves)
            ),

            format_func=lambda i:

                f"{eleves[i].get('prenom','')} "
                f"{eleves[i].get('nom','')}"
        )

        eleve = eleves[choix]


        with st.form(
            "modifier_eleve"
        ):

            prenom = st.text_input(
                "Prénom",
                value=eleve.get(
                    "prenom",
                    ""
                )
            )

            nom = st.text_input(
                "Nom",
                value=eleve.get(
                    "nom",
                    ""
                )
            )

            telephone = st.text_input(
                "Téléphone",
                value=eleve.get(
                    "telephone",
                    ""
                )
            )

            email = st.text_input(
                "E-mail",
                value=eleve.get(
                    "email",
                    ""
                )
            )

            responsable = st.text_input(
                "Responsable légal",
                value=eleve.get(
                    "responsable",
                    ""
                )
            )

            notes = st.text_area(
                "Notes",
                value=eleve.get(
                    "notes",
                    ""
                )
            )

            modifier = st.form_submit_button(
                "💾 Enregistrer les modifications"
            )


            if modifier:

                try:

                    modifier_eleve(
                        eleve["id"],
                        nom,
                        prenom,
                        telephone,
                        email,
                        responsable,
                        notes
                    )

                    st.success(
                        "Élève modifié."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Erreur : {e}"
                    )


# ============================================================
# GESTION DES SEANCES
# ============================================================

elif menu == "📚 Gestion des séances":

    st.title(
        "📚 Gestion des séances"
    )

    if not noms_eleves:

        st.warning(
            "Ajoute d'abord un élève."
        )

    else:

        disciplines_disponibles = [

            "Mathématiques",
            "Physique",
            "Informatique",
            "Français",
            "Anglais",
            "Technologie",
            "Culture générale"

        ]


        with st.form(
            "nouvelle_seance"
        ):

            eleve = st.selectbox(
                "Élève",
                noms_eleves
            )

            date_seance = st.date_input(
                "Date",
                value=date.today()
            )


            col1, col2 = st.columns(2)


            with col1:

                heure_debut = st.time_input(
                    "Heure de début"
                )


            with col2:

                heure_fin = st.time_input(
                    "Heure de fin"
                )


            disciplines = st.multiselect(
                "Discipline(s)",
                disciplines_disponibles
            )


            contenu = st.text_area(
                "Contenu de la séance",
                placeholder=(
                    "Exemple : "
                    "Théorème de Pythagore, "
                    "exercices d'application..."
                )
            )


            observations = st.text_area(
                "Observations",
                placeholder=(
                    "Exemple : "
                    "Bonne participation + "
                    "difficulté de compréhension"
                )
            )


            enregistrer = st.form_submit_button(
                "💾 Enregistrer la séance"
            )


            if enregistrer:

                if not disciplines:

                    st.error(
                        "Sélectionne au moins une discipline."
                    )

                elif not contenu:

                    st.error(
                        "Le contenu est obligatoire."
                    )

                else:

                    try:

                        ajouter_seance(
                            date_seance,
                            heure_debut.strftime(
                                "%H:%M"
                            ),
                            heure_fin.strftime(
                                "%H:%M"
                            ),
                            eleve,
                            disciplines,
                            contenu,
                            observations
                        )

                        st.success(
                            "Séance enregistrée."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Erreur : {e}"
                        )


# ============================================================
# CAHIER DE TEXTE
# ============================================================

elif menu == "📖 Cahier de texte":

    st.title(
        "📖 Cahier de texte"
    )

    if noms_eleves:

        eleve = st.selectbox(
            "Élève",
            noms_eleves
        )


        seances_eleve = [

            s for s in seances

            if s.get(
                "eleve"
            ) == eleve

        ]


        for s in seances_eleve:

            with st.expander(

                f"📅 {s.get('date')} — "
                f"{s.get('heure_debut')} → "
                f"{s.get('heure_fin')}"

            ):

                st.write(
                    "**Discipline :**",
                    s.get(
                        "disciplines",
                        ""
                    )
                )

                st.write(
                    "**Contenu :**",
                    s.get(
                        "contenu",
                        ""
                    )
                )

                st.write(
                    "**Observations :**",
                    s.get(
                        "observations",
                        ""
                    )
                )

    else:

        st.info(
            "Aucun élève."
        )


# ============================================================
# MODIFIER SEANCE
# ============================================================

elif menu == "✏️ Modifier une séance":

    st.title(
        "✏️ Modifier une séance"
    )

    if not seances:

        st.info(
            "Aucune séance enregistrée."
        )

    else:

        index = st.selectbox(

            "Séance",

            range(
                len(seances)
            ),

            format_func=lambda i:

                f"{seances[i].get('date')} - "
                f"{seances[i].get('eleve')}"
        )


        s = seances[index]


        disciplines_disponibles = [

            "Mathématiques",
            "Physique",
            "Informatique",
            "Français",
            "Anglais",
            "Technologie",
            "Culture générale"

        ]


        try:

            date_initiale = datetime.strptime(

                str(
                    s.get(
                        "date"
                    )
                ),

                "%Y-%m-%d"

            ).date()

        except:

            date_initiale = date.today()


        with st.form(
            "modifier_seance"
        ):

            eleve = st.selectbox(
                "Élève",
                noms_eleves,
                index=(
                    noms_eleves.index(
                        s.get("eleve")
                    )
                    if
                    s.get("eleve")
                    in noms_eleves
                    else 0
                )
            )


            date_seance = st.date_input(
                "Date",
                value=date_initiale
            )


            heure_debut = st.time_input(

                "Heure de début",

                value=datetime.strptime(

                    s.get(
                        "heure_debut",
                        "17:00"
                    ),

                    "%H:%M"

                ).time()
            )


            heure_fin = st.time_input(

                "Heure de fin",

                value=datetime.strptime(

                    s.get(
                        "heure_fin",
                        "18:00"
                    ),

                    "%H:%M"

                ).time()
            )


            anciennes_disciplines = [

                x.strip()

                for x in s.get(
                    "disciplines",
                    ""
                ).split(",")

                if x.strip()

            ]


            disciplines = st.multiselect(

                "Disciplines",

                disciplines_disponibles,

                default=anciennes_disciplines

            )


            contenu = st.text_area(

                "Contenu",

                value=s.get(
                    "contenu",
                    ""
                )

            )


            observations = st.text_area(

                "Observations",

                value=s.get(
                    "observations",
                    ""
                )

            )


            modifier = st.form_submit_button(
                "💾 Modifier"
            )

            supprimer = st.form_submit_button(
                "🗑️ Supprimer"
            )


            if modifier:

                try:

                    modifier_seance(

                        s["id"],

                        date_seance,

                        heure_debut.strftime(
                            "%H:%M"
                        ),

                        heure_fin.strftime(
                            "%H:%M"
                        ),

                        eleve,

                        disciplines,

                        contenu,

                        observations

                    )

                    st.success(
                        "Séance modifiée."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Erreur : {e}"
                    )


            if supprimer:

                supprimer_seance(
                    s["id"]
                )

                st.success(
                    "Séance supprimée."
                )

                st.rerun()


# ============================================================
# BILAN
# ============================================================

elif menu == "📊 Bilan":

    st.title(
        "📊 Bilan de l'élève"
    )

    if noms_eleves:

        eleve = st.selectbox(
            "Élève",
            noms_eleves
        )


        col1, col2 = st.columns(2)


        with col1:

            date_debut = st.date_input(
                "Du",
                value=date.today().replace(
                    day=1
                )
            )


        with col2:

            date_fin = st.date_input(
                "Au",
                value=date.today()
            )


        donnees = filtrer_seances(

            seances,

            eleve,

            date_debut,

            date_fin

        )


        st.metric(
            "Nombre de séances",
            len(donnees)
        )


        duree = sum(

            int(
                s.get(
                    "duree",
                    0
                ) or 0
            )

            for s in donnees

        )


        st.metric(
            "Durée totale",
            f"{duree} min"
        )


        st.subheader(
            "📝 Observation générée automatiquement"
        )


        observation = generer_observation(
            donnees
        )


        observation_modifiable = st.text_area(

            "Observation",

            value=observation,

            height=180

        )


        st.download_button(

            "📥 Télécharger l'observation",

            observation_modifiable,

            file_name=(
                f"bilan_"
                f"{eleve.replace(' ', '_')}.txt"
            )

        )


        st.subheader(
            "📚 Séances de la période"
        )


        for s in donnees:

            st.write(

                f"**{s.get('date')}** — "
                f"{s.get('disciplines')} — "
                f"{s.get('duree')} min"

            )


            if s.get(
                "observations"
            ):

                st.caption(
                    s.get(
                        "observations"
                    )
                )


    else:

        st.info(
            "Aucun élève."
        )


# ============================================================
# FACTURATION
# ============================================================

elif menu == "🧾 Facturation":

    st.title(
        "🧾 Facturation"
    )


    if not noms_eleves:

        st.info(
            "Ajoute d'abord un élève."
        )

    else:

        # ====================================================
        # ELEVE
        # ====================================================

        eleve = st.selectbox(
            "👨‍🎓 Élève",
            noms_eleves
        )


        # ====================================================
        # PERIODE
        # Mensuelle = choix par défaut
        # ====================================================

        periode = st.selectbox(

            "📅 Période de facturation",

            [
                "Mensuelle",
                "Hebdomadaire",
                "Personnalisée",
                "Toutes les séances"
            ],

            index=0

        )


        aujourd_hui = date.today()


        # ====================================================
        # MENSUELLE
        # ====================================================

        if periode == "Mensuelle":

            st.info(
                "📅 Facturation mensuelle"
            )


            col1, col2 = st.columns(2)


            with col1:

                annee = st.number_input(

                    "Année",

                    min_value=2020,

                    max_value=2100,

                    value=aujourd_hui.year,

                    step=1

                )


            with col2:

                mois = st.selectbox(

                    "Mois",

                    list(range(1, 13)),

                    index=aujourd_hui.month - 1,

                    format_func=lambda x:

                        [

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


            date_debut = date(

                int(annee),

                mois,

                1

            )


            dernier_jour = calendar.monthrange(

                int(annee),

                mois

            )[1]


            date_fin = date(

                int(annee),

                mois,

                dernier_jour

            )


        # ====================================================
        # HEBDOMADAIRE
        # ====================================================

        elif periode == "Hebdomadaire":

            st.info(
                "📅 Facturation hebdomadaire"
            )


            date_reference = st.date_input(

                "Date de référence",

                value=aujourd_hui

            )


            date_debut = (

                date_reference

                -

                timedelta(

                    days=date_reference.weekday()

                )

            )


            date_fin = (

                date_debut

                +

                timedelta(

                    days=6

                )

            )


        # ====================================================
        # PERSONNALISEE
        # ====================================================

        elif periode == "Personnalisée":

            st.info(
                "📅 Période personnalisée"
            )


            col1, col2 = st.columns(2)


            with col1:

                date_debut = st.date_input(

                    "Date de début",

                    value=aujourd_hui.replace(
                        day=1
                    )

                )


            with col2:

                date_fin = st.date_input(

                    "Date de fin",

                    value=aujourd_hui

                )


        # ====================================================
        # TOUTES LES SEANCES
        # ====================================================

        else:

            st.info(
                "📋 Toutes les séances de l'élève"
            )


            dates = []


            for s in seances:

                if s.get(
                    "eleve"
                ) == eleve:

                    try:

                        dates.append(

                            datetime.strptime(

                                str(
                                    s.get(
                                        "date"
                                    )
                                ),

                                "%Y-%m-%d"

                            ).date()

                        )

                    except:

                        pass


            if dates:

                date_debut = min(
                    dates
                )

                date_fin = max(
                    dates
                )

            else:

                date_debut = aujourd_hui

                date_fin = aujourd_hui


        # ====================================================
        # AFFICHAGE PERIODE
        # ====================================================

        st.write(
            f"**Période sélectionnée :** "
            f"{date_debut.strftime('%d/%m/%Y')} "
            f"→ "
            f"{date_fin.strftime('%d/%m/%Y')}"
        )


        # ====================================================
        # RECUPERATION SEANCES
        # ====================================================

        donnees = filtrer_seances(

            seances,

            eleve,

            date_debut,

            date_fin

        )


        st.divider()


        # ====================================================
        # RESULTATS
        # ====================================================

        if donnees:

            st.subheader(
                "📋 Résumé de la facturation"
            )


            total_minutes = sum(

                int(

                    s.get(
                        "duree",
                        0
                    ) or 0

                )

                for s in donnees

            )


            total_heures = (

                total_minutes

                / 60

            )


            montant = (

                total_heures

                * TARIF_HORAIRE

            )


            col1, col2, col3 = st.columns(3)


            with col1:

                st.metric(

                    "Séances",

                    len(donnees)

                )


            with col2:

                st.metric(

                    "Durée",

                    f"{total_minutes} min"

                )


            with col3:

                st.metric(

                    "Montant",

                    f"{montant:.2f} €"

                )


            st.divider()


            # =================================================
            # DETAIL
            # =================================================

            st.subheader(
                "📚 Détail des séances"
            )


            for s in donnees:

                minutes = int(

                    s.get(
                        "duree",
                        0
                    ) or 0

                )


                prix = (

                    minutes

                    / 60

                ) * TARIF_HORAIRE


                st.write(

                    f"📅 **{s.get('date')}**  "
                    f"| {minutes} min  "
                    f"| {s.get('disciplines')}  "
                    f"| **{prix:.2f} €**"

                )


            st.divider()


            # =================================================
            # OBSERVATION
            # =================================================

            st.subheader(
                "📝 Observation / bilan"
            )


            observation = generer_observation(
                donnees
            )


            observation = st.text_area(

                "Observation générée automatiquement",

                value=observation,

                height=160

            )


            st.divider()


            # =================================================
            # FACTURE
            # =================================================

            st.subheader(
                "📄 Facture"
            )


            pdf = creer_facture_pdf(

                eleve,

                donnees,

                date_debut,

                date_fin,

                TARIF_HORAIRE

            )


            st.download_button(

                "📥 Télécharger la facture PDF",

                data=pdf,

                file_name=(

                    "facture_"

                    + eleve.replace(
                        " ",
                        "_"
                    )

                    + "_"

                    + str(
                        date_debut
                    )

                    + "_"

                    + str(
                        date_fin
                    )

                    + ".pdf"

                ),

                mime="application/pdf"

            )


        else:

            st.warning(

                "Aucune séance trouvée "
                "pour cette période."

            )


# ============================================================
# DECONNEXION
# ============================================================

st.sidebar.divider()


if st.sidebar.button(
    "🚪 Se déconnecter"
):

    st.session_state.connecte = False

    st.rerun()
