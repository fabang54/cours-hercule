import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cours Hercule",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# OBSERVATIONS DISPONIBLES
# ============================================================

OBSERVATIONS = [
    "Élève attentif",
    "Élève très attentif",
    "Bonne participation",
    "Participation satisfaisante",
    "Élève fatigué",
    "Élève peu concentré",
    "Bonne compréhension",
    "Difficultés de compréhension",
    "Progrès constatés",
    "Travail sérieux",
    "Manque de travail",
    "Bonne autonomie",
    "Doit encore gagner en autonomie"
]


# ============================================================
# FONCTION DE GÉNÉRATION DU BILAN
# ============================================================

def generer_bilan(observations, total_seances):

    compteurs = {}

    for liste_observations in observations:

        for observation in liste_observations:

            if observation not in compteurs:
                compteurs[observation] = 0

            compteurs[observation] += 1


    # --------------------------------------------------------
    # COMPTEURS
    # --------------------------------------------------------

    attentif = compteurs.get(
        "Élève attentif", 0
    )

    tres_attentif = compteurs.get(
        "Élève très attentif", 0
    )

    participation = compteurs.get(
        "Bonne participation", 0
    )

    participation_satisfaisante = compteurs.get(
        "Participation satisfaisante", 0
    )

    fatigue = compteurs.get(
        "Élève fatigué", 0
    )

    peu_concentre = compteurs.get(
        "Élève peu concentré", 0
    )

    bonne_comprehension = compteurs.get(
        "Bonne compréhension", 0
    )

    difficultes = compteurs.get(
        "Difficultés de compréhension", 0
    )

    progres = compteurs.get(
        "Progrès constatés", 0
    )

    travail_serieux = compteurs.get(
        "Travail sérieux", 0
    )

    manque_travail = compteurs.get(
        "Manque de travail", 0
    )

    autonomie = compteurs.get(
        "Bonne autonomie", 0
    )

    manque_autonomie = compteurs.get(
        "Doit encore gagner en autonomie", 0
    )


    # --------------------------------------------------------
    # PHRASES
    # --------------------------------------------------------

    phrases = []


    # ATTENTION

    attention = attentif + tres_attentif

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


    if peu_concentre >= total_seances * 0.5:

        phrases.append(
            "La concentration reste cependant "
            "à renforcer."
        )


    # PARTICIPATION

    participation_totale = (
        participation +
        participation_satisfaisante
    )

    if participation_totale >= total_seances * 0.875:

        phrases.append(
            "La participation est très active "
            "et régulière."
        )

    elif participation_totale >= total_seances * 0.5:

        phrases.append(
            "L'élève participe de manière satisfaisante "
            "aux séances."
        )


    # COMPRÉHENSION

    if bonne_comprehension >= total_seances * 0.5:

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


    # PROGRÈS

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


    # TRAVAIL

    if travail_serieux >= total_seances * 0.5:

        phrases.append(
            "L'élève fait preuve de sérieux et "
            "d'implication dans son travail."
        )

    if manque_travail >= total_seances * 0.5:

        phrases.append(
            "Un travail personnel plus régulier "
            "permettrait de consolider les acquis."
        )


    # AUTONOMIE

    if autonomie >= total_seances * 0.5:

        phrases.append(
            "L'élève gagne progressivement "
            "en autonomie."
        )

    if manque_autonomie >= total_seances * 0.5:

        phrases.append(
            "L'autonomie doit encore être développée."
        )


    # FATIGUE

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


    # AUCUNE OBSERVATION

    if not phrases:

        phrases.append(
            "La période s'est déroulée normalement. "
            "Le travail se poursuit régulièrement."
        )


    bilan = " ".join(phrases)

    return compteurs, bilan


# ============================================================
# INTERFACE
# ============================================================

st.title("📚 Cours Hercule")

st.header("📋 Génération du bilan élève")


# ============================================================
# NOM DE L'ÉLÈVE
# ============================================================

nom = st.text_input(
    "👨‍🎓 Nom et prénom de l'élève",
    placeholder="Ex. Nino Dupont"
)


# ============================================================
# NOMBRE DE SÉANCES
# ============================================================

total_seances = st.number_input(
    "📅 Nombre de séances",
    min_value=1,
    max_value=50,
    value=8,
    step=1
)


st.divider()


# ============================================================
# OBSERVATIONS DE CHAQUE SÉANCE
# ============================================================

st.subheader("📝 Observations des séances")

observations_seances = []


for numero in range(1, total_seances + 1):

    choix = st.multiselect(
        f"Séance {numero}",
        OBSERVATIONS,
        key=f"observation_{numero}",
        placeholder="Choisir une ou plusieurs observations"
    )

    observations_seances.append(choix)


st.divider()


# ============================================================
# BOUTON GÉNÉRER
# ============================================================

if st.button(
    "📊 Générer le bilan",
    type="primary"
):

    if not nom.strip():

        st.error(
            "Veuillez indiquer le nom de l'élève."
        )

    else:

        compteurs, bilan = generer_bilan(
            observations_seances,
            total_seances
        )


        # ====================================================
        # STATISTIQUES
        # ====================================================

        st.subheader(
            "📊 Bilan de la période"
        )

        st.write(
            f"**Élève :** {nom}"
        )

        st.write(
            f"**Nombre de séances :** {total_seances}"
        )


        for observation, nombre in compteurs.items():

            st.write(
                f"**{observation} :** "
                f"{nombre} / {total_seances} séances"
            )


        st.divider()


        # ====================================================
        # OBSERVATION AUTOMATIQUE
        # ====================================================

        st.subheader(
            "📝 Observation générale"
        )

        st.info(bilan)


        # ====================================================
        # MODIFICATION MANUELLE
        # ====================================================

        st.subheader(
            "✏️ Modifier le bilan si nécessaire"
        )

        bilan_modifie = st.text_area(
            "Texte qui apparaîtra sur la facture",
            value=bilan,
            height=150
        )


        st.success(
            "Le bilan est prêt à être intégré à la facture."
        )
