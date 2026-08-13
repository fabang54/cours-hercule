import streamlit as st

st.set_page_config(
    page_title="Cours Hercule",
    page_icon="📚",
    layout="wide"
)

# =========================
# EN-TÊTE
# =========================

st.title("📚 Cours Hercule")

st.subheader(
    "Cours particuliers de mathématiques, physique et informatique"
)

st.write(
    """
    **Comprendre • Progresser • Réussir**
    
    Un accompagnement personnalisé adapté au niveau,
    aux objectifs et aux besoins de chaque élève.
    """
)

st.divider()

# =========================
# MATIÈRES
# =========================

st.header("Nos matières")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📐 Mathématiques")
    st.write(
        """
        Collège, lycée et enseignement supérieur.

        • Compréhension du cours  
        • Exercices et méthodes  
        • Préparation aux contrôles et examens
        """
    )

with col2:
    st.subheader("⚛️ Physique")
    st.write(
        """
        • Compréhension des notions  
        • Méthodes de résolution  
        • Exercices d'application
        """
    )

with col3:
    st.subheader("💻 Informatique")
    st.write(
        """
        • Python  
        • SQL  
        • Bases de données  
        • Algorithmique
        """
    )

st.divider()

# =========================
# MODALITÉS
# =========================

st.header("Nos modalités")

col1, col2 = st.columns(2)

with col1:
    st.subheader("💻 Cours à distance")
    st.write(
        """
        Cours en visioconférence depuis votre domicile,
        avec accompagnement personnalisé.
        """
    )

with col2:
    st.subheader("🏠 Cours en présentiel")
    st.write(
        """
        Cours en présentiel selon les possibilités
        géographiques.
        """
    )

st.divider()

# =========================
# POUR QUI ?
# =========================

st.header("Un accompagnement adapté")

st.write(
    """
    Les séances peuvent répondre à différents objectifs :

    • reprendre les bases ;  
    • comprendre une notion difficile ;  
    • progresser en autonomie ;  
    • préparer un contrôle ;  
    • préparer un examen ;  
    • bénéficier d'un suivi régulier.
    """
)

st.divider()

# =========================
# CONTACT
# =========================

st.header("📞 Contact")

st.write(
    """
    Vous souhaitez obtenir des informations ou organiser
    un premier échange ?
    """
)

if "contact_envoye" not in st.session_state:
    st.session_state.contact_envoye = False

if st.session_state.contact_envoye:

    st.success(
        "Votre demande a bien été envoyée. Merci !"
    )

    if st.button("Nouvelle demande"):
        st.session_state.contact_envoye = False
        st.rerun()

else:

    with st.form("formulaire_contact"):

        nom_parent = st.text_input(
            "Nom du parent"
        )

        email = st.text_input(
            "Adresse e-mail"
        )

        telephone = st.text_input(
            "Téléphone (facultatif)"
        )

        nom_eleve = st.text_input(
            "Nom de l'élève"
        )

        niveau = st.selectbox(
            "Niveau de l'élève",
            [
                "Collège",
                "Lycée",
                "Enseignement supérieur",
                "Autre"
            ]
        )

        matieres = st.multiselect(
            "Matière(s) souhaitée(s)",
            [
                "Mathématiques",
                "Physique",
                "Informatique"
            ]
        )

        modalite = st.selectbox(
            "Modalité souhaitée",
            [
                "Distanciel",
                "Présentiel",
                "Je ne sais pas encore"
            ]
        )

        message = st.text_area(
            "Votre demande"
        )

        envoyer = st.form_submit_button(
            "Envoyer la demande"
        )

        if envoyer:

            if nom_parent and email and nom_eleve and matieres:

                # Ici, nous ajouterons ensuite
                # l'enregistrement dans contacts.csv

                st.session_state.contact_envoye = True
                st.rerun()

            else:

                st.error(
                    "Merci de renseigner le nom du parent, "
                    "l'e-mail, le nom de l'élève et la matière."
)

st.caption(
    "Cours Hercule — Accompagnement scolaire personnalisé"
)
